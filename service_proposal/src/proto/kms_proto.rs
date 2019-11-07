#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct CreateKeyRequest {
    #[prost(enumeration="EncType", tag="1")]
    pub enc_type: i32,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct AeadConfig {
    #[prost(bytes, tag="1")]
    pub key: std::vec::Vec<u8>,
    #[prost(bytes, tag="2")]
    pub nonce: std::vec::Vec<u8>,
    #[prost(bytes, tag="3")]
    pub ad: std::vec::Vec<u8>,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct KeyConfig {
    #[prost(oneof="key_config::Config", tags="1, 2")]
    pub config: ::std::option::Option<key_config::Config>,
}
pub mod key_config {
    #[derive(Clone, PartialEq, ::prost::Oneof)]
    #[derive(serde_derive::Serialize, serde_derive::Deserialize)]
    pub enum Config {
        #[prost(message, tag="1")]
        Aead(super::AeadConfig),
        #[prost(bytes, tag="2")]
        Sgxfs(std::vec::Vec<u8>),
    }
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct CreateKeyResponse {
    #[prost(string, tag="1")]
    pub key_id: std::string::String,
    #[prost(message, optional, tag="2")]
    pub config: ::std::option::Option<KeyConfig>,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct GetKeyRequest {
    #[prost(string, tag="1")]
    pub key_id: std::string::String,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct GetKeyResponse {
    #[prost(message, optional, tag="1")]
    pub config: ::std::option::Option<KeyConfig>,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct DeleteKeyRequest {
    #[prost(string, tag="1")]
    pub key_id: std::string::String,
}
#[derive(Clone, PartialEq, ::prost::Message)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub struct DeleteKeyResponse {
    #[prost(message, optional, tag="1")]
    pub config: ::std::option::Option<KeyConfig>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, ::prost::Enumeration)]
#[repr(i32)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub enum EncType {
    Aead = 0,
    Sgxfs = 1,
}
#[derive(Clone, serde_derive::Serialize, serde_derive::Deserialize, Debug)]
#[serde(tag = "type")]
pub enum KMSRequest {
    GetKey(GetKeyRequest),
    DelKey(DeleteKeyRequest),
    CreateKey(CreateKeyRequest),
}
#[derive(Clone, serde_derive::Serialize, serde_derive::Deserialize, Debug)]
#[serde(tag = "type")]
pub enum KMSResponse {
    GetKey(GetKeyResponse),
    DelKey(DeleteKeyResponse),
    CreateKey(CreateKeyResponse),
}
pub trait KMSService {
    fn get_key(req: GetKeyRequest) -> mesatee_core::Result<GetKeyResponse>;
    fn del_key(req: DeleteKeyRequest) -> mesatee_core::Result<DeleteKeyResponse>;
    fn create_key(req: CreateKeyRequest) -> mesatee_core::Result<CreateKeyResponse>;
    fn handle_invoke(&self, req: KMSRequest) -> mesatee_core::Result<KMSResponse> {
        match req {
            KMSRequest::GetKey(req) => Self::get_key(req).map(KMSResponse::GetKey),
            KMSRequest::DelKey(req) => Self::del_key(req).map(KMSResponse::DelKey),
            KMSRequest::CreateKey(req) => Self::create_key(req).map(KMSResponse::CreateKey),
        }
    }
}
