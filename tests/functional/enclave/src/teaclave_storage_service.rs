use std::prelude::v1::*;
use teaclave_config::RuntimeConfig;
use teaclave_proto::teaclave_storage_service::*;
use teaclave_rpc::endpoint::Endpoint;

pub fn run_tests() -> bool {
    use teaclave_test_utils::*;

    run_tests!(
        test_get_success,
        test_get_fail,
        test_put_success,
        test_delete_success,
        test_enqueue_success,
        test_dequeue_success,
        test_dequeue_fail,
    )
}

fn get_client() -> TeaclaveStorageClient {
    let runtime_config = RuntimeConfig::from_toml("runtime.config.toml").expect("runtime");
    let channel = Endpoint::new(&runtime_config.internal_endpoints.storage.advertised_address)
        .connect()
        .unwrap();
    TeaclaveStorageClient::new(channel).unwrap()
}

fn test_get_success() {
    let mut client = get_client();
    let request = GetRequest::new("test_get_key");
    let response_result = client.get(request);
    info!("{:?}", response_result);
    assert!(response_result.is_ok());
}

fn test_get_fail() {
    let mut client = get_client();
    let request = GetRequest::new("test_key_not_exist");
    let response_result = client.get(request);
    assert!(response_result.is_err());
}

fn test_put_success() {
    let mut client = get_client();
    let request = PutRequest::new("test_put_key", "test_put_value");
    let response_result = client.put(request);
    info!("{:?}", response_result);
    assert!(response_result.is_ok());

    let request = GetRequest::new("test_put_key");
    let response_result = client.get(request);
    info!("{:?}", response_result);
    assert!(response_result.is_ok());
    assert_eq!(response_result.unwrap().value, b"test_put_value");
}

fn test_delete_success() {
    let mut client = get_client();
    let request = DeleteRequest::new("test_delete_key");
    let response_result = client.delete(request);
    info!("{:?}", response_result);
    assert!(response_result.is_ok());

    let request = GetRequest::new("test_delete_key");
    let response_result = client.get(request);
    assert!(response_result.is_err());
}

fn test_enqueue_success() {
    let mut client = get_client();
    let request = EnqueueRequest::new("test_enqueue_key", "test_enqueue_value");
    let response_result = client.enqueue(request);
    info!("{:?}", response_result);
    assert!(response_result.is_ok());
}

fn test_dequeue_success() {
    let mut client = get_client();
    let request = DequeueRequest::new("test_dequeue_key");
    let response_result = client.dequeue(request);
    assert!(response_result.is_err());
    let request = EnqueueRequest::new("test_dequeue_key", "1");
    let response_result = client.enqueue(request);
    assert!(response_result.is_ok());
    let request = EnqueueRequest::new("test_dequeue_key", "2");
    let response_result = client.enqueue(request);
    assert!(response_result.is_ok());
    let request = DequeueRequest::new("test_dequeue_key");
    let response_result = client.dequeue(request);
    assert!(response_result.is_ok());
    assert_eq!(response_result.unwrap().value, b"1");
    let request = DequeueRequest::new("test_dequeue_key");
    let response_result = client.dequeue(request);
    assert!(response_result.is_ok());
    assert_eq!(response_result.unwrap().value, b"2");
}

fn test_dequeue_fail() {
    let mut client = get_client();
    let request = DequeueRequest::new("test_dequeue_key");
    let response_result = client.dequeue(request);
    assert!(response_result.is_err());

    let request = EnqueueRequest::new("test_dequeue_key", "1");
    let response_result = client.enqueue(request);
    assert!(response_result.is_ok());
    let request = DequeueRequest::new("test_dequeue_key");
    let response_result = client.dequeue(request);
    assert!(response_result.is_ok());
    assert_eq!(response_result.unwrap().value, b"1");
    let request = DequeueRequest::new("test_dequeue_key");
    let response_result = client.dequeue(request);
    assert!(response_result.is_err());
}
