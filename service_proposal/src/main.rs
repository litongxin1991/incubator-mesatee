// Copyright 2019 MesaTEE Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

mod proto;
mod services;
use crate::services::kms;
use proto::kms_proto::{self, KMSService};
fn main() {
    let service = kms::KMSEnclave;
    let request = kms_proto::KMSRequest::CreateKey(kms_proto::CreateKeyRequest {
        enc_type: kms_proto::EncType::Aead as i32,
    });
    println!("{:?}", request);
    let response = service.handle_invoke(request);
    println!("{:?}", response);
}
