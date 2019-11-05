#[derive(Clone, PartialEq, ::prost::Message, serde_derive::Serialize, serde_derive::Deserialize)]
pub struct CreateKeyRequest {
    #[prost(enumeration = "EncType", tag = "1")]
    pub enc_type: i32,
}
#[derive(Clone, PartialEq, ::prost::Message, serde_derive::Serialize, serde_derive::Deserialize)]
pub struct AeadConfig {
    #[prost(bytes, tag = "1")]
    pub key: std::vec::Vec<u8>,
    #[prost(bytes, tag = "2")]
    pub nonce: std::vec::Vec<u8>,
    #[prost(bytes, tag = "3")]
    pub ad: std::vec::Vec<u8>,
}
#[derive(Clone, PartialEq, ::prost::Message, serde_derive::Serialize, serde_derive::Deserialize)]
pub struct KeyConfig {
    #[prost(oneof = "key_config::Config", tags = "1, 2")]
    pub config: ::std::option::Option<key_config::Config>,
}
pub mod key_config {
    #[derive(
        Clone, PartialEq, ::prost::Oneof, serde_derive::Serialize, serde_derive::Deserialize,
    )]
    pub enum Config {
        #[prost(message, tag = "1")]
        Aead(super::AeadConfig),
        #[prost(bytes, tag = "2")]
        Sgxfs(std::vec::Vec<u8>),
    }
}
#[derive(Clone, PartialEq, ::prost::Message, serde_derive::Serialize, serde_derive::Deserialize)]
pub struct CreateKeyResponse {
    #[prost(string, tag = "1")]
    pub key_id: std::string::String,
    #[prost(message, optional, tag = "2")]
    pub config: ::std::option::Option<KeyConfig>,
}
#[derive(Clone, PartialEq, ::prost::Message, serde_derive::Serialize, serde_derive::Deserialize)]
pub struct GetKeyRequest {
    #[prost(string, tag = "1")]
    pub key_id: std::string::String,
}
#[derive(Clone, PartialEq, ::prost::Message, serde_derive::Serialize, serde_derive::Deserialize)]
pub struct GetKeyResponse {
    #[prost(message, optional, tag = "1")]
    pub config: ::std::option::Option<KeyConfig>,
}
#[derive(Clone, PartialEq, ::prost::Message, serde_derive::Serialize, serde_derive::Deserialize)]
pub struct DeleteKeyRequest {
    #[prost(string, tag = "1")]
    pub key_id: std::string::String,
}
#[derive(Clone, PartialEq, ::prost::Message, serde_derive::Serialize, serde_derive::Deserialize)]
pub struct DeleteKeyResponse {
    #[prost(message, optional, tag = "1")]
    pub config: ::std::option::Option<KeyConfig>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, ::prost::Enumeration)]
#[repr(i32)]
#[derive(serde_derive::Serialize, serde_derive::Deserialize)]
pub enum EncType {
    Aead = 0,
    Sgxfs = 1,
}
