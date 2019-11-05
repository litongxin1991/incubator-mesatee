/*
use mesatee_core::db::Memdb;
use lazy_static::lazy_static;
use std::collections::HashSet;

// File
#[derive(Clone)]
struct FileMeta {
    hash: String,
    plaintxt_hash: String,
    size: usize,
    plaintxt_size: usize,
}
#[derive(Clone)]
struct MTFile {
    meta: Option<FileMeta>, // null if it's incomplete;
    owner: String,  // Platform or user-id
    key_id: String, // retrive key from KMS
    physical_access_info: PhysicalAccessInfo,
    description: String,
}

lazy_static! {
    static ref FILE_STORE: Memdb<String, MTFile> = {
        Memdb::<String, MTFile>::open().expect("cannot open db")
    };
    static ref INCOMPLETE_FILE: Memdb<String, MTFile> = {
        Memdb::<String, MTFile>::open().expect("cannot open db")
    };
    static ref USER_FLIE_LIST: Memdb<String, HashSet<String>> = {
        Memdb::<String, HashSet<String>>::open().expect("cannot open db")
    };
}

// Physical Access
#[derive(Clone)]
struct S3Bucket {
    access_id: String,
    access_token: String,
}
#[derive(Clone)]
struct NFSBucket {
    server: String,
    root_dir: String,
}
#[derive(Clone)]
struct LocalBucket {
    root_dir: String,
}
#[derive(Clone)]
struct Bucket {
    owner: String,
    info: BucketInfo,
}
#[derive(Clone)]
enum BucketInfo {
    S3(S3Bucket),
    LOCAL(LocalBucket),
    NFS(NFSBucket),
}
#[derive(Clone)]
struct PhysicalAccessInfo {
    path: Option<String>,
    bucket_id: String, // retrive bucket from BUCKET_STORE
}

lazy_static! {
    static ref BUCKET_STORE: Memdb<String, Bucket> = {
        Memdb::<String, Bucket>::open().expect("cannot open db")
    };
}
*/
