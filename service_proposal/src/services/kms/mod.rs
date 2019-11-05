use crate::proto::kms_proto;
use lazy_static::lazy_static;
use mesatee_core::db::Memdb;
use mesatee_core::{Error, ErrorKind, Result};
use uuid::Uuid;
#[derive(Clone)]
pub struct AEADKeyConfig {
    pub key: [u8; 32],
    pub nonce: [u8; 12],
    pub ad: [u8; 5],
}

impl AEADKeyConfig {
    pub fn new() -> Self {
        use rand::prelude::RngCore;
        let mut key_config = AEADKeyConfig {
            key: [0; 32],
            nonce: [0; 12],
            ad: [0; 5],
        };
        let mut rng = rand::thread_rng();
        rng.fill_bytes(&mut key_config.key);
        rng.fill_bytes(&mut key_config.nonce);
        rng.fill_bytes(&mut key_config.ad);
        key_config
    }
}

pub fn new_sgxfs_key() -> [u8; 16] {
    use rand::prelude::RngCore;
    let mut key = [0; 16];
    let mut rng = rand::thread_rng();
    rng.fill_bytes(&mut key);
    key
}

#[derive(Clone)]
pub enum KeyConfig {
    AEAD(AEADKeyConfig),
    SGXFS([u8; 16]),
}
impl From<AEADKeyConfig> for kms_proto::AeadConfig {
    fn from(config: AEADKeyConfig) -> Self {
        kms_proto::AeadConfig {
            key: config.key.to_vec(),
            nonce: config.nonce.to_vec(),
            ad: config.ad.to_vec(),
        }
    }
}
impl From<KeyConfig> for kms_proto::KeyConfig {
    fn from(config: KeyConfig) -> Self {
        let key_config = match config {
            KeyConfig::AEAD(config) => kms_proto::key_config::Config::Aead(config.into()),
            KeyConfig::SGXFS(key) => kms_proto::key_config::Config::Sgxfs(key.to_vec()),
        };
        kms_proto::KeyConfig {
            config: Some(key_config),
        }
    }
}

lazy_static! {
    pub static ref KEY_STORE: Memdb<String, KeyConfig> =
        { Memdb::<String, KeyConfig>::open().expect("cannot open db") };
}

#[derive(Clone, serde_derive::Serialize, serde_derive::Deserialize, Debug)]
#[serde(tag = "type")]
pub enum KMSRequest {
    Create(kms_proto::CreateKeyRequest),
    Get(kms_proto::GetKeyRequest),
    Delete(kms_proto::DeleteKeyRequest),
}

#[derive(Clone, serde_derive::Serialize, serde_derive::Deserialize, Debug)]
#[serde(tag = "type")]
pub enum KMSResponse {
    Create(kms_proto::CreateKeyResponse),
    Get(kms_proto::GetKeyResponse),
    Delete(kms_proto::DeleteKeyResponse),
}

pub fn get_key(req: kms_proto::GetKeyRequest) -> Result<kms_proto::GetKeyResponse> {
    let key_config = KEY_STORE
        .get(&req.key_id)?
        .ok_or_else(|| Error::from(ErrorKind::MissingValue))?;

    Ok(kms_proto::GetKeyResponse {
        config: Some(key_config.into()),
    })
}

pub fn del_key(req: kms_proto::DeleteKeyRequest) -> Result<kms_proto::DeleteKeyResponse> {
    let key_config = KEY_STORE
        .del(&req.key_id)?
        .ok_or_else(|| Error::from(ErrorKind::MissingValue))?;

    Ok(kms_proto::DeleteKeyResponse {
        config: Some(key_config.into()),
    })
}

pub fn create_key(req: kms_proto::CreateKeyRequest) -> Result<kms_proto::CreateKeyResponse> {
    let config = match kms_proto::EncType::from_i32(req.enc_type) {
        Some(kms_proto::EncType::Aead) => KeyConfig::AEAD(AEADKeyConfig::new()),
        Some(kms_proto::EncType::Sgxfs) => KeyConfig::SGXFS(new_sgxfs_key()),
        None => return Err(Error::from(ErrorKind::InvalidInputError)),
    };

    let key_id = Uuid::new_v4().to_string();
    if KEY_STORE.get(&key_id)?.is_some() {
        return Err(Error::from(ErrorKind::UUIDError));
    }
    KEY_STORE.set(&key_id, &config)?;
    Ok(kms_proto::CreateKeyResponse {
        key_id,
        config: Some(config.into()),
    })
}

pub fn handle_invoke(req: KMSRequest) -> Result<KMSResponse> {
    match req {
        KMSRequest::Create(req) => create_key(req).map(KMSResponse::Create),
        KMSRequest::Get(req) => get_key(req).map(KMSResponse::Get),
        KMSRequest::Delete(req) => del_key(req).map(KMSResponse::Delete),
    }
}
