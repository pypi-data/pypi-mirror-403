// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use nix::NixPath;
use serde::Deserialize;
use std::env;
use std::error::Error;
use std::ffi::OsString;
use std::fmt;
use std::fs;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tracing::{error, warn};
use uuid::Uuid;

use tokio::sync::RwLock;

use hg::config::Config as CoreConfig;

const CLIENT_ID_FILE_NAME: &str = "rhgitaly.client-id";
const DEFAULT_CONFIG_DIRECTORY: &str = "/etc/hgitaly";

#[derive(Debug, Clone)]
#[allow(clippy::upper_case_acronyms)]
/// Necessary infortion to bind the listening socket
pub enum BindAddress {
    Unix(PathBuf),
    TCP(SocketAddr),
}

#[derive(Debug, Clone)]
#[allow(clippy::upper_case_acronyms)]
/// Necessary infortion to call a server (e.g., HGitaly (Python) sidecar)
pub enum ServerAddress {
    Unix(PathBuf),
    URI(String),
}

/// Parse the URL to listen to
///
/// There are two cases: `unix:/some/path/sock` and `tcp://hostname:port`, where
/// hostname can only be an IP address (v4 or v6).
///
/// This is a toy implementation anyway, we'll add a proper dependency to the `url` crate later on
fn parse_listen_url(url: &str) -> Result<BindAddress, Box<dyn Error>> {
    if let Some(path) = url.strip_prefix("unix:") {
        return Ok(BindAddress::Unix(path.into()));
    }
    if let Some(addr) = url.strip_prefix("tcp://") {
        return Ok(BindAddress::TCP(addr.parse()?));
    }
    Err("Unsupported URL".into())
}

/// Parse the URI of a gRPC server
///
/// There are two cases: `unix:/some/path/sock` and URIs directly supported by Tonic
/// (`http` or `https` schemes). The latter are not validated at this point.
pub fn parse_server_uri(uri: &str) -> Result<ServerAddress, Box<dyn Error>> {
    if let Some(path) = uri.strip_prefix("unix:") {
        return Ok(ServerAddress::Unix(path.into()));
    }
    Ok(ServerAddress::URI(uri.to_owned()))
}

pub struct Config {
    pub repositories_root: PathBuf,
    pub listen_address: BindAddress,
    pub hg_executable: PathBuf,
    pub git_executable: PathBuf,
    pub sidecar: RwLock<SidecarConfig>,
    pub hg_core_config: CoreConfig,
    pub hgweb: HgWebConfig,
    pub managed_sidecar: bool,
    pub hgrc_path: Option<OsString>,
    pub logging: LoggingConfig,
}

/// Configuration encapsulated so that it can be shared across all subsystems and updatable.
pub type SharedConfig = Arc<Config>;

impl Default for Config {
    /// This is used in tests only
    fn default() -> Self {
        Self {
            repositories_root: "".into(),
            hg_executable: "hg".into(),
            git_executable: "git".into(),
            hgweb: HgWebConfig::default(),
            managed_sidecar: false,
            listen_address: BindAddress::Unix("/tmp/rhgitaly.socket".into()),
            sidecar: SidecarConfig::default().into(),
            hgrc_path: None,
            logging: LoggingConfig::default(),
            hg_core_config: CoreConfig::load_non_repo()
                .expect("Should have been able to read Mercurial core config"),
        }
    }
}

impl fmt::Debug for Config {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Config")
            .field("repositories_root", &self.repositories_root)
            .field("listen_address", &self.listen_address)
            .field("hg_executable", &self.hg_executable)
            .field("git_executable", &self.git_executable)
            .field("hgweb", &self.hgweb)
            .field("sidecar", &self.sidecar)
            .field(
                "hg_core_config",
                &self.hgrc_path.as_ref().map_or(
                    "read from global and user configuration files".to_owned(),
                    |path| format!("read from HGRCPATH={:?}", &path),
                ),
            )
            .finish()
    }
}

fn load_set_client_id(client_id_path: &Path) -> String {
    if client_id_path.exists() {
        fs::read_to_string(client_id_path)
    } else {
        let client_id = format!("rhgitaly-{}", &Uuid::new_v4());
        fs::write(client_id_path, &client_id).map(|_| client_id)
    }
    .unwrap_or_else(|_| {
        panic!(
            "Could not read or write client id file {}",
            client_id_path.display()
        )
    })
}

impl Config {
    /// Read configuration from environment variables
    ///
    /// This is useful for Gitaly Comparison tests, especially until we can
    /// support the HGitaly configuration file (i.e., HGRC)
    pub fn from_env() -> Self {
        Config {
            repositories_root: env::var_os("RHGITALY_REPOSITORIES_ROOT")
                .expect("RHGITALY_REPOSITORIES_ROOT not set in environment")
                .into(),
            listen_address: parse_listen_url(
                &env::var("RHGITALY_LISTEN_URL")
                    .expect("RHGITALY_LISTEN_URL not set in environment"),
            )
            .expect("Could not parse listen URL"),
            sidecar: SidecarConfig::from_env().into(),
            hg_executable: env::var("RHGITALY_HG_EXECUTABLE").map_or_else(
                |e| match e {
                    env::VarError::NotPresent => "hg".into(),
                    env::VarError::NotUnicode(os_string) => os_string.into(),
                },
                |v| v.into(),
            ),
            git_executable: env::var("RHGITALY_GIT_EXECUTABLE").map_or_else(
                |e| match e {
                    env::VarError::NotPresent => "git".into(),
                    env::VarError::NotUnicode(os_string) => os_string.into(),
                },
                |v| v.into(),
            ),
            hgrc_path: env::var_os("HGRCPATH"),
            ..Default::default()
        }
    }

    pub async fn reload(&self, fc: &FileConfig) {
        self.sidecar.write().await.reload(&fc.sidecar);
    }
}

/// Read the sidecar Client ID path from environment variables, defaulting to constant only if
/// `defaulting` is true.
///
/// The optional defaulting is useful for callers with their own defaulting logic.
fn client_id_path_from_env(defaulting: bool) -> Option<PathBuf> {
    let mut path_buf: PathBuf = if let Some(dir_path) = env::var_os("RHGITALY_CONFIG_DIRECTORY") {
        dir_path.into()
    } else if defaulting {
        DEFAULT_CONFIG_DIRECTORY.into()
    } else {
        return None;
    };

    path_buf.push(CLIENT_ID_FILE_NAME);
    Some(path_buf)
}

impl From<FileConfig> for Config {
    fn from(mut fc: FileConfig) -> Self {
        fc.sidecar.init_client_id();
        let listen_url = &env::var("RHGITALY_LISTEN_URL").unwrap_or(fc.listen_url);
        Self {
            repositories_root: env::var_os("RHGITALY_REPOSITORIES_ROOT")
                .map_or(fc.mercurial.repositories_root, Into::into),
            listen_address: parse_listen_url(listen_url).expect("Could not parse listen URL"),
            sidecar: fc.sidecar.into(),
            hg_executable: env::var("RHGITALY_HG_EXECUTABLE")
                .map_or(fc.mercurial.executable, Into::into),
            git_executable: env::var("RHGITALY_GIT_EXECUTABLE")
                .map_or(fc.git.executable, Into::into),
            hgweb: fc.mercurial.hgweb,
            hgrc_path: env::var_os("HGRCPATH").or(fc.mercurial.hgrc.map(Into::into)),
            logging: fc.logging,
            ..Default::default()
        }
    }
}

/// A more organized vision of configuration, meant to be read from a configuration file.
///
/// All fields are optional, because they have associated default values OR they can also
/// be set in the final config by environment variables.
#[derive(Deserialize, Debug)]
#[serde(default)]
pub struct FileConfig {
    pub listen_url: String,
    pub mercurial: MercurialConfig,
    pub git: GitConfig,
    pub sidecar: SidecarConfig,
    pub logging: LoggingConfig,
}

impl Default for FileConfig {
    fn default() -> Self {
        Self {
            listen_url: "unix:/run/hgitaly/rhgitaly.socket".to_owned(),
            mercurial: MercurialConfig::default(),
            git: GitConfig::default(),
            sidecar: SidecarConfig::default(),
            logging: LoggingConfig::default(),
        }
    }
}

/// Serializable log level
///
/// Tedious, yet more straightforward than making a new type for [`tracing::Level`] and
/// implementing [`Deserialize`] for it.
#[derive(Deserialize, Debug, Copy, Clone, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum LogLevel {
    Trace,
    Debug,
    Info,
    Warn,
    Error,
}

impl From<LogLevel> for tracing::Level {
    fn from(level: LogLevel) -> Self {
        match level {
            LogLevel::Trace => tracing::Level::TRACE,
            LogLevel::Debug => tracing::Level::DEBUG,
            LogLevel::Info => tracing::Level::INFO,
            LogLevel::Warn => tracing::Level::WARN,
            LogLevel::Error => tracing::Level::ERROR,
        }
    }
}

#[derive(Deserialize, Debug)]
#[serde(default)]
pub struct LoggingConfig {
    pub level: LogLevel,
}

impl Default for LoggingConfig {
    fn default() -> Self {
        Self {
            level: LogLevel::Info,
        }
    }
}

#[derive(Deserialize, Debug)]
#[serde(default)]
pub struct MercurialConfig {
    pub executable: PathBuf,
    pub repositories_root: PathBuf,
    pub hgrc: Option<String>, // OsString not suitable, and the TOML file is parsed as UTF-8 anyway
    pub hgweb: HgWebConfig,
}

#[derive(Deserialize, Debug)]
#[serde(default)]
pub struct HgWebConfig {
    pub managed: bool,
    pub executable: PathBuf,
    pub additional_args: Vec<String>, // OsString not suitable, would expect Unix(...) etc.
}

impl Default for HgWebConfig {
    fn default() -> Self {
        Self {
            managed: false,
            executable: "gunicorn".into(),
            additional_args: Vec::new(),
        }
    }
}

impl Default for MercurialConfig {
    fn default() -> Self {
        Self {
            executable: "hg".into(),
            repositories_root: "/var/lib/hgitaly".into(),
            hgrc: None,
            hgweb: HgWebConfig::default(),
        }
    }
}

#[derive(Deserialize, Debug)]
#[serde(default)]
pub struct GitConfig {
    pub executable: PathBuf,
}

impl Default for GitConfig {
    fn default() -> Self {
        Self {
            executable: "git".into(),
        }
    }
}

#[derive(Deserialize, Debug, Clone)]
#[serde(default)]
pub struct SidecarConfig {
    pub managed: bool,
    pub address: String, // will be removed once sidecar is always managed
    pub incarnation_id: String,
    pub client_id: String,
    pub client_id_path: PathBuf,
    pub min_idle_workers: u16,
    pub max_idle_workers: u16,
    pub max_workers: u16,
    pub max_rss_mib: u32,
    pub housekeeping_interval_seconds: u16, // at most ~18h (quite unreasonable already)
    pub worker_startup: WorkerStartupConfig,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(default)]
pub struct WorkerStartupConfig {
    pub readiness_timeout_ms: u16,
    pub socket_check_every_ms: u16,
    pub connect_check_every_ms: u16,
}

impl Default for SidecarConfig {
    fn default() -> Self {
        let incarnation = Uuid::new_v4();
        Self {
            managed: true,
            address: "unix:/run/hgitaly/hgitaly.socket".to_owned(),
            incarnation_id: incarnation.into(),
            // not fan of empty default values, but in this case there is no ambiguity
            client_id: String::new(),
            client_id_path: PathBuf::new(),
            min_idle_workers: 2,
            max_idle_workers: 4,
            max_workers: 8,
            max_rss_mib: 4096,
            housekeeping_interval_seconds: 30,
            worker_startup: WorkerStartupConfig::default(),
        }
    }
}

impl Default for WorkerStartupConfig {
    fn default() -> Self {
        Self {
            readiness_timeout_ms: 2000,
            socket_check_every_ms: 50,
            connect_check_every_ms: 5,
        }
    }
}

impl SidecarConfig {
    fn from_env() -> Self {
        let client_id_path = client_id_path_from_env(true)
            .expect("With defaulting=`true` client_id_path should never return None");
        Self {
            address: env::var("RHGITALY_SIDECAR_ADDRESS")
                .expect("RHGITALY_SIDECAR_ADDRESS not specified or not UTF-8"),
            client_id_path,
            ..Default::default() // initializes `incarnation_id`
        }
    }

    /// Read client_id from client_id_path if not already set.
    ///
    /// `client_id` can be set in the configuration file.
    fn init_client_id(&mut self) {
        if self.client_id.is_empty() {
            self.client_id = load_set_client_id(&self.client_id_path);
        }
    }

    /// Take the lock to return a sidecar configuration with only the information
    /// useful to maintain the pool.
    ///
    /// No allocation occurs, the lock is releasd immeditely.
    pub(crate) async fn pool_config(locked: &RwLock<Self>) -> Self {
        let this = locked.read().await;
        Self {
            // `managed` is not needed for pool size maintenance, but if would be weird
            // to replace it by a hardcoded value. This item will eventually disappear anyway.
            managed: this.managed,
            housekeeping_interval_seconds: this.housekeeping_interval_seconds,
            max_rss_mib: this.max_rss_mib,
            min_idle_workers: this.min_idle_workers,
            max_idle_workers: this.max_idle_workers,
            max_workers: this.max_workers,
            worker_startup: this.worker_startup.clone(),
            // avoid `Default::default()` for maintainability: if we introduce a new
            // relevant field, we do not want to forget updating this associated function and
            // to replace it by its default value. We are happy to get instead a compiler error
            address: String::new(),
            incarnation_id: String::new(),
            client_id: String::new(),
            client_id_path: PathBuf::new(),
        }
    }

    /// Partial reload: only those attributes that make sense
    ///
    /// In particular, we don't change the workdir identification attributes (`client_id` and
    /// `incarnation_id`), nor the `managed` boolean.
    fn reload(&mut self, other: &Self) {
        self.housekeeping_interval_seconds = other.housekeeping_interval_seconds;
        self.min_idle_workers = other.min_idle_workers;
        self.max_idle_workers = other.max_idle_workers;
        self.max_workers = other.max_workers;
        self.max_rss_mib = other.max_rss_mib;
        self.worker_startup = other.worker_startup.clone();

        warn!("Sidecar configuration reloaded, new values: {self:?}");
    }
}

fn client_id_path_from_config_path(config: &Path) -> PathBuf {
    config
        .parent()
        .expect("Configuration file path should not be empty nor the filesystem root")
        .join(CLIENT_ID_FILE_NAME)
}

impl FileConfig {
    pub fn read(
        path: &Path,
        managed_hgweb: bool,
        managed_sidecar: bool,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let bytes = std::fs::read(path)?;
        let config_str = String::from_utf8(bytes)?;
        let mut config: Self = toml::from_str(&config_str)?;

        // defaulting chain for client_id_path:
        // config file -> environment -> sibling of `path`
        if config.sidecar.client_id_path.is_empty() {
            config.sidecar.client_id_path = client_id_path_from_env(false)
                .unwrap_or_else(|| client_id_path_from_config_path(path));
        }
        match env::var("RHGITALY_SIDECAR_ADDRESS") {
            Err(env::VarError::NotPresent) => {}
            Err(env::VarError::NotUnicode(os_string)) => {
                error!("RHGITALY_SIDECAR_ADDRESS value {os_string:?} is not unicode");
                return Err("Invalid RHGITALY_SIDECAR_ADDRESS".into());
            }
            Ok(address) => {
                config.sidecar.address = address;
            }
        }
        if managed_hgweb {
            config.mercurial.hgweb.managed = true;
        }
        if managed_sidecar {
            config.sidecar.managed = true;
        }
        Ok(config)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default() {
        let hgweb_conf: HgWebConfig = toml::from_str("").unwrap();
        assert!(!hgweb_conf.managed);

        let hg_conf: MercurialConfig = toml::from_str("[hgweb]").unwrap();
        assert!(!hg_conf.hgweb.managed);
    }

    #[test]
    fn test_hgweb() {
        let hgweb_conf: HgWebConfig = toml::from_str("additional_args = [\"foo\"]").unwrap();
        assert_eq!(hgweb_conf.additional_args, vec!["foo"]);
    }

    #[test]
    fn test_logging() {
        let conf: FileConfig = toml::from_str("[logging]\nlevel = \"debug\"").unwrap();
        assert_eq!(conf.logging.level, LogLevel::Debug);
    }
}
