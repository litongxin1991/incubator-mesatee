#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct S3Bucket {
    #[prost(string, required, tag="1")]
    pub access_id: std::string::String,
    #[prost(string, required, tag="2")]
    pub access_token: std::string::String,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct NfsBucket {
    #[prost(string, required, tag="1")]
    pub server: std::string::String,
    #[prost(string, required, tag="2")]
    pub root_dir: std::string::String,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct LocalBucket {
    #[prost(string, required, tag="1")]
    pub root_dir: std::string::String,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct BucketInfo {
    #[prost(oneof="bucket_info::Info", tags="1, 2, 3")]
    pub info: ::std::option::Option<bucket_info::Info>,
}
pub mod bucket_info {
    #[derive(Clone, PartialEq, ::prost::Oneof)]
    #[derive(serde_derive::Serialize, serde_derive::Deserialize)]
    pub enum Info {
        #[prost(message, tag="1")]
        S3(super::S3Bucket),
        #[prost(message, tag="2")]
        Nfs(super::NfsBucket),
        #[prost(message, tag="3")]
        Local(super::LocalBucket),
    }
}
