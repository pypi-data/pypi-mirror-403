// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use clap::Parser;
use std::path::PathBuf;
use std::sync::Arc;

use tokio::fs::remove_file;
use tokio::net::UnixListener;
use tokio::select;
use tokio::sync::broadcast;
use tokio::task::JoinError;
use tokio_stream::wrappers::UnixListenerStream;
use tonic::transport::Server;

use rhgitaly::config::{BindAddress, Config, FileConfig, LoggingConfig};
use rhgitaly::hgweb;
use rhgitaly::license::load_license_nicknames;
use rhgitaly::service::analysis::analysis_server;
use rhgitaly::service::blob::blob_server;
use rhgitaly::service::commit::commit_server;
use rhgitaly::service::diff::diff_server;
use rhgitaly::service::health::health_server;
use rhgitaly::service::mercurial_aux_git::mercurial_aux_git_server;
use rhgitaly::service::mercurial_changeset::mercurial_changeset_server;
use rhgitaly::service::mercurial_namespace::mercurial_namespace_server;
use rhgitaly::service::mercurial_operations::mercurial_operations_server;
use rhgitaly::service::mercurial_repository::mercurial_repository_server;
use rhgitaly::service::operations::operations_server;
use rhgitaly::service::r#ref::ref_server;
use rhgitaly::service::remote::remote_server;
use rhgitaly::service::repository::repository_server;
use rhgitaly::service::server::{server_server, HGITALY_VERSION};
use rhgitaly::sidecar;
use rhgitaly::streaming::WRITE_BUFFER_SIZE;
use tracing::{error, info, warn, Level};
use tracing_subscriber::{fmt::format::FmtSpan, FmtSubscriber};

fn setup_tracing(config: &LoggingConfig) {
    // a builder for `FmtSubscriber`.
    let level: Level = config.level.into();
    let subscriber = FmtSubscriber::builder()
        .with_max_level(level)
        .with_span_events(FmtSpan::CLOSE)
        .finish();

    tracing::subscriber::set_global_default(subscriber).expect("setting default subscriber failed");
}

/// For those settings that require an immediate mutation
fn apply_config(config: &Config) {
    setup_tracing(&config.logging); // hoping this won't duplicate the logs
}

#[derive(Parser, Debug)]
#[command(name = "RHGitaly")]
#[command(
    about = "RHGitaly is a partial implementation of the Gitaly and HGitaly gRPC protocols \
for Mercurial repositories"
)]
#[command(
    long_about = "RHGitaly is a performance-oriented partial implementation of the Gitaly \
and HGitaly gRPC protocols for Mercurial repositories.

It is asynchronous with a pool of worker threads, leveraging the Tonic (Tokio) gRPC framework, \
and the Mercurial primitives implemented in Rust (hg-core crate).

Configuration is for now entirely done by environment variables (see
https://foss.heptapod.net/heptapod/hgitaly/-/issues/181 to follow progress on this)
"
)]
#[command(version = HGITALY_VERSION)]
struct Args {
    /// Path to the main configuration file
    ///
    /// There is no default value, because configuring RHGitaly by environment variables
    /// is still supported for backwards compatibility.
    #[arg(short, long)]
    config: Option<PathBuf>,

    /// Launch and manage the hgweb server (currently Gunicorn).
    ///
    /// Configuration of Gunicorn can be made through the `GUNICORN_CMD_ARGS` environment variable,
    /// or by putting a `gunicorn.conf.py` file in its default location
    /// which is the RHGitaly working directory
    #[arg(long, default_value_t = false)]
    hgweb: bool,

    /// Launch and manage the (Python) HGitaly workers instead of connecting to HGitaly as a
    /// separate service.
    #[arg(long, default_value_t = false)]
    manage_sidecar: bool,
}

use tokio::signal::unix::{signal, SignalKind};
use tokio_util::sync::CancellationToken;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    load_license_nicknames();
    let args = Args::parse();

    let shutdown_token = CancellationToken::new();
    // The `broadcast` channel is multiple-sender, multi-receiver. Its documentation explicitly
    // states it is the one to be used for single-sender, multiple receiver use-cases.
    // The `watch` channel is more suited to actual payloads (typically configuration)
    let (reload_tx, reload_rx) = broadcast::channel(1);

    let config_res: Result<Config, Box<dyn std::error::Error>> = args.config.as_ref().map_or_else(
        || Ok(Config::from_env()),
        |path| Ok(FileConfig::read(path, args.hgweb, args.manage_sidecar)?.into()),
    );
    let config = match config_res {
        Err(e) => {
            eprintln!("FATAL Could not read or parse TOML configuration file: {e}");
            std::process::exit(exitcode::CONFIG);
        }
        Ok(c) => c,
    };

    apply_config(&config);

    info!("RHGitaly starting, version {}", HGITALY_VERSION);
    info!("WRITE_BUFFER_SIZE={}", *WRITE_BUFFER_SIZE);
    if config.hgrc_path.is_none() {
        warn!(
            "No HGRCPATH supplied, hence depending on global Mercurial settings. \
                   In most situations as of this writing, this is not likely to work."
        );
    }

    let hgweb_join_handle = if config.hgweb.managed {
        // We're using the initial receiver. To create other subsystems listening for the reload
        // messages, we'll need to create more handles with `reload_tx.subscribe()` before
        // the SIGHUP listening task above is started, taking ownership of `reload_tx`
        Some(hgweb::start(
            &config.hgweb,
            config.hgrc_path.as_ref(),
            &shutdown_token,
            reload_rx,
        ))
    } else {
        None
    };

    // we don't want to give a reference holding the config lock to Tonic server
    let bind_addr = config.listen_address.clone();

    let config = Arc::new(config);

    let mut sidecar_servers = match sidecar::Servers::new(&config, &shutdown_token).await {
        Ok(servers) => servers,
        Err(e) => {
            error!("Could not initialize (Python) HGitaly sidecar: {e}");
            std::process::exit(exitcode::IOERR);
        }
    };
    let sidecar_join_handle = sidecar_servers.initial_launch().await;
    let sidecar_servers = Arc::new(sidecar_servers);

    let server = Server::builder()
        .add_service(server_server(&sidecar_servers))
        .add_service(analysis_server(&config))
        .add_service(blob_server(&config, &sidecar_servers))
        .add_service(commit_server(&config, &sidecar_servers))
        .add_service(diff_server(&config, &sidecar_servers))
        .add_service(health_server(&sidecar_servers))
        .add_service(mercurial_aux_git_server(&config, &shutdown_token))
        .add_service(mercurial_changeset_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(mercurial_namespace_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(mercurial_operations_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(mercurial_repository_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(operations_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ))
        .add_service(ref_server(&config, &sidecar_servers))
        .add_service(remote_server(&config, &shutdown_token))
        .add_service(repository_server(
            &config,
            &shutdown_token,
            &sidecar_servers,
        ));

    let mut sighup = signal(SignalKind::hangup())?;

    tokio::spawn(async move {
        loop {
            sighup.recv().await;
            if let Some(path) = args.config.as_ref() {
                let new_config = FileConfig::read(path, args.hgweb, args.manage_sidecar).unwrap();
                config.reload(&new_config).await;
            } else {
                warn!(
                    "RHGitaly entirely configured from environment \
                       variables, nothing to reload"
                );
            }
            if reload_tx.send(()).is_err() {
                warn!(
                    "SIGHUP received, but cannot transmit on internal \
                       channel: no active listeners"
                );
            }
        }
    });
    let shutdown_token2 = shutdown_token.clone();

    let mut sigterm = signal(SignalKind::terminate())?;
    let mut sigint = signal(SignalKind::interrupt())?;
    // sigterm.recv() returns `None` if "no more events can be received by this stream"
    // In the case of SIGTERM, it probably cannot happen, and by default we will consider
    // it to be a termination condition.
    let wait_sigterm = async move {
        select! {
            _ = sigterm.recv() => {
                shutdown_token.cancel();
            },
            _ = sigint.recv() => {
                shutdown_token.cancel();
            },
            _ = shutdown_token.cancelled() => {}
        }
    };

    info!("RHGitaly binding to {:?}", bind_addr);
    //    let tonic_result: Result<(), Box<dyn std::error::Error>>
    let tonic_result = match bind_addr {
        BindAddress::TCP(addr) => server.serve_with_shutdown(addr, wait_sigterm).await,
        BindAddress::Unix(ref path) => match UnixListener::bind(path) {
            Ok(uds) => {
                let uds_stream = UnixListenerStream::new(uds);
                server
                    .serve_with_incoming_shutdown(uds_stream, wait_sigterm)
                    .await
            }
            Err(e) => {
                error!("Could not bind to Unix Domain Socket: {e:?}");
                shutdown_token2.cancel();
                Ok(()) // Technically not an error within Tonic server
            }
        },
    };

    // gRPC Server now has shut down (maybe with error)
    if let BindAddress::Unix(path) = bind_addr {
        info!("Removing Unix Domain socket file at '{}'", &path.display());
        if let Err(e) = remove_file(&path).await {
            error!("Could not remove Unix Domain socket file: {e:?}");
        }
    }

    if let Some(jh) = hgweb_join_handle {
        // let it finish it shuting down
        log_join_error_main_task("hgweb", jh.await);
    }

    if let Some(jh) = sidecar_join_handle {
        // let it finish its tidying up
        log_join_error_main_task("sidecar", jh.await);
    }

    Ok(tonic_result?)
}

fn log_join_error_main_task<T>(task_descr: &str, res: Result<T, JoinError>) {
    if let Err(e) = res {
        if e.is_cancelled() {
            warn!("Task {task_descr} was already cancelled");
        } else {
            error!("Task {task_descr} panicked");
        }
    }
}
