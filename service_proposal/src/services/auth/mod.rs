use crate::proto::credential_proto::Credential;

impl Credential {
    pub fn auth(&self) -> bool {
        return true;
    }
}