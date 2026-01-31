import os
import shutil
from base64 import b64encode
from urllib.parse import urljoin
import requests
from dotenv import load_dotenv
from huggingface_hub import snapshot_download
from fastapi import HTTPException
from typing import Optional, List, Dict, Any
import json
import logging
import time
import uuid
import re
from tqdm import tqdm  # Fixed import error
from concurrent.futures import ThreadPoolExecutor, as_completed # For parallel processing

from .CephS3Manager import CephS3Manager

load_dotenv()

logger = logging.getLogger(__name__)

class ProjectsAPI:
    def __init__(self, post, verbose):
        self.verbose = verbose
        if self.verbose:
            print("[SDK_DEBUG] Initializing ProjectsAPI...")
        self._post = post
        if self.verbose:
            print("[SDK_SUCCESS] ProjectsAPI initialized")

    def create(self, name, description=""):
        if self.verbose:
            print(f"[SDK_INFO] Creating project: name={name}")
        
        response = self._post("/projects.create", {"name": name, "description": description})
        if not response or "id" not in response:
            error_msg = "Failed to create project in ClearML"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        if self.verbose:
            print(f"[SDK_SUCCESS] Project created: id={response['id']}")
        return response

    def get_all(self):
        if self.verbose:
            print("[SDK_INFO] Retrieving all projects...")
        
        response = self._post("/projects.get_all")
        if not response or "projects" not in response:
            error_msg = "Failed to retrieve projects from ClearML"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        if self.verbose:
            print(f"[SDK_SUCCESS] Retrieved {len(response['projects'])} projects")
        return response["projects"]

class ModelsAPI:
    def __init__(self, post, verbose):
        self.verbose = verbose
        if self.verbose:
            print("[SDK_DEBUG] Initializing ModelsAPI...")
        self._post = post
        if self.verbose:
            print("[SDK_SUCCESS] ModelsAPI initialized")

    def get_all(self, project_id=None):
        if self.verbose:
            print(f"[SDK_INFO] Retrieving models for project_id={project_id}")
        
        payload = {"project": project_id} if project_id else {}
        response = self._post("/models.get_all", payload)

        if isinstance(response, dict):
            if "models" in response and isinstance(response["models"], list):
                if self.verbose:
                    print(f"[SDK_SUCCESS] Retrieved {len(response['models'])} models")
                return response["models"]
            if "data" in response and isinstance(response["data"], dict) and "models" in response["data"]:
                if self.verbose:
                    print(f"[SDK_SUCCESS] Retrieved {len(response['data']['models'])} models")
                return response["data"]["models"]

        error_msg = f"'models' not found in response"
        print(f"[SDK_ERROR] {error_msg}")
        raise ValueError("Failed to retrieve models from ClearML")

    def create(self, name, project_id, metadata=None, uri="", tags=None):
        if self.verbose:
            print(f"[SDK_INFO] Creating model structure: name={name}, tags={tags}")
        
        payload = {
            "name": name,
            "project": project_id,
            "uri": uri
        }
        if tags:
            payload["tags"] = tags

        if isinstance(metadata, (dict, list)):
            payload["metadata"] = metadata

        response = self._post("/models.create", payload)
        if not response or "id" not in response:
            error_msg = "Failed to create model in ClearML"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        if self.verbose:
            print(f"[SDK_SUCCESS] Model structure created: id={response['id']}")
        return response

    def update_metadata(self, model_id, metadata=None):
        if self.verbose:
            print(f"[SDK_INFO] Updating model metadata: id={model_id}")
        
        payload = {"model": model_id}
        if isinstance(metadata, (dict, list)):
            payload["metadata"] = metadata

        response = self._post("/models.add_or_update_metadata", payload)
        if not response:
            error_msg = "Failed to update model metadata"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        if self.verbose:
            print(f"[SDK_SUCCESS] Model metadata updated: id={model_id}")
        return response

    def update_info(self, model_id, uri=None, tags=None):
        if self.verbose:
            print(f"[SDK_INFO] Updating model info (URI/Tags): id={model_id}")
        
        payload = {"model": model_id}
        if uri:
            payload["uri"] = uri
        if tags is not None:
            payload["tags"] = tags

        response = self._post("/models.update", payload)
        if not response:
            error_msg = "Failed to update model info"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        if self.verbose:
            print(f"[SDK_SUCCESS] Model info updated: id={model_id}")
        return response

    def get_by_id(self, model_id):
        if self.verbose:
            print(f"[SDK_INFO] Retrieving model by id: {model_id}")
        
        response = self._post("/models.get_by_id", {"model": model_id})
        model_object = response.get("model") or response.get("data", {}).get("model")
        
        if not model_object:
            error_msg = f"Failed to retrieve model with ID {model_id}"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        if self.verbose:
            print(f"[SDK_SUCCESS] Model retrieved: id={model_object.get('id')}")
        
        return model_object 

    def delete(self, model_id):
        if self.verbose:
            print(f"[SDK_INFO] Deleting model: id={model_id}")
        
        response = self._post("/models.delete", {"model": model_id})
        if not response:
            error_msg = f"Failed to delete model {model_id}"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)
        
        if self.verbose:
            print(f"[SDK_SUCCESS] Model deleted: id={model_id}")
        return response

def get_user_info_with_bearer(bearer_token: str, user_management_url):
    try:
        url = urljoin(user_management_url.rstrip("/") + "/", "metadata")
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {bearer_token}"},
            timeout=100,
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to authenticate: {response.text}",
            )
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error calling user management API: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with user management service: {str(e)}",
        )

def get_user_metadata(bearer_token: Optional[str] = None, user_management_url: str = None):
    if bearer_token:
        user_data = get_user_info_with_bearer(bearer_token , user_management_url)
        user_metadata = user_data.get("metadata")
        authenticated_username = user_data.get("username")
        
        if not user_metadata or not authenticated_username:
             raise KeyError(f"User API returned invalid data (missing metadata/username)")
             
        return user_metadata, authenticated_username
    else:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

class MLOpsManager:
    ALLOWED_CATEGORIES = ["Text Generation", "Image Classification"]

    def _parse_versions_map(self, metadata_container):
        versions_map_raw = "{}"
        if isinstance(metadata_container, dict):
            if "versions_map" in metadata_container:
                val = metadata_container["versions_map"]
                if isinstance(val, dict) and "value" in val:
                    versions_map_raw = val["value"]
                elif isinstance(val, str):
                     versions_map_raw = val
        elif isinstance(metadata_container, list):
            for item in metadata_container:
                if isinstance(item, dict) and item.get("key") == "versions_map":
                    versions_map_raw = item.get("value", "{}")
                    break
        if isinstance(versions_map_raw, dict):
             return versions_map_raw
        try:
            return json.loads(versions_map_raw)
        except:
            return {}

    def _extract_metadata_value(self, metadata_container, key, default=None):
        if isinstance(metadata_container, dict):
            if key in metadata_container:
                val = metadata_container[key]
                if isinstance(val, dict) and "value" in val:
                    return str(val["value"])
                return str(val)
            return default
        elif isinstance(metadata_container, list):
            for item in metadata_container:
                if isinstance(item, dict) and item.get("key") == key:
                    value = item.get("value", default)
                    return str(value) if value is not None else default
        return default

    def _get_ceph_manager(self, public=False):
        if public:
            if self.verbose:
                 print(f"[SDK_DEBUG] Using Public Bucket Manager ({self.public_ceph.bucket_name})")
            return self.public_ceph
        else:
            if self.verbose:
                 print(f"[SDK_DEBUG] Using User Bucket Manager ({self.ceph.bucket_name})")
            return self.ceph

    def set_latest_version(self, model_name, version):
        print(f"[SDK_INFO] Setting latest version for '{model_name}' to '{version}'...")
        
        model_id = self.get_model_id_by_name(model_name)
        if not model_id:
            raise ValueError(f"Model {model_name} not found")

        model_data = self.models.get_by_id(model_id)
        metadata = model_data.get("metadata", {}) 
        
        versions_map = self._parse_versions_map(metadata)
        
        if version not in versions_map:
            raise ValueError(f"Version '{version}' does not exist")

        latest_path = versions_map[version]["path"]
        
        # Check 'public' flag
        is_public = self._extract_metadata_value(metadata, "public", "false").lower() == "true"
        target_bucket = self.public_ceph.bucket_name if is_public else self.ceph.bucket_name
        
        uri = f"s3://{target_bucket}/{latest_path}"

        self.models.update_info(model_id, uri=uri)
        
        new_metadata = [
            {"key": "latest_version", "type": "str", "value": version},
            {"key": "haveModelPy", "type": "str", "value": versions_map[version].get("haveModelPy", "false")}
        ]
        self.models.update_metadata(model_id, metadata=new_metadata)
        
        print(f"[SDK_SUCCESS] Latest version set to '{version}'")

    def __init__(
        self,
        user_token,
        CLEARML_API_HOST=None,
        CLEARML_WEB_HOST=None,
        CEPH_ENDPOINT_URL=None,
        USER_MANAGEMENT_API=None,
        verbose=False,
        skip_connection_check=False
    ):
        self.verbose = verbose
        if self.verbose:
            print("[SDK_INFO] Initializing MLOpsManager...")

        self.USER_TOKEN = user_token
        self.CLEARML_API_HOST = CLEARML_API_HOST or os.environ.get("CLEARML_API_HOST")
        # Ensure we prioritize specific env var for WEB HOST
        self.CLEARML_WEB_HOST = CLEARML_WEB_HOST or os.environ.get("CLEARML_WEB_HOST")
        
        if not self.CLEARML_WEB_HOST:
            self.CLEARML_WEB_HOST = self.CLEARML_API_HOST
            print(f"[SDK_WARN] CLEARML_WEB_HOST not set. Defaulting to API host: {self.CLEARML_API_HOST}")
            print("[SDK_WARN] Web links generated might be incorrect if API and Web UI ports differ.")
        
        self.USER_MANAGEMENT_API = USER_MANAGEMENT_API or os.environ.get("USER_MANAGEMENT_API")
        self.CEPH_ENDPOINT_URL = CEPH_ENDPOINT_URL or os.environ.get("CEPH_ENDPOINT_URL")
        
        # Public Bucket Configuration
        self.CEPH_PUBLIC_BUCKET_NAME = os.environ.get("CEPH_PUBLIC_BUCKET_NAME", "aip-public")
        self.PUBLIC_ACCESS_KEY = os.environ.get("CEPH_ADMIN_ACCESS_KEY")
        self.PUBLIC_SECRET_KEY = os.environ.get("CEPH_ADMIN_SECRET_KEY")

        user_info, self.CLEARML_USERNAME = get_user_metadata(bearer_token=user_token, user_management_url=self.USER_MANAGEMENT_API)

        if not all([self.CLEARML_API_HOST, self.USER_MANAGEMENT_API, self.CEPH_ENDPOINT_URL]):
            error_msg = "Missing required configuration parameters"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)

        # User Credentials (Private)
        self.CEPH_ADMIN_ACCESS_KEY = user_info["s3_access_key"]
        self.CEPH_ADMIN_SECRET_KEY = user_info["s3_secret_key"]
        self.CEPH_USER_BUCKET = user_info["s3_bucket"]
        
        self.CLEARML_ACCESS_KEY = user_info["clearml_access_key"]
        self.CLEARML_SECRET_KEY = user_info["clearml_secret_key"]
        
        if not skip_connection_check:
            if self.verbose:
                print("[SDK_INFO] Performing health checks...")
            if not self.check_user_management_service():
                 raise ValueError("User Management API unreachable")
            if not self.check_clearml_service():
                raise ValueError("ClearML Server down")
            if not self.check_clearml_auth():
                raise ValueError("ClearML Auth incorrect")
            if self.verbose:
                print("[SDK_SUCCESS] Health checks passed")

        if self.verbose:
            print("[SDK_INFO] Initializing CephS3Manager (User & Public)...")
        
        # Private Manager (User Bucket)
        self.ceph = CephS3Manager(
            self.CEPH_ENDPOINT_URL,
            self.CEPH_ADMIN_ACCESS_KEY,
            self.CEPH_ADMIN_SECRET_KEY,
            self.CEPH_USER_BUCKET,
            verbose=self.verbose
        )

        # Public Manager (Public Bucket)
        if self.PUBLIC_ACCESS_KEY and self.PUBLIC_SECRET_KEY:
            self.public_ceph = CephS3Manager(
                self.CEPH_ENDPOINT_URL,
                self.PUBLIC_ACCESS_KEY,
                self.PUBLIC_SECRET_KEY,
                self.CEPH_PUBLIC_BUCKET_NAME,
                verbose=self.verbose
            )
        else:
            print("[SDK_WARN] Missing Public Bucket Credentials. Public visibility features may fail.")
            self.public_ceph = None
        
        if self.verbose:
            print("[SDK_INFO] Authenticating with ClearML...")
        
        creds = f"{self.CLEARML_ACCESS_KEY}:{self.CLEARML_SECRET_KEY}"
        auth_header = b64encode(creds.encode("utf-8")).decode("utf-8")
        res = requests.post(
            f"{self.CLEARML_API_HOST}/auth.login",
            headers={"Authorization": f"Basic {auth_header}"}
        )
        if res.status_code != 200:
            error_msg = "Failed to authenticate with ClearML"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)
        self.token = res.json()["data"]["token"]
        
        if self.verbose:
            print("[SDK_SUCCESS] Authenticated with ClearML")

        self.projects = ProjectsAPI(self._post, verbose=self.verbose)
        self.models = ModelsAPI(self._post, verbose=self.verbose)

        projects = self.projects.get_all()
        self.project_name = f"project_{self.CLEARML_USERNAME}"
        exists = [p for p in projects if p["name"] == self.project_name]
        self.project_id = exists[0]["id"] if exists else self.projects.create(self.project_name)["id"]
        
        if self.verbose:
            print(f"[SDK_SUCCESS] MLOpsManager Ready (Project ID: {self.project_id})")

    def _post(self, path, params=None):
        if self.verbose:
            print(f"[SDK_DEBUG] POST {path}")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            res = requests.post(f"{self.CLEARML_API_HOST}{path}", headers=headers, json=params)
            res.raise_for_status()

            data = res.json()
            if "data" not in data:
                error_msg = f"No 'data' in response from {path}"
                print(f"[SDK_ERROR] {error_msg}")
                raise ValueError(error_msg)
            
            return data["data"]

        except requests.exceptions.RequestException as e:
            error_msg = f"Request to {path} failed: {e}"
            print(f"[SDK_ERROR] {error_msg}")
            raise ValueError(error_msg)
        except ValueError as e:
            error_msg = f"Parsing error from {path}: {e}"
            print(f"[SDK_ERROR] {error_msg}")
            raise ValueError(error_msg)

    def check_user_management_service(self):
        try:
            url = urljoin(self.USER_MANAGEMENT_API.rstrip("/") + "/", "health") 
            try:
                requests.get(url, timeout=5)
            except:
                get_user_info_with_bearer(self.USER_TOKEN, self.USER_MANAGEMENT_API)
            
            if self.verbose:
                print("[SDK_SUCCESS] User Management API Reachable")
            return True
        except Exception as e:
            if self.verbose:
                print(f"[SDK_FAIL] User Management API Check Failed: {e}")
            return False

    def check_clearml_service(self):
        try:
            r = requests.get(self.CLEARML_API_HOST + "/auth.login", timeout=5)
            if r.status_code in [200, 401]:
                if self.verbose:
                    print("[SDK_SUCCESS] ClearML Service Reachable")
                return True
            raise ValueError(f"Status Code: {r.status_code}")
        except Exception as e:
            if self.verbose:
                print(f"[SDK_FAIL] ClearML Service Check Failed: {e}")
            return False

    def check_clearml_auth(self):
        try:
            creds = f"{self.CLEARML_ACCESS_KEY}:{self.CLEARML_SECRET_KEY}"
            auth_header = b64encode(creds.encode("utf-8")).decode("utf-8")
            r = requests.post(
                self.CLEARML_API_HOST + "/auth.login",
                headers={"Authorization": f"Basic {auth_header}"},
                timeout=5
            )
            if r.status_code == 200:
                if self.verbose:
                    print("[SDK_SUCCESS] ClearML Auth Valid")
                return True
            raise ValueError(f"Status Code: {r.status_code}")
        except Exception as e:
            if self.verbose:
                print(f"[SDK_FAIL] ClearML Auth Check Failed: {e}")
            return False

    def get_model_id_by_name(self, name):
        models = self.models.get_all(self.project_id)
        for m in models:
            if m["name"] == name:
                return m["id"]
        return None

    def get_model_link(self, model_id):
        self.get_model_name_by_id(model_id) # Verify existence
        
        host = self.CLEARML_WEB_HOST.rstrip('/')
        link = f"{host}/projects/{self.project_id}/models/{model_id}"
        
        if self.verbose:
            print(f"[SDK_INFO] Generated link: {link}")
        return link

    def get_model_name_by_id(self, model_id):
        model = self.models.get_by_id(model_id)
        return model.get("name") if model else None

    def generate_random_string(self):
        import random
        import string
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=10))

    def transfer_from_s3(self, source_endpoint_url, source_access_key, source_secret_key, source_bucket, source_path, dest_prefix, dest_manager):
        if self.verbose:
            print(f"[SDK_INFO] Transferring from S3: {source_path} -> {dest_prefix}")
        
        tmp_dir = f"./tmp_{self.generate_random_string()}"
        try:
            os.makedirs(tmp_dir, exist_ok=True)

            src_ceph = CephS3Manager(source_endpoint_url, source_access_key, source_secret_key, source_bucket, verbose=self.verbose)
            
            if not source_path.endswith("/") and src_ceph.is_folder(source_path):
                source_path += "/"
            
            try:
                src_ceph.download(source_path, tmp_dir, keep_folder=True, exclude=[".git", ".DS_Store"], overwrite=True)
            except Exception as e:
                if "404" in str(e) and not source_path.endswith("/"):
                    source_path += "/"
                    src_ceph.download(source_path, tmp_dir, keep_folder=True, exclude=[".git", ".DS_Store"], overwrite=True)
                else:
                    raise e

            # Using specific dest_manager for upload
            dest_manager.delete_folder(dest_prefix)
            dest_manager.upload(tmp_dir, dest_prefix)

            if self.verbose:
                print("[SDK_SUCCESS] S3 Transfer completed")
            return True
        except Exception as e:
            error_msg = f"S3 Transfer failed: {e}"
            print(f"[SDK_FAIL] {error_msg}")
            try:
                dest_manager.delete_folder(dest_prefix)
            except:
                pass
            raise ValueError(error_msg)
        finally:
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)

    def add_model(self, source_type, model_name=None, version=None, source_path=None, code_path=None, category=None, tags=None,
                  public=False, external_ceph_endpoint_url=None, external_ceph_bucket_name=None, external_ceph_access_key=None, external_ceph_secret_key=None):

        print(f"[SDK_INFO] Adding model: {model_name} (Source: {source_type}, Public: {public})")

        if not model_name or not isinstance(model_name, str):
            print("[SDK_ERROR] model_name must be a non-empty string")
            return None
        
        if model_name.startswith("tmp_") or model_name.startswith("_tmp_"):
             raise ValueError("Model name cannot start with 'tmp_' or '_tmp_'.")
        
        if model_name.startswith("#"):
             raise ValueError("Model name cannot start with '#'.")

        if version and version.startswith("_"):
             raise ValueError("Version name cannot start with '_'. This is reserved for auto-generated versions.")

        if category:
            if category not in self.ALLOWED_CATEGORIES:
                raise ValueError(f"Invalid category '{category}'. Allowed: {self.ALLOWED_CATEGORIES}")

        if public and not self.public_ceph:
             raise ValueError("Cannot set public=True: Public bucket credentials not configured.")

        # Select the correct manager based on boolean public flag
        current_manager = self._get_ceph_manager(public)

        if source_type not in ["local", "hf", "s3"]:
            print(f"[SDK_ERROR] Unknown source_type: {source_type}")
            return None
        
        if source_type == "local" and (not source_path or not os.path.exists(source_path)):
            print(f"[SDK_FAIL] Local path {source_path} does not exist")
            return None
        
        if source_type == "s3":
            provided_creds = all([external_ceph_access_key, external_ceph_secret_key, external_ceph_bucket_name, external_ceph_endpoint_url])
            if not provided_creds:
                if self.verbose:
                    print("[SDK_INFO] Auto-fetching S3 credentials (User Env)...")
                try:
                    user_meta, _ = get_user_metadata(bearer_token=self.USER_TOKEN, user_management_url=self.USER_MANAGEMENT_API)
                    external_ceph_access_key = user_meta["s3_access_key"]
                    external_ceph_secret_key = user_meta["s3_secret_key"]
                    external_ceph_bucket_name = user_meta["s3_bucket"]
                    external_ceph_endpoint_url = self.CEPH_ENDPOINT_URL
                except Exception as e:
                    print(f"[SDK_FAIL] Credentials fetch failed: {e}")
                    return None

            if not all([source_path, external_ceph_access_key, external_ceph_secret_key, external_ceph_endpoint_url, external_ceph_bucket_name]):
                print(f"[SDK_FAIL] Missing required S3 parameters")
                return None

        is_new_model = False
        existing_model_id = self.get_model_id_by_name(model_name)
        versions_map = {}
        max_version_number = 0

        final_tags = tags if tags else []
        
        if existing_model_id:
            model_id = existing_model_id
            if self.verbose:
                print(f"[SDK_INFO] Updating existing model: {model_id}")
            model_data = self.models.get_by_id(model_id)
            metadata = model_data.get("metadata", {})
            versions_map = self._parse_versions_map(metadata)
            
            # --- STRICT VISIBILITY CHECK ---
            current_public_str = self._extract_metadata_value(metadata, "public", "false")
            is_currently_public = current_public_str.lower() == "true"
            
            if is_currently_public != public:
                status_str = "Public" if is_currently_public else "Private"
                req_str = "Public" if public else "Private"
                error_message = (
                    f"Consistency Error: Model '{model_name}' is currently {status_str}. "
                    f"You cannot add a {req_str} version. "
                    f"Please set public={is_currently_public} or use 'set_model_public' to change the model type first."
                )
                print(f"[SDK_FAIL] {error_message}")
                raise ValueError(error_message)
            # -------------------------------
            
            current_tags = model_data.get("tags", [])
            if final_tags:
                final_tags = list(set(current_tags + final_tags))
            else:
                final_tags = current_tags

            for v_info in versions_map.values():
                if isinstance(v_info, dict) and "version_number" in v_info:
                    try:
                        vn = int(v_info["version_number"])
                        if vn > max_version_number:
                            max_version_number = vn
                    except:
                        pass
        else:
            if self.verbose:
                print("[SDK_INFO] Creating new model entry...")
            # We use a placeholder URI initially, updated later
            created_model = self.models.create(name=model_name, project_id=self.project_id, uri="s3://placeholder", tags=final_tags)
            model_id = created_model["id"]
            is_new_model = True

        next_version_number = max_version_number + 1
        
        if not version:
            version = f"_v{next_version_number}"
            print(f"[SDK_INFO] Auto-generated version: {version}")

        if source_type == "hf":
            model_folder_name = f"hf_{model_name}"
        elif source_type == "local" or source_type == "s3":
            model_folder_name = os.path.basename(source_path.rstrip('/'))
        else:
            model_folder_name = "unknown"

        dest_version_path = f"_models/{model_id}/{version}/"
        temp_suffix = self.generate_random_string()
        dest_temp_path = f"_models/{model_id}/{version}_tmp_{temp_suffix}/"

        local_path = None
        temp_local_path = None
        have_model_py = False
        size_mb = 0.0

        try:
            if self.verbose:
                print(f"[SDK_INFO] Uploading to temporary path: {dest_temp_path}")

            if source_type == "local":
                temp_local_path = f"./tmp_{temp_suffix}"
                shutil.copytree(source_path, temp_local_path, dirs_exist_ok=True)
                size_mb = current_manager.upload(temp_local_path, dest_temp_path)
            elif source_type == "hf":
                local_path = snapshot_download(repo_id=source_path)
                size_mb = current_manager.upload(local_path, os.path.join(dest_temp_path, model_folder_name))
            elif source_type == "s3":
                success = self.transfer_from_s3(
                    external_ceph_endpoint_url, external_ceph_access_key, external_ceph_secret_key,
                    external_ceph_bucket_name, source_path, dest_temp_path, current_manager
                )
                if not success: raise ValueError("S3 Transfer failed")
                size_mb = current_manager.get_uri_size(f"s3://{current_manager.bucket_name}/{dest_temp_path}")

            if code_path and os.path.isfile(code_path):
                current_manager.upload(code_path, dest_temp_path + "model.py")
                have_model_py = True

            if current_manager.check_if_exists(dest_version_path):
                print(f"[SDK_WARN] Version {version} exists. Overwriting...")
                current_manager.delete_folder(dest_version_path)
            
            current_manager.move_folder(dest_temp_path, dest_version_path)

            model_data = self.models.get_by_id(model_id)
            metadata = model_data.get("metadata", {})
            versions_map = self._parse_versions_map(metadata)

            version_info = {
                "path": dest_version_path,
                "size": size_mb,
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "haveModelPy": str(have_model_py).lower(),
                "folderName": model_folder_name,
                "version_number": next_version_number
            }
            versions_map[version] = version_info
            
            keys_to_clean = [k for k in versions_map.keys() if k in ["key", "value", "type"]]
            for k in keys_to_clean:
                del versions_map[k]
            
            total_size = sum(float(v["size"]) for v in versions_map.values() if isinstance(v, dict) and "size" in v)
            
            new_metadata = [
                {"key": "versions_map", "type": "str", "value": json.dumps(versions_map)},
                {"key": "latest_version", "type": "str", "value": version},
                {"key": "modelSize", "type": "float", "value": f"{total_size:.2f}"},
                {"key": "modelFolderName", "type": "str", "value": model_folder_name},
                {"key": "haveModelPy", "type": "str", "value": str(have_model_py).lower()},
                {"key": "version_count", "type": "int", "value": str(len(versions_map))},
                {"key": "public", "type": "bool", "value": str(public).lower()} 
            ]
            
            if category:
                new_metadata.append({"key": "category", "type": "str", "value": category})

            uri = f"s3://{current_manager.bucket_name}/{dest_version_path}"
            
            self.models.update_info(model_id, uri=uri, tags=final_tags)
            self.models.update_metadata(model_id, metadata=new_metadata)

            status_str = "Public" if public else "Private"
            print(f"[SDK_SUCCESS] Model '{model_name}' (Ver: {version}) added successfully to {status_str} storage.")
            return model_id

        except (Exception, KeyboardInterrupt) as e:
            print(f"[SDK_ERROR] Add model failed: {e}")
            if "model_id" in locals():
                try:
                    if is_new_model:
                        self.models.delete(model_id)
                        if self.verbose:
                            print("[SDK_INFO] Rolled back new model creation")
                except:
                    pass
            if dest_temp_path and "current_manager" in locals():
                try:
                    current_manager.delete_folder(dest_temp_path)
                except:
                    pass
            # Re-raise the exception if it was our consistency check
            if "Consistency Error" in str(e):
                raise e
            return None
        finally:
            for path in [local_path, temp_local_path]:
                if path and os.path.exists(path):
                    try:
                        shutil.rmtree(path)
                    except:
                        pass

    def set_model_public(self, model_name, public: bool):
        target_status = "Public" if public else "Private"
        print(f"[SDK_INFO] Changing visibility for '{model_name}' to '{target_status}' (Transactional & Parallel)")
        
        if public and not self.public_ceph:
             raise ValueError("Public bucket not configured.")

        model_id = self.get_model_id_by_name(model_name)
        if not model_id:
             raise ValueError(f"Model {model_name} not found")

        model_data = self.models.get_by_id(model_id)
        metadata = model_data.get("metadata", {})
        
        current_public_str = self._extract_metadata_value(metadata, "public", "false")
        is_currently_public = current_public_str.lower() == "true"

        if is_currently_public == public:
            print(f"[SDK_WARN] Model is already {target_status}")
            return

        # Determine source and destination managers
        src_manager = self._get_ceph_manager(is_currently_public)
        dest_manager = self._get_ceph_manager(public)
        
        model_root_path = f"_models/{model_id}/"

        try:
            # 1. List files in source
            print(f"[SDK_INFO] Listing files in {src_manager.bucket_name}...")
            files = src_manager.list_folder_contents(model_root_path)
            
            if not files:
                 print("[SDK_WARN] No files found for model in source bucket.")
            else:
                print(f"[SDK_INFO] Moving {len(files)} objects from {src_manager.bucket_name} to {dest_manager.bucket_name}...")
                
                # --- PHASE 1: Parallel Server-Side Copy ---
                # Helper function for a single copy operation
                def copy_single_object(key):
                    dest_manager.server_side_copy(
                        src_bucket=src_manager.bucket_name,
                        src_key=key,
                        dest_key=key
                    )
                    return key

                # Execute copies in parallel (max 20 workers)
                copied_files = []
                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = {executor.submit(copy_single_object, f): f for f in files}
                    
                    with tqdm(total=len(files), desc="Parallel Copy", unit="file", ascii=True) as pbar:
                        for future in as_completed(futures):
                            try:
                                result = future.result()
                                copied_files.append(result)
                                pbar.update(1)
                            except Exception as e:
                                raise ValueError(f"Copy failed for a file: {e}")

                # --- PHASE 2: Validation ---
                if len(copied_files) != len(files):
                    raise ValueError("Mismatch in copied files count. Aborting delete.")
                
            # --- PHASE 3: Commit (Metadata Update) ---
            versions_map = self._parse_versions_map(metadata)
            latest_version = self._extract_metadata_value(metadata, "latest_version")
            
            if latest_version and latest_version in versions_map:
                latest_path = versions_map[latest_version]["path"]
                new_uri = f"s3://{dest_manager.bucket_name}/{latest_path}"
                self.models.update_info(model_id, uri=new_uri)

            new_metadata = [
                 {"key": "public", "type": "bool", "value": str(public).lower()}
            ]
            self.models.update_metadata(model_id, metadata=new_metadata)

            # --- PHASE 4: Cleanup (Delete Source) ---
            print("[SDK_INFO] Transaction committed. Cleaning up source bucket...")
            src_manager.delete_folder(model_root_path)

            print(f"[SDK_SUCCESS] Visibility changed to {target_status}")

        except Exception as e:
            print(f"[SDK_FAIL] Transaction Aborted: {e}")
            print("[SDK_INFO] No files were deleted from source. You may have partial files in destination.")
            raise ValueError(f"Failed to change visibility: {e}")

    def get_model(self, model_name, local_dest, version=None):
        print(f"[SDK_INFO] Downloading model: {model_name} (Ver: {version or 'latest'})")

        try:
            model_id = self.get_model_id_by_name(model_name)
            if not model_id: raise ValueError(f"Model {model_name} not found")
            
            model_data = self.models.get_by_id(model_id)
            metadata = model_data.get("metadata", {})
            versions_map = self._parse_versions_map(metadata)
            
            # Check public flag to use correct manager
            is_public = self._extract_metadata_value(metadata, "public", "false").lower() == "true"
            ceph_manager = self._get_ceph_manager(is_public)

            if version:
                if version not in versions_map: raise ValueError(f"Version {version} not found")
                target_path = versions_map[version]["path"]
            else:
                uri = model_data.get("uri")
                if uri and uri.startswith("s3://"):
                    latest_version = self._extract_metadata_value(metadata, "latest_version")
                    if latest_version and latest_version in versions_map:
                         target_path = versions_map[latest_version]["path"]
                    else:
                         parts = uri.replace("s3://", "").split("/", 1)
                         if len(parts) > 1:
                             target_path = parts[1]
                         else:
                             raise ValueError("Invalid URI format")
                else: raise ValueError("No valid URI for latest version")

            ceph_manager.download(
                target_path,
                local_dest,
                keep_folder=True,
                exclude=[".git", ".DS_Store"],
                overwrite=True,
            )
            bucket_label = "Public" if is_public else "Private"
            print(f"[SDK_SUCCESS] Downloaded to {local_dest} (from {bucket_label} bucket)")

        except Exception as exc:
            print(f"[SDK_FAIL] Download failed: {exc}")
            raise ValueError(f"Failed to download model: {exc}") from exc

    def get_model_info(self, identifier):
        if self.verbose:
            print(f"[SDK_INFO] Fetching info for: {identifier}")
        
        model_id = self.get_model_id_by_name(identifier)
        if not model_id: 
            if not re.match(r'^[a-f0-9]{32}$', identifier):
                 raise ValueError(f"No model found with identifier: '{identifier}'")
            model_id = identifier

        try:
            data = self.models.get_by_id(model_id)
        except:
             raise ValueError(f"No model found with identifier: '{identifier}'")

        m = data
        metadata = m.get("metadata", {})
        tags = m.get("tags", [])
        
        total_size = self._extract_metadata_value(metadata, "modelSize", "0")
        latest_version = self._extract_metadata_value(metadata, "latest_version", "N/A")
        category = self._extract_metadata_value(metadata, "category", "N/A")
        version_count = self._extract_metadata_value(metadata, "version_count", "0")
        is_public = self._extract_metadata_value(metadata, "public", "false").lower() == "true"
        
        versions_map = self._parse_versions_map(metadata)
        
        print("=" * 50)
        print(f"SDK_INFO: ID: {m.get('id')}")
        print(f"SDK_INFO: Name: {m.get('name')}")
        print(f"SDK_INFO: Category: {category}")
        print(f"SDK_INFO: Public: {is_public}")
        print(f"SDK_INFO: Tags: {tags}")
        print(f"SDK_INFO: Total Versions: {version_count}")
        print(f"SDK_INFO: Total Size: {total_size} MB")
        print(f"SDK_INFO: Latest Version: {latest_version}")
        
        link = self.get_model_link(model_id)
        print(f"SDK_INFO: Web Link: {link}")
        
        if self.verbose:
            print("\nSDK_INFO: [Full Metadata (Transparency)]")
            print(json.dumps(metadata, indent=4, default=str))

        print("\nSDK_INFO: [Versions]")
        if versions_map:
            def sort_key(item):
                v, info = item
                if isinstance(info, dict) and "version_number" in info:
                     return (0, int(info["version_number"]))
                if v.startswith('v') and v[1:].isdigit():
                    return (1, int(v[1:]))
                return (2, v)
                
            sorted_versions = sorted(versions_map.items(), key=sort_key)

            for v, info in sorted_versions:
                if not isinstance(info, dict):
                    continue 
                size_mb = info.get('size', 0)
                vn = info.get('version_number', 'N/A')
                print(f"SDK_INFO:   - {v:<10} | # {vn} | Size: {size_mb:.2f} MB | Created: {info.get('created')}")
        print("=" * 50)

    def list_models(self, verbose=False):
        if self.verbose:
            print("[SDK_INFO] Listing models...")
        try:
            models = self.models.get_all(self.project_id)
            results = []
            
            print(f"{'Model Name':<25} | {'ID':<25} | {'Latest':<10} | {'Public':<6} | {'Size (MB)':<10} | {'Versions'}")
            print("-" * 130)

            for m in models:
                name = m["name"]
                mid = m["id"]
                metadata = m.get("metadata", {})
                
                versions_map = self._parse_versions_map(metadata)
                latest = self._extract_metadata_value(metadata, "latest_version", "N/A")
                total_size = self._extract_metadata_value(metadata, "modelSize", "0.00")
                is_public = self._extract_metadata_value(metadata, "public", "false").lower() == "true"
                public_display = "T" if is_public else "F"
                version_count = len(versions_map)
                
                valid_versions = [v for v in versions_map.keys() if isinstance(versions_map[v], dict)]

                def sort_key(v):
                    info = versions_map[v]
                    if isinstance(info, dict) and "version_number" in info:
                        return (0, int(info["version_number"]))
                    if v.startswith('v') and v[1:].isdigit():
                        return (1, int(v[1:]))
                    return (2, v)

                sorted_keys = sorted(valid_versions, key=sort_key)
                
                formatted_versions = []
                for v in sorted_keys:
                    if v == latest:
                        formatted_versions.append(f"{v} (latest)")
                    else:
                        formatted_versions.append(v)
                
                display_versions = ", ".join(formatted_versions)
                print(f"{name:<25} | {mid:<25} | {latest:<10} | {public_display:<6} | {str(total_size):<10} | {display_versions}")
                
                model_entry = {
                    "name": name, 
                    "id": mid, 
                    "latest": latest,
                    "total_size_mb": total_size
                }

                if verbose:
                    model_entry["versions_data"] = versions_map
                    model_entry["sorted_versions"] = sorted_keys
                    model_entry["metadata_raw"] = metadata
                    print(f"\n[SDK_DEBUG] Metadata for {name}:")
                    print(json.dumps(metadata, indent=2, default=str))
                    print("-" * 60)
                else:
                    model_entry["versions"] = sorted_keys

                results.append(model_entry)
            
            return results
        except Exception as e:
            print(f"[SDK_FAIL] Failed to list models: {e}")
            raise ValueError(f"Failed to list models: {e!s}")

    def delete_model(self, model_id=None, model_name=None, version=None):
        print(f"[SDK_INFO] Deleting model: {model_name or model_id} (Ver: {version})")
        
        if model_name and not model_id:
            model_id = self.get_model_id_by_name(model_name)
        if not model_id: raise ValueError(f"No model found")

        model_data = self.models.get_by_id(model_id)
        metadata = model_data.get("metadata", {})
        versions_map = self._parse_versions_map(metadata)
        
        # Determine manager based on public flag
        is_public = self._extract_metadata_value(metadata, "public", "false").lower() == "true"
        ceph_manager = self._get_ceph_manager(is_public)

        keys_to_clean = [k for k in versions_map.keys() if k in ["key", "value", "type"]]
        for k in keys_to_clean:
            del versions_map[k]

        if version:
            if version not in versions_map: raise ValueError(f"Version {version} not found")
            
            path_to_delete = versions_map[version]["path"]
            ceph_manager.delete_folder(path_to_delete)
            del versions_map[version]
            
            if not versions_map:
                print(f"[SDK_INFO] No versions left for model. Deleting entire model...")
                ceph_manager.delete_folder(f"_models/{model_id}/") 
                self.models.delete(model_id)
                print(f"[SDK_SUCCESS] Model '{model_name or model_id}' completely deleted.")
                return
            else:
                total_size = sum(float(v["size"]) for v in versions_map.values() if isinstance(v, dict) and "size" in v)
                latest_ver = self._extract_metadata_value(metadata, "latest_version", None)
                new_latest = latest_ver

                if latest_ver == version:
                    def sort_key(v):
                        info = versions_map[v]
                        if isinstance(info, dict) and "version_number" in info:
                            return (0, int(info["version_number"]))
                        if v.startswith('v') and v[1:].isdigit():
                            return (1, int(v[1:]))
                        return (2, v)

                    sorted_versions_keys = sorted(versions_map.keys(), key=sort_key)
                    if sorted_versions_keys:
                        new_latest = sorted_versions_keys[-1]
                        new_uri = f"s3://{ceph_manager.bucket_name}/{versions_map[new_latest]['path']}"
                        self.models.update_info(model_id, uri=new_uri)
                        print(f"[SDK_WARN] Deleted latest version. New latest is {new_latest}")
                    else:
                         new_latest = "N/A"

                new_metadata = [
                    {"key": "versions_map", "type": "str", "value": json.dumps(versions_map)},
                    {"key": "modelSize", "type": "float", "value": f"{total_size:.2f}"},
                    {"key": "latest_version", "type": "str", "value": new_latest},
                    {"key": "version_count", "type": "int", "value": str(len(versions_map))},
                    {"key": "haveModelPy", "type": "str", "value": versions_map[new_latest].get("haveModelPy", "false") if new_latest in versions_map else "false"}
                ]
                self.models.update_metadata(model_id, metadata=new_metadata)
            
            print(f"[SDK_SUCCESS] Version {version} deleted.")

        else:
            ceph_manager.delete_folder(f"_models/{model_id}/")
            self.models.delete(model_id)
            print(f"[SDK_SUCCESS] Model '{model_id}' deleted completely.")