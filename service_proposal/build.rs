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

use std::path::PathBuf;

fn main() {
    let _ = env_logger::init();

    let src = PathBuf::from("src/proto");

    let includes = &[src.clone()];
    let mut config = prost_build::Config::new();
    config.out_dir(src.clone());
    config.type_attribute(
        ".",
        "#[derive(serde_derive::Serialize, serde_derive::Deserialize)]",
    );
    config
        .compile_protos(&[src.join("kms.proto")], includes)
        .unwrap();
}
