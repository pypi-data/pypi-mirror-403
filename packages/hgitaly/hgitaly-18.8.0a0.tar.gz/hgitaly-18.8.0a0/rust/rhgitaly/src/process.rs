// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
//! Asynchronous process handling

use nix::libc::pid_t;
use nix::sys::signal::{kill, Signal};
use nix::unistd::Pid;
use tokio::process::{Child, Command};
use tokio_util::sync::CancellationToken;
use tracing::{error, warn};

/// Send SIGTERM and reap process
///
/// This is to be used in cases of cancellation, such as general shutdown
/// There is a risk of race condition if another thread is waiting on the
/// child process (in theory, should lead to warning logs only) that
/// is avoidable if the normal waiting and the early termination
/// conditions (all async of course) are in the arms of a common [`tokio::select!`]
/// as these are run in a single task.
pub async fn terminate(child: &mut Child) {
    signal(child, Signal::SIGTERM);
    // even if signal could not be sent, we still have to wait in case it is not reaped yet

    // this is our best shot at reaping the child process. At this
    // point, we do not care about possible errors.
    if let Err(e) = child.wait().await {
        warn!("Error reaping process {:?}: {}", child.id(), e)
    }
}

pub fn launch_or_cancel(cmd: &mut Command, token: &mut CancellationToken) -> Option<Child> {
    cmd.spawn().map_or_else(
        |err| {
            error!("Error launching {:?}: {}", cmd.as_std().get_program(), err);
            token.cancel();
            None
        },
        Some,
    )
}

/// Send a signal to the given child process
///
/// This function is kept private because it uses [`Signal`] instead of
/// [`tokio::signal::unix::SignalKind`], and this should be hidden
/// from callers.
fn signal(child: &mut Child, sig: Signal) {
    if let Some(id) = child.id() {
        let pid = Pid::from_raw(id as pid_t);
        if let Err(e) = kill(pid, sig) {
            warn!("Error sending signal {sig} to child process {pid}: {e}");
        }
    } else {
        warn!("Cannot send signal to terminated child process");
    }
}

pub fn sighup(child: &mut Child) {
    signal(child, Signal::SIGHUP)
}
