import json

class NexusTypeGenerator:
    def __init__(self, schema_json):
        self.schema = json.loads(schema_json) if isinstance(schema_json, str) else schema_json

    def generate_c_structs(self):
        code = "#include <stdint.h>\n\ntypedef struct {\n"
        for key, value in self.schema.items():
            if isinstance(value, int):
                code += f"    int {key};\n"
            elif isinstance(value, float):
                code += f"    float {key};\n"
            elif isinstance(value, str):
                code += f"    char {key}[256];\n"
            elif isinstance(value, bool):
                code += f"    int {key};\n"
        code += "} GlobalState;\n"
        return code

    def generate_rust_structs(self):
        code = "use serde::{Serialize, Deserialize};\n\n#[derive(Serialize, Deserialize, Debug)]\npub struct GlobalState {\n"
        for key, value in self.schema.items():
            if isinstance(value, int):
                code += f"    pub {key}: i32,\n"
            elif isinstance(value, float):
                code += f"    pub {key}: f32,\n"
            elif isinstance(value, str):
                code += f"    pub {key}: String,\n"
            elif isinstance(value, bool):
                code += f"    pub {key}: bool,\n"
        code += "}\n"
        return code

    def generate_java_class(self):
        code = "package nexus;\n\npublic class GlobalState {\n"
        for key, value in self.schema.items():
            if isinstance(value, int):
                code += f"    public int {key};\n"
            elif isinstance(value, float):
                code += f"    public float {key};\n"
            elif isinstance(value, str):
                code += f"    public String {key};\n"
            elif isinstance(value, bool):
                code += f"    public boolean {key};\n"
        code += "}\n"
        return code
    
    def generate_ts_interface(self):
        code = "export interface GlobalState {\n"
        for key, value in self.schema.items():
            if isinstance(value, int) or isinstance(value, float):
                code += f"  {key}: number;\n"
            elif isinstance(value, str):
                code += f"  {key}: string;\n"
            elif isinstance(value, bool):
                code += f"  {key}: boolean;\n"
        code += "}\n"
        return code
