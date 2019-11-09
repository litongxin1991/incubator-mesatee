#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct UploadBucketRequest {
    /// the name must be creds
    #[prost(message, required, tag="1")]
    pub creds: super::credential_proto::Credential,
    #[prost(message, required, tag="2")]
    pub bucket: super::file_common_proto::BucketInfo,
    #[prost(string, required, tag="3")]
    pub description: std::string::String,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct UploadBucketResponse {
    #[prost(string, required, tag="1")]
    pub bucket_id: std::string::String,
}
#[derive(Clone, serde_derive::Serialize, serde_derive::Deserialize, Debug)]
#[serde(tag = "type")]
pub enum FileExternalRequest {
    UploadBucket(UploadBucketRequest),
}
#[derive(Clone, serde_derive::Serialize, serde_derive::Deserialize, Debug)]
#[serde(tag = "type")]
pub enum FileExternalResponse {
    UploadBucket(UploadBucketResponse),
}
pub trait FileExternalService {
    fn upload_bucket(req: UploadBucketRequest) -> mesatee_core::Result<UploadBucketResponse>;
    fn handle_invoke(&self, req: FileExternalRequest) -> mesatee_core::Result<FileExternalResponse> {
        let authenticated = match req {
            FileExternalRequest::UploadBucket(ref req) => req.creds.auth(),
        };

        if !authenticated {
            return Err(mesatee_core::Error::from(mesatee_core::ErrorKind::PermissionDenied));
        }
        match req {
            FileExternalRequest::UploadBucket(req) => Self::upload_bucket(req).map(FileExternalResponse::UploadBucket),
        }
    }
}
