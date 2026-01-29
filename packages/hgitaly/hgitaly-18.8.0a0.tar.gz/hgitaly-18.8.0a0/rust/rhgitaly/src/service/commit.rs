// Copyright 2023-2025 Georges Racinet <georges.racinet@cloudcrane.io>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::fmt::{Debug, Formatter};
use std::sync::Arc;

use tonic::{
    metadata::{Ascii, MetadataMap, MetadataValue},
    Request, Response, Status, Streaming,
};
use tracing::{info, instrument, Instrument};

use hg::errors::HgError;
use hg::revlog::GraphError;

use super::{
    load_repo_commit_for_node, traced_method, traced_method_wrapped,
    traced_method_wrapped_with_metadata,
};
use crate::config::SharedConfig;
use crate::errors::unimplemented_with_issue;
use crate::gitaly::commit_service_client::CommitServiceClient;
use crate::gitaly::commit_service_server::{CommitService, CommitServiceServer};
use crate::gitaly::{
    CheckObjectsExistRequest, CheckObjectsExistResponse, CommitIsAncestorRequest,
    CommitIsAncestorResponse, CommitLanguagesRequest, CommitLanguagesResponse, CommitStatsRequest,
    CommitStatsResponse, CommitsByMessageRequest, CommitsByMessageResponse, CountCommitsRequest,
    CountCommitsResponse, CountDivergingCommitsRequest, CountDivergingCommitsResponse,
    FilterShasWithSignaturesRequest, FilterShasWithSignaturesResponse, FindAllCommitsRequest,
    FindAllCommitsResponse, FindCommitRequest, FindCommitResponse, FindCommitsRequest,
    FindCommitsResponse, GetCommitMessagesRequest, GetCommitMessagesResponse,
    GetCommitSignaturesRequest, GetCommitSignaturesResponse, GetTreeEntriesRequest,
    GetTreeEntriesResponse, LastCommitForPathRequest, LastCommitForPathResponse,
    ListCommitsByOidRequest, ListCommitsByOidResponse, ListCommitsByRefNameRequest,
    ListCommitsByRefNameResponse, ListCommitsRequest, ListCommitsResponse, ListFilesRequest,
    ListFilesResponse, ListLastCommitsForTreeRequest, ListLastCommitsForTreeResponse,
    RawBlameRequest, RawBlameResponse, Repository, TreeEntryRequest, TreeEntryResponse,
};
use crate::gitlab::revision::gitlab_revision_node_prefix;
use crate::metadata::{correlation_id, fallback_if_feature_disabled};
use crate::repository::{default_repo_spec_error_status, repo_store_vfs, RequestWithRepo};
use crate::sidecar;
use crate::streaming::ResultResponseStream;
use crate::util::tracing_span_id;
use crate::workdir::with_workdir;

mod commit_languages;
mod get_tree_entries;
mod is_ancestor;
mod last_commits;
mod list_by_oid;
mod list_by_ref_name;
mod many_commits;
mod raw_blame;
mod tree_entry;

#[derive(Debug)]
pub struct CommitServiceImpl {
    config: SharedConfig,
    sidecar_servers: Arc<sidecar::Servers>,
}

const COMMITS_CHUNK_SIZE: usize = 50;

fn not_found_for_path(_path: &[u8]) -> Status {
    Status::not_found("tree entry not found")
}

impl RequestWithRepo for FindCommitRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

#[tonic::async_trait]
impl CommitService for CommitServiceImpl {
    async fn commit_is_ancestor(
        &self,
        request: Request<CommitIsAncestorRequest>,
    ) -> Result<Response<CommitIsAncestorResponse>, Status> {
        sidecar::fallback_unary!(
            self,
            inner_commit_is_ancestor,
            request,
            CommitServiceClient,
            commit_is_ancestor
        )
    }

    async fn list_commits_by_oid(
        &self,
        request: Request<ListCommitsByOidRequest>,
    ) -> ResultResponseStream<ListCommitsByOidResponse> {
        traced_method!(self, request, inner_list_commits_by_oid)
    }

    async fn list_commits_by_ref_name(
        &self,
        request: Request<ListCommitsByRefNameRequest>,
    ) -> ResultResponseStream<ListCommitsByRefNameResponse> {
        traced_method!(self, request, inner_list_commits_by_ref_name)
    }

    async fn find_commits(
        &self,
        request: Request<FindCommitsRequest>,
    ) -> ResultResponseStream<FindCommitsResponse> {
        sidecar::fallback_server_streaming!(
            self,
            inner_find_commits,
            request,
            CommitServiceClient,
            find_commits
        )
    }

    async fn commit_languages(
        &self,
        request: Request<CommitLanguagesRequest>,
    ) -> Result<Response<CommitLanguagesResponse>, Status> {
        traced_method_wrapped_with_metadata!(self, request, inner_commit_languages)
    }

    async fn last_commit_for_path(
        &self,
        request: Request<LastCommitForPathRequest>,
    ) -> Result<Response<LastCommitForPathResponse>, Status> {
        traced_method_wrapped!(self, request, inner_last_commit_for_path)
    }

    async fn list_last_commits_for_tree(
        &self,
        request: Request<ListLastCommitsForTreeRequest>,
    ) -> ResultResponseStream<ListLastCommitsForTreeResponse> {
        traced_method!(self, request, inner_list_last_commits_for_tree)
    }

    async fn find_commit(
        &self,
        request: Request<FindCommitRequest>,
    ) -> Result<Response<FindCommitResponse>, Status> {
        traced_method_wrapped!(self, request, inner_find_commit)
    }

    async fn tree_entry(
        &self,
        request: Request<TreeEntryRequest>,
    ) -> ResultResponseStream<TreeEntryResponse> {
        traced_method!(self, request, inner_tree_entry)
    }

    async fn count_commits(
        &self,
        request: Request<CountCommitsRequest>,
    ) -> Result<Response<CountCommitsResponse>, Status> {
        sidecar::fallback_unary!(
            self,
            inner_count_commits,
            request,
            CommitServiceClient,
            count_commits
        )
    }

    async fn count_diverging_commits(
        &self,
        request: Request<CountDivergingCommitsRequest>,
    ) -> Result<Response<CountDivergingCommitsResponse>, Status> {
        sidecar::unary!(self, request, CommitServiceClient, count_diverging_commits)
    }

    async fn get_tree_entries(
        &self,
        request: Request<GetTreeEntriesRequest>,
    ) -> ResultResponseStream<GetTreeEntriesResponse> {
        traced_method!(self, request, inner_get_tree_entries)
    }

    async fn list_files(
        &self,
        request: Request<ListFilesRequest>,
    ) -> ResultResponseStream<ListFilesResponse> {
        sidecar::server_streaming!(self, request, CommitServiceClient, list_files)
    }

    async fn commit_stats(
        &self,
        request: Request<CommitStatsRequest>,
    ) -> Result<Response<CommitStatsResponse>, Status> {
        sidecar::unary!(self, request, CommitServiceClient, commit_stats)
    }

    async fn find_all_commits(
        &self,
        request: Request<FindAllCommitsRequest>,
    ) -> ResultResponseStream<FindAllCommitsResponse> {
        sidecar::server_streaming!(self, request, CommitServiceClient, find_all_commits)
    }

    async fn raw_blame(
        &self,
        request: Request<RawBlameRequest>,
    ) -> ResultResponseStream<RawBlameResponse> {
        sidecar::fallback_server_streaming!(
            self,
            inner_raw_blame,
            request,
            CommitServiceClient,
            raw_blame
        )
    }

    async fn commits_by_message(
        &self,
        request: Request<CommitsByMessageRequest>,
    ) -> ResultResponseStream<CommitsByMessageResponse> {
        sidecar::server_streaming!(self, request, CommitServiceClient, commits_by_message)
    }

    async fn check_objects_exist(
        &self,
        _request: Request<Streaming<CheckObjectsExistRequest>>,
    ) -> ResultResponseStream<CheckObjectsExistResponse> {
        Err(unimplemented_with_issue(101))
    }

    async fn list_commits(
        &self,
        request: Request<ListCommitsRequest>,
    ) -> ResultResponseStream<ListCommitsResponse> {
        sidecar::fallback_server_streaming!(
            self,
            inner_list_commits,
            request,
            CommitServiceClient,
            list_commits
        )
    }

    async fn filter_shas_with_signatures(
        &self,
        _request: Request<Streaming<FilterShasWithSignaturesRequest>>,
    ) -> ResultResponseStream<FilterShasWithSignaturesResponse> {
        Err(unimplemented_with_issue(24))
    }

    async fn get_commit_signatures(
        &self,
        _request: Request<GetCommitSignaturesRequest>,
    ) -> ResultResponseStream<GetCommitSignaturesResponse> {
        Err(unimplemented_with_issue(24))
    }

    async fn get_commit_messages(
        &self,
        request: Request<GetCommitMessagesRequest>,
    ) -> ResultResponseStream<GetCommitMessagesResponse> {
        sidecar::server_streaming!(self, request, CommitServiceClient, get_commit_messages)
    }
}

struct FindCommitTracingRequest<'a>(&'a FindCommitRequest);

impl Debug for FindCommitTracingRequest<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FindCommitRequest")
            .field("repository", &self.0.repository)
            .field("revision", &String::from_utf8_lossy(&self.0.revision))
            .finish()
    }
}

/// Convert a GraphError to RevlogError
///
/// Talk upstream about this. When both are intertwined, it is painful not to have the
/// `From<GraphError>` implementation.
fn revlog_err_from_graph_err(err: GraphError) -> HgError {
    HgError::corrupted(format!("{:?}", err))
}

impl CommitServiceImpl {
    #[instrument(name = "tree_entry", skip(self, request), fields(span_id))]
    async fn inner_tree_entry(
        &self,
        request: TreeEntryRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<TreeEntryResponse> {
        tracing_span_id!();
        tree_entry::inner_impl(&self.config, &request).await
    }

    #[instrument(name = "count_commits", skip(self, request, metadata), fields(span_id))]
    async fn inner_count_commits(
        &self,
        request: &CountCommitsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<CountCommitsResponse, Status> {
        fallback_if_feature_disabled(metadata, "rhgitaly-count-commits", true)?;
        if request.revision.is_empty() && !request.all {
            // minimal case to prove that fallback works
            Err(Status::invalid_argument("empty Revision and false All"))
        } else {
            many_commits::count_commits(&self.config, request, metadata).await
        }
    }

    #[instrument(name = "get_tree_entries", skip(self, request), fields(span_id))]
    async fn inner_get_tree_entries(
        &self,
        request: GetTreeEntriesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<GetTreeEntriesResponse> {
        tracing_span_id!();
        get_tree_entries::inner_impl(&self.config, request).await
    }

    #[instrument(name = "raw_blame", skip(self, request, metadata), fields(span_id))]
    async fn inner_raw_blame(
        &self,
        request: &RawBlameRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> ResultResponseStream<RawBlameResponse> {
        tracing_span_id!();
        fallback_if_feature_disabled(metadata, "rhgitaly-raw-blame", false)?;
        raw_blame::inner_impl(&self.config, request).await
    }

    #[instrument(name = "list_commits_by_oid", skip(self, request), fields(span_id))]
    async fn inner_list_commits_by_oid(
        &self,
        request: ListCommitsByOidRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<ListCommitsByOidResponse> {
        tracing_span_id!();
        list_by_oid::inner_impl(self.config.clone(), request).await
    }

    #[instrument(
        name = "list_commits_by_ref_name",
        skip(self, request),
        fields(span_id)
    )]
    async fn inner_list_commits_by_ref_name(
        &self,
        request: ListCommitsByRefNameRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<ListCommitsByRefNameResponse> {
        tracing_span_id!();
        list_by_ref_name::inner_impl(self.config.clone(), request).await
    }

    #[instrument(name = "find_commits", skip(self, request, metadata), fields(span_id))]
    async fn inner_find_commits(
        &self,
        request: &FindCommitsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> ResultResponseStream<FindCommitsResponse> {
        tracing_span_id!();
        many_commits::find_commits(&self.config, request, metadata).await
    }

    #[instrument(name = "list_commits", skip(self, request, metadata), fields(span_id))]
    async fn inner_list_commits(
        &self,
        request: &ListCommitsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> ResultResponseStream<ListCommitsResponse> {
        tracing_span_id!();
        fallback_if_feature_disabled(metadata, "rhgitaly-list-commits", true)?;
        many_commits::list_commits(&self.config, request, metadata).await
    }

    #[instrument(
        name = "commit_is_ancestor",
        skip(self, request, metadata),
        fields(span_id)
    )]
    async fn inner_commit_is_ancestor(
        &self,
        request: &CommitIsAncestorRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<CommitIsAncestorResponse, Status> {
        tracing_span_id!();
        fallback_if_feature_disabled(metadata, "rhgitaly-commit-is-ancestor", true)?;
        is_ancestor::inner_impl(&self.config, request).await
    }

    #[instrument(
        name = "commit_languages",
        skip(self, request, metadata),
        fields(span_id)
    )]
    async fn inner_commit_languages(
        &self,
        request: CommitLanguagesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<CommitLanguagesResponse, Status> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            commit_languages::CommitLanguagesTracingRequest(&request)
        );
        let rev: &[u8] = if request.revision.is_empty() {
            b"HEAD"
        } else {
            &request.revision
        };

        with_workdir(
            &self.config,
            request.repository.as_ref().unwrap(), // TODO unwrap
            rev,
            &self.sidecar_servers,
            metadata,
            |path| tokio::task::spawn_blocking(move || commit_languages::at_path(&path)),
        )
        .await
    }

    #[instrument(name = "last_commit_for_path", skip(self, request), fields(span_id))]
    async fn inner_last_commit_for_path(
        &self,
        request: LastCommitForPathRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<LastCommitForPathResponse, Status> {
        tracing_span_id!();
        last_commits::one_for_path(&self.config, request).await
    }

    #[instrument(
        name = "list_last_commits_for_tree",
        skip(self, request),
        fields(span_id)
    )]
    async fn inner_list_last_commits_for_tree(
        &self,
        request: ListLastCommitsForTreeRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<ListLastCommitsForTreeResponse> {
        tracing_span_id!();
        last_commits::several_for_tree(&self.config, request).await
    }

    #[instrument(name = "find_commit", skip(self, request), fields(span_id))]
    async fn inner_find_commit(
        &self,
        request: FindCommitRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<FindCommitResponse, Status> {
        tracing_span_id!();
        info!(
            "Processing, request={:?}",
            FindCommitTracingRequest(&request)
        );
        if request.revision.is_empty() {
            return Err(Status::invalid_argument("empty revision"));
        }

        let config = self.config.clone();
        let store_vfs = repo_store_vfs(&config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        match gitlab_revision_node_prefix(&store_vfs, &request.revision)
            .await
            .map_err(|e| Status::internal(format!("Error resolving revision: {:?}", e)))?
        {
            None => {
                info!("Revision not resolved");
                Ok(FindCommitResponse::default())
            }
            Some(np) => {
                info!("Revision resolved as {:x}", &np);
                Ok(FindCommitResponse {
                    commit: load_repo_commit_for_node(&self.config, request, np).await?,
                })
            }
        }
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn commit_server(
    config: &SharedConfig,
    sidecar_servers: &Arc<sidecar::Servers>,
) -> CommitServiceServer<CommitServiceImpl> {
    CommitServiceServer::new(CommitServiceImpl {
        config: config.clone(),
        sidecar_servers: sidecar_servers.clone(),
    })
}
