// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
//
// SPDX-License-Identifier: GPL-2.0-or-later
//! This module provides utilities for fallbacks to the Python implementation of HGitaly.
//!
//! In other words, this module makes Pyhton HGitaly a sidecar of RHGitaly
use std::cmp::max;
use std::cmp::Ordering;
use std::collections::BTreeMap;
use std::ffi::{OsStr, OsString};
use std::fmt;
use std::io;
use std::os::unix::ffi::OsStrExt;
use std::path::PathBuf;
use std::process::ExitStatus;
use std::sync::Arc;
use std::time::{Duration, Instant};

use procfs::{page_size, process::Process, ProcResult};

use tokio::fs;
use tokio::net::UnixStream;
use tokio::process::{Child, Command};
use tokio::select;
use tokio::sync::{Mutex, RwLock};
use tokio::task::{JoinHandle, JoinSet};
use tokio::time::sleep;
use tokio_util::sync::CancellationToken;
use tonic::transport::{Channel, Endpoint, Error, Uri};
use tonic::{metadata::MetadataMap, Request, Status};
use tonic_health::pb::health_client::HealthClient;
use tonic_health::pb::{health_check_response, HealthCheckRequest};
use tower::service_fn;
use tracing::{debug, error, info, warn};

use crate::config::{Config, ServerAddress, SharedConfig, SidecarConfig, WorkerStartupConfig};
use crate::metadata::grpc_timeout;
use crate::process;

const SIDECAR_SOCKETS_RELATIVE_DIR: &str = "+hgitaly/sidecar";

use crate::config::parse_server_uri;

// All necessary state
//
// At this stage, the sidecar uses a full (prefork etc) HGitaly server so the
// state is made of a single channel.
#[derive(Debug)]
pub enum Servers {
    External(Server),
    ManagedPool(WorkersPool<WorkerImpl>),
}

#[derive(PartialEq, Eq, Copy, Clone)]
enum WorkerStatus {
    /// We are currently starting the worker
    Starting,
    /// The worker is fully ready (healthcheck passed)
    Idle,
    /// The worker is busy treating a request, until the givent [`Instant`] (worst case scenarui
    /// based on gRPC timeout
    Busy(u16, Instant),
    Terminating,
}

impl fmt::Debug for WorkerStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            WorkerStatus::Starting => f.write_str("Starting"),
            WorkerStatus::Idle => f.write_str("Idle"),
            WorkerStatus::Busy(count, deadline) => {
                let now = Instant::now();
                let deadline_in = if *deadline > now {
                    format!("{:?}", deadline.saturating_duration_since(now))
                } else {
                    format!("-{:?}", now.saturating_duration_since(*deadline))
                };

                f.debug_struct("Busy")
                    .field("count", count)
                    .field("deadline_in", &deadline_in)
                    .finish()
            }
            WorkerStatus::Terminating => f.write_str("Terminating"),
        }
    }
}

mod private {
    /// Used to make the Worker trait a sealed trait without the compiler warning
    /// that we are leaking private interfaces.
    ///
    /// The only purpose of this trait is to allow unit tests meant to work on scheduling
    /// avoid starting actual processes
    use std::io;
    use std::process::ExitStatus;

    use procfs::ProcResult;
    use tonic::{transport::Channel, Status};

    use crate::config::{SharedConfig, WorkerStartupConfig};

    /// Represents an HGitaly worker and allows sending it requests via Tonic [`Channel`]
    ///
    ///
    /// It has to be `'static`, which in practice means in this context to be
    /// owned.
    pub trait Worker: Sized + Send + Sync + 'static {
        /// Start the worker
        ///
        ///
        fn start(
            config: &SharedConfig,
            wid: usize,
        ) -> impl std::future::Future<Output = Result<Self, io::Error>> + Send;

        /// Opens all necessary connections and wait for worker to be ready
        fn wait_ready(
            &mut self,
            config: &WorkerStartupConfig,
        ) -> impl std::future::Future<Output = Result<(), Status>> + Send;

        /// Return `Some(opt_code)` if the worker has a dead process, `None` otherwise
        ///
        /// `opt_code` itself is an option because we may not be able to retrieve the
        /// exit code at this point.
        fn dead_process(&mut self) -> Option<Option<ExitStatus>>;

        fn terminate(self) -> impl std::future::Future<Output = ()> + Send;

        fn pid(&self) -> Option<i32>;

        /// Return the memory resident size for process given with pid.
        ///
        /// This is blocking (typically using `procfs`), hence cannot be a method on Worker
        /// instances, because these are typically held in an async call.
        /// In case of error, the pid is returned
        fn rss_mib(pid: i32) -> ProcResult<u64>;

        /// Clone the Channel
        ///
        /// Cloning channels is cheap and encouraged (see doc-comment for `Channel` struct).
        ///
        /// Panics if there is no Channel, as everything is designed so that
        /// this is called only on fully ready workers.
        fn clone_channel(&self) -> Channel;
    }
}

use private::Worker;

#[derive(Debug)]
/// Represents a [`Worker`] together with what we know about it.
///
/// The type is generic over the worker type so that we can write tests about it without
/// launching real processes.
pub struct ManagedWorker<W: Worker> {
    status: WorkerStatus,
    /// The gRPC Channel. It It can be `None` only if the status is
    /// `Starting` or `Terminating`.
    worker: Option<W>,
    /// The actual worker process.     process: Option<Child>,
    /// Used while busy to mark for shutdown after current request
    /// and thus avoid passing it new requests before shutdown is initiated (thus preventing
    /// race conditions).
    ///
    /// It will be used in next round, when the housekeeping thread starts shutting down workers
    /// with too large a RAM footprint
    shutdown_required: bool,
}

impl<W: Worker> Default for ManagedWorker<W> {
    fn default() -> Self {
        Self {
            status: WorkerStatus::Starting,
            worker: None,
            shutdown_required: false,
        }
    }
}

impl<W: Worker> ManagedWorker<W> {
    pub fn is_busy(&self) -> bool {
        matches!(self.status, WorkerStatus::Busy(_, _))
    }

    pub fn is_idle(&self) -> bool {
        self.status == WorkerStatus::Idle
    }

    pub fn is_terminating(&self) -> bool {
        self.status == WorkerStatus::Terminating
    }

    pub fn is_starting(&self) -> bool {
        self.status == WorkerStatus::Starting
    }

    pub fn pid(&self) -> Option<i32> {
        self.worker.as_ref().and_then(|w| w.pid())
    }
}

type UnlockedWorkersCollection<W> = BTreeMap<usize, ManagedWorker<W>>;

#[derive(Debug)]
pub struct WorkersPool<W: Worker> {
    /// We keep ManagedWorkers in a BTreeMap for simple access.
    ///
    /// Using a mapping type compared to the even simpler vector prevents confusing
    /// the worker id with its index in the vector (which would be constant because of
    /// restarts).
    /// Performance is not so much an issue as we expect the number of workers to be small.
    /// Still, it is more comfortable to have a direct access API rather than to resort
    /// to sequential scanning.
    ///
    /// This can change for
    config: SharedConfig,
    workers: Arc<RwLock<UnlockedWorkersCollection<W>>>,
    shutdown_token: CancellationToken,
}

impl<W: Worker> Clone for WorkersPool<W> {
    // derive could not do it
    fn clone(&self) -> Self {
        Self {
            config: self.config.clone(),
            workers: self.workers.clone(),
            shutdown_token: self.shutdown_token.clone(),
        }
    }
}

fn worker_sockets_dir(config: &Config) -> PathBuf {
    config.repositories_root.join(SIDECAR_SOCKETS_RELATIVE_DIR)
}

impl<W: Worker + 'static> WorkersPool<W> {
    pub fn new(
        config: &SharedConfig,
        shutdown_token: &CancellationToken,
    ) -> Result<Self, io::Error> {
        let shutdown_token = shutdown_token.clone();
        let workers = Arc::new(RwLock::new(UnlockedWorkersCollection::new()));
        let sockets_dir = worker_sockets_dir(config);
        // yes, this is sync, called from main()
        std::fs::create_dir_all(&sockets_dir).inspect_err(|e| {
            error!(
                "Could not ensure the existence of directory {} to host sockets: {e}",
                sockets_dir.display()
            )
        })?;

        Ok(Self {
            config: config.clone(),
            workers,
            shutdown_token,
        })
    }

    /// Perform some reading on the managed workers
    async fn with_workers<R>(&self, f: impl FnOnce(&UnlockedWorkersCollection<W>) -> R) -> R {
        let workers = self.workers.read().await;
        f(&workers)
    }

    /// Perform some mutation on the managed workers
    async fn with_workers_mut<R>(
        &self,
        f: impl FnOnce(&mut UnlockedWorkersCollection<W>) -> R,
    ) -> R {
        let mut workers = self.workers.write().await;
        f(&mut workers)
    }

    /// Add a worker, do not start it
    ///
    /// To be used while holding the lock, because callers such as [`maintain_pool_size`] will
    /// typically use it several times.
    /// The smallest available ID is assigned to the new worker
    fn add_worker(workers: &mut UnlockedWorkersCollection<W>) -> usize {
        let mut new_id = None;
        let mut prev_existing_id = 0;
        for (existing_id, _) in workers.iter() {
            if *existing_id - prev_existing_id > 1 {
                new_id = Some(prev_existing_id + 1);
            }
            prev_existing_id = *existing_id;
        }
        let new_id = new_id.unwrap_or_else(|| workers.len() + 1);

        debug!("Registered new worker with id {new_id}");
        workers.insert(new_id, ManagedWorker::default());
        new_id
    }

    /// Iterates on workers with given status, yielding shared references.
    ///
    /// Of course, pretty useless with busy workers, unless the deadline is known down to the
    /// nanosecond.
    fn iter_workers_with_status(
        workers: &UnlockedWorkersCollection<W>,
        status: WorkerStatus,
    ) -> impl Iterator<Item = (&usize, &ManagedWorker<W>)> {
        workers.iter().filter(move |(_id, mw)| mw.status == status)
    }

    /// Same as [`iter_workers_with_status`], yielding mutable references.
    fn iter_workers_with_status_mut(
        workers: &mut UnlockedWorkersCollection<W>,
        status: WorkerStatus,
    ) -> impl Iterator<Item = (&usize, &mut ManagedWorker<W>)> {
        workers
            .iter_mut()
            .filter(move |(_id, mw)| mw.status == status)
    }

    fn iter_idle_workers(
        workers: &UnlockedWorkersCollection<W>,
    ) -> impl Iterator<Item = (&usize, &ManagedWorker<W>)> {
        // Demonstrates how better it'd be to have a separate collection for idle workers
        Self::iter_workers_with_status(workers, WorkerStatus::Idle)
    }

    fn iter_idle_workers_mut(
        workers: &mut UnlockedWorkersCollection<W>,
    ) -> impl Iterator<Item = (&usize, &mut ManagedWorker<W>)> {
        // Demonstrates how better it'd be to have a separate collection for idle workers
        Self::iter_workers_with_status_mut(workers, WorkerStatus::Idle)
    }

    fn iter_idle_workers_to_shutdown_mut(
        workers: &mut UnlockedWorkersCollection<W>,
    ) -> impl Iterator<Item = (&usize, &mut ManagedWorker<W>)> {
        // Demonstrates how better it'd be to have a separate collection for idle workers
        workers
            .iter_mut()
            .filter(|(_id, mw)| mw.status == WorkerStatus::Idle && mw.shutdown_required)
    }

    /// Remove a worker
    ///
    /// Does not take care of actually stopping it.
    async fn rm_worker(&self, id: usize) {
        let mut managed_workers = self.workers.write().await;
        managed_workers.remove(&id);
    }

    /// Perform some mutation on the worker with given id
    ///
    /// The lock is held until the end of the mutation, so this is not for long processing
    async fn with_managed_worker<R>(
        &self,
        id: usize,
        f: impl FnOnce(Option<&mut ManagedWorker<W>>) -> R,
    ) -> R {
        let mut workers = self.workers.write().await;
        f(workers.get_mut(&id))
    }

    /// Start a registered managed worker
    ///
    async fn start_worker(&self, wid: usize) -> Result<(), Status> {
        let startup_config = self.config.sidecar.read().await.worker_startup.clone();

        // FAILED_PRECONDITION because we expect permanent problems to be more frequent
        // than transient ones (such as fds depleted etc)
        let mut worker = W::start(&self.config, wid).await.map_err(|e| {
            Status::failed_precondition(format!("Could not spawn HGitaly worker {wid}: {e:?}"))
        })?;

        worker.wait_ready(&startup_config).await?;
        let unregistered_worker = self
            .with_managed_worker(wid, |mw| {
                if let Some(mw) = mw {
                    debug!("Worker {wid} is now started, marking as Idle");
                    mw.status = WorkerStatus::Idle;
                    mw.worker = Some(worker);
                    None
                } else {
                    Some(worker)
                }
            })
            .await;

        if let Some(worker) = unregistered_worker {
            // if this happens, this is a bug.
            error!(
                "Worker {wid} unregistered while it was starting, have to terminate \
                   right away (pid={:?}).",
                worker.pid()
            );
            worker.terminate().await;
        }

        Ok(())
    }

    /// Spawn enough idle workers to reach `min_idle_workers`
    ///
    /// The lock is held just long enough to register the workers. A separate thread
    /// takes care of actually starting them and of waiting for readiness.
    async fn maintain_pool_size(&self) {
        let config = SidecarConfig::pool_config(&self.config.sidecar).await;

        let mut to_terminate_ids = self
            .with_workers_mut(|workers| {
                // making sure to allocate just once (must be fast since we are holding the lock)
                let mut to_terminate_ids = Vec::with_capacity(workers.len());
                for (id, w) in Self::iter_idle_workers_to_shutdown_mut(workers) {
                    to_terminate_ids.push(*id);
                    w.status = WorkerStatus::Terminating;
                }
                to_terminate_ids
            })
            .await;

        let mut to_spawn_ids = Vec::new();
        let min_idle = config.min_idle_workers as usize;
        let max_workers = config.max_workers as usize;

        while let Some(wid) = self
            .with_workers_mut(|workers| {
                let idle_count = to_spawn_ids.len()
                    + Self::iter_idle_workers(workers)
                        .filter(|(_, mw)| !mw.shutdown_required)
                        .count();
                if idle_count >= min_idle {
                    None
                } else if workers.len() < max_workers {
                    Some(Self::add_worker(workers))
                } else {
                    None
                }
            })
            .await
        {
            to_spawn_ids.push(wid);
        }

        let cloned = self.clone(); // cheap thanks to Arc, RwLock etc
        tokio::task::spawn(async move {
            let mut task_set = JoinSet::new();
            for wid in to_spawn_ids {
                let recloned = cloned.clone();
                task_set.spawn(async move {
                    if let Err(e) = recloned.start_worker(wid).await {
                        error!("Failed to start worker {wid}: {e}. Forgetting about it");
                        recloned.rm_worker(wid).await
                    }
                });
            }
            task_set.join_all().await;
        });

        let max_idle = config.max_idle_workers as usize;

        while let Some(wid) = self
            .with_workers_mut(|workers| {
                let idle_count = Self::iter_idle_workers(workers).count();

                if idle_count <= max_idle {
                    None
                } else if let Some((wid, worker)) = Self::iter_idle_workers_mut(workers).next() {
                    // terminating the smallest id is good enough for now: with the current
                    // worker id resuse, it is essentially random. This can be refined later
                    // (e.g., selecting the one with the highest RSS, either on the latests stats
                    // or by spawning a blocking thread to do the sorting)
                    info!(
                        "Idle workers count {idle_count} too high, \
                           marking worker {wid} for termination"
                    );

                    // immediately changing status so that it will not be listed in next iteration
                    worker.status = WorkerStatus::Terminating;
                    Some(*wid)
                } else {
                    None
                }
            })
            .await
        {
            to_terminate_ids.push(wid);
        }

        let cloned = self.clone(); // cheap thanks to Arc, RwLock etc
        tokio::task::spawn(async move {
            for wid in to_terminate_ids {
                cloned.terminate_worker(wid).await;
            }
        });
    }

    /// terminate and remove a managed worker
    async fn terminate_worker(&self, id: usize) {
        if let Some(worker) = self
            .with_managed_worker(id, |mw| {
                if let Some(mw) = mw {
                    mw.status = WorkerStatus::Terminating;
                    mw.worker.take()
                } else {
                    warn!("Terminating worker {id} not possible as it is not registered anymore");
                    None
                }
            })
            .await
        {
            info!("Terminating worker {id}");
            // TODO error treatment (in case of error, put the worker back so that it is not
            // dropped and we can try and recover)
            worker.terminate().await;
            self.rm_worker(id).await;
            info!("Worker {id} terminated, reaped and forgotten");
        }
        // else there is no `Worker`, meaning that some other task is taking care of
        // actual termination, hence why we do nothing
    }

    /// Goes over all workers, detect if some have been killed, reap and forget them if so
    ///
    /// Workers processes can disappear for reasons out of our control, the most extreme
    /// being the OOMKiller, despite all the efforts we are doing to keep the memory under
    /// control
    async fn check_workers_alive(&self) {
        // allocate only in exceptional case of dead workers
        let mut dead_worker_ids = Vec::new();
        self.with_workers_mut(|mws| {
            for (id, mw) in mws.iter_mut().filter(|(_, mw)| !mw.is_terminating()) {
                if let Some(worker) = mw.worker.as_mut() {
                    if let Some(death) = worker.dead_process() {
                        dead_worker_ids.push((*id, death))
                    }
                }
            }
        })
        .await;

        for (wid, death) in dead_worker_ids {
            let death_msg = death.map_or_else(
                || "exit status unknown".to_owned(),
                |code| format!("{code}"),
            );
            warn!("Worker {wid} exited unexpectedly ({death_msg}). Forgetting about it");
            self.rm_worker(wid).await;
        }
    }

    async fn reserve_and_then<R>(
        &self,
        for_timeout: Duration,
        and_then: impl FnOnce(usize, &W) -> R,
    ) -> Result<R, Status> {
        let deadline = Instant::now() + for_timeout;
        self.check_workers_alive().await;
        let res = self
            .with_workers_mut(|workers| {
                for (id, mw) in workers.iter_mut() {
                    if mw.status == WorkerStatus::Idle && !mw.shutdown_required {
                        mw.status = WorkerStatus::Busy(1, Instant::now() + for_timeout);
                        info!("Reserving worker {id} with timeout {for_timeout:?}");
                        return Ok(and_then(
                            *id,
                            mw.worker
                                .as_ref()
                                .expect("Available ManagedWorker should have a Worker"),
                        ));
                    }
                }

                info!("Could not find an idle worker, using a busy one to schedule request");
                // No idle worker, let's pile on the busy worker with the shortest deadline
                // TODO maybe start a worker if possible, that's generally speaking
                // a 400-500ms overhead, could be shorter (and safer) than using a busy worker.
                // But waiting for  startup should be done outside of this lock.
                //
                let mut selected_busy = None;
                for (id, mw) in workers.iter_mut() {
                    let prefer = if let WorkerStatus::Busy(count, deadline) = mw.status {
                        match selected_busy {
                            None => Some((count, deadline)),
                            Some((_id, ref _mw, _count, selected_deadline)) => {
                                if deadline < selected_deadline {
                                    Some((count, deadline))
                                } else {
                                    None
                                }
                            }
                        }
                    } else {
                        None
                    };
                    if let Some((count, deadline)) = prefer {
                        selected_busy = Some((id, mw, count, deadline));
                    }
                }

                if let Some((id, mw, count, selected_deadline)) = selected_busy {
                    let now = Instant::now();
                    warn!(
                        "Scheduling on worker {id} although status is {:?} \
                         new deadline in {:?}, original deadline was in {:?}",
                        mw.status,
                        deadline.saturating_duration_since(now),
                        selected_deadline.saturating_duration_since(now),
                    );
                    mw.status = WorkerStatus::Busy(count + 1, max(deadline, selected_deadline));
                    return Ok(and_then(
                        *id,
                        mw.worker
                            .as_ref()
                            .expect("Available ManagedWorker should have a Worker"),
                    ));
                }

                error!("Could not find a worker to schedule request");
                Err(Status::unavailable("No available worker"))
            })
            .await;

        self.maintain_pool_size().await;
        res
    }

    async fn mark_for_termination(&self, wid: usize) {
        info!("Marking worker {wid} for termination after current requests are handled");
        self.with_managed_worker(wid, |mut mw| {
            if let Some(mw) = mw.as_mut() {
                mw.shutdown_required = true;
            }
        })
        .await;
    }

    /// Sleeps the given amount of time or terminate workers in case of shutdown request.
    ///
    /// Returns `true` in case of shutdown, `false` otherwise
    async fn sleep_or_shutdown(&self, duration: Duration) -> bool {
        select! {
            _ = sleep(duration) => {false},
            _ = self.shutdown_token.cancelled() => {
                warn!("General shutdown required");
                // workers themselves shoudl have graceful shutdown, meaning
                // that they are supposed to finish current requests (with timeout)
                let mut to_terminate = Vec::new();
                self.with_workers_mut(|workers| {
                    for (wid, mw) in workers.iter_mut() {
                        mw.status = WorkerStatus::Terminating;
                        to_terminate.push(*wid);
                    }
                }).await;

                for wid in to_terminate {
                    self.terminate_worker(wid).await;
                }
                true
            },
        }
    }

    async fn statuses(&self) -> Vec<(usize, WorkerStatus, Option<i32>)> {
        self.with_workers(|workers| {
            workers
                .iter()
                .map(|(id, mw)| (*id, mw.status, mw.pid()))
                .collect()
        })
        .await
    }

    /// Return stats and ids of workers in error. This is not async
    fn complete_stats(
        statuses: Vec<(usize, WorkerStatus, Option<i32>)>,
    ) -> (Vec<WorkerStats>, Vec<usize>) {
        let mut stats = Vec::with_capacity(statuses.len());
        let mut errors = Vec::new();
        for (id, status, pid) in statuses {
            let res = pid.map_or(Ok(0), W::rss_mib);
            match res {
                Ok(rss_mib) => stats.push(WorkerStats {
                    id,
                    pid,
                    status,
                    rss_mib,
                }),
                Err(e) => {
                    // The process is supposed to be our child. Can happen only if it has died
                    // and its pid got reused since then.
                    error!(
                        "Could not get stats for process of Worker {id} with pid {pid:?}: {e}. \
                         It has likely died and the pid now belongs to some other process."
                    );
                    errors.push(id);
                }
            }
        }
        (stats, errors)
    }

    /// Mark as idle workers that are busy yet exceeded their deadlines.
    ///
    /// This is a line of last defense in case cancellation detection failed.
    /// Such workers would otherwise keep their `Busy` status forever, leading
    /// to starvation if this accumulates
    async fn cleanup_exceeded_deadlines(&self) {
        // Some margin to avoid it to happen by tight coincicence
        let a_sec_ago = Instant::now() - Duration::from_secs(1);

        self.with_workers_mut(|mws| {
            for (wid, mw) in mws.iter_mut() {
                if let WorkerStatus::Busy(_count, deadline) = mw.status {
                    if deadline < a_sec_ago {
                        warn!(
                            "Housekeeping: worker {wid} is Busy but missed its deadline. \
                             Marking it as Idle to unblock it."
                        );
                        mw.status = WorkerStatus::Idle;
                    }
                }
            }
        })
        .await;
    }

    async fn housekeeping_once(&self) {
        self.check_workers_alive().await;
        self.cleanup_exceeded_deadlines().await;

        let config = SidecarConfig::pool_config(&self.config.sidecar).await;

        let statuses = self.statuses().await;

        let (mut stats, errors) =
            match tokio::task::spawn_blocking(move || Self::complete_stats(statuses)).await {
                Err(e) => {
                    warn!("Task to read workers RSS aborted: {e}");
                    return;
                }
                Ok(ok) => ok,
            };

        for wid in errors {
            // the process is no longer ours for some reason (maybe killed and pid reused).
            // It makes no sense to try and terminate it, but we need to forget it.
            self.rm_worker(wid).await;
        }

        // because we count in MiB, we'll have rounding errors (not a problem)
        let mut total_rss: u64 = stats.iter().map(|s| s.rss_mib).sum();
        let max_rss = config.max_rss_mib as u64;
        info!(
            "Housekeeping thread: total RSS {total_rss}MiB (configured max {max_rss}MiB) \
                 dumping worker stats before tidying up: {stats:?}"
        );

        if total_rss > max_rss {
            warn!(
                "Total RSS {total_rss} is above threshold {max_rss}. \
                           Marking some workers for termination after they finish handling \
                           current requests."
            );
            stats.sort_by(|a, b| b.cmp_rss(a));
            for wstats in stats.iter() {
                if wstats.rss_mib == 0 {
                    warn!(
                        "All running workers are already marked for termination. \
                                   Likely cannot get back under max memory footprint {max_rss}"
                    );
                    break;
                }
                self.mark_for_termination(wstats.id).await;

                total_rss -= wstats.rss_mib;
                if total_rss < max_rss {
                    break;
                }
            }
        }

        self.maintain_pool_size().await;
    }

    pub fn start_housekeeping_thread(&self) -> JoinHandle<()> {
        let cloned = self.clone(); // cheap thanks to Arc, RwLock etc
        tokio::task::spawn(async move {
            loop {
                let interval = cloned
                    .config
                    .sidecar
                    .read()
                    .await
                    .housekeeping_interval_seconds as u64;
                info!("Housekeeping thread sleeping for {interval} seconds");

                if cloned
                    .sleep_or_shutdown(Duration::from_secs(interval))
                    .await
                {
                    return;
                }
                info!("Housekeeping thread waking up");
                cloned.housekeeping_once().await;
            }
        })
    }

    pub async fn available_channel(
        &self,
        for_timeout: Duration,
    ) -> Result<(usize, Channel), Status> {
        self.reserve_and_then(for_timeout, |id, w| (id, w.clone_channel()))
            .await
    }

    pub async fn release_worker(&self, id: usize) {
        self.with_managed_worker(id, |mw| {
            if let Some(mw) = mw {
                if let WorkerStatus::Busy(count, deadline) = mw.status {
                    if count > 1 {
                        info!("Decrementing business of worker {id} (was {:?}", mw.status);
                        mw.status = WorkerStatus::Busy(count - 1, deadline)
                    } else {
                        info!("Marking worker {id} as idle (was {:?})", mw.status);
                        mw.status = WorkerStatus::Idle
                    }
                } else {
                    mw.status = WorkerStatus::Idle
                }
            }
        })
        .await;
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct WorkerStats {
    id: usize,
    pid: Option<i32>,
    status: WorkerStatus,
    rss_mib: u64,
}

impl WorkerStats {
    fn cmp_rss(&self, other: &Self) -> Ordering {
        self.rss_mib.cmp(&other.rss_mib)
    }
}

#[derive(Debug)]
/// This is the actual HGitaly worker
pub struct WorkerImpl {
    socket_path: PathBuf,
    process: Option<Child>,
    channel: Option<Channel>,
}

impl WorkerImpl {
    async fn wait_open_channel(
        &mut self,
        config: &WorkerStartupConfig,
        deadline: Instant,
    ) -> Result<(), Error> {
        info!(
            "Connecting to sidecar Unix Domain socket at {}",
            self.socket_path.display()
        );

        let start = Instant::now();

        // used for logging, the reference is `deadline`.
        let timeout = config.readiness_timeout_ms;

        let startup_delay = Duration::from_millis(config.socket_check_every_ms.into());
        let connect_delay = Duration::from_millis(config.connect_check_every_ms.into());

        loop {
            match fs::metadata(&self.socket_path).await {
                Ok(_) => {
                    break;
                }
                _ => {
                    if Instant::now() > deadline {
                        error!(
                            "After worker startup, its socket {} did not appear in {timeout}ms",
                            self.socket_path.display(),
                        );
                        break; // Let tonic attempt to connect and return its error
                    }
                    debug!("Unix Domain socket not visible yet, sleeping for {startup_delay:?}");
                    sleep(startup_delay).await;
                }
            }
        }
        loop {
            // we need to give the path to the closure, which itself will need
            // to clone it to avoid giving it away to `connect` (and hence being only
            // `FnOnce`)
            let p = self.socket_path.clone();
            // TODO fake URL from example in tonic
            match Endpoint::try_from("http://[::]:50051")?
                .connect_with_connector(service_fn(move |_: Uri| UnixStream::connect(p.clone())))
                .await
            {
                Ok(channel) => {
                    info!(
                        "Connected to worker at {} after {:?}",
                        self.socket_path.display(),
                        Instant::now() - start
                    );
                    self.channel = Some(channel);
                    break;
                }
                Err(e) => {
                    if Instant::now() > deadline {
                        error!(
                            "After startup of worker on socket {}, could not connect \
                               in {timeout}ms",
                            self.socket_path.display(),
                        );
                        return Err(e);
                    }
                    sleep(connect_delay).await;
                }
            }
        }
        Ok(())
    }

    async fn health_check(&self) -> bool {
        let channel = self.clone_channel();

        let mut health_client = HealthClient::new(channel);
        health_client
            .check(Request::new(HealthCheckRequest::default()))
            .await
            .is_ok_and(|resp| {
                resp.get_ref().status == health_check_response::ServingStatus::Serving as i32
            })
    }

    async fn wait_health_check(
        &self,
        deadline: Instant,
        full_timeout: Duration,
    ) -> Result<(), Status> {
        info!(
            "Waiting for HealthCheck of Worker on socket {}",
            self.socket_path.display()
        );
        let start = Instant::now();
        let timeout = deadline.saturating_duration_since(Instant::now());
        select! {
            _ = sleep(timeout) => {
                Err(Status::unavailable(format!(
                    "Worker expected to respond on socket {} did not pass \
                     health check after {:?} total startup time",
                    self.socket_path.display(), full_timeout)))
            },
            healthy = self.health_check() => {
                if healthy {
                    let elapsed = Instant::now() - start;
                    // Duration Debug formatting is nicely human-readable, with unit
                    info!(
                        "Worker on socket {} healthy after {elapsed:?}",
                        self.socket_path.display()
                    );
                    Ok(())
                }
                else {
                    Err(Status::unavailable(format!(
                        "Worker responding on socket {} returned a bad health check result",
                        self.socket_path.display())))
                }
            }
        }
    }
}

impl Worker for WorkerImpl {
    async fn start(config: &SharedConfig, wid: usize) -> Result<Self, io::Error> {
        let mut socket_path = worker_sockets_dir(config);
        socket_path.push(format!("hgitaly-worker-{wid}.socket"));

        // Ensure there is no lingering file at socket_path
        match fs::remove_file(&socket_path).await {
            Err(e) => {
                if e.kind() == io::ErrorKind::NotFound {
                    Ok(())
                } else {
                    Err(e)
                }
            }
            ok => ok,
        }?;

        let mut cmd = Command::new(&config.hg_executable);
        // The hgitaly extension is currently not activated in Omnibus by default
        cmd.args([
            "--config",
            "extensions.hgitaly=",
            "hgitaly-serve",
            "--mono-process",
            "--client-id-file-name",
            &format!("managed-worker-{wid}.client-id"),
            "--listen",
        ]);
        let socket_path_ref = socket_path.as_os_str();
        let mut socket_arg = OsString::with_capacity(socket_path_ref.len() + 5);
        socket_arg.push("unix:");
        socket_arg.push(socket_path_ref);
        cmd.arg(&socket_arg);
        if let Some(hgrc_path) = &config.hgrc_path {
            cmd.env(OsStr::from_bytes(b"HGRCPATH"), hgrc_path.clone());
        }
        info!("Starting new worker on {}", socket_path.display());
        debug!("Starting worker with command {cmd:?}");
        let child = cmd.spawn()?;
        Ok(Self {
            socket_path,
            process: Some(child),
            channel: None,
        })
    }

    async fn wait_ready(&mut self, config: &WorkerStartupConfig) -> Result<(), Status> {
        let timeout = Duration::from_millis(config.readiness_timeout_ms.into());
        let deadline = Instant::now() + timeout;
        self.wait_open_channel(config, deadline)
            .await
            .map_err(|e| {
                Status::failed_precondition(format!(
                    "Could not open channel to worker at {}: {e}. Failed to start?",
                    self.socket_path.display()
                ))
            })?;
        self.wait_health_check(deadline, timeout).await
    }

    async fn terminate(self) {
        if let Some(mut child) = self.process {
            process::terminate(&mut child).await
        }
    }

    fn dead_process(&mut self) -> Option<Option<ExitStatus>> {
        if let Some(p) = self.process.as_mut() {
            match p.try_wait() {
                Err(e) => {
                    warn!("Got error polling process to check if dead: {e}");
                    Some(None)
                }
                Ok(None) => None,
                Ok(some_code) => Some(some_code),
            }
        } else {
            None
        }
    }

    fn clone_channel(&self) -> Channel {
        self.channel
            .as_ref()
            .expect("Should be called only on workers with an established connection")
            .clone()
    }

    fn pid(&self) -> Option<i32> {
        // procfs wants i32, but we should avoid panics and question ourselves about
        // portability (`nix` would use pid_t)
        self.process
            .as_ref()
            .and_then(|child| child.id().map(|u| u as i32))
    }

    fn rss_mib(pid: i32) -> ProcResult<u64> {
        Ok((Process::new(pid)?.stat()?.rss * page_size()) >> 20)
    }
}

// A single server.
//
// Can be used with external servers able of concurrency as well as for managed workers
#[derive(Debug)]
pub struct Server {
    address: ServerAddress,
    channel: Mutex<Option<Channel>>,
}

impl Servers {
    /// Async to read the sidecar config, which is somewhat inelegant but good enough
    /// for the time being and to be revised if we want reloads to switch back and
    /// forth between managed and not.
    pub async fn new(
        config: &SharedConfig,
        shutdown_token: &CancellationToken,
    ) -> Result<Self, io::Error> {
        let sidecar_config = config.sidecar.read().await;
        if sidecar_config.managed {
            Ok(Self::ManagedPool(WorkersPool::new(config, shutdown_token)?))
        } else {
            Ok(Self::External(Server {
                address: parse_server_uri(&sidecar_config.address)
                    .expect("Could not parse sidecar URL"),
                channel: None.into(),
            }))
        }
    }

    pub async fn initial_launch(&mut self) -> Option<JoinHandle<()>> {
        if let Self::ManagedPool(ref mut pool) = self {
            pool.maintain_pool_size().await;
            Some(pool.start_housekeeping_thread())
        } else {
            None
        }
    }

    /// Selects an available worker and returns its id and a channel.
    pub async fn available_channel(
        &self,
        for_timeout: Duration,
    ) -> Result<(usize, Channel), Status> {
        match self {
            Self::External(server) => server.available_channel().await.map(|chan| (0, chan)),
            Self::ManagedPool(pool) => pool.available_channel(for_timeout).await,
        }
    }

    /// Record that worker is no longer busy
    ///
    /// This allows the worker to take requests again.
    pub async fn release_worker(&self, id: usize) {
        if let Self::ManagedPool(pool) = self {
            pool.release_worker(id).await
        }
    }
}

impl Server {
    async fn open_channel(&self) -> Result<Channel, Error> {
        Ok(match &self.address {
            ServerAddress::URI(uri) => {
                info!("Connecting to sidecar URI {}", uri);

                Endpoint::try_from(uri.clone())?.connect().await?
            }
            ServerAddress::Unix(path) => {
                info!(
                    "Connecting to sidecar Unix Domain socket at {}",
                    path.display()
                );

                // we need to give the path to the closure, which itself will need
                // to clone it to avoid giving it away to `connect` (and hence being only
                // `FnOnce`)
                let p = path.clone();
                // TODO fake URL from example in tonic, we should get rid of it
                // if this code persists when `Servers` becomes a pool of managed processes.
                Endpoint::try_from("http://[::]:50051")?
                    .connect_with_connector(service_fn(move |_: Uri| {
                        UnixStream::connect(p.clone())
                    }))
                    .await?
            }
        })
    }

    pub async fn available_channel(&self) -> Result<Channel, Status> {
        let mut lock = self.channel.lock().await;
        let chan = match &*lock {
            None => {
                let chan = self.open_channel().await.map_err(|e| {
                    Status::internal(format!(
                        "Could not connect to HGitaly (Python) sidecar: {}",
                        e
                    ))
                })?;

                // Cloning channel is cheap and encouraged (see doc-comment for `Channel` struct)
                *lock = Some(chan.clone());
                chan
            }
            Some(chan) => chan.clone(),
        };
        Ok(chan)
    }
}

/// Helper for gRPC timeout with a default value
///
/// In a full instance, the default timeout is used only with some requests from Workhorse.
/// Indeed, GitLab always sends a timeout (`GitalyClient.call` has a default value for its
/// `timeout` argument).
/// The case we spotted from Workhorse is `GetArchive`. We need the timeout to account for
/// the large repositories around. (TODO make configurable)
pub fn grpc_timeout_or(md: &MetadataMap) -> Duration {
    grpc_timeout(md).unwrap_or(Duration::from_secs(300))
}

macro_rules! unary {
    ($self:ident, $request:ident, $client_class:ident, $meth:ident) => {{
        let task_token = tokio_util::sync::CancellationToken::new();
        let _drop_guard = task_token.clone().drop_guard();
        let sidecar = $self.sidecar_servers.clone();
        let sub_span = tracing::info_span!(
            "sidecar::unary!",
            sidecar_id = &format!("{:x}", rand::random::<u32>()),
            worker_id = tracing::field::Empty
        );

        // Using a separate task to clean up on cancellation (main task is simply dropped).
        tokio::task::spawn(
            async move {
                let timeout = crate::sidecar::grpc_timeout_or($request.metadata());
                let (wid, channel) = sidecar.available_channel(timeout).await.map_err(|e| {
                    Status::internal(format!("Could not initiate the sidecar channel: {}", e))
                })?;
                let current_span = tracing::Span::current();
                current_span.record("worker_id", wid);
                let mut client = $client_class::new(channel);

                let res = tokio::select! {
                    res = client.$meth($request) => res,
                    _ = task_token.cancelled() => {
                        tracing::warn!("task cancelled");
                        // TODO check if us dropping the task is enough to send cancellation
                        // to the client.
                        Err(tonic::Status::cancelled(
                            "Unary task dropped, probably due to client-side cancellation"
                        ))
                    },
                };
                sidecar.release_worker(wid).await;
                res
            }
            .instrument(sub_span),
        )
        .await
        .map_err(|e| tonic::Status::internal(format!("Unary task aborted: {e}")))?
    }};
}

macro_rules! server_streaming {
    ($self:ident, $request:ident, $client_class:ident, $meth:ident) => {{
        // on each service `sidecar_servers` is an `Arc<_>`
        let timeout = crate::sidecar::grpc_timeout_or($request.metadata());
        let sidecar = $self.sidecar_servers.clone();

        let (tx, rx) = tokio::sync::mpsc::channel(1);
        let sub_span = tracing::info_span!(
            "sidecar::server_streaming!",
            sidecar_id = &format!("{:x}", rand::random::<u32>()),
            worker_id = tracing::field::Empty
        );

        tokio::task::spawn(async move {
            let start = std::time::Instant::now();
            let (wid, channel) = sidecar.available_channel(timeout).await?;
            let current_span = tracing::Span::current();
            current_span.record("worker_id", wid);

            tokio::task::spawn(
                async move {
                    let mut client = $client_class::new(channel);
                    let elapsed = std::time::Instant::now() - start;
                    let remaining_timeout = timeout.saturating_sub(elapsed);
                    let mut stream = tokio::select! {
                        resp = client.$meth($request) => {
                            match resp {
                                Err(e) => {
                                    let _ = tx.send(Err(e)).await;
                                    tracing::info!("error from client at initial call");
                                    sidecar.release_worker(wid).await;
                                    return;
                                },
                                Ok(resp) => resp
                            }
                        },
                        _ = tokio::time::sleep(remaining_timeout) => {
                            tracing::info!("timeout detected on our side");
                            sidecar.release_worker(wid).await;
                            let _ = tx.send(Err(tonic::Status::deadline_exceeded(
                                "Timeout detected by RHGitaly sidecar at initial call"
                            ))).await;
                            return;
                        },
                        _ = tx.closed() => {
                            tracing::info!(
                                "Request cancelled at initial call (mpsc Receiver dropped)"
                            );
                            sidecar.release_worker(wid).await;
                            // TODO check if us dropping the task is enough to send cancellation
                            // to the client.
                            let _ = tx.send(Err(tonic::Status::cancelled(
                                "Server streaming task dropped, probably due to \
                                 client-side cancellation"
                            ))).await;
                            return;
                        },
                    }
                    .into_inner();

                    loop {
                        let elapsed = std::time::Instant::now() - start;
                        let remaining_timeout = timeout.saturating_sub(elapsed);
                        tokio::select! {
                            _ = tokio::time::sleep(remaining_timeout) => {
                                tracing::warn!("Timeout detected on our side \
                                                while waiting for worker gRPC messages");
                                let _ = tx.send(Err(tonic::Status::deadline_exceeded(
                                    "Timeout detected by RHGitaly sidecar after initial response"
                                ))).await;
                                break;
                            },
                            _ = tx.closed() => {
                                tracing::warn!(
                                    "Request cancelled  (mpsc receiver dropped) \
                                        while listening for worker messages");
                                break;

                            },
                            msg = stream.message() => match msg {
                                Ok(None) => {
                                    tracing::info!("Request normal completion");
                                    break;
                                }
                                Err(e) => {
                                    tracing::info!("Sending back error {}", &e);
                                    if tx.send(Err(e)).await.is_err() {
                                        // We have no other choice, info! because it is
                                        // not unexpected
                                        tracing::info!(
                                            "mpsc Receiver already dropped when sending back \
                                                a gRPC error from worker to our client "
                                        );
                                    }
                                    break;
                                }
                                Ok(Some(resp)) => {
                                    tracing::debug!("Sending back a response message");
                                    if tx.send(Ok(resp)).await.is_err() {
                                        // The Receiver has been dropped, which means that the
                                        // request is cancelled from the client side.
                                        tracing::warn!(
                                            "Task cancelled after start of streaming back \
                                             to our client (mpsc receiver dropped)"
                                        );
                                        break;
                                    }
                                }
                            }
                        }
                    }
                    sidecar.release_worker(wid).await;
                }
                .instrument(current_span),
            );
            Result::<(), tonic::Status>::Ok(())
        }
        .instrument(sub_span),
        )
        .await
        .map_err(|e| {
            tracing::warn!("sidecar::server_streaming got task joining error: {e}");
            tonic::Status::internal(format!("Server streaming task aborted: {e}"))
        })??;

        Ok(Response::new(Box::pin(
            tokio_stream::wrappers::ReceiverStream::new(rx),
        )))
    }};
}

macro_rules! client_streaming {
    ($self:ident, $request:ident, $client_class:ident, $meth:ident) => {{
        let timeout = crate::sidecar::grpc_timeout_or($request.metadata());

        let (metadata, extensions, inner) = $request.into_parts();
        let (tx, mut rx) = tokio::sync::mpsc::channel(1);
        let _keeping_open = tx.clone();

        let sub_span = tracing::info_span!(
            "sidecar::client_streaming!",
            sidecar_id = &format!("{:x}", rand::random::<u32>()),
            worker_id = tracing::field::Empty
        );

        let transmit = inner
            .filter(move |req| match req {
                Err(e) => {
                    let tx = tx.clone();
                    let e = e.clone();
                    tracing::info!("Got client stream error {}", e);
                    tokio::task::spawn(async move {
                        if tx.send(e).await.is_err() {
                            // We have no other choice
                            tracing::warn!(
                                "mpsc receiver already dropped when sending back \
                                  an error streaming client request"
                            );
                        }
                    });
                    false
                }
                _ => true,
            })
            .map(|res| res.expect("Error cases should already have been filtered out"));

        let task_token = tokio_util::sync::CancellationToken::new();
        let _drop_guard = task_token.clone().drop_guard();
        let sidecar = $self.sidecar_servers.clone();

        // Using a separate task to clean up on cancellation (main task is simply dropped).
        tokio::task::spawn(async move {
            let (wid, channel) = sidecar.available_channel(timeout).await?;
            let current_span = tracing::Span::current();
            current_span.record("worker_id", wid);
            let mut client = $client_class::new(channel);

            let res = tokio::select! {
                err = rx.recv() => {
                    Err(err.unwrap_or_else(
                        || Status::internal("Unexpected closing of inner channel for errors")))
                },
                resp = client.$meth(tonic::Request::from_parts(metadata, extensions, transmit)) =>
                    resp,
                _ = task_token.cancelled() => {
                    tracing::warn!("Client-streaming task cancelled");
                    // Did check using hgitaly-load script that us dropping the task is
                    // enough to send cancellation to the client, but how to make it an
                    // automated test?
                    Err(tonic::Status::cancelled(
                        "Client-streaming task dropped, probably due to client-side cancellation"
                    ))
                }
            };
            sidecar.release_worker(wid).await;
            res
        }.instrument(sub_span))
        .await
        .map_err(|e| {
            tonic::Status::internal(format!(
                "Internal task for client-streaming request aborted: {e}"
            ))
        })?
    }};
}

macro_rules! fallback {
    ($fallback_macro:ident, $wrapper_macro: ident,
     $self:ident, $inner_meth:ident,
     $request:ident, $client_class:ident, $meth:ident) => {{
        let (metadata, extensions, inner) = $request.into_parts();

        let corr_id = correlation_id(&metadata);
        let result = $self.$inner_meth(&inner, corr_id, &metadata).await;
        if let Err(status) = result {
            if status.code() != tonic::Code::Unimplemented {
                return Err(status);
            } else {
                let mut details = status.message();
                if details.is_empty() {
                    details = "no details";
                }
                tracing::info!(
                    "Falling back to sidecar, correlation_id={:?}, method={}, \
                     reason: not implemented in Rust ({})",
                    corr_id,
                    stringify!($meth),
                    details,
                );
                let request = Request::from_parts(metadata, extensions, inner);
                crate::sidecar::$fallback_macro!($self, request, $client_class, $meth)
            }
        } else {
            crate::sidecar::$wrapper_macro!(result)
        }
    }};
}

macro_rules! resp_wrap {
    ($res:ident) => {
        $res.map(Response::new)
    };
}

macro_rules! no_resp_wrap {
    ($res:ident) => {
        $res
    };
}

macro_rules! fallback_unary {
    ($($args:ident),*) => { crate::sidecar::fallback!(unary, resp_wrap $(,$args)*) };
}

macro_rules! fallback_server_streaming {
    ($($args:ident),*) => { crate::sidecar::fallback!(server_streaming, no_resp_wrap $(,$args)*) };
}

// TODO fallback_client_streaming

// make visible to other modules
pub(crate) use {
    client_streaming, fallback, fallback_server_streaming, fallback_unary, no_resp_wrap, resp_wrap,
    server_streaming, unary,
};

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{Config, SidecarConfig};

    const DURATION_10_MS: Duration = Duration::from_millis(10);

    #[allow(dead_code)]
    #[derive(Debug)]
    struct FakeWorker {
        pid: Option<i32>,
    }
    type TestingPool = WorkersPool<FakeWorker>;

    const LARGE_RSS_PID: i32 = 2;
    const MEDIUM_RSS_PID: i32 = 1;

    impl Worker for FakeWorker {
        #[allow(unused_variables)]
        async fn start(config: &SharedConfig, wid: usize) -> Result<Self, io::Error> {
            Ok(Self { pid: None })
        }
        fn pid(&self) -> Option<i32> {
            self.pid
        }
        fn dead_process(&mut self) -> Option<Option<ExitStatus>> {
            None
        }
        fn rss_mib(pid: i32) -> ProcResult<u64> {
            // keeping a dynamic global mapping based on pid in tests would be tedious.
            // instead, the memory usage tests will set the pids on workers, and we'll use
            // fixed associated values:
            Ok(match pid {
                MEDIUM_RSS_PID => 257,
                LARGE_RSS_PID => 513,
                _ => 80, // rough size of actual HGitaly processes right after startup
            })
        }
        async fn wait_ready(&mut self, _config: &WorkerStartupConfig) -> Result<(), Status> {
            sleep(DURATION_10_MS).await;
            Ok(())
        }
        async fn terminate(self) {
            sleep(DURATION_10_MS).await
        }
        fn clone_channel(&self) -> Channel {
            unimplemented!("Not in tests!");
        }
    }

    fn make_pool(max_workers: u16) -> TestingPool {
        let config = Arc::new(Config {
            sidecar: SidecarConfig {
                min_idle_workers: 1,
                max_idle_workers: 1,
                max_workers,
                max_rss_mib: 512,
                ..Default::default()
            }
            .into(),
            ..Default::default()
        });
        let shutdown_token = CancellationToken::new();
        return WorkersPool::new(&config, &shutdown_token).unwrap();
    }

    async fn worker_ids(pool: &TestingPool) -> Vec<usize> {
        pool.with_workers(|workers| workers.iter().map(|(id, _w)| id).cloned().collect())
            .await
    }

    async fn starting_worker_ids(pool: &TestingPool) -> Vec<usize> {
        pool.with_workers(|workers| {
            TestingPool::iter_workers_with_status(workers, WorkerStatus::Starting)
                .map(|(id, _w)| id)
                .cloned()
                .collect()
        })
        .await
    }

    async fn worker_business_count(pool: &TestingPool, wid: usize) -> u16 {
        pool.with_managed_worker(wid, |mw| {
            if let WorkerStatus::Busy(count, _) = mw.unwrap().status {
                count
            } else {
                0
            }
        })
        .await
    }

    async fn assert_managed_worker(
        pool: &TestingPool,
        wid: usize,
        f: impl FnOnce(&ManagedWorker<FakeWorker>) -> bool,
    ) {
        assert!(pool.with_managed_worker(wid, |opt| f(opt.unwrap())).await);
    }

    /// Wait for [`ManagedWorker`] status field to be as expected.
    ///
    /// This is not to be confused with [`Worker`] primitives that are waiting
    /// for some condition to be met, in order to update the status.
    ///
    /// This is implemented in tests only because it is generally a bad idea to wait for
    /// a given status in main code:
    ///
    /// - usually we don't want to wait, precisely. An example would be at startup : we need
    ///   RHGitaly to be able to handle requests as fast as possible. Most of them will not
    ///   need the sidecar
    /// - a worker can switch to the given status and then to some other one in an impredictable
    ///   way in a live system with incoming requests (Starting -> Idle -> Busy), thus defeating
    ///   the purpose.
    async fn wait_worker_status(pool: &TestingPool, wid: usize, status: WorkerStatus) {
        let mut count = 0;
        loop {
            let actual_status = pool.with_managed_worker(wid, |mw| mw.unwrap().status).await;

            if actual_status == status {
                break;
            }
            count += 1;
            if count > 10 {
                panic!("Worker {wid} status {actual_status:?} is not the expected {status:?}");
            }
            sleep(DURATION_10_MS).await;
        }
    }

    async fn assert_wait_worker_dropped(pool: &TestingPool, wid: usize) {
        let mut count = 0;
        loop {
            if !pool
                .with_workers(|workers| workers.contains_key(&wid))
                .await
            {
                break;
            }
            count += 1;
            if count > 10 {
                panic!("Worker {wid} still not dropped");
            }
            sleep(DURATION_10_MS).await;
        }
    }

    async fn set_worker_pid(pool: &TestingPool, wid: usize, pid: i32) {
        pool.with_managed_worker(wid, |mut mw| {
            mw.as_mut().unwrap().worker.as_mut().unwrap().pid = Some(pid)
        })
        .await;
    }

    async fn set_worker_status(pool: &TestingPool, wid: usize, status: WorkerStatus) {
        pool.with_managed_worker(wid, |mut mw| mw.as_mut().unwrap().status = status)
            .await;
    }

    async fn stats(pool: &TestingPool) -> Vec<WorkerStats> {
        let statuses = pool.statuses().await;
        let (stats, _errors) =
            tokio::task::spawn_blocking(move || TestingPool::complete_stats(statuses))
                .await
                .unwrap();
        stats
    }

    #[tokio::test]
    async fn test_reserve_use_busy() -> Result<(), Status> {
        let pool = make_pool(2);

        // The pool size maintainer starts the required (min_idle=1) worker, and does not wait
        // for its readiness.
        pool.maintain_pool_size().await;
        assert_eq!(starting_worker_ids(&pool).await, [1]);

        // Wait for worker 1 readiness and reserve it
        wait_worker_status(&pool, 1, WorkerStatus::Idle).await;
        let w1_id = pool.reserve_and_then(DURATION_10_MS, |id, _w| id).await?;
        assert_eq!(w1_id, 1);

        // Worker 1 is now busy and a new worker started immediately in a background task to
        // honour min_idle=1, since max_idle is not reached.
        assert_managed_worker(&pool, 1, |w| w.is_busy()).await;
        assert_eq!(worker_ids(&pool).await, [1, 2]);

        // Let's wait for worker 2 to be ready. Of course it gets chosen for a new request
        wait_worker_status(&pool, 2, WorkerStatus::Idle).await;
        assert_eq!(pool.reserve_and_then(DURATION_10_MS, |id, _w| id).await?, 2);

        // When the third request arrives, both workers are busy, and we've reached the maximum,
        // so one of the two workers is reused and its business is now 2
        let req3_wid = pool.reserve_and_then(DURATION_10_MS, |id, _w| id).await?;
        assert!(req3_wid < 3);
        assert_eq!(worker_business_count(&pool, req3_wid).await, 2);

        // Releasing completely a worker
        pool.release_worker(req3_wid).await;
        pool.release_worker(req3_wid).await;
        assert_managed_worker(&pool, req3_wid, |w| w.is_idle()).await;

        Ok(())
    }

    #[tokio::test]
    async fn test_housekeeping_deadline_exceeded() -> Result<(), Status> {
        let pool = make_pool(1);

        pool.maintain_pool_size().await;
        assert_eq!(starting_worker_ids(&pool).await, [1]);
        wait_worker_status(&pool, 1, WorkerStatus::Idle).await;

        set_worker_status(
            &pool,
            1,
            WorkerStatus::Busy(1, Instant::now() - Duration::from_secs(10)),
        )
        .await;
        pool.housekeeping_once().await;
        assert_managed_worker(&pool, 1, |w| w.is_idle()).await;

        // the worker can now be normally used and of course housekeeping does not
        // bring it back to Idle
        let w1_id = pool.reserve_and_then(DURATION_10_MS, |id, _w| id).await?;
        assert_eq!(w1_id, 1);
        assert_managed_worker(&pool, 1, |w| w.is_busy()).await;
        pool.housekeeping_once().await;
        assert_managed_worker(&pool, 1, |w| w.is_busy()).await;

        Ok(())
    }

    #[tokio::test]
    async fn test_memory_footprint() -> Result<(), Status> {
        let pool = make_pool(3);

        pool.maintain_pool_size().await;
        wait_worker_status(&pool, 1, WorkerStatus::Idle).await;

        // just demonstrating how to set memory footprint from tests
        // (waiting for actual memory-based management and its tests).
        set_worker_pid(&pool, 1, LARGE_RSS_PID).await;
        // checking that it worked.
        assert_eq!(
            stats(&pool).await,
            vec![WorkerStats {
                id: 1,
                pid: Some(LARGE_RSS_PID),
                status: WorkerStatus::Idle,
                rss_mib: 513,
            }]
        );

        // The total memory footprint being above threshold, worker 1 is selected for shutdown.
        // Being Idle, it transitions to Terminating right away and a new worker is starting.
        pool.housekeeping_once().await;
        assert_managed_worker(&pool, 1, |w| w.is_terminating()).await;
        assert_eq!(worker_ids(&pool).await, [1, 2]);
        wait_worker_status(&pool, 2, WorkerStatus::Idle).await;
        // after a while the first worker is terminated and dropped
        assert_wait_worker_dropped(&pool, 1).await;
        assert_eq!(worker_ids(&pool).await, [2]);

        // Now worker 2 is treating a request and total RSS goes above threshold before the call
        // is finished. Housekeeping will only flag it for later shutdown.
        assert_eq!(pool.reserve_and_then(DURATION_10_MS, |id, _w| id).await?, 2);
        set_worker_pid(&pool, 2, LARGE_RSS_PID).await;
        assert_eq!(worker_ids(&pool).await, [1, 2]);
        // Run housekeeping once worker 1 is fully started, so that it does not launch a new one.
        wait_worker_status(&pool, 1, WorkerStatus::Idle).await;
        pool.housekeeping_once().await;

        assert_managed_worker(&pool, 2, |w| w.is_busy() && w.shutdown_required).await;
        // After its RPC is done, no request can be handled by worker 2, hence they all go
        // to worker 1. To prove it, let's mark worker 1 as already busy (deadline does not matter)
        set_worker_status(&pool, 1, WorkerStatus::Busy(1, Instant::now())).await;
        pool.release_worker(2).await;
        assert_managed_worker(&pool, 2, |w| w.is_idle() && w.shutdown_required).await;
        assert_eq!(pool.reserve_and_then(DURATION_10_MS, |id, _w| id).await?, 1);
        // reservation happened on worker 1 despite worker 2 being idle. It also triggered the
        // pool size maintenance, marking worker 2 for termination and launching worker 3.
        assert_managed_worker(&pool, 2, |w| w.is_terminating()).await;
        assert_eq!(worker_business_count(&pool, 1).await, 2);
        assert_managed_worker(&pool, 3, |w| w.is_starting()).await;
        // finish startups and terminations. Worker 1 is still busy
        wait_worker_status(&pool, 3, WorkerStatus::Idle).await;
        assert_wait_worker_dropped(&pool, 2).await;

        // Now worker 3 goes over limit, worker 1 grows a bit. The housekeeping will
        // choose to terminate worker 3, because it is enough to get back under limits.
        // In the end, worker 2 is added back to the pool.
        set_worker_pid(&pool, 3, LARGE_RSS_PID).await;
        set_worker_pid(&pool, 1, MEDIUM_RSS_PID).await;
        pool.housekeeping_once().await; // will launch a new worker, since worker 3 is busy
        assert_managed_worker(&pool, 3, |w| w.shutdown_required).await;
        assert_managed_worker(&pool, 1, |w| !w.shutdown_required).await;
        assert_eq!(worker_ids(&pool).await, [1, 2, 3]);
        assert_wait_worker_dropped(&pool, 3).await;

        // Finally both workers grow so that releasing just one is not enough to get back
        // under memory threshold. This time, the housekeeping thread will mark both for shutdown
        wait_worker_status(&pool, 2, WorkerStatus::Idle).await;
        set_worker_pid(&pool, 2, LARGE_RSS_PID).await;
        set_worker_pid(&pool, 1, LARGE_RSS_PID).await;
        pool.housekeeping_once().await; // will launch a new worker, since worker 1 is busy

        assert_eq!(worker_ids(&pool).await, [1, 2, 3]);
        assert_managed_worker(&pool, 1, |w| w.shutdown_required).await;
        assert_managed_worker(&pool, 2, |w| w.is_terminating()).await;
        // and we have to release worker 1 for it to be finally shut down
        pool.release_worker(1).await;
        pool.release_worker(1).await;
        wait_worker_status(&pool, 3, WorkerStatus::Idle).await;
        assert_eq!(pool.reserve_and_then(DURATION_10_MS, |id, _w| id).await?, 3);
        // we have evenutally two workers: 3 (Busy) and a new Idle one. It's hard to
        // guess which id will get recycled, so let's wait enough and inspect.
        sleep(Duration::from_millis(30)).await;
        let worker_ids = worker_ids(&pool).await;
        assert_eq!(worker_ids.len(), 2);
        let new_idle = worker_ids[0];

        assert_managed_worker(&pool, 3, |w| w.is_busy()).await;
        assert_eq!(
            stats(&pool)
                .await
                .into_iter()
                .map(|st| (st.id, st.status, st.rss_mib))
                .next(),
            Some((new_idle, WorkerStatus::Idle, 0))
        );
        Ok(())
    }
}
