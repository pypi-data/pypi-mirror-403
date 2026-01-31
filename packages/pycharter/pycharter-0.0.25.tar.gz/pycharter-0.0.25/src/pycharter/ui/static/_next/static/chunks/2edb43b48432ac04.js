(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["object"==typeof document?document.currentScript:void 0,33558,e=>{"use strict";var t=e.i(43476),a=e.i(71645),i=e.i(19455),r=e.i(61246),o=e.i(75254);let s=(0,o.default)("Play",[["polygon",{points:"6 3 20 12 6 21 6 3",key:"1oa8hb"}]]),n=(0,o.default)("Copy",[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2",key:"17jyea"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2",key:"zix9uf"}]]),l=(0,o.default)("Check",[["path",{d:"M20 6 9 17l-5-5",key:"1gmf2c"}]]);var d=e.i(78583),c=e.i(58041);let m=(0,o.default)("Code",[["polyline",{points:"16 18 22 12 16 6",key:"z7tu5w"}],["polyline",{points:"8 6 2 12 8 18",key:"1eg1df"}]]),p=(0,o.default)("ShieldCheck",[["path",{d:"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",key:"oel41y"}],["path",{d:"m9 12 2 2 4-4",key:"dzmm74"}]]);var u=e.i(42009);e.i(80428);var h=e.i(50398);let _=[{id:"parse_contract",title:"Contract Parser",description:"Read and decompose data contract files",method:"parse_contract(contract_dict, validate=True)",apiEndpoint:"/api/v1/contracts/parse",apiMethod:"POST",exampleRequest:{contract:{schema:{type:"object",properties:{name:{type:"string"},age:{type:"integer"}}},metadata:{title:"User Contract",version:"1.0.0"}}},exampleCode:`from pycharter import parse_contract, parse_contract_file

parse_contract(contract_dict)
parse_contract_file(file_path)`,arguments:[{name:"contract_data",type:"Dict[str, Any]",description:"Contract data as dictionary containing schema, metadata, ownership, governance_rules, coercion_rules, and validation_rules",required:!0},{name:"validate",type:"bool",description:"If True (default), validate contract against schema before parsing",required:!1,default:"True"}],returns:{type:"ContractMetadata",description:"ContractMetadata object with decomposed components (schema, metadata, ownership, governance_rules, coercion_rules, validation_rules) and version tracking"}},{id:"parse_contract_file",title:"Contract Parser - From File",description:"Parse a data contract from an uploaded file (YAML or JSON)",method:"parse_contract_file(file_path, validate=True)",apiEndpoint:"/api/v1/contracts/parse/upload",apiMethod:"POST",exampleRequest:null,exampleCode:`from pycharter import parse_contract_file

# Parse contract from file
contract_metadata = parse_contract_file("contract.yaml")
# or
contract_metadata = parse_contract_file("contract.json", validate=True)`,arguments:[{name:"file_path",type:"str",description:"Path to contract file (YAML or JSON)",required:!0},{name:"validate",type:"bool",description:"If True (default), validate contract against schema before parsing",required:!1,default:"True"}],returns:{type:"ContractMetadata",description:"ContractMetadata object with decomposed components (schema, metadata, ownership, governance_rules, coercion_rules, validation_rules)"}},{id:"build_contract",title:"Contract Builder",description:"Construct consolidated contracts from separate artifacts",method:"build_contract(artifacts: ContractArtifacts, include_metadata=True, include_ownership=True, include_governance=True)",apiEndpoint:"/api/v1/contracts/build",apiMethod:"POST",exampleRequest:{artifacts:{schema:{type:"object",version:"1.0.0",properties:{name:{type:"string"},age:{type:"integer"}}},coercion_rules:{version:"1.0.0",age:"coerce_to_integer"},validation_rules:{version:"1.0.0",age:{greater_than_or_equal_to:{threshold:0}}},metadata:{version:"1.0.0",description:"User contract"}},include_metadata:!0,include_ownership:!0,include_governance:!0},exampleCode:`from pycharter import build_contract, ContractArtifacts

artifacts = ContractArtifacts(
    schema={"type": "object", "version": "1.0.0", "properties": {...}},
    coercion_rules={"version": "1.0.0", "age": "coerce_to_integer"},
    validation_rules={"version": "1.0.0", "age": {...}},
    metadata={"version": "1.0.0", "description": "User contract"}
)
contract = build_contract(artifacts)`,arguments:[{name:"artifacts",type:"ContractArtifacts",description:"ContractArtifacts dataclass containing schema (required), coercion_rules (optional), validation_rules (optional), and metadata (optional)",required:!0},{name:"include_metadata",type:"bool",description:"Whether to include metadata in the contract",required:!1,default:"True"},{name:"include_ownership",type:"bool",description:"Whether to include ownership information",required:!1,default:"True"},{name:"include_governance",type:"bool",description:"Whether to include governance rules",required:!1,default:"True"}],returns:{type:"Dict[str, Any]",description:"Consolidated contract dictionary ready for runtime validation, containing schema (with merged coercion/validation rules), coercion_rules, validation_rules, metadata (if included), and versions tracking dictionary"}},{id:"build_contract_from_store",title:"Contract Builder - From Store",description:"Build a consolidated contract from artifacts stored in metadata store with individual version control for each component",method:"build_contract_from_store(store, schema_title, schema_version=None, coercion_rules_title=None, coercion_rules_version=None, validation_rules_title=None, validation_rules_version=None, metadata_title=None, metadata_version=None)",apiEndpoint:"/api/v1/contracts/build",apiMethod:"POST",exampleRequest:{schema_title:"user_schema",schema_version:"1.0.0",coercion_rules_title:"user_schema",coercion_rules_version:"1.0.0",validation_rules_title:"user_schema",validation_rules_version:"1.0.0",metadata_title:"user_schema",metadata_version:"1.0.0"},exampleCode:`from pycharter import build_contract_from_store

store = PostgresMetadataStore(connection_string)
store.connect()
contract = build_contract_from_store(
    store=store,
    schema_title="user_schema",
    schema_version="1.0.0",
    coercion_rules_title="user_schema",
    coercion_rules_version="1.0.0",
    validation_rules_title="user_schema",
    validation_rules_version="1.0.0",
    metadata_title="user_schema",
    metadata_version="1.0.0"
)`,arguments:[{name:"store",type:"MetadataStoreClient",description:"MetadataStoreClient instance connected to the metadata store",required:!0},{name:"schema_title",type:"str",description:"Schema title/identifier",required:!0},{name:"schema_version",type:"Optional[str]",description:"Optional schema version (if None, uses latest version)",required:!1,default:"None"},{name:"coercion_rules_title",type:"Optional[str]",description:"Optional coercion rules title/identifier (if None, uses schema_title)",required:!1,default:"None"},{name:"coercion_rules_version",type:"Optional[str]",description:"Optional coercion rules version (if None, uses latest version or schema_version)",required:!1,default:"None"},{name:"validation_rules_title",type:"Optional[str]",description:"Optional validation rules title/identifier (if None, uses schema_title)",required:!1,default:"None"},{name:"validation_rules_version",type:"Optional[str]",description:"Optional validation rules version (if None, uses latest version or schema_version)",required:!1,default:"None"},{name:"metadata_title",type:"Optional[str]",description:"Optional metadata title/identifier (if None, uses schema_title)",required:!1,default:"None"},{name:"metadata_version",type:"Optional[str]",description:"Optional metadata version (if None, uses latest version or schema_version)",required:!1,default:"None"}],returns:{type:"Dict[str, Any]",description:"Consolidated contract dictionary ready for runtime validation, containing schema (with merged coercion/validation rules), coercion_rules, validation_rules, metadata (if included), and versions tracking dictionary"}},{id:"store_schema",title:"Metadata Store - Store Schema",description:"Store a JSON Schema in the metadata store",method:"store.store_schema(schema_name, schema, version)",apiEndpoint:"/api/v1/metadata/schemas",apiMethod:"POST",exampleRequest:{schema_name:"user_schema",schema:{type:"object",properties:{name:{type:"string"},age:{type:"integer"}}},version:"1.0.0"},exampleCode:`from pycharter import MetadataStoreClient

store = MetadataStoreClient(database_url)
store.store_schema(schema_id, schema, version)
store.get_schema(schema_id, version)
store.store_metadata(schema_id, metadata, version)`,arguments:[{name:"schema_name",type:"str",description:"Name/identifier for the schema (used as data_contract name)",required:!0},{name:"schema",type:"Dict[str, Any]",description:'JSON Schema dictionary (must contain "version" field or it will be added)',required:!0},{name:"version",type:"str",description:'Required version string (must match schema["version"] if present)',required:!0}],returns:{type:"str",description:"Schema ID or identifier"}},{id:"get_schema",title:"Metadata Store - Get Schema",description:"Retrieve a schema from the metadata store",method:"store.get_schema(schema_id, version=None)",apiEndpoint:"/api/v1/metadata/schemas/{schema_id}",apiMethod:"GET",exampleRequest:null,exampleCode:`from pycharter import MetadataStoreClient

store = MetadataStoreClient(database_url)
store.get_schema(schema_id, version)`,arguments:[{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"version",type:"Optional[str]",description:"Optional version string (if None, returns latest version)",required:!1,default:"None"}],returns:{type:"Optional[Dict[str, Any]]",description:"Schema dictionary with version included, or None if not found"}},{id:"list_schemas",title:"Metadata Store - List Schemas",description:"Retrieve a list of all schemas stored in the metadata store",method:"store.list_schemas()",apiEndpoint:"/api/v1/metadata/schemas",apiMethod:"GET",exampleRequest:null,exampleCode:`from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(connection_string)
store.connect()

# List all schemas
schemas = store.list_schemas()
for schema in schemas:
    print(f"Schema: {schema.get('name')}, Version: {schema.get('version')}")`,arguments:[],returns:{type:"List[Dict[str, Any]]",description:"List of schema metadata dictionaries, each containing id, name, title, and version"}},{id:"store_metadata",title:"Metadata Store - Store Metadata",description:"Store metadata (ownership, governance rules, etc.) for a schema",method:"store.store_metadata(schema_id, metadata, version=None)",apiEndpoint:"/api/v1/metadata/metadata",apiMethod:"POST",exampleRequest:{schema_id:"user_schema",metadata:{title:"user_schema_metadata",description:"Metadata for user schema",business_owners:["owner@example.com"],team:"data-engineering",governance_rules:{data_retention:{days:2555},access_control:{level:"public"}}},version:"1.0.0"},exampleCode:`from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(connection_string)
store.connect()

# Store metadata for a schema
metadata_id = store.store_metadata(
    schema_id='user_schema',
    metadata={
        'title': 'user_schema_metadata',
        'description': 'Metadata for user schema',
        'business_owners': ['owner@example.com'],
        'team': 'data-engineering',
        'governance_rules': {
            'data_retention': {'days': 2555},
            'access_control': {'level': 'public'}
        }
    },
    version='1.0.0'
)`,arguments:[{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"metadata",type:"Dict[str, Any]",description:"Metadata dictionary containing ownership, governance_rules, and other metadata",required:!0},{name:"version",type:"Optional[str]",description:"Optional version string (if None, uses schema version)",required:!1,default:"None"}],returns:{type:"str",description:"Metadata record ID"}},{id:"get_metadata",title:"Metadata Store - Get Metadata",description:"Retrieve metadata for a schema from the metadata store",method:"store.get_metadata(schema_id, version=None)",apiEndpoint:"/api/v1/metadata/metadata/{schema_id}",apiMethod:"GET",exampleRequest:null,exampleCode:`from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(connection_string)
store.connect()

# Get metadata for a schema
metadata = store.get_metadata(
    schema_id='user_schema',
    version='1.0.0'  # Optional, defaults to latest
)`,arguments:[{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"version",type:"Optional[str]",description:"Optional version string (if None, uses latest version)",required:!1,default:"None"}],returns:{type:"Optional[Dict[str, Any]]",description:"Metadata dictionary or None if not found"}},{id:"get_complete_schema",title:"Metadata Store - Get Complete Schema",description:"Retrieve a complete schema with coercion and validation rules merged",method:"store.get_complete_schema(schema_id, version=None)",apiEndpoint:"/api/v1/metadata/schemas/{schema_id}/complete",apiMethod:"GET",exampleRequest:null,exampleCode:`from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(connection_string)
store.connect()

# Get complete schema with rules merged
complete_schema = store.get_complete_schema(
    schema_id='user_schema',
    version='1.0.0'  # Optional, defaults to latest
)
# The schema now includes coercion and validation rules
# merged into the properties`,arguments:[{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"version",type:"Optional[str]",description:"Optional version string (if None, defaults to latest)",required:!1,default:"None"}],returns:{type:"Optional[Dict[str, Any]]",description:"Complete schema dictionary with coercion and validation rules merged into the properties, or None if not found"}},{id:"store_coercion_rules",title:"Metadata Store - Store Coercion Rules",description:"Store coercion rules that define how data should be transformed before validation",method:"store.store_coercion_rules(schema_id, coercion_rules, version=None)",apiEndpoint:"/api/v1/metadata/coercion-rules",apiMethod:"POST",exampleRequest:{schema_id:"user_schema",coercion_rules:{age:"coerce_to_integer",email:"coerce_to_lowercase",price:"coerce_to_float",name:"coerce_to_stripped_string"},version:"1.0.0"},exampleCode:`from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(connection_string)
store.connect()

# Store coercion rules for a schema
rule_id = store.store_coercion_rules(
    schema_id='user_schema',
    coercion_rules={
        'age': 'coerce_to_integer',
        'email': 'coerce_to_lowercase',
        'name': 'coerce_to_stripped_string'
    },
    version='1.0.0'
)`,arguments:[{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"coercion_rules",type:"Dict[str, Any]",description:'Dictionary mapping field names to coercion rule types (e.g., "coerce_to_integer", "coerce_to_lowercase")',required:!0},{name:"version",type:"Optional[str]",description:"Optional version string (if None, uses schema version)",required:!1,default:"None"}],returns:{type:"str",description:"Coercion rule record ID"}},{id:"get_coercion_rules",title:"Metadata Store - Get Coercion Rules",description:"Retrieve coercion rules for a schema from the metadata store",method:"store.get_coercion_rules(schema_id, version=None)",apiEndpoint:"/api/v1/metadata/coercion-rules/{schema_id}",apiMethod:"GET",exampleRequest:null,exampleCode:`from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(connection_string)
store.connect()

# Get coercion rules for a schema
coercion_rules = store.get_coercion_rules(
    schema_id='user_schema',
    version='1.0.0'  # Optional, defaults to latest
)`,arguments:[{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"version",type:"Optional[str]",description:"Optional version string (if None, defaults to latest)",required:!1,default:"None"}],returns:{type:"Optional[Dict[str, Any]]",description:"Coercion rules dictionary mapping field names to coercion types, or None if not found"}},{id:"store_validation_rules",title:"Metadata Store - Store Validation Rules",description:"Store validation rules that define custom validation logic beyond JSON Schema",method:"store.store_validation_rules(schema_id, validation_rules, version=None)",apiEndpoint:"/api/v1/metadata/validation-rules",apiMethod:"POST",exampleRequest:{schema_id:"user_schema",validation_rules:{age:{greater_than_or_equal_to:{threshold:0},less_than_or_equal_to:{threshold:150}},email:{min_length:{threshold:5},matches_pattern:{pattern:"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}}},version:"1.0.0"},exampleCode:`from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(connection_string)
store.connect()

# Store validation rules for a schema
rule_id = store.store_validation_rules(
    schema_id='user_schema',
    validation_rules={
        'age': {
            'greater_than_or_equal_to': {'threshold': 0},
            'less_than_or_equal_to': {'threshold': 150}
        },
        'email': {
            'min_length': {'threshold': 5},
            'matches_pattern': {'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'}
        }
    },
    version='1.0.0'
)`,arguments:[{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"validation_rules",type:"Dict[str, Any]",description:'Dictionary mapping field names to validation rule dictionaries (e.g., {"age": {"greater_than_or_equal_to": {"threshold": 0}}})',required:!0},{name:"version",type:"Optional[str]",description:"Optional version string (if None, uses schema version)",required:!1,default:"None"}],returns:{type:"str",description:"Validation rule record ID"}},{id:"get_validation_rules",title:"Metadata Store - Get Validation Rules",description:"Retrieve validation rules for a schema from the metadata store",method:"store.get_validation_rules(schema_id, version=None)",apiEndpoint:"/api/v1/metadata/validation-rules/{schema_id}",apiMethod:"GET",exampleRequest:null,exampleCode:`from pycharter import PostgresMetadataStore

store = PostgresMetadataStore(connection_string)
store.connect()

# Get validation rules for a schema
validation_rules = store.get_validation_rules(
    schema_id='user_schema',
    version='1.0.0'  # Optional, defaults to latest
)`,arguments:[{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"version",type:"Optional[str]",description:"Optional version string (if None, defaults to latest)",required:!1,default:"None"}],returns:{type:"Optional[Dict[str, Any]]",description:"Validation rules dictionary mapping field names to validation rule dictionaries, or None if not found"}},{id:"generate_model",title:"Pydantic Generator",description:"Generate Pydantic models from JSON Schema",method:'generate_model(schema, model_name="DynamicModel")',apiEndpoint:"/api/v1/schemas/generate",apiMethod:"POST",exampleRequest:{schema:{type:"object",properties:{name:{type:"string"},age:{type:"integer"}}},model_name:"User"},exampleCode:`from pycharter import generate_model, generate_model_file, from_dict, from_file, from_json, from_url

# Advanced: More control
UserModel = generate_model(schema_dict, model_name="User")

# Quick helpers: Generate and return model
UserModel = from_dict(schema_dict)  # From dictionary
UserModel = from_file("schema.json")  # From file
UserModel = from_json(json_string)  # From JSON string
UserModel = from_url("https://example.com/schema.json")  # From URL

# Generate model and save to file
generate_model_file(schema_dict, "models.py", model_name="User")`,arguments:[{name:"schema",type:"Dict[str, Any]",description:"JSON Schema dictionary",required:!0},{name:"model_name",type:"str",description:"Name for the generated Pydantic model class",required:!1,default:'"DynamicModel"'}],returns:{type:"Type[BaseModel]",description:"A Pydantic model class generated from the schema"}},{id:"from_dict",title:"Generate Model from Dict",description:"Quick helper: Generate Pydantic model from JSON Schema dictionary",method:"from_dict(schema_dict)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import from_dict

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    }
}

UserModel = from_dict(schema)
user = UserModel(name="Alice", age=30)`,arguments:[{name:"schema_dict",type:"Dict[str, Any]",description:"JSON Schema dictionary",required:!0}],returns:{type:"Type[BaseModel]",description:"Pydantic model class generated from the schema"}},{id:"from_file",title:"Generate Model from File",description:"Quick helper: Generate Pydantic model from JSON Schema file",method:"from_file(file_path)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import from_file

UserModel = from_file("schema.json")
# or
UserModel = from_file("schema.yaml")`,arguments:[{name:"file_path",type:"str",description:"Path to JSON Schema file (JSON or YAML)",required:!0}],returns:{type:"Type[BaseModel]",description:"Pydantic model class generated from the schema file"}},{id:"from_json",title:"Generate Model from JSON String",description:"Quick helper: Generate Pydantic model from JSON Schema JSON string",method:"from_json(json_string)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import from_json

json_schema = '{"type": "object", "properties": {"name": {"type": "string"}}}'
UserModel = from_json(json_schema)`,arguments:[{name:"json_string",type:"str",description:"JSON Schema as JSON string",required:!0}],returns:{type:"Type[BaseModel]",description:"Pydantic model class generated from the JSON string"}},{id:"from_url",title:"Generate Model from URL",description:"Quick helper: Generate Pydantic model from JSON Schema URL",method:"from_url(url)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import from_url

UserModel = from_url("https://example.com/schema.json")`,arguments:[{name:"url",type:"str",description:"URL to JSON Schema file",required:!0}],returns:{type:"Type[BaseModel]",description:"Pydantic model class generated from the URL"}},{id:"generate_model_file",title:"Generate Model File",description:"Generate Pydantic model and save to Python file",method:'generate_model_file(schema, output_file, model_name="DynamicModel")',apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import generate_model_file

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    }
}

generate_model_file(
    schema=schema,
    output_file="models.py",
    model_name="User"
)`,arguments:[{name:"schema",type:"Dict[str, Any]",description:"JSON Schema dictionary",required:!0},{name:"output_file",type:"str",description:"Path to output Python file",required:!0},{name:"model_name",type:"str",description:"Name for the generated Pydantic model class",required:!1,default:'"DynamicModel"'}],returns:{type:"None",description:"Saves the generated model to the specified file"}},{id:"model_to_schema",title:"JSON Schema Converter (Advanced)",description:"Convert Pydantic models to JSON Schema - core conversion function",method:"model_to_schema(model_class)",apiEndpoint:"/api/v1/schemas/convert",apiMethod:"POST",exampleRequest:{model_class:"pydantic.BaseModel"},exampleCode:`from pycharter import model_to_schema
from pydantic import BaseModel

class UserModel(BaseModel):
    name: str
    age: int

schema = model_to_schema(UserModel)
print(schema)`,arguments:[{name:"model_class",type:"Type[BaseModel] | str",description:'Pydantic model class or fully qualified class name (e.g., "mymodule.UserModel")',required:!0}],returns:{type:"Dict[str, Any]",description:"JSON Schema dictionary with optional title and version fields"}},{id:"to_dict",title:"Convert Model to Dict",description:"Quick helper: Convert Pydantic model to JSON Schema dictionary",method:"to_dict(model_class)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import to_dict
from pydantic import BaseModel

class UserModel(BaseModel):
    name: str
    age: int

schema = to_dict(UserModel)`,arguments:[{name:"model_class",type:"Type[BaseModel] | str",description:"Pydantic model class or fully qualified class name",required:!0}],returns:{type:"Dict[str, Any]",description:"JSON Schema dictionary"}},{id:"to_json",title:"Convert Model to JSON String",description:"Quick helper: Convert Pydantic model to JSON Schema JSON string",method:"to_json(model_class)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import to_json
from pydantic import BaseModel

class UserModel(BaseModel):
    name: str
    age: int

json_schema = to_json(UserModel)
print(json_schema)`,arguments:[{name:"model_class",type:"Type[BaseModel] | str",description:"Pydantic model class or fully qualified class name",required:!0}],returns:{type:"str",description:"JSON Schema as JSON string"}},{id:"to_file",title:"Convert Model to File",description:"Quick helper: Convert Pydantic model to JSON Schema file",method:"to_file(model_class, file_path)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import to_file
from pydantic import BaseModel

class UserModel(BaseModel):
    name: str
    age: int

to_file(UserModel, "schema.json")
# or
to_file(UserModel, "schema.yaml")`,arguments:[{name:"model_class",type:"Type[BaseModel] | str",description:"Pydantic model class or fully qualified class name",required:!0},{name:"file_path",type:"str",description:"Path to output file (JSON or YAML)",required:!0}],returns:{type:"None",description:"Saves the JSON Schema to the specified file"}},{id:"validator_class",title:"Validator Class (PRIMARY INTERFACE)",description:"⭐ PRIMARY: Use Validator class for all validation - best performance and flexibility",method:"Validator(contract_dir=None, contract_file=None, contract_dict=None, contract_metadata=None, store=None, schema_id=None, schema_version=None)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import Validator, create_validator
from pycharter.metadata_store import SQLiteMetadataStore

# From contract directory
validator = Validator(contract_dir="data/contracts/user")
result = validator.validate({"name": "Alice", "age": 30})

# From metadata store
store = SQLiteMetadataStore("metadata.db")
store.connect()
validator = Validator(store=store, schema_id="user_schema")
result = validator.validate({"name": "Alice", "age": 30})

# From contract file
validator = Validator(contract_file="contracts/user.yaml")
result = validator.validate({"name": "Alice", "age": 30})

# Batch validation
results = validator.validate_batch([
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
])

# Factory function
validator = create_validator(contract_file="contract.yaml")`,arguments:[{name:"contract_dir",type:"Optional[str]",description:"Directory containing contract files (schema.yaml, coercion_rules.yaml, validation_rules.yaml)",required:!1},{name:"contract_file",type:"Optional[str]",description:"Path to complete contract file (YAML/JSON)",required:!1},{name:"contract_dict",type:"Optional[Dict[str, Any]]",description:"Contract as dictionary with schema, coercion_rules, validation_rules keys",required:!1},{name:"contract_metadata",type:"Optional[ContractMetadata]",description:"ContractMetadata object (from parse_contract)",required:!1},{name:"store",type:"Optional[MetadataStoreClient]",description:"MetadataStoreClient instance (for loading from metadata store)",required:!1},{name:"schema_id",type:"Optional[str]",description:"Schema identifier (required when using store)",required:!1},{name:"schema_version",type:"Optional[str]",description:"Optional schema version (defaults to latest when using store)",required:!1}],returns:{type:"Validator",description:"Validator instance with validate() and validate_batch() methods"}},{id:"validate_with_store",title:"Validate with Store (Convenience)",description:"Quick validation using schema from metadata store",method:"validate_with_store(store, schema_id, data, version=None, strict=False)",apiEndpoint:"/api/v1/validation/validate",apiMethod:"POST",exampleRequest:{schema_id:"user_schema",data:{name:"Alice",age:30},version:"1.0.0",strict:!1},exampleCode:`from pycharter import validate_with_store
from pycharter.metadata_store import SQLiteMetadataStore

store = SQLiteMetadataStore("metadata.db")
store.connect()

result = validate_with_store(
    store=store,
    schema_id="user_schema",
    data={"name": "Alice", "age": 30},
    version="1.0.0"
)

if result.is_valid:
    print("Valid data:", result.data)
else:
    print("Errors:", result.errors)`,arguments:[{name:"store",type:"MetadataStoreClient",description:"MetadataStoreClient instance",required:!0},{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"data",type:"Dict[str, Any]",description:"Data dictionary to validate",required:!0},{name:"version",type:"Optional[str]",description:"Optional schema version (if None, uses latest)",required:!1,default:"None"},{name:"strict",type:"bool",description:"If True, raise exceptions on validation errors",required:!1,default:"False"}],returns:{type:"ValidationResult",description:"ValidationResult object with is_valid flag, validated data (if valid), and list of errors (if invalid)"}},{id:"validate_with_contract",title:"Validate with Contract (Convenience)",description:"Quick validation using contract dictionary or file",method:"validate_with_contract(contract, data, strict=False)",apiEndpoint:"/api/v1/validation/validate",apiMethod:"POST",exampleRequest:{contract:{schema:{type:"object",properties:{name:{type:"string"},age:{type:"integer"}}}},data:{name:"Alice",age:30},strict:!1},exampleCode:`from pycharter import validate_with_contract

contract = {
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }
}

result = validate_with_contract(
    contract=contract,
    data={"name": "Alice", "age": 30}
)

# Or from file
result = validate_with_contract(
    contract="contracts/user.yaml",
    data={"name": "Alice", "age": 30}
)`,arguments:[{name:"contract",type:"Dict[str, Any] | ContractMetadata | str",description:"Contract dictionary, ContractMetadata object, or file path",required:!0},{name:"data",type:"Dict[str, Any]",description:"Data dictionary to validate",required:!0},{name:"strict",type:"bool",description:"If True, raise exceptions on validation errors",required:!1,default:"False"}],returns:{type:"ValidationResult",description:"ValidationResult object with is_valid flag, validated data (if valid), and list of errors (if invalid)"}},{id:"validate_batch_with_store",title:"Batch Validate with Store",description:"Validate multiple records using schema from metadata store",method:"validate_batch_with_store(store, schema_id, data_list, version=None, strict=False)",apiEndpoint:"/api/v1/validation/validate-batch",apiMethod:"POST",exampleRequest:{schema_id:"user_schema",data_list:[{name:"Alice",age:30},{name:"Bob",age:25}],version:"1.0.0",strict:!1},exampleCode:`from pycharter import validate_batch_with_store
from pycharter.metadata_store import SQLiteMetadataStore

store = SQLiteMetadataStore("metadata.db")
store.connect()

results = validate_batch_with_store(
    store=store,
    schema_id="user_schema",
    data_list=[
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ],
    version="1.0.0"
)

print(f"Valid: {results.total_count - len(results.errors)}/{results.total_count}")`,arguments:[{name:"store",type:"MetadataStoreClient",description:"MetadataStoreClient instance",required:!0},{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"data_list",type:"List[Dict[str, Any]]",description:"List of data dictionaries to validate",required:!0},{name:"version",type:"Optional[str]",description:"Optional schema version (if None, uses latest)",required:!1,default:"None"},{name:"strict",type:"bool",description:"If True, raise exceptions on validation errors",required:!1,default:"False"}],returns:{type:"ValidationBatchResponse",description:"Batch validation results with total_count, valid_count, error_count, and results list"}},{id:"validate_batch_with_contract",title:"Batch Validate with Contract",description:"Validate multiple records using contract dictionary or file",method:"validate_batch_with_contract(contract, data_list, strict=False)",apiEndpoint:"/api/v1/validation/validate-batch",apiMethod:"POST",exampleRequest:{contract:{schema:{type:"object",properties:{name:{type:"string"},age:{type:"integer"}}}},data_list:[{name:"Alice",age:30},{name:"Bob",age:25}],strict:!1},exampleCode:`from pycharter import validate_batch_with_contract

contract = {
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }
}

results = validate_batch_with_contract(
    contract=contract,
    data_list=[
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ]
)`,arguments:[{name:"contract",type:"Dict[str, Any] | ContractMetadata | str",description:"Contract dictionary, ContractMetadata object, or file path",required:!0},{name:"data_list",type:"List[Dict[str, Any]]",description:"List of data dictionaries to validate",required:!0},{name:"strict",type:"bool",description:"If True, raise exceptions on validation errors",required:!1,default:"False"}],returns:{type:"ValidationBatchResponse",description:"Batch validation results with total_count, valid_count, error_count, and results list"}},{id:"get_model_from_store",title:"Get Model from Store",description:"Get Pydantic model class from schema stored in metadata store",method:"get_model_from_store(store, schema_id, version=None)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import get_model_from_store
from pycharter.metadata_store import SQLiteMetadataStore

store = SQLiteMetadataStore("metadata.db")
store.connect()

# Get Pydantic model class
UserModel = get_model_from_store(
    store=store,
    schema_id="user_schema",
    version="1.0.0"
)

# Use the model directly
user = UserModel(name="Alice", age=30)
print(user.model_dump())`,arguments:[{name:"store",type:"MetadataStoreClient",description:"MetadataStoreClient instance",required:!0},{name:"schema_id",type:"str",description:"Schema identifier",required:!0},{name:"version",type:"Optional[str]",description:"Optional schema version (if None, uses latest)",required:!1,default:"None"}],returns:{type:"Type[BaseModel]",description:"Pydantic model class generated from the schema"}},{id:"get_model_from_contract",title:"Get Model from Contract",description:"Get Pydantic model class from contract dictionary or file",method:"get_model_from_contract(contract)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import get_model_from_contract

contract = {
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }
}

# Get Pydantic model class
UserModel = get_model_from_contract(contract)

# Use the model directly
user = UserModel(name="Alice", age=30)
print(user.model_dump())

# Or from file
UserModel = get_model_from_contract("contracts/user.yaml")`,arguments:[{name:"contract",type:"Dict[str, Any] | ContractMetadata | str",description:"Contract dictionary, ContractMetadata object, or file path",required:!0}],returns:{type:"Type[BaseModel]",description:"Pydantic model class generated from the contract schema"}},{id:"validate",title:"Validate (Low-level)",description:"Low-level validation with existing Pydantic model",method:"validate(data, model, coercion_rules=None, validation_rules=None, strict=False)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import validate
from pydantic import BaseModel

# Define model manually or get from contract
class UserModel(BaseModel):
    name: str
    age: int

# Validate with model
result = validate(
    data={"name": "Alice", "age": 30},
    model=UserModel,
    coercion_rules=None,
    validation_rules=None
)

if result.is_valid:
    print("Valid:", result.data)
else:
    print("Errors:", result.errors)`,arguments:[{name:"data",type:"Dict[str, Any]",description:"Data dictionary to validate",required:!0},{name:"model",type:"Type[BaseModel]",description:"Pydantic model class",required:!0},{name:"coercion_rules",type:"Optional[Dict[str, Any]]",description:"Optional coercion rules dictionary",required:!1,default:"None"},{name:"validation_rules",type:"Optional[Dict[str, Any]]",description:"Optional validation rules dictionary",required:!1,default:"None"},{name:"strict",type:"bool",description:"If True, raise exceptions on validation errors",required:!1,default:"False"}],returns:{type:"ValidationResult",description:"ValidationResult object with is_valid flag, validated data (if valid), and list of errors (if invalid)"}},{id:"validate_batch",title:"Batch Validate (Low-level)",description:"Low-level batch validation with existing Pydantic model",method:"validate_batch(data_list, model, coercion_rules=None, validation_rules=None, strict=False)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import validate_batch
from pydantic import BaseModel

# Define model manually or get from contract
class UserModel(BaseModel):
    name: str
    age: int

# Batch validate with model
results = validate_batch(
    data_list=[
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ],
    model=UserModel
)

print(f"Valid: {results.valid_count}/{results.total_count}")`,arguments:[{name:"data_list",type:"List[Dict[str, Any]]",description:"List of data dictionaries to validate",required:!0},{name:"model",type:"Type[BaseModel]",description:"Pydantic model class",required:!0},{name:"coercion_rules",type:"Optional[Dict[str, Any]]",description:"Optional coercion rules dictionary",required:!1,default:"None"},{name:"validation_rules",type:"Optional[Dict[str, Any]]",description:"Optional validation rules dictionary",required:!1,default:"None"},{name:"strict",type:"bool",description:"If True, raise exceptions on validation errors",required:!1,default:"False"}],returns:{type:"ValidationBatchResponse",description:"Batch validation results with total_count, valid_count, error_count, and results list"}},{id:"quality_check",title:"QualityCheck Class (PRIMARY INTERFACE)",description:"⭐ PRIMARY: Use QualityCheck class for quality assurance - monitor data quality, calculate metrics, and track violations",method:"QualityCheck(store=None, db_session=None).run(schema_id=None, contract=None, data=None, options=None)",apiEndpoint:"/api/v1/quality/check",apiMethod:"POST",exampleRequest:{schema_id:"user_schema",data:[{name:"Alice",age:30},{name:"Bob",age:25}],calculate_metrics:!0,record_violations:!0},exampleCode:`from pycharter import QualityCheck, QualityCheckOptions, QualityReport, QualityThresholds
from pycharter.metadata_store import SQLiteMetadataStore
from sqlalchemy.orm import Session

# Create quality check instance
store = SQLiteMetadataStore("metadata.db")
store.connect()
db_session = Session()  # Your database session

check = QualityCheck(store=store, db_session=db_session)

# Configure options
options = QualityCheckOptions(
    record_violations=True,
    calculate_metrics=True,
    check_thresholds=True,
    include_field_metrics=True,
    sample_size=None  # Process all data
)

# Set thresholds (optional)
thresholds = QualityThresholds(
    overall_score_min=80.0,
    accuracy_min=95.0,
    completeness_min=90.0
)

# Run quality check
report = check.run(
    schema_id='user_schema',
    data="data/users.json",  # File path, list, or callable
    options=options
)

# Access results
print(f"Quality Score: {report.quality_score.overall_score:.2f}/100")
print(f"Passed: {report.passed}")
print(f"Metrics: {report.metrics}")
print(f"Violations: {len(report.violations)}")`,arguments:[{name:"store",type:"Optional[MetadataStoreClient]",description:"Optional metadata store for retrieving contracts and storing violations",required:!1,default:"None"},{name:"db_session",type:"Optional[Session]",description:"Optional SQLAlchemy database session for persisting metrics and violations",required:!1,default:"None"},{name:"schema_id",type:"Optional[str]",description:"Schema ID (if using store-based validation)",required:!1},{name:"contract",type:"Optional[Dict[str, Any] | str]",description:"Contract dictionary or file path (if using contract-based validation)",required:!1},{name:"data",type:"List[Dict[str, Any]] | str | Callable",description:"Data to validate. Can be a list of dictionaries, file path (JSON/CSV), or callable that returns data",required:!0},{name:"options",type:"Optional[QualityCheckOptions]",description:"Quality check options including record_violations, calculate_metrics, check_thresholds, include_field_metrics, sample_size, data_source, data_version, etc.",required:!1,default:"None"}],returns:{type:"QualityReport",description:"QualityReport object containing validation results, quality score (QualityScore), field metrics (FieldQualityMetrics), violations (List[ViolationRecord]), and threshold breaches"}},{id:"quality_check_options",title:"QualityCheckOptions",description:"Configuration options for quality checks",method:"QualityCheckOptions(record_violations=True, calculate_metrics=True, check_thresholds=False, include_field_metrics=True, sample_size=None, data_source=None, data_version=None, skip_if_unchanged=False)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import QualityCheckOptions

options = QualityCheckOptions(
    record_violations=True,      # Record violations to database
    calculate_metrics=True,      # Calculate quality metrics
    check_thresholds=False,      # Check against quality thresholds
    include_field_metrics=True,  # Include field-level metrics
    sample_size=1000,            # Sample size for large datasets
    data_source="users.csv",     # Data source identifier
    data_version="v1.0",         # Data version identifier
    skip_if_unchanged=True       # Skip if data hasn't changed
)`,arguments:[{name:"record_violations",type:"bool",description:"Whether to record violations to database",required:!1,default:"True"},{name:"calculate_metrics",type:"bool",description:"Whether to calculate quality metrics",required:!1,default:"True"},{name:"check_thresholds",type:"bool",description:"Whether to check against quality thresholds",required:!1,default:"False"},{name:"include_field_metrics",type:"bool",description:"Whether to include field-level quality metrics",required:!1,default:"True"},{name:"sample_size",type:"Optional[int]",description:"Sample size for large datasets (None = process all)",required:!1,default:"None"},{name:"data_source",type:"Optional[str]",description:"Data source identifier (e.g., file name)",required:!1,default:"None"},{name:"data_version",type:"Optional[str]",description:"Data version identifier",required:!1,default:"None"},{name:"skip_if_unchanged",type:"bool",description:"Skip quality check if data fingerprint hasn't changed",required:!1,default:"False"}],returns:{type:"QualityCheckOptions",description:"QualityCheckOptions instance for configuring quality checks"}},{id:"quality_thresholds",title:"QualityThresholds",description:"Define quality thresholds for monitoring and alerting",method:"QualityThresholds(overall_score_min=None, accuracy_min=None, completeness_min=None, violation_rate_max=None, field_thresholds=None)",apiEndpoint:null,apiMethod:"N/A",exampleRequest:null,exampleCode:`from pycharter import QualityThresholds

thresholds = QualityThresholds(
    overall_score_min=80.0,        # Minimum overall quality score
    accuracy_min=95.0,              # Minimum accuracy percentage
    completeness_min=90.0,           # Minimum completeness percentage
    violation_rate_max=0.05,        # Maximum violation rate (5%)
    field_thresholds={              # Field-specific thresholds
        "email": {"completeness_min": 98.0},
        "age": {"accuracy_min": 99.0}
    }
)`,arguments:[{name:"overall_score_min",type:"Optional[float]",description:"Minimum overall quality score (0-100)",required:!1,default:"None"},{name:"accuracy_min",type:"Optional[float]",description:"Minimum accuracy percentage (0-100)",required:!1,default:"None"},{name:"completeness_min",type:"Optional[float]",description:"Minimum completeness percentage (0-100)",required:!1,default:"None"},{name:"violation_rate_max",type:"Optional[float]",description:"Maximum violation rate (0-1)",required:!1,default:"None"},{name:"field_thresholds",type:"Optional[Dict[str, Dict[str, float]]]",description:'Field-specific thresholds (e.g., {"email": {"completeness_min": 98.0}})',required:!1,default:"None"}],returns:{type:"QualityThresholds",description:"QualityThresholds instance for defining quality requirements"}}];function f({method:o}){let[d,c]=(0,a.useState)(o.exampleRequest?JSON.stringify(o.exampleRequest,null,2):""),[m,p]=(0,a.useState)(null),[u,h]=(0,a.useState)(null),[_,f]=(0,a.useState)(!1),[y,v]=(0,a.useState)(!1);if(!o.apiEndpoint)return null;let g=o.apiEndpoint?.includes("/upload")??!1,x=async()=>{f(!0),h(null);try{let t,a,{getApiBaseUrl:i}=await e.A(36909),r=i(),s=o.apiEndpoint;if(!s){h({success:!1,error:"This method does not have an API endpoint (Python-only)"}),f(!1);return}s.includes("{schema_id}")&&(s=s.replace("{schema_id}","user_schema"));let n=`${r}${s}`;if("GET"===o.apiMethod)t=await fetch(n);else if(g){if(!m){h({success:!1,error:"Please select a file to upload"}),f(!1);return}let e=new FormData;e.append("file",m),s.includes("/contracts/parse/upload")&&e.append("validate","true"),t=await fetch(n,{method:o.apiMethod,body:e})}else{let e=d?JSON.parse(d):{};t=await fetch(n,{method:o.apiMethod,headers:{"Content-Type":"application/json"},body:JSON.stringify(e)})}let l=t.headers.get("content-type");a=l&&l.includes("application/json")?await t.json():{message:await t.text()},t.ok?h({success:!0,data:a}):h({success:!1,error:a.detail||a.message||`HTTP ${t.status}: ${t.statusText}`})}catch(t){let e=t.message;e.includes("JSON")&&(e="Invalid JSON in request body. Please check your input."),h({success:!1,error:e||"Failed to test API"})}finally{f(!1)}};return(0,t.jsxs)("div",{className:"border rounded-lg p-4 bg-muted/30",children:[(0,t.jsxs)("div",{className:"flex items-center justify-between mb-3",children:[(0,t.jsx)("h5",{className:"text-sm font-semibold",children:"Test API"}),o.apiEndpoint&&(0,t.jsxs)("div",{className:"flex gap-2",children:[(0,t.jsx)(i.Button,{size:"sm",variant:"outline",onClick:()=>{var e;return o.apiEndpoint&&(e=o.apiEndpoint,void(navigator.clipboard.writeText(e),v(!0),setTimeout(()=>v(!1),2e3)))},className:"h-7",disabled:!o.apiEndpoint,children:y?(0,t.jsx)(l,{className:"h-3 w-3"}):(0,t.jsx)(n,{className:"h-3 w-3"})}),(0,t.jsx)(i.Button,{size:"sm",onClick:x,disabled:_||"GET"!==o.apiMethod&&!g&&!d||g&&!m,className:"h-7",children:_?(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)("div",{className:"mr-1",children:(0,t.jsx)(r.default,{size:"sm"})}),"Testing..."]}):(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(s,{className:"h-3 w-3 mr-1"}),"Test"]})})]})]}),o.apiEndpoint&&"GET"!==o.apiMethod&&(0,t.jsx)("div",{className:"mb-3",children:g?(0,t.jsxs)("div",{children:[(0,t.jsx)("label",{className:"block text-xs font-medium mb-1",children:"Upload File"}),(0,t.jsx)("input",{type:"file",accept:".yaml,.yml,.json",onChange:e=>p(e.target.files?.[0]||null),className:"w-full px-2 py-1 border rounded text-xs bg-background"}),m&&(0,t.jsxs)("div",{className:"mt-1 text-xs text-muted-foreground",children:["Selected: ",m.name," (",(m.size/1024).toFixed(2)," KB)"]})]}):(0,t.jsxs)("div",{children:[(0,t.jsx)("label",{className:"block text-xs font-medium mb-1",children:"Request Body (JSON)"}),(0,t.jsx)("textarea",{value:d,onChange:e=>c(e.target.value),rows:6,className:"w-full px-2 py-1 border rounded text-xs font-mono bg-background",placeholder:"Enter JSON request body..."})]})}),o.apiEndpoint&&(0,t.jsxs)("div",{className:"text-xs text-muted-foreground mb-2",children:[(0,t.jsx)("span",{className:"font-mono font-semibold",children:o.apiMethod})," ",o.apiEndpoint]}),u&&(0,t.jsx)("div",{className:"mt-3",children:u.success?(0,t.jsxs)("div",{className:"bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded p-2",children:[(0,t.jsx)("div",{className:"text-xs font-semibold text-green-800 dark:text-green-200 mb-1",children:"Success"}),(0,t.jsx)("pre",{className:"text-xs overflow-x-auto text-green-700 dark:text-green-300",children:JSON.stringify(u.data,null,2)})]}):(0,t.jsxs)("div",{className:"bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-2",children:[(0,t.jsx)("div",{className:"text-xs font-semibold text-red-800 dark:text-red-200 mb-1",children:"Error"}),(0,t.jsx)("div",{className:"text-xs text-red-700 dark:text-red-300",children:u.error})]})})]})}function y(){let[e,i]=(0,a.useState)("contract-management"),r={"contract-management":["parse_contract","parse_contract_file","build_contract","build_contract_from_store"],"metadata-store":["store_schema","get_schema","list_schemas","store_metadata","get_metadata","store_coercion_rules","get_coercion_rules","store_validation_rules","get_validation_rules","get_complete_schema"],"model-generator":["generate_model","generate_model_file","from_dict","from_file","from_json","from_url","model_to_schema","to_dict","to_json","to_file"],validation:["validator_class","validate_with_store","validate_with_contract","validate_batch_with_store","validate_batch_with_contract","get_model_from_store","get_model_from_contract","validate","validate_batch"],"quality-assurance":["quality_check","quality_check_options","quality_thresholds"]},o=e=>{let t=Object.keys(r).find(t=>r[t].includes(e));if(t)i(t),setTimeout(()=>{let t=document.getElementById(`method-${e}`);t&&t.scrollIntoView({behavior:"smooth",block:"start"})},150);else{let t=document.getElementById(`method-${e}`);t&&t.scrollIntoView({behavior:"smooth",block:"start"})}},s=[{id:"contract-management",title:"Contract Management",icon:d.FileText,items:[{id:"parse_contract",label:"Parse Contract",onClick:()=>o("parse_contract")},{id:"build_contract",label:"Build Contract",onClick:()=>o("build_contract")}]},{id:"metadata-store",title:"Metadata Store Client",icon:c.Database,items:[{id:"store_schema",label:"Store Schema",onClick:()=>o("store_schema")},{id:"get_schema",label:"Get Schema",onClick:()=>o("get_schema")},{id:"list_schemas",label:"List Schemas",onClick:()=>o("list_schemas")},{id:"store_metadata",label:"Store Metadata",onClick:()=>o("store_metadata")},{id:"get_metadata",label:"Get Metadata",onClick:()=>o("get_metadata")},{id:"store_coercion_rules",label:"Store Coercion Rules",onClick:()=>o("store_coercion_rules")},{id:"get_coercion_rules",label:"Get Coercion Rules",onClick:()=>o("get_coercion_rules")},{id:"store_validation_rules",label:"Store Validation Rules",onClick:()=>o("store_validation_rules")},{id:"get_validation_rules",label:"Get Validation Rules",onClick:()=>o("get_validation_rules")},{id:"get_complete_schema",label:"Get Complete Schema",onClick:()=>o("get_complete_schema")}]},{id:"model-generator",title:"Model Generator",icon:m,items:[{id:"generate_model",label:"Generate Model",onClick:()=>o("generate_model")},{id:"generate_model_file",label:"Generate Model File",onClick:()=>o("generate_model_file")},{id:"from_dict",label:"From Dict",onClick:()=>o("from_dict")},{id:"from_file",label:"From File",onClick:()=>o("from_file")},{id:"from_json",label:"From JSON",onClick:()=>o("from_json")},{id:"from_url",label:"From URL",onClick:()=>o("from_url")},{id:"model_to_schema",label:"Model to Schema",onClick:()=>o("model_to_schema")},{id:"to_dict",label:"To Dict",onClick:()=>o("to_dict")},{id:"to_json",label:"To JSON",onClick:()=>o("to_json")},{id:"to_file",label:"To File",onClick:()=>o("to_file")}]},{id:"validation",title:"Validation",icon:p,items:[{id:"validator_class",label:"⭐ Validator Class",onClick:()=>o("validator_class")},{id:"validate_with_store",label:"Validate with Store",onClick:()=>o("validate_with_store")},{id:"validate_with_contract",label:"Validate with Contract",onClick:()=>o("validate_with_contract")},{id:"validate_batch_with_store",label:"Batch Validate (Store)",onClick:()=>o("validate_batch_with_store")},{id:"validate_batch_with_contract",label:"Batch Validate (Contract)",onClick:()=>o("validate_batch_with_contract")},{id:"get_model_from_store",label:"Get Model (Store)",onClick:()=>o("get_model_from_store")},{id:"get_model_from_contract",label:"Get Model (Contract)",onClick:()=>o("get_model_from_contract")},{id:"validate",label:"Validate (Low-level)",onClick:()=>o("validate")},{id:"validate_batch",label:"Batch Validate (Low-level)",onClick:()=>o("validate_batch")}]},{id:"quality-assurance",title:"Quality Assurance",icon:u.Award,items:[{id:"quality_check",label:"⭐ QualityCheck Class",onClick:()=>o("quality_check")},{id:"quality_check_options",label:"QualityCheckOptions",onClick:()=>o("quality_check_options")},{id:"quality_thresholds",label:"QualityThresholds",onClick:()=>o("quality_thresholds")}]}],n=r[e]?_.filter(t=>r[e].includes(t.id)):_;return(0,t.jsxs)("div",{className:"flex h-full bg-background",style:{height:"calc(100vh - 4rem)",overflow:"hidden"},children:[(0,t.jsx)("div",{className:"flex-shrink-0",style:{height:"100%",overflow:"hidden"},children:(0,t.jsx)(h.CollapsibleSidebar,{sections:s,defaultCollapsed:!1,headerTitle:"Documentation",selectedSection:e,onSectionClick:e=>{i(e),setTimeout(()=>{let t=document.getElementById(`section-${e}`);t&&t.scrollIntoView({behavior:"smooth",block:"start"})},100)}})}),(0,t.jsx)("div",{className:"flex-1 min-w-0",style:{height:"100%",overflowY:"auto",overflowX:"hidden"},"data-content-area":!0,children:(0,t.jsx)("div",{className:"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8",children:(0,t.jsxs)("div",{className:"space-y-8",children:[(0,t.jsxs)("div",{id:`section-${e}`,className:"scroll-mt-4 mb-4",children:[(0,t.jsx)("h2",{className:"text-2xl font-bold text-foreground mb-1",children:s.find(t=>t.id===e)?.title||"Documentation"}),(0,t.jsxs)("p",{className:"text-sm text-muted-foreground",children:["contract-management"===e&&"Manage and work with data contracts","metadata-store"===e&&"Store and retrieve schemas, metadata, coercion rules, and validation rules","model-generator"===e&&"Generate Pydantic models from schemas","validation"===e&&"Validate data against schemas and contracts","quality-assurance"===e&&"Monitor data quality and track violations"]})]}),(0,t.jsx)("div",{className:"space-y-6",children:n.map(e=>(0,t.jsx)("div",{id:`method-${e.id}`,className:"border rounded-lg overflow-hidden scroll-mt-4",children:(0,t.jsxs)("div",{className:"grid grid-cols-1 lg:grid-cols-2 gap-4 p-4",children:[(0,t.jsxs)("div",{children:[(0,t.jsx)("h4",{className:"font-semibold mb-2",children:e.title}),(0,t.jsx)("p",{className:"text-sm text-muted-foreground mb-3",children:e.description}),e.arguments&&e.arguments.length>0&&(0,t.jsxs)("div",{className:"mb-4",children:[(0,t.jsx)("h5",{className:"text-sm font-semibold mb-2",children:"Arguments"}),(0,t.jsx)("div",{className:"space-y-2",children:e.arguments.map((e,a)=>(0,t.jsxs)("div",{className:"text-xs border-l-2 border-primary/20 pl-2",children:[(0,t.jsxs)("div",{className:"font-mono font-semibold text-foreground",children:[e.name,!e.required&&(0,t.jsx)("span",{className:"text-muted-foreground ml-1",children:"(optional)"})]}),(0,t.jsxs)("div",{className:"text-muted-foreground mt-0.5",children:[(0,t.jsx)("span",{className:"font-mono",children:e.type}),e.default&&(0,t.jsxs)("span",{className:"ml-1",children:["default: ",e.default]})]}),(0,t.jsx)("div",{className:"text-muted-foreground mt-1",children:e.description})]},a))})]}),e.returns&&(0,t.jsxs)("div",{className:"mb-4",children:[(0,t.jsx)("h5",{className:"text-sm font-semibold mb-2",children:"Returns"}),(0,t.jsxs)("div",{className:"text-xs border-l-2 border-green-500/20 pl-2",children:[(0,t.jsx)("div",{className:"font-mono font-semibold text-foreground mb-0.5",children:e.returns.type}),(0,t.jsx)("div",{className:"text-muted-foreground",children:e.returns.description})]})]}),(0,t.jsx)("div",{className:"bg-muted p-3 rounded font-mono text-xs overflow-x-auto mb-3",children:(0,t.jsx)("pre",{className:"whitespace-pre-wrap",children:e.exampleCode})}),(0,t.jsxs)("div",{className:"text-xs text-muted-foreground",children:[(0,t.jsx)("span",{className:"font-semibold",children:"Method:"})," ",e.method]})]}),(0,t.jsx)("div",{children:(0,t.jsx)(f,{method:e})})]})},e.id))}),(0,t.jsxs)("div",{className:"border rounded-lg p-4 bg-primary/5",children:[(0,t.jsx)("h4",{className:"font-semibold mb-2",children:"Additional Resources"}),(0,t.jsxs)("ul",{className:"text-sm space-y-1 text-muted-foreground",children:[(0,t.jsx)("li",{children:"• Full documentation: See README.md and REFERENCE.md"}),(0,t.jsx)("li",{children:"• Examples: Check the examples/ directory"}),(0,t.jsx)("li",{children:"• API Documentation: Available at /docs when running the API server"})]})]})]})})})]})}e.s(["default",()=>y],33558)}]);