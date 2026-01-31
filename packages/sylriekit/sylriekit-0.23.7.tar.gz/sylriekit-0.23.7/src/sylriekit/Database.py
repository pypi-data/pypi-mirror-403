from __future__ import annotations

import base64
import hashlib
import inspect
import json
import os
import pickle
import re
import sqlite3
import time
import uuid
from decimal import Decimal
from datetime import datetime, date, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import boto3
from boto3.dynamodb.conditions import Key, Attr
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
from botocore.exceptions import ClientError
import psycopg2
from psycopg2 import extras
import mysql.connector
from cryptography.fernet import Fernet


class Database:
    DB_TYPE_DYNAMODB = "dynamodb"
    DB_TYPE_SQLITE = "sqlite"
    DB_TYPE_POSTGRES = "postgres"
    DB_TYPE_MYSQL = "mysql"
    DEFAULT_REGION = "us-east-1"
    DEFAULT_SQLITE_PATH = ":memory:"
    DEFAULT_TIMEOUT = 30
    FINGERPRINT_SUFFIX = "_fp"

    DEFAULT_DB_TYPE = None
    AWS_ACCESS_KEY_ID = None
    AWS_SECRET_ACCESS_KEY = None
    REGION_NAME = None
    ENDPOINT_URL = None
    SQLITE_DATABASE_PATH = None
    POSTGRES_CONFIG = None
    MYSQL_CONFIG = None
    ENCRYPTION_KEY = None
    FERNET_KEY = None

    _dynamodb_client = None
    _dynamodb_resource = None
    _type_serializer = None
    _type_deserializer = None
    _fernet = None
    _table_schemas: Dict[str, List] = {}
    _encryption_algorithms: Dict[str, Tuple[Callable, Callable]] = {}
    _hash_algorithms: Dict[str, Tuple[Callable, Callable]] = {}
    _char_to_group: Dict[str, str] = {}

    @classmethod
    def load_config(cls, config: dict):
        api_keys = config.get("api_key", {})
        env_variables = config.get("env", {})
        if "Database" in config.keys():
            tool_config = config["Database"]
            cls.DEFAULT_DB_TYPE = tool_config.get("DEFAULT_DB_TYPE", cls.DB_TYPE_SQLITE)
            cls.REGION_NAME = tool_config.get("REGION_NAME", cls.DEFAULT_REGION)
            cls.ENDPOINT_URL = tool_config.get("ENDPOINT_URL", None)
            cls.SQLITE_DATABASE_PATH = tool_config.get("SQLITE_DATABASE_PATH", cls.DEFAULT_SQLITE_PATH)
            cls.POSTGRES_CONFIG = tool_config.get("POSTGRES_CONFIG", None)
            cls.MYSQL_CONFIG = tool_config.get("MYSQL_CONFIG", None)
            cls.ENCRYPTION_KEY = tool_config.get("ENCRYPTION_KEY", None)
            cls.FERNET_KEY = tool_config.get("FERNET_KEY", None)
        if "AWS_ACCESS_KEY_ID" in api_keys.keys():
            cls.AWS_ACCESS_KEY_ID = api_keys["AWS_ACCESS_KEY_ID"]
        if "AWS_SECRET_ACCESS_KEY" in api_keys.keys():
            cls.AWS_SECRET_ACCESS_KEY = api_keys["AWS_SECRET_ACCESS_KEY"]
        if "AWS_ACCESS_KEY_ID" in env_variables.keys():
            cls.AWS_ACCESS_KEY_ID = env_variables["AWS_ACCESS_KEY_ID"]
        if "AWS_SECRET_ACCESS_KEY" in env_variables.keys():
            cls.AWS_SECRET_ACCESS_KEY = env_variables["AWS_SECRET_ACCESS_KEY"]
        if "AWS_REGION" in env_variables.keys():
            cls.REGION_NAME = env_variables["AWS_REGION"]
        if "ENCRYPTION_KEY" in api_keys.keys():
            cls.ENCRYPTION_KEY = api_keys["ENCRYPTION_KEY"]
        if "FERNET_KEY" in api_keys.keys():
            cls.FERNET_KEY = api_keys["FERNET_KEY"]
        cls._init_builtin_algorithms()

    @classmethod
    def use_encryption(cls, name: str, encrypt_func: Callable, decrypt_func: Callable) -> str:
        try:
            cls._encryption_algorithms[name] = (encrypt_func, decrypt_func)
            return json.dumps({"status": "success", "algorithm": name, "type": "encryption"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def use_hash(cls, name: str, hash_func: Callable, verify_func: Callable) -> str:
        try:
            cls._hash_algorithms[name] = (hash_func, verify_func)
            return json.dumps({"status": "success", "algorithm": name, "type": "hash"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def create_table(cls, table_name: str, columns: List) -> str:
        db_type = cls._get_db_type()
        try:
            parsed_columns = cls._parse_column_definitions(columns)
            cls._table_schemas[table_name] = columns

            if db_type == cls.DB_TYPE_DYNAMODB:
                return cls._create_table_dynamodb(table_name, parsed_columns)
            elif db_type == cls.DB_TYPE_SQLITE:

                return cls._create_table_sql(table_name, parsed_columns, cls._get_sqlite_connection, "sqlite")
            elif db_type == cls.DB_TYPE_POSTGRES:
                return cls._create_table_sql(table_name, parsed_columns, cls._get_postgres_connection, "postgres")
            elif db_type == cls.DB_TYPE_MYSQL:
                return cls._create_table_sql(table_name, parsed_columns, cls._get_mysql_connection, "mysql")
            return json.dumps({"error": f"Unsupported database type: {db_type}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def add(cls, table_name: str, item: dict) -> str:
        db_type = cls._get_db_type()
        try:
            item_with_auto = cls._apply_auto_fields(table_name, item, is_update=False)
            processed_item = cls._process_item_for_storage(table_name, item_with_auto)

            if db_type == cls.DB_TYPE_DYNAMODB:
                return cls._add_dynamodb(table_name, processed_item)
            elif db_type == cls.DB_TYPE_SQLITE:
                return cls._add_sql(table_name, processed_item, cls._get_sqlite_connection)
            elif db_type == cls.DB_TYPE_POSTGRES:
                return cls._add_sql(table_name, processed_item, cls._get_postgres_connection)
            elif db_type == cls.DB_TYPE_MYSQL:
                return cls._add_sql(table_name, processed_item, cls._get_mysql_connection)
            return json.dumps({"error": f"Unsupported database type: {db_type}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def edit(cls, table_name: str, search_json: dict, new_values: dict) -> str:
        db_type = cls._get_db_type()
        try:
            new_values_with_auto = cls._apply_auto_fields(table_name, new_values, is_update=True)
            processed_values = cls._process_item_for_storage(table_name, new_values_with_auto)
            processed_search = cls._process_search_for_query(table_name, search_json)

            if db_type == cls.DB_TYPE_DYNAMODB:
                return cls._edit_dynamodb(table_name, processed_search, processed_values)
            elif db_type == cls.DB_TYPE_SQLITE:
                return cls._edit_sql(table_name, processed_search, processed_values, cls._get_sqlite_connection)
            elif db_type == cls.DB_TYPE_POSTGRES:
                return cls._edit_sql(table_name, processed_search, processed_values, cls._get_postgres_connection)
            elif db_type == cls.DB_TYPE_MYSQL:
                return cls._edit_sql(table_name, processed_search, processed_values, cls._get_mysql_connection)
            return json.dumps({"error": f"Unsupported database type: {db_type}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def delete(cls, table_name: str, search_json: dict) -> str:
        db_type = cls._get_db_type()
        try:
            processed_search = cls._process_search_for_query(table_name, search_json)

            if db_type == cls.DB_TYPE_DYNAMODB:
                return cls._delete_dynamodb(table_name, processed_search)
            elif db_type == cls.DB_TYPE_SQLITE:
                return cls._delete_sql(table_name, processed_search, cls._get_sqlite_connection)
            elif db_type == cls.DB_TYPE_POSTGRES:
                return cls._delete_sql(table_name, processed_search, cls._get_postgres_connection)
            elif db_type == cls.DB_TYPE_MYSQL:
                return cls._delete_sql(table_name, processed_search, cls._get_mysql_connection)
            return json.dumps({"error": f"Unsupported database type: {db_type}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def search(cls, table_name: str, wanted_cols: List[str], search_json: dict) -> str:
        db_type = cls._get_db_type()
        try:
            processed_search, fingerprint_searches = cls._process_search_with_fingerprint(table_name, search_json)

            if db_type == cls.DB_TYPE_DYNAMODB:
                result = cls._search_dynamodb(table_name, processed_search, fingerprint_searches)
            elif db_type == cls.DB_TYPE_SQLITE:
                result = cls._search_sql(table_name, processed_search, fingerprint_searches, cls._get_sqlite_connection)
            elif db_type == cls.DB_TYPE_POSTGRES:
                result = cls._search_sql(table_name, processed_search, fingerprint_searches,
                                         cls._get_postgres_connection)
            elif db_type == cls.DB_TYPE_MYSQL:
                result = cls._search_sql(table_name, processed_search, fingerprint_searches, cls._get_mysql_connection)
            else:
                return json.dumps({"error": f"Unsupported database type: {db_type}"})

            result_data = json.loads(result)
            if "error" in result_data:
                return result

            decrypted_items = []
            for item in result_data.get("items", []):
                decrypted_item = cls._process_item_for_retrieval(table_name, item, wanted_cols)
                decrypted_items.append(decrypted_item)

            return json.dumps({
                "status": "success",
                "table_name": table_name,
                "count": len(decrypted_items),
                "items": decrypted_items
            }, default=cls._json_serializer)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def query(cls, query_string: str) -> str:
        db_type = cls._get_db_type()
        if db_type == cls.DB_TYPE_DYNAMODB:
            return json.dumps({"error": "Raw SQL queries not supported for DynamoDB. Use search() instead."})
        elif db_type == cls.DB_TYPE_SQLITE:
            return cls._query_sql(query_string, cls._get_sqlite_connection)
        elif db_type == cls.DB_TYPE_POSTGRES:
            return cls._query_sql(query_string, cls._get_postgres_connection)
        elif db_type == cls.DB_TYPE_MYSQL:
            return cls._query_sql(query_string, cls._get_mysql_connection)
        return json.dumps({"error": f"Unsupported database type: {db_type}"})

    @classmethod
    def save_schema(cls, filename: str) -> str:
        try:
            schema_data = {"tables": cls._table_schemas}
            with open(filename, "w") as f:
                json.dump(schema_data, f, indent=2)
            return json.dumps({"status": "success", "filename": filename, "tables_saved": len(cls._table_schemas)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def load_schema(cls, filename: str) -> str:
        try:
            with open(filename, "r") as f:
                schema_data = json.load(f)
            cls._table_schemas = schema_data.get("tables", {})
            return json.dumps({"status": "success", "filename": filename, "tables_loaded": len(cls._table_schemas)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def save_algorithms(cls, filename: str) -> str:
        try:
            algo_data = {"encryption": {}, "hash": {}}
            for name, (enc_func, dec_func) in cls._encryption_algorithms.items():
                if name not in ["encrypt", "base64"]:
                    algo_data["encryption"][name] = {
                        "encrypt": inspect.getsource(enc_func),
                        "decrypt": inspect.getsource(dec_func)
                    }
            for name, (hash_func, verify_func) in cls._hash_algorithms.items():
                if name not in ["hash", "fingerprint"]:
                    algo_data["hash"][name] = {
                        "hash": inspect.getsource(hash_func),
                        "verify": inspect.getsource(verify_func)
                    }
            with open(filename, "w") as f:
                json.dump(algo_data, f, indent=2)
            return json.dumps({"status": "success", "filename": filename})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def load_algorithms(cls, filename: str) -> str:
        try:
            with open(filename, "r") as f:
                algo_data = json.load(f)
            loaded_count = 0
            for name, funcs in algo_data.get("encryption", {}).items():
                enc_globals = {}
                dec_globals = {}
                exec(funcs["encrypt"], enc_globals)
                exec(funcs["decrypt"], dec_globals)
                enc_func = [v for v in enc_globals.values() if callable(v)][0]
                dec_func = [v for v in dec_globals.values() if callable(v)][0]
                cls._encryption_algorithms[name] = (enc_func, dec_func)
                loaded_count += 1
            for name, funcs in algo_data.get("hash", {}).items():
                hash_globals = {}
                verify_globals = {}
                exec(funcs["hash"], hash_globals)
                exec(funcs["verify"], verify_globals)
                hash_func = [v for v in hash_globals.values() if callable(v)][0]
                verify_func = [v for v in verify_globals.values() if callable(v)][0]
                cls._hash_algorithms[name] = (hash_func, verify_func)
                loaded_count += 1
            return json.dumps({"status": "success", "filename": filename, "algorithms_loaded": loaded_count})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def encrypt(cls, text: str, key: str = None) -> str:
        try:
            use_key = key or cls.FERNET_KEY
            if use_key is None:
                return json.dumps({"error": "No encryption key configured"})
            fernet = Fernet(use_key.encode() if isinstance(use_key, str) else use_key)
            encrypted = fernet.encrypt(text.encode()).decode()
            return json.dumps({"status": "success", "encrypted": encrypted})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def decrypt(cls, encrypted_text: str, key: str = None) -> str:
        try:
            use_key = key or cls.FERNET_KEY
            if use_key is None:
                return json.dumps({"error": "No encryption key configured"})
            fernet = Fernet(use_key.encode() if isinstance(use_key, str) else use_key)
            decrypted = fernet.decrypt(encrypted_text.encode()).decode()
            return json.dumps({"status": "success", "decrypted": decrypted})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def hash(cls, text: str) -> str:
        try:
            hashed = hashlib.sha256(text.encode()).hexdigest()
            return json.dumps({"status": "success", "hash": hashed})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def hash_verify(cls, text: str, hash_value: str) -> str:
        try:
            computed = hashlib.sha256(text.encode()).hexdigest()
            matches = computed == hash_value
            return json.dumps({"status": "success", "matches": matches})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def base64_encode(cls, text: str) -> str:
        try:
            encoded = base64.b64encode(text.encode()).decode()
            return json.dumps({"status": "success", "encoded": encoded})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def base64_decode(cls, encoded_text: str) -> str:
        try:
            decoded = base64.b64decode(encoded_text.encode()).decode()
            return json.dumps({"status": "success", "decoded": decoded})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def fingerprint(cls, text: str) -> str:
        try:
            char_to_group = cls._build_group_mapping()
            text_lower = text.lower().strip()
            groups_sequence = []
            for char in text_lower:
                group = char_to_group.get(char)
                if group:
                    groups_sequence.append(group)
            group_set = "".join(sorted(set(groups_sequence)))
            bigrams_set = set()
            for i in range(len(groups_sequence) - 1):
                bigram = groups_sequence[i] + groups_sequence[i + 1]
                bigrams_set.add(bigram)
            bigrams = "".join(sorted(bigrams_set))
            fingerprint_val = f"{group_set}.{bigrams}"
            return json.dumps({"status": "success", "fingerprint": fingerprint_val})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def fingerprint_verify(cls, stored_fingerprint: str, search_text: str) -> str:
        try:
            search_fp_result = json.loads(cls.fingerprint(search_text))
            if "error" in search_fp_result:
                return json.dumps(search_fp_result)
            search_fingerprint = search_fp_result["fingerprint"]

            stored_parts = stored_fingerprint.split(".")
            search_parts = search_fingerprint.split(".")

            stored_groups = set(stored_parts[0]) if len(stored_parts) > 0 else set()
            stored_bigrams = set()
            if len(stored_parts) > 1:
                bg = stored_parts[1]
                stored_bigrams = {bg[i:i + 2] for i in range(0, len(bg), 2)}

            search_groups = set(search_parts[0]) if len(search_parts) > 0 else set()
            search_bigrams = set()
            if len(search_parts) > 1:
                bg = search_parts[1]
                search_bigrams = {bg[i:i + 2] for i in range(0, len(bg), 2)}

            groups_match = search_groups.issubset(stored_groups)
            bigrams_match = search_bigrams.issubset(stored_bigrams)
            matches = groups_match and bigrams_match

            return json.dumps({"status": "success", "matches": matches})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def delete_table(cls, table_name: str) -> str:
        db_type = cls._get_db_type()
        try:
            if table_name in cls._table_schemas:
                del cls._table_schemas[table_name]

            if db_type == cls.DB_TYPE_DYNAMODB:
                return cls._delete_table_dynamodb(table_name)
            elif db_type == cls.DB_TYPE_SQLITE:
                return cls._delete_table_sql(table_name, cls._get_sqlite_connection)
            elif db_type == cls.DB_TYPE_POSTGRES:
                return cls._delete_table_sql(table_name, cls._get_postgres_connection)
            elif db_type == cls.DB_TYPE_MYSQL:
                return cls._delete_table_sql(table_name, cls._get_mysql_connection)
            return json.dumps({"error": f"Unsupported database type: {db_type}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def table_exists(cls, table_name: str) -> str:
        db_type = cls._get_db_type()
        try:
            if db_type == cls.DB_TYPE_DYNAMODB:
                return cls._table_exists_dynamodb(table_name)
            elif db_type == cls.DB_TYPE_SQLITE:
                return cls._table_exists_sql(table_name, cls._get_sqlite_connection, "sqlite")
            elif db_type == cls.DB_TYPE_POSTGRES:
                return cls._table_exists_sql(table_name, cls._get_postgres_connection, "postgres")
            elif db_type == cls.DB_TYPE_MYSQL:
                return cls._table_exists_sql(table_name, cls._get_mysql_connection, "mysql")
            return json.dumps({"error": f"Unsupported database type: {db_type}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### AUTO FIELD GENERATION START
    @classmethod
    def _generate_auto_id(cls) -> str:
        timestamp = time.time_ns() // 1000
        random_part = uuid.uuid4().hex[:8]
        return f"{timestamp}-{random_part}"

    @classmethod
    def _generate_timestamp(cls) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @classmethod
    def _apply_auto_fields(cls, table_name: str, item: dict, is_update: bool = False) -> dict:
        if table_name not in cls._table_schemas:
            return item

        result = dict(item)
        columns = cls._parse_column_definitions(cls._table_schemas[table_name])

        for col in columns:
            col_name = col["name"]
            auto_type = col.get("auto_type")

            if not auto_type:
                continue

            if is_update and auto_type in ("id", "created_at"):
                continue

            if col_name in result and auto_type != "updated_at":
                continue

            if auto_type == "id":
                result[col_name] = cls._generate_auto_id()
            elif auto_type == "created_at":
                result[col_name] = cls._generate_timestamp()
            elif auto_type == "updated_at":
                result[col_name] = cls._generate_timestamp()

        return result

    ### AUTO FIELD GENERATION END

    ### BUILTIN ALGORITHM INITIALIZATION START
    @classmethod
    def _init_builtin_algorithms(cls):
        if cls.FERNET_KEY:
            cls._fernet = Fernet(cls.FERNET_KEY.encode() if isinstance(cls.FERNET_KEY, str) else cls.FERNET_KEY)

        def builtin_encrypt(val, key):
            fernet = Fernet(key.encode() if isinstance(key, str) else key)
            return fernet.encrypt(val.encode()).decode()

        def builtin_decrypt(val, key):
            fernet = Fernet(key.encode() if isinstance(key, str) else key)
            return fernet.decrypt(val.encode()).decode()

        cls._encryption_algorithms["encrypt"] = (builtin_encrypt, builtin_decrypt)

        def builtin_base64_enc(val, key=None):
            return base64.b64encode(val.encode()).decode()

        def builtin_base64_dec(val, key=None):
            return base64.b64decode(val.encode()).decode()

        cls._encryption_algorithms["base64"] = (builtin_base64_enc, builtin_base64_dec)

        def builtin_hash(val):
            return hashlib.sha256(val.encode()).hexdigest()

        def builtin_hash_verify(val, stored_hash):
            return hashlib.sha256(val.encode()).hexdigest() == stored_hash

        cls._hash_algorithms["hash"] = (builtin_hash, builtin_hash_verify)

        def builtin_fp(val):
            result = json.loads(cls.fingerprint(val))
            return result.get("fingerprint", "")

        def builtin_fp_verify(stored_fp, search_val):
            result = json.loads(cls.fingerprint_verify(stored_fp, search_val))
            return result.get("matches", False)

        cls._hash_algorithms["fingerprint"] = (builtin_fp, builtin_fp_verify)

    ### BUILTIN ALGORITHM INITIALIZATION END

    ### COLUMN PARSING START
    @classmethod
    def _parse_column_definitions(cls, columns: List) -> List[dict]:
        parsed = []
        for col_def in columns:
            if isinstance(col_def, str):
                parsed.append({"name": col_def, "primary": False, "transforms": [], "filters": [], "fingerprint": False,
                               "auto_type": None})
            elif isinstance(col_def, list):
                col_name = col_def[0]
                col_config = {"name": col_name, "primary": False, "transforms": [], "filters": [], "fingerprint": False,
                              "auto_type": None}

                for i, modifier in enumerate(col_def[1:]):
                    if modifier == "primary":
                        col_config["primary"] = True
                    elif modifier == "fingerprint":
                        col_config["fingerprint"] = True
                        if i + 2 < len(col_def):
                            col_config["fingerprint_hash"] = col_def[i + 2]
                    elif modifier in ["alpha_only", "alpha_num_only", "num_only"]:
                        col_config["filters"].append(modifier)
                    elif modifier == "auto":
                        if col_name == "id":
                            col_config["auto_type"] = "id"
                        elif col_name == "created_at":
                            col_config["auto_type"] = "created_at"
                        elif col_name == "updated_at":
                            col_config["auto_type"] = "updated_at"
                    elif modifier == "auto-id":
                        col_config["auto_type"] = "id"
                    elif modifier == "auto-created_at":
                        col_config["auto_type"] = "created_at"
                    elif modifier == "auto-updated_at":
                        col_config["auto_type"] = "updated_at"
                    elif modifier in cls._encryption_algorithms or modifier in cls._hash_algorithms:
                        col_config["transforms"].append(modifier)
                    elif modifier not in ["primary", "fingerprint", "auto", "auto-id", "auto-created_at",
                                          "auto-updated_at"]:
                        col_config["transforms"].append(modifier)

                parsed.append(col_config)
        return parsed

    @classmethod
    def _get_column_config(cls, table_name: str, col_name: str) -> Optional[dict]:
        if table_name not in cls._table_schemas:
            return None
        columns = cls._parse_column_definitions(cls._table_schemas[table_name])
        for col in columns:
            if col["name"] == col_name:
                return col
        return None

    ### COLUMN PARSING END

    ### INPUT FILTERS START
    @classmethod
    def _apply_filters(cls, value: str, filters: List[str]) -> str:
        result = str(value)
        for filt in filters:
            if filt == "alpha_only":
                result = re.sub(r"[^a-zA-Z]", "", result)
            elif filt == "alpha_num_only":
                result = re.sub(r"[^a-zA-Z0-9]", "", result)
            elif filt == "num_only":
                result = re.sub(r"[^0-9]", "", result)
        return result

    @classmethod
    def _validate_filters(cls, value: str, filters: List[str]) -> Tuple[bool, str]:
        for filt in filters:
            if filt == "alpha_only" and not re.match(r"^[a-zA-Z]*$", str(value)):
                return False, f"Value must contain only alphabetic characters"
            elif filt == "alpha_num_only" and not re.match(r"^[a-zA-Z0-9]*$", str(value)):
                return False, f"Value must contain only alphanumeric characters"
            elif filt == "num_only" and not re.match(r"^[0-9]*$", str(value)):
                return False, f"Value must contain only numeric characters"
        return True, ""

    ### INPUT FILTERS END

    ### TRANSFORM PROCESSING START
    @classmethod
    def _apply_transforms_encrypt(cls, value: str, transforms: List[str]) -> str:
        result = value
        for transform in transforms:
            if transform in cls._encryption_algorithms:
                enc_func, _ = cls._encryption_algorithms[transform]
                if transform == "base64":
                    result = enc_func(result, None)
                else:
                    key = cls.FERNET_KEY or cls.ENCRYPTION_KEY
                    result = enc_func(result, key)
            elif transform in cls._hash_algorithms:
                hash_func, _ = cls._hash_algorithms[transform]
                result = hash_func(result)
        return result

    @classmethod
    def _apply_transforms_decrypt(cls, value: str, transforms: List[str]) -> str:
        result = value
        for transform in reversed(transforms):
            if transform in cls._encryption_algorithms:
                _, dec_func = cls._encryption_algorithms[transform]
                if transform == "base64":
                    result = dec_func(result, None)
                else:
                    key = cls.FERNET_KEY or cls.ENCRYPTION_KEY
                    result = dec_func(result, key)
        return result

    ### TRANSFORM PROCESSING END

    ### ITEM PROCESSING START
    @classmethod
    def _process_item_for_storage(cls, table_name: str, item: dict) -> dict:
        if table_name not in cls._table_schemas:
            return item

        processed = {}
        columns = cls._parse_column_definitions(cls._table_schemas[table_name])
        col_configs = {col["name"]: col for col in columns}

        for key, value in item.items():
            if key in col_configs:
                config = col_configs[key]
                str_value = str(value) if value is not None else ""

                if config["filters"]:
                    is_valid, error = cls._validate_filters(str_value, config["filters"])
                    if not is_valid:
                        raise ValueError(f"Column {key}: {error}")
                    str_value = cls._apply_filters(str_value, config["filters"])

                if config["fingerprint"]:
                    fp_result = json.loads(cls.fingerprint(str_value))
                    fp_value = fp_result.get("fingerprint", "")
                    processed[key + cls.FINGERPRINT_SUFFIX] = fp_value

                if config["transforms"]:
                    processed[key] = cls._apply_transforms_encrypt(str_value, config["transforms"])
                else:
                    processed[key] = value
            else:
                processed[key] = value

        return processed

    @classmethod
    def _process_item_for_retrieval(cls, table_name: str, item: dict, wanted_cols: List[str]) -> dict:
        if table_name not in cls._table_schemas:
            filtered = {k: v for k, v in item.items() if k in wanted_cols} if wanted_cols else item
            return filtered

        processed = {}
        columns = cls._parse_column_definitions(cls._table_schemas[table_name])
        col_configs = {col["name"]: col for col in columns}

        select_cols = wanted_cols if wanted_cols else list(item.keys())

        for key in select_cols:
            if key not in item:
                continue
            if key.endswith(cls.FINGERPRINT_SUFFIX):
                continue

            value = item[key]
            if key in col_configs:
                config = col_configs[key]
                if config["transforms"] and value is not None:
                    has_hash = any(t in cls._hash_algorithms and t != "fingerprint" for t in config["transforms"])
                    if not has_hash:
                        try:
                            processed[key] = cls._apply_transforms_decrypt(str(value), config["transforms"])
                        except Exception:
                            processed[key] = value
                    else:
                        processed[key] = value
                else:
                    processed[key] = value
            else:
                processed[key] = value

        return processed

    @classmethod
    def _process_search_for_query(cls, table_name: str, search_json: dict) -> dict:
        if table_name not in cls._table_schemas:
            return search_json

        processed = {}
        columns = cls._parse_column_definitions(cls._table_schemas[table_name])
        col_configs = {col["name"]: col for col in columns}

        for key, value in search_json.items():
            if key in col_configs:
                config = col_configs[key]
                if config["transforms"] and not isinstance(value, dict):
                    has_hash = any(t in cls._hash_algorithms for t in config["transforms"])
                    if has_hash:
                        processed[key] = cls._apply_transforms_encrypt(str(value), config["transforms"])
                    else:
                        processed[key] = cls._apply_transforms_encrypt(str(value), config["transforms"])
                else:
                    processed[key] = value
            else:
                processed[key] = value

        return processed

    @classmethod
    def _process_search_with_fingerprint(cls, table_name: str, search_json: dict) -> Tuple[dict, dict]:
        if table_name not in cls._table_schemas:
            return search_json, {}

        processed = {}
        fingerprint_searches = {}
        columns = cls._parse_column_definitions(cls._table_schemas[table_name])
        col_configs = {col["name"]: col for col in columns}

        for key, value in search_json.items():
            if key in col_configs:
                config = col_configs[key]
                if config["fingerprint"] and not isinstance(value, dict):
                    fp_result = json.loads(cls.fingerprint(str(value)))
                    fp_value = fp_result.get("fingerprint", "")
                    fingerprint_searches[key + cls.FINGERPRINT_SUFFIX] = fp_value
                elif config["transforms"] and not isinstance(value, dict):
                    has_hash = any(t in cls._hash_algorithms and t != "fingerprint" for t in config["transforms"])
                    if has_hash:
                        processed[key] = cls._apply_transforms_encrypt(str(value), config["transforms"])
                    else:
                        processed[key] = value
                else:
                    processed[key] = value
            else:
                processed[key] = value

        return processed, fingerprint_searches

    ### ITEM PROCESSING END

    ### GROUP MAPPING START
    @classmethod
    def _build_group_mapping(cls) -> Dict[str, str]:
        if cls._char_to_group:
            return cls._char_to_group

        groups = {}
        for i, letter in enumerate("abcdefghijklmnopqrstuvwxyz", 1):
            group_num = (i - 1) // 3 + 1
            group_letter = chr(ord("A") + group_num - 1)
            groups[letter] = group_letter

        for digit in "0123456789":
            groups[digit] = "J"

        for sym in "._-+@":
            groups[sym] = "K"

        cls._char_to_group = groups
        return groups

    ### GROUP MAPPING END

    ### DATABASE TYPE UTILITIES START
    @classmethod
    def _get_db_type(cls) -> str:
        if cls.DEFAULT_DB_TYPE is None:
            return cls.DB_TYPE_SQLITE
        return cls.DEFAULT_DB_TYPE

    @classmethod
    def _get_sqlite_connection(cls):
        db_path = cls.SQLITE_DATABASE_PATH or cls.DEFAULT_SQLITE_PATH
        conn = sqlite3.connect(db_path, timeout=cls.DEFAULT_TIMEOUT)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def _get_postgres_connection(cls):
        if cls.POSTGRES_CONFIG is None:
            raise ValueError("PostgreSQL configuration not set")
        return psycopg2.connect(**cls.POSTGRES_CONFIG)

    @classmethod
    def _get_mysql_connection(cls):
        if cls.MYSQL_CONFIG is None:
            raise ValueError("MySQL configuration not set")
        return mysql.connector.connect(**cls.MYSQL_CONFIG)

    ### DATABASE TYPE UTILITIES END

    ### SQL CREATE TABLE START
    @classmethod
    def _create_table_sql(cls, table_name: str, parsed_columns: List[dict], get_connection, db_type: str) -> str:
        try:
            conn = get_connection()
            cursor = conn.cursor()

            col_defs = []
            primary_keys = []

            for col in parsed_columns:
                col_name = col["name"]
                col_type = "TEXT" if db_type != "mysql" else "VARCHAR(255)"

                if col["primary"]:
                    primary_keys.append(col_name)
                    col_defs.append(f"{col_name} {col_type} NOT NULL")
                else:
                    col_defs.append(f"{col_name} {col_type}")

                if col["fingerprint"]:
                    fp_col_name = col_name + cls.FINGERPRINT_SUFFIX
                    col_defs.append(f"{fp_col_name} {col_type}")

            if primary_keys:
                col_defs.append(f"PRIMARY KEY ({', '.join(primary_keys)})")

            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
            cursor.execute(create_sql)
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "table_name": table_name, "message": "Table created successfully"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### SQL CREATE TABLE END

    ### SQL DELETE TABLE START
    @classmethod
    def _delete_table_sql(cls, table_name: str, get_connection) -> str:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            drop_sql = f"DROP TABLE IF EXISTS {table_name}"
            cursor.execute(drop_sql)
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "table_name": table_name, "message": "Table deleted successfully"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### SQL DELETE TABLE END

    ### SQL TABLE EXISTS START
    @classmethod
    def _table_exists_sql(cls, table_name: str, get_connection, db_type: str) -> str:
        try:
            conn = get_connection()
            cursor = conn.cursor()

            if db_type == "sqlite":
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            elif db_type == "postgres":
                cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                               (table_name,))
            elif db_type == "mysql":
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s", (table_name,))

            result = cursor.fetchone()
            conn.close()

            if db_type == "sqlite":
                exists = result is not None
            elif db_type == "postgres":
                exists = result[0] if result else False
            elif db_type == "mysql":
                exists = result[0] > 0 if result else False
            else:
                exists = False

            return json.dumps({"status": "success", "table_name": table_name, "exists": exists})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### SQL TABLE EXISTS END

    ### SQL ADD START
    @classmethod
    def _add_sql(cls, table_name: str, item: dict, get_connection) -> str:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            columns = list(item.keys())
            placeholders = ", ".join(["?" if isinstance(conn, sqlite3.Connection) else "%s"] * len(columns))
            columns_str = ", ".join(columns)
            values = [cls._serialize_sql_value(v) for v in item.values()]

            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            cursor.execute(insert_sql, values)
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "table_name": table_name, "item": item})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### SQL ADD END

    ### SQL EDIT START
    @classmethod
    def _edit_sql(cls, table_name: str, search_json: dict, new_values: dict, get_connection) -> str:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            placeholder = "?" if isinstance(conn, sqlite3.Connection) else "%s"

            set_parts = []
            set_values = []
            for key, value in new_values.items():
                set_parts.append(f"{key} = {placeholder}")
                set_values.append(cls._serialize_sql_value(value))

            where_parts = []
            where_values = []
            for key, value in search_json.items():
                where_clause, where_val = cls._build_sql_where_condition(key, value, placeholder)
                where_parts.append(where_clause)
                if isinstance(where_val, list):
                    where_values.extend(where_val)
                elif where_val is not None:
                    where_values.append(where_val)

            update_sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
            cursor.execute(update_sql, set_values + where_values)
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "table_name": table_name, "rows_affected": rows_affected})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### SQL EDIT END

    ### SQL DELETE START
    @classmethod
    def _delete_sql(cls, table_name: str, search_json: dict, get_connection) -> str:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            placeholder = "?" if isinstance(conn, sqlite3.Connection) else "%s"

            where_parts = []
            where_values = []
            for key, value in search_json.items():
                where_clause, where_val = cls._build_sql_where_condition(key, value, placeholder)
                where_parts.append(where_clause)
                if isinstance(where_val, list):
                    where_values.extend(where_val)
                elif where_val is not None:
                    where_values.append(where_val)

            delete_sql = f"DELETE FROM {table_name} WHERE {' AND '.join(where_parts)}"
            cursor.execute(delete_sql, where_values)
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "table_name": table_name, "rows_affected": rows_affected})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### SQL DELETE END

    ### SQL SEARCH START
    @classmethod
    def _search_sql(cls, table_name: str, search_json: dict, fingerprint_searches: dict, get_connection) -> str:
        try:
            conn = get_connection()
            is_sqlite = isinstance(conn, sqlite3.Connection)
            placeholder = "?" if is_sqlite else "%s"

            if is_sqlite:
                cursor = conn.cursor()
            elif "psycopg2" in str(type(conn).__module__):
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            else:
                cursor = conn.cursor(dictionary=True)

            combined_search = {**search_json}

            if not combined_search and not fingerprint_searches:
                select_sql = f"SELECT * FROM {table_name}"
                cursor.execute(select_sql)
            else:
                where_parts = []
                where_values = []

                for key, value in combined_search.items():
                    where_clause, where_val = cls._build_sql_where_condition(key, value, placeholder)
                    where_parts.append(where_clause)
                    if isinstance(where_val, list):
                        where_values.extend(where_val)
                    elif where_val is not None:
                        where_values.append(where_val)

                select_sql = f"SELECT * FROM {table_name}"
                if where_parts:
                    select_sql += f" WHERE {' AND '.join(where_parts)}"
                cursor.execute(select_sql, where_values)

            if is_sqlite:
                rows = [dict(row) for row in cursor.fetchall()]
            else:
                rows = cursor.fetchall()
                if rows and not isinstance(rows[0], dict):
                    columns = [desc[0] for desc in cursor.description]
                    rows = [dict(zip(columns, row)) for row in rows]

            if fingerprint_searches:
                filtered_rows = []
                for row in rows:
                    match = True
                    for fp_col, fp_search_val in fingerprint_searches.items():
                        stored_fp = row.get(fp_col, "")
                        if stored_fp:
                            verify_result = json.loads(cls.fingerprint_verify(stored_fp, ""))
                            stored_parts = stored_fp.split(".")
                            search_parts = fp_search_val.split(".")

                            stored_groups = set(stored_parts[0]) if stored_parts else set()
                            search_groups = set(search_parts[0]) if search_parts else set()

                            stored_bigrams = set()
                            if len(stored_parts) > 1:
                                bg = stored_parts[1]
                                stored_bigrams = {bg[i:i + 2] for i in range(0, len(bg), 2)}

                            search_bigrams = set()
                            if len(search_parts) > 1:
                                bg = search_parts[1]
                                search_bigrams = {bg[i:i + 2] for i in range(0, len(bg), 2)}

                            if not (search_groups.issubset(stored_groups) and search_bigrams.issubset(stored_bigrams)):
                                match = False
                                break
                    if match:
                        filtered_rows.append(row)
                rows = filtered_rows

            conn.close()
            return json.dumps({"status": "success", "table_name": table_name, "count": len(rows), "items": rows},
                              default=cls._json_serializer)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def _build_sql_where_condition(cls, key: str, value: Any, placeholder: str) -> Tuple[str, Any]:
        if isinstance(value, dict):
            if "eq" in value:
                return f"{key} = {placeholder}", value["eq"]
            if "ne" in value:
                return f"{key} != {placeholder}", value["ne"]
            if "gt" in value:
                return f"{key} > {placeholder}", value["gt"]
            if "gte" in value:
                return f"{key} >= {placeholder}", value["gte"]
            if "lt" in value:
                return f"{key} < {placeholder}", value["lt"]
            if "lte" in value:
                return f"{key} <= {placeholder}", value["lte"]
            if "between" in value:
                return f"{key} BETWEEN {placeholder} AND {placeholder}", value["between"]
            if "like" in value:
                return f"{key} LIKE {placeholder}", value["like"]
            if "in" in value:
                placeholders = ", ".join([placeholder] * len(value["in"]))
                return f"{key} IN ({placeholders})", value["in"]
            if "is_null" in value:
                if value["is_null"]:
                    return f"{key} IS NULL", None
                return f"{key} IS NOT NULL", None
            return f"{key} = {placeholder}", value
        return f"{key} = {placeholder}", value

    ### SQL SEARCH END

    ### SQL QUERY START
    @classmethod
    def _query_sql(cls, query_string: str, get_connection) -> str:
        try:
            conn = get_connection()
            is_sqlite = isinstance(conn, sqlite3.Connection)

            if is_sqlite:
                cursor = conn.cursor()
            elif "psycopg2" in str(type(conn).__module__):
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            else:
                cursor = conn.cursor(dictionary=True)

            cursor.execute(query_string)

            if query_string.strip().upper().startswith("SELECT"):
                if is_sqlite:
                    rows = [dict(row) for row in cursor.fetchall()]
                else:
                    rows = cursor.fetchall()
                    if rows and not isinstance(rows[0], dict):
                        columns = [desc[0] for desc in cursor.description]
                        rows = [dict(zip(columns, row)) for row in rows]
                conn.close()
                return json.dumps({"status": "success", "count": len(rows), "rows": rows}, default=cls._json_serializer)
            else:
                conn.commit()
                rows_affected = cursor.rowcount
                conn.close()
                return json.dumps({"status": "success", "rows_affected": rows_affected})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def _serialize_sql_value(cls, value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, dict) or isinstance(value, list):
            return json.dumps(value)
        return value

    ### SQL QUERY END

    ### DYNAMODB INITIALIZATION START
    @classmethod
    def _init_dynamodb(cls):
        session_kwargs = {}
        if cls.AWS_ACCESS_KEY_ID:
            session_kwargs["aws_access_key_id"] = cls.AWS_ACCESS_KEY_ID
        if cls.AWS_SECRET_ACCESS_KEY:
            session_kwargs["aws_secret_access_key"] = cls.AWS_SECRET_ACCESS_KEY
        if cls.REGION_NAME:
            session_kwargs["region_name"] = cls.REGION_NAME
        else:
            session_kwargs["region_name"] = cls.DEFAULT_REGION

        client_kwargs = session_kwargs.copy()
        if cls.ENDPOINT_URL:
            client_kwargs["endpoint_url"] = cls.ENDPOINT_URL

        cls._dynamodb_client = boto3.client("dynamodb", **client_kwargs)
        cls._dynamodb_resource = boto3.resource("dynamodb", **client_kwargs)
        cls._type_serializer = TypeSerializer()
        cls._type_deserializer = TypeDeserializer()

    @classmethod
    def _ensure_dynamodb_initialized(cls):
        if cls._dynamodb_client is None or cls._dynamodb_resource is None:
            cls._init_dynamodb()

    ### DYNAMODB INITIALIZATION END

    ### DYNAMODB CREATE TABLE START
    @classmethod
    def _create_table_dynamodb(cls, table_name: str, parsed_columns: List[dict]) -> str:
        try:
            cls._ensure_dynamodb_initialized()

            key_schema = []
            attribute_definitions = []

            for col in parsed_columns:
                if col["primary"]:
                    key_schema.append({"AttributeName": col["name"], "KeyType": "HASH"})
                    attribute_definitions.append({"AttributeName": col["name"], "AttributeType": "S"})
                    break

            create_params = {
                "TableName": table_name,
                "KeySchema": key_schema,
                "AttributeDefinitions": attribute_definitions,
                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
            }

            cls._dynamodb_client.create_table(**create_params)
            waiter = cls._dynamodb_client.get_waiter("table_exists")
            waiter.wait(TableName=table_name)

            return json.dumps({"status": "success", "table_name": table_name, "message": "Table created successfully"})
        except ClientError as e:
            return json.dumps({"error": e.response["Error"]["Message"]})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### DYNAMODB CREATE TABLE END

    ### DYNAMODB DELETE TABLE START
    @classmethod
    def _delete_table_dynamodb(cls, table_name: str) -> str:
        try:
            cls._ensure_dynamodb_initialized()
            cls._dynamodb_client.delete_table(TableName=table_name)
            waiter = cls._dynamodb_client.get_waiter("table_not_exists")
            waiter.wait(TableName=table_name)
            return json.dumps({"status": "success", "table_name": table_name, "message": "Table deleted successfully"})
        except ClientError as e:
            return json.dumps({"error": e.response["Error"]["Message"]})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### DYNAMODB DELETE TABLE END

    ### DYNAMODB TABLE EXISTS START
    @classmethod
    def _table_exists_dynamodb(cls, table_name: str) -> str:
        try:
            cls._ensure_dynamodb_initialized()
            cls._dynamodb_client.describe_table(TableName=table_name)
            return json.dumps({"status": "success", "table_name": table_name, "exists": True})
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return json.dumps({"status": "success", "table_name": table_name, "exists": False})
            return json.dumps({"error": e.response["Error"]["Message"]})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### DYNAMODB TABLE EXISTS END

    ### DYNAMODB ADD START
    @classmethod
    def _add_dynamodb(cls, table_name: str, item: dict) -> str:
        try:
            cls._ensure_dynamodb_initialized()
            table = cls._dynamodb_resource.Table(table_name)
            serialized_item = cls._serialize_dynamodb_item(item)
            table.put_item(Item=serialized_item)
            return json.dumps({"status": "success", "table_name": table_name, "item": item})
        except ClientError as e:
            return json.dumps({"error": e.response["Error"]["Message"]})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def _serialize_dynamodb_item(cls, item: dict) -> dict:
        serialized = {}
        for key, value in item.items():
            serialized[key] = cls._serialize_dynamodb_value(value)
        return serialized

    @classmethod
    def _serialize_dynamodb_value(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        if isinstance(value, dict):
            return {k: cls._serialize_dynamodb_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [cls._serialize_dynamodb_value(v) for v in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    ### DYNAMODB ADD END

    ### DYNAMODB EDIT START
    @classmethod
    def _edit_dynamodb(cls, table_name: str, search_json: dict, new_values: dict) -> str:
        try:
            cls._ensure_dynamodb_initialized()
            table = cls._dynamodb_resource.Table(table_name)
            key = cls._extract_key_from_search_dynamodb(table_name, search_json)

            set_parts = []
            expression_values = {}
            expression_names = {}
            counter = 0

            for attr_name, attr_value in new_values.items():
                name_placeholder = f"#n{counter}"
                value_placeholder = f":v{counter}"
                expression_names[name_placeholder] = attr_name
                expression_values[value_placeholder] = cls._serialize_dynamodb_value(attr_value)
                set_parts.append(f"{name_placeholder} = {value_placeholder}")
                counter += 1

            update_expression = f"SET {', '.join(set_parts)}"

            response = table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW"
            )

            return json.dumps({"status": "success", "table_name": table_name}, default=cls._json_serializer)
        except ClientError as e:
            return json.dumps({"error": e.response["Error"]["Message"]})
        except Exception as e:
            return json.dumps({"error": str(e)})

    ### DYNAMODB EDIT END

    ### DYNAMODB DELETE START
    @classmethod
    def _delete_dynamodb(cls, table_name: str, search_json: dict) -> str:
        try:
            cls._ensure_dynamodb_initialized()
            table = cls._dynamodb_resource.Table(table_name)
            key = cls._extract_key_from_search_dynamodb(table_name, search_json)
            table.delete_item(Key=key)
            return json.dumps({"status": "success", "table_name": table_name})
        except ClientError as e:
            return json.dumps({"error": e.response["Error"]["Message"]})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def _extract_key_from_search_dynamodb(cls, table_name: str, search_json: dict) -> dict:
        table_info = cls._dynamodb_client.describe_table(TableName=table_name)
        key_schema = table_info["Table"]["KeySchema"]
        key = {}
        for key_element in key_schema:
            attr_name = key_element["AttributeName"]
            if attr_name in search_json:
                key[attr_name] = cls._serialize_dynamodb_value(search_json[attr_name])
        if not key:
            raise ValueError("Search JSON must contain at least the partition key")
        return key

    ### DYNAMODB DELETE END

    ### DYNAMODB SEARCH START
    @classmethod
    def _search_dynamodb(cls, table_name: str, search_json: dict, fingerprint_searches: dict) -> str:
        try:
            cls._ensure_dynamodb_initialized()
            table = cls._dynamodb_resource.Table(table_name)

            if not search_json and not fingerprint_searches:
                response = table.scan()
                items = response.get("Items", [])
            else:
                filter_expression = None
                for attr_name, attr_value in search_json.items():
                    condition = Attr(attr_name).eq(attr_value)
                    if filter_expression is None:
                        filter_expression = condition
                    else:
                        filter_expression = filter_expression & condition

                if filter_expression:
                    response = table.scan(FilterExpression=filter_expression)
                else:
                    response = table.scan()
                items = response.get("Items", [])

            if fingerprint_searches:
                filtered_items = []
                for item in items:
                    match = True
                    for fp_col, fp_search_val in fingerprint_searches.items():
                        stored_fp = item.get(fp_col, "")
                        if stored_fp:
                            stored_parts = stored_fp.split(".")
                            search_parts = fp_search_val.split(".")

                            stored_groups = set(stored_parts[0]) if stored_parts else set()
                            search_groups = set(search_parts[0]) if search_parts else set()

                            stored_bigrams = set()
                            if len(stored_parts) > 1:
                                bg = stored_parts[1]
                                stored_bigrams = {bg[i:i + 2] for i in range(0, len(bg), 2)}

                            search_bigrams = set()
                            if len(search_parts) > 1:
                                bg = search_parts[1]
                                search_bigrams = {bg[i:i + 2] for i in range(0, len(bg), 2)}

                            if not (search_groups.issubset(stored_groups) and search_bigrams.issubset(stored_bigrams)):
                                match = False
                                break
                    if match:
                        filtered_items.append(item)
                items = filtered_items

            deserialized = [cls._deserialize_dynamodb_item(item) for item in items]
            return json.dumps(
                {"status": "success", "table_name": table_name, "count": len(deserialized), "items": deserialized},
                default=cls._json_serializer)
        except ClientError as e:
            return json.dumps({"error": e.response["Error"]["Message"]})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def _deserialize_dynamodb_item(cls, item: dict) -> dict:
        deserialized = {}
        for key, value in item.items():
            deserialized[key] = cls._deserialize_dynamodb_value(value)
        return deserialized

    @classmethod
    def _deserialize_dynamodb_value(cls, value: Any) -> Any:
        if isinstance(value, Decimal):
            if value % 1 == 0:
                return int(value)
            return float(value)
        if isinstance(value, dict):
            return {k: cls._deserialize_dynamodb_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [cls._deserialize_dynamodb_value(v) for v in value]
        return value

    ### DYNAMODB SEARCH END

    ### JSON SERIALIZATION START
    @classmethod
    def _json_serializer(cls, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        if isinstance(obj, set):
            return list(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    ### JSON SERIALIZATION END