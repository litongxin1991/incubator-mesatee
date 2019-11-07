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

use prost_build;
use std::path::PathBuf;

#[derive(Debug)]
pub struct MesaTEEServiceGenerator;

impl prost_build::ServiceGenerator for MesaTEEServiceGenerator {
    fn generate(&mut self, service: prost_build::Service, buf: &mut String) {
        let request_name = format!("{}{}", &service.proto_name, "Request");
        let response_name = format!("{}{}", &service.proto_name, "Response");
        let service_name = format!("{}{}", &service.proto_name, "Service");
        // Generate request enum structure
        buf.push_str(
            "#[derive(Clone, serde_derive::Serialize, serde_derive::Deserialize, Debug)]\n",
        );
        buf.push_str("#[serde(tag = \"type\")]\n");
        buf.push_str(&format!("pub enum {} {{\n", &request_name));
        for method in &service.methods {
            buf.push_str(&format!(
                "    {}({}),\n",
                method.proto_name, method.input_type
            ));
        }
        buf.push_str(&format!("}}\n"));

        // Generate response enum structure
        buf.push_str(
            "#[derive(Clone, serde_derive::Serialize, serde_derive::Deserialize, Debug)]\n",
        );
        buf.push_str("#[serde(tag = \"type\")]\n");
        buf.push_str(&format!("pub enum {} {{\n", &response_name));
        for method in &service.methods {
            buf.push_str(&format!(
                "    {}({}),\n",
                method.proto_name, method.output_type
            ));
        }
        buf.push_str(&format!("}}\n"));

        // Genreate trait
        buf.push_str(&format!("pub trait {} {{\n", &service_name));
        for method in &service.methods {
            buf.push_str(&format!(
                "    fn {}(req: {}) -> mesatee_core::Result<{}>;\n",
                method.name, method.input_type, method.output_type
            ));
        }
        // Generate handle_invoke
        buf.push_str(&format!(
            "    fn handle_invoke(&self, req: {}) -> mesatee_core::Result<{}> {{\n",
            &request_name, &response_name
        ));
        buf.push_str("        match req {\n");
        for method in &service.methods {
            buf.push_str(&format!(
                "            {}::{}(req) => Self::{}(req).map({}::{}),\n",
                &request_name, &method.proto_name, method.name, &response_name, &method.proto_name
            ));
        }
        buf.push_str("        }\n");
        buf.push_str("    }\n");
        buf.push_str("}\n");
    }
}

fn main() {
    let _ = env_logger::init();

    let src = PathBuf::from("src/proto");

    let includes = &[src.clone()];
    let mut config = prost_build::Config::new();
    config.service_generator(Box::new(MesaTEEServiceGenerator));
    config.out_dir(src.clone());
    config.type_attribute(
        ".",
        "#[derive(serde_derive::Serialize, serde_derive::Deserialize)]",
    );
    config
        .compile_protos(&[src.join("kms.proto")], includes)
        .unwrap();
}
