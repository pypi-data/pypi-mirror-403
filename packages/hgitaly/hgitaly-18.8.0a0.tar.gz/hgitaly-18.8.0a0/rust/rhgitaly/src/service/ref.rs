// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
use std::fmt::Debug;
use std::sync::Arc;

use tokio_stream::StreamExt;

use tonic::{
    metadata::{Ascii, MetadataMap, MetadataValue},
    Request, Response, Status, Streaming,
};
use tracing::{info, instrument, Instrument};

use super::{load_repo_commit_for_node, traced_method, traced_method_wrapped};
use crate::config::SharedConfig;
use crate::errors::unimplemented_with_issue;
use crate::gitaly::ref_service_client::RefServiceClient;
use crate::gitaly::ref_service_server::{RefService, RefServiceServer};
use crate::gitaly::{
    DeleteRefsRequest, DeleteRefsResponse, FindAllBranchesRequest, FindAllBranchesResponse,
    FindAllRemoteBranchesRequest, FindAllRemoteBranchesResponse, FindAllTagsRequest,
    FindAllTagsResponse, FindBranchRequest, FindBranchResponse, FindDefaultBranchNameRequest,
    FindDefaultBranchNameResponse, FindLocalBranchesRequest, FindLocalBranchesResponse,
    FindRefsByOidRequest, FindRefsByOidResponse, FindTagError, FindTagRequest, FindTagResponse,
    GetTagMessagesRequest, GetTagMessagesResponse, GetTagSignaturesRequest,
    GetTagSignaturesResponse, ListBranchNamesContainingCommitRequest,
    ListBranchNamesContainingCommitResponse, ListRefsRequest, ListRefsResponse,
    ListTagNamesContainingCommitRequest, ListTagNamesContainingCommitResponse, RefExistsRequest,
    RefExistsResponse, Repository, UpdateReferencesRequest, UpdateReferencesResponse,
};
use crate::gitlab::gitlab_branch_ref;
use crate::gitlab::revision::existing_default_gitlab_branch;
use crate::metadata::{correlation_id, fallback_if_feature_disabled};
use crate::repository::{
    aux_git_to_main_hg, default_repo_spec_error_status, repo_store_vfs, RequestWithRepo,
};
use crate::sidecar;
use crate::streaming::ResultResponseStream;
use crate::util::tracing_span_id;

mod find_many;
mod find_one;
mod list;

#[derive(Debug)]
pub struct RefServiceImpl {
    config: SharedConfig,
    sidecar_servers: Arc<sidecar::Servers>,
}

impl RequestWithRepo for FindDefaultBranchNameRequest {
    fn repository_ref(&self) -> Option<&Repository> {
        self.repository.as_ref()
    }
}

#[tonic::async_trait]
impl RefService for RefServiceImpl {
    async fn find_default_branch_name(
        &self,
        request: Request<FindDefaultBranchNameRequest>,
    ) -> Result<Response<FindDefaultBranchNameResponse>, Status> {
        traced_method_wrapped!(self, request, inner_find_default_branch_name)
    }

    async fn find_local_branches(
        &self,
        request: Request<FindLocalBranchesRequest>,
    ) -> ResultResponseStream<FindLocalBranchesResponse> {
        traced_method!(self, request, inner_find_local_branches)
    }

    async fn find_all_branches(
        &self,
        request: Request<FindAllBranchesRequest>,
    ) -> ResultResponseStream<FindAllBranchesResponse> {
        traced_method!(self, request, inner_find_all_branches)
    }

    async fn find_all_tags(
        &self,
        request: Request<FindAllTagsRequest>,
    ) -> ResultResponseStream<FindAllTagsResponse> {
        traced_method!(self, request, inner_find_all_tags)
    }

    async fn find_tag(
        &self,
        request: Request<FindTagRequest>,
    ) -> Result<Response<FindTagResponse>, Status> {
        traced_method_wrapped!(self, request, inner_find_tag)
    }

    async fn find_all_remote_branches(
        &self,
        request: Request<FindAllRemoteBranchesRequest>,
    ) -> ResultResponseStream<FindAllRemoteBranchesResponse> {
        sidecar::server_streaming!(self, request, RefServiceClient, find_all_remote_branches)
    }

    async fn ref_exists(
        &self,
        request: Request<RefExistsRequest>,
    ) -> Result<Response<RefExistsResponse>, Status> {
        traced_method_wrapped!(self, request, inner_ref_exists)
    }

    async fn find_branch(
        &self,
        request: Request<FindBranchRequest>,
    ) -> Result<Response<FindBranchResponse>, Status> {
        traced_method_wrapped!(self, request, inner_find_branch)
    }

    #[instrument(name = "update_references", skip(self, request))]
    async fn update_references(
        &self,
        request: Request<Streaming<UpdateReferencesRequest>>,
    ) -> Result<Response<UpdateReferencesResponse>, Status> {
        sidecar::client_streaming!(self, request, RefServiceClient, update_references)
    }

    async fn delete_refs(
        &self,
        request: Request<DeleteRefsRequest>,
    ) -> Result<Response<DeleteRefsResponse>, Status> {
        sidecar::unary!(self, request, RefServiceClient, delete_refs)
    }

    async fn list_branch_names_containing_commit(
        &self,
        request: Request<ListBranchNamesContainingCommitRequest>,
    ) -> ResultResponseStream<ListBranchNamesContainingCommitResponse> {
        sidecar::server_streaming!(
            self,
            request,
            RefServiceClient,
            list_branch_names_containing_commit
        )
    }

    async fn list_tag_names_containing_commit(
        &self,
        request: Request<ListTagNamesContainingCommitRequest>,
    ) -> ResultResponseStream<ListTagNamesContainingCommitResponse> {
        sidecar::server_streaming!(
            self,
            request,
            RefServiceClient,
            list_tag_names_containing_commit
        )
    }

    async fn get_tag_signatures(
        &self,
        _request: Request<GetTagSignaturesRequest>,
    ) -> ResultResponseStream<GetTagSignaturesResponse> {
        Err(unimplemented_with_issue(75))
    }

    async fn get_tag_messages(
        &self,
        request: Request<GetTagMessagesRequest>,
    ) -> ResultResponseStream<GetTagMessagesResponse> {
        sidecar::server_streaming!(self, request, RefServiceClient, get_tag_messages)
    }

    async fn list_refs(
        &self,
        request: Request<ListRefsRequest>,
    ) -> ResultResponseStream<ListRefsResponse> {
        traced_method!(self, request, inner_list_refs)
    }

    async fn find_refs_by_oid(
        &self,
        request: Request<FindRefsByOidRequest>,
    ) -> Result<Response<FindRefsByOidResponse>, Status> {
        sidecar::fallback_unary!(
            self,
            inner_find_refs_by_oid,
            request,
            RefServiceClient,
            find_refs_by_oid
        )
    }
}

impl prost::Name for FindTagError {
    const NAME: &'static str = "FindTagError";
    const PACKAGE: &'static str = "gitaly";
}

impl RefServiceImpl {
    #[instrument(name = "find_default_branch_name", skip(self, request))]
    async fn inner_find_default_branch_name(
        &self,
        mut request: FindDefaultBranchNameRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<FindDefaultBranchNameResponse, Status> {
        tracing_span_id!();
        info!("Processing, repository={:?}", &request.repository);

        if let Some(main_hg_path) = aux_git_to_main_hg(&request) {
            let main_hg_path = main_hg_path.to_owned();
            if let Some(repo) = request.repository.as_mut() {
                repo.relative_path = main_hg_path;
            }
        }

        let store_vfs = repo_store_vfs(&self.config, &request.repository)
            .await
            .map_err(default_repo_spec_error_status)?;

        Ok(FindDefaultBranchNameResponse {
            name: existing_default_gitlab_branch(&store_vfs)
                .await
                .map_err(|e| {
                    Status::internal(format!(
                        "Error reading or checking GitLab default branch: {:?}",
                        e
                    ))
                })?
                .map(|ref name_node| gitlab_branch_ref(&name_node.0))
                .unwrap_or_else(Vec::new),
        })
    }

    #[instrument(name = "find_local_branches", skip(self, request), fields(span_id))]
    async fn inner_find_local_branches(
        &self,
        request: FindLocalBranchesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<FindLocalBranchesResponse> {
        tracing_span_id!();
        find_many::local_branches(&self.config, &request).await
    }

    #[instrument(name = "find_all_branches", skip(self, request), fields(span_id))]
    async fn inner_find_all_branches(
        &self,
        request: FindAllBranchesRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<FindAllBranchesResponse> {
        tracing_span_id!();
        find_many::all_branches(&self.config, &request).await
    }

    #[instrument(name = "find_all_tags", skip(self, request), fields(span_id))]
    async fn inner_find_all_tags(
        &self,
        request: FindAllTagsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<FindAllTagsResponse> {
        tracing_span_id!();
        find_many::all_tags(&self.config, &request).await
    }

    #[instrument(name = "ref_exists", skip(self, request), fields(span_id))]
    async fn inner_ref_exists(
        &self,
        request: RefExistsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<RefExistsResponse, Status> {
        tracing_span_id!();
        find_one::ref_exists(&self.config, request).await
    }

    #[instrument(name = "find_branch", skip(self, request), fields(span_id))]
    async fn inner_find_branch(
        &self,
        request: FindBranchRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<FindBranchResponse, Status> {
        tracing_span_id!();
        find_one::branch(&self.config, &request).await
    }

    #[instrument(name = "find_tag", skip(self, request), fields(span_id))]
    async fn inner_find_tag(
        &self,
        request: FindTagRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> Result<FindTagResponse, Status> {
        tracing_span_id!();
        find_one::tag(&self.config, request).await
    }

    #[instrument(name = "list_refs", skip(self, request), fields(span_id))]
    async fn inner_list_refs(
        &self,
        request: ListRefsRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
    ) -> ResultResponseStream<ListRefsResponse> {
        tracing_span_id!();
        list::refs(&self.config, request).await
    }

    #[instrument(
        name = "find_refs_by_oid",
        skip(self, request, metadata),
        fields(span_id)
    )]
    async fn inner_find_refs_by_oid(
        &self,
        request: &FindRefsByOidRequest,
        correlation_id: Option<&MetadataValue<Ascii>>,
        metadata: &MetadataMap,
    ) -> Result<FindRefsByOidResponse, Status> {
        tracing_span_id!();
        fallback_if_feature_disabled(metadata, "rhgitaly-find-refs-by-oid", true)?;
        list::find_by_oid(&self.config, request).await
    }
}

/// Takes care of boilerplate that would instead be in the startup sequence.
pub fn ref_server(
    config: &SharedConfig,
    sidecar_servers: &Arc<sidecar::Servers>,
) -> RefServiceServer<RefServiceImpl> {
    RefServiceServer::new(RefServiceImpl {
        config: config.clone(),
        sidecar_servers: sidecar_servers.clone(),
    })
}
