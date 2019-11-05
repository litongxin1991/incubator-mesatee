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
use proto::kms_proto::EncType;
fn main() {
    let enc: i32 = 0;
    let enc_type: EncType = EncType::Aead;
    assert_eq!(enc, enc_type as i32);
    println!("Hello, world!");
}
