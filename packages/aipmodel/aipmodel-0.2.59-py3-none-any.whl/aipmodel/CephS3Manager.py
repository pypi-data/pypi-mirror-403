import json
import mimetypes
import os
import random
import shutil
import string
import subprocess
import sys
import difflib
import re

import boto3
import requests
from botocore.exceptions import ClientError, EndpointConnectionError
from tqdm import tqdm


class CephS3Manager:
    def __init__(self, CEPH_ENDPOINT_URL, CEPH_ADMIN_ACCESS_KEY, CEPH_ADMIN_SECRET_KEY, CEPH_USER_BUCKET, verbose=True):
        self.verbose = verbose
        if self.verbose:
            print("[SDK_INFO] Initializing CephS3Manager...")
        
        if not all([CEPH_ENDPOINT_URL, CEPH_ADMIN_ACCESS_KEY, CEPH_ADMIN_SECRET_KEY, CEPH_USER_BUCKET]):
            error_msg = "Missing required Ceph configuration parameters"
            print(f"[SDK_FAIL] {error_msg}")
            raise ValueError(error_msg)

        self.bucket_name = CEPH_USER_BUCKET
        
        if self.verbose:
            print(f"[SDK_INFO] Bucket: {self.bucket_name}")
            print("[SDK_DEBUG] Creating S3 client...")
        
        self.s3 = boto3.client(
            "s3",
            endpoint_url=CEPH_ENDPOINT_URL,
            aws_access_key_id=CEPH_ADMIN_ACCESS_KEY,
            aws_secret_access_key=CEPH_ADMIN_SECRET_KEY,
        )
        
        if self.verbose:
            print("[SDK_DEBUG] Checking connection...")
        
        if not self.check_connection():
            print(f"[SDK_FAIL] Connection failed")
            raise ValueError("Ceph connection failed")

        if self.verbose:
            print("[SDK_DEBUG] Checking authentication...")
        
        if not self.check_auth():
            print(f"[SDK_FAIL] Authentication failed")
            raise ValueError("Ceph authentication failed")

        if self.verbose:
            print("[SDK_DEBUG] Ensuring bucket exists...")
        self.ensure_bucket_exists()
        
        if self.verbose:
            print("[SDK_SUCCESS] CephS3Manager initialized")

    def generate_random_string(self, length=12):
        if self.verbose:
            print(f"[SDK_DEBUG] Generating random string (len={length})...")
        try:
            characters = string.ascii_letters + string.digits
            return "".join(random.choices(characters) for _ in range(length))
        except Exception as e:
            raise ValueError(f"Error generating string: {e}")

    def generate_key(self, length=12, characters=None):
        try:
            if characters is None:
                characters = string.ascii_letters + string.digits
            return "".join(random.choices(characters) for _ in range(length))
        except Exception as e:
            raise ValueError(f"Error generating key: {e}")

    def generate_access_key(self):
        try:
            characters = string.ascii_uppercase + string.digits
            return "".join(random.choices(characters) for _ in range(20))
        except Exception as e:
            raise ValueError(f"Error generating access key: {e}")

    def generate_secret_key(self):
        try:
            characters = string.ascii_letters + string.digits
            return "".join(random.choices(characters) for _ in range(40))
        except Exception as e:
            raise ValueError(f"Error generating secret key: {e}")

    def create_user(self, username):
        if self.verbose:
            print(f"[SDK_INFO] Creating user: {username}...")
        try:
            access_key = self.generate_access_key()
            secret_key = self.generate_secret_key()

            endpoint_url = self.s3.meta.endpoint_url
            admin_access_key = self.s3.meta.client._request_signer._credentials.access_key
            admin_secret_key = self.s3.meta.client._request_signer._credentials.secret_key

            params = {
                "uid": username,
                "display-name": username,
                "access-key": access_key,
                "secret-key": secret_key,
                "format": "json"
            }

            response = requests.put(
                f"{endpoint_url}/admin/user",
                params=params,
                auth=(admin_access_key, admin_secret_key)
            )

            if response.status_code != 200:
                raise ValueError(f"API error: {response.status_code} - {response.text}")

            if self.verbose:
                print(f"[SDK_SUCCESS] User {username} created")
            return access_key, secret_key

        except Exception as e:
            print(f"[SDK_FAIL] Create user failed: {e}")
            raise ValueError(f"Create user failed: {e}")

    def set_user_quota(self, username, quota_gb):
        if self.verbose:
            print(f"[SDK_INFO] Setting quota for {username}: {quota_gb} GB")
        try:
            endpoint_url = self.s3.meta.endpoint_url
            admin_access_key = self.s3.meta.client._request_signer._credentials.access_key
            admin_secret_key = self.s3.meta.client._request_signer._credentials.secret_key

            max_size_bytes = int(quota_gb * 1024 * 1024 * 1024)

            params = {
                "uid": username,
                "quota-type": "user",
                "max-size": str(max_size_bytes),
                "enabled": "true",
                "format": "json"
            }

            response = requests.put(
                f"{endpoint_url}/admin/user?quota",
                params=params,
                auth=(admin_access_key, admin_secret_key)
            )

            if response.status_code != 200:
                raise ValueError(f"API error: {response.status_code} - {response.text}")

            if self.verbose:
                print(f"[SDK_SUCCESS] Quota set for {username}")

        except Exception as e:
            print(f"[SDK_FAIL] Set quota failed: {e}")
            raise ValueError(f"Set quota failed: {e}")

    def enforce_storage_limit(self, bucket_name, storage_limit):
        if self.verbose:
            print(f"[SDK_INFO] Enforcing storage limit ({storage_limit} GB) on {bucket_name}")
        try:
            size_mb = self.get_uri_size(f"s3://{bucket_name}/")
            size_gb = size_mb / 1024

            if size_gb > storage_limit:
                print(f"[SDK_WARN] Bucket {bucket_name} ({size_gb:.2f} GB) exceeds limit ({storage_limit} GB)")
                return False

            if self.verbose:
                print(f"[SDK_SUCCESS] Bucket size ({size_gb:.2f} GB) within limit")
            return True

        except Exception as e:
            print(f"[SDK_FAIL] Enforce limit failed: {e}")
            raise ValueError(f"Enforce limit failed: {e}")

    def run_cmd(self, cmd, shell=False):
        if self.verbose:
            print(f"[SDK_DEBUG] Running command: {cmd}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=shell, check=True)
            if self.verbose:
                print(f"[SDK_SUCCESS] Command executed")
            return result
        except subprocess.CalledProcessError as e:
            print(f"[SDK_FAIL] Command failed: {e.stderr}")
            raise ValueError(f"Command failed: {e.stderr}")

    def check_s5cmd(self):
        if self.verbose:
            print("[SDK_DEBUG] Checking s5cmd installation...")
        try:
            subprocess.run(["s5cmd", "--version"], capture_output=True, text=True, check=True)
            if self.verbose:
                print("[SDK_SUCCESS] s5cmd found")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            if self.verbose:
                print("[SDK_WARN] s5cmd not found")
            return False

    def check_command_exists(self, cmd_name, path=None):
        if self.verbose:
            print(f"[SDK_DEBUG] Checking command: {cmd_name}")
        try:
            if path:
                exists = os.path.isfile(path) and os.access(path, os.X_OK)
                if self.verbose:
                    print(f"[SDK_INFO] Path check for {cmd_name}: {exists}")
                return exists
            
            path_result = shutil.which(cmd_name)
            if self.verbose:
                print(f"[SDK_INFO] Which check for {cmd_name}: {path_result}")
            return bool(path_result)
        except Exception as e:
            raise ValueError(f"Error checking command: {e}")

    def check_aws_credentials_folder(self):
        if self.verbose:
            print("[SDK_DEBUG] Checking AWS creds folder...")
        try:
            aws_dir = os.path.expanduser("~/.aws")
            os.makedirs(aws_dir, exist_ok=True)
            return True
        except Exception as e:
            print(f"[SDK_FAIL] Failed to create AWS folder: {e}")
            raise ValueError(f"Failed to create AWS folder: {e}")

    def _list_all_files(self):
        if self.verbose:
            print("[SDK_DEBUG] Listing all files...")
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name)
            result = []
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        result.append(obj["Key"])
            return result
        except Exception as e:
            raise ValueError(f"Error listing files: {e}")

    def _find_closest_match(self, target_name, file_list):
        if self.verbose:
            print(f"[SDK_DEBUG] Finding closest match for {target_name}...")
        try:
            matches = difflib.get_close_matches(target_name, file_list, n=1, cutoff=0.5)
            return matches[0] if matches else None
        except Exception as e:
            raise ValueError(f"Error finding match: {e}")

    def get_local_path(self, key):
        return os.path.join("./downloads", self.bucket_name, key)

    def print_file_info(self, file_key, response):
        if self.verbose:
            metadata = response.get("ResponseMetadata", {}).get("HTTPHeaders", {})
            print("\n[SDK_INFO] File Details:")
            print(f"  Name: {file_key}")
            print(f"  Size: {metadata.get('content-length', 'Unknown')} bytes")
            print(f"  Type: {metadata.get('content-type', 'Unknown')}")
            print(f"  Modified: {response.get('LastModified', 'Unknown')}")

    def read_file_from_s3(self, key):
        if self.verbose:
            print(f"[SDK_INFO] Reading file: {key}")
        try:
            if not self.check_if_exists(key):
                file_list = self._list_all_files()
                match = self._find_closest_match(key, file_list)
                msg = f"File '{key}' not found."
                if match: msg += f" Did you mean '{match}'?"
                print(f"[SDK_FAIL] {msg}")
                raise ValueError(msg)

            file_type, _ = mimetypes.guess_type(key)
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            body = response["Body"].read()

            if file_type and ("text" in file_type or file_type in ["application/json", "application/xml"]):
                content = body.decode("utf-8")
                if self.verbose:
                    print("[SDK_SUCCESS] Text file read")
                return content
            
            # Binary fallback
            local_path = f"downloaded_{os.path.basename(key)}"
            with open(local_path, "wb") as f:
                f.write(body)
            if self.verbose:
                print(f"[SDK_SUCCESS] Binary file saved to {local_path}")
            return local_path

        except Exception as e:
            print(f"[SDK_FAIL] Read failed: {e}")
            raise ValueError(f"Read failed: {e}")

    def get_identity(self):
        try:
            sts = boto3.client(
                "sts",
                endpoint_url=self.s3.meta.endpoint_url,
                aws_access_key_id=self.s3.meta.client._request_signer._credentials.access_key,
                aws_secret_access_key=self.s3.meta.client._request_signer._credentials.secret_key,
            )
            return sts.get_caller_identity()
        except Exception as e:
            raise ValueError(f"Identity check failed: {e}")

    def get_user_info(self):
        try:
            iam = boto3.client(
                "iam",
                endpoint_url=self.s3.meta.endpoint_url,
                aws_access_key_id=self.s3.meta.client._request_signer._credentials.access_key,
                aws_secret_access_key=self.s3.meta.client._request_signer._credentials.secret_key,
            )
            return iam.get_user()["User"]
        except Exception as e:
            raise ValueError(f"User info check failed: {e}")

    def ensure_bucket_exists(self):
        try:
            buckets = self.s3.list_buckets()
            names = [b["Name"] for b in buckets.get("Buckets", [])]
            
            if self.bucket_name not in names:
                if self.verbose:
                    print(f"[SDK_INFO] Creating bucket {self.bucket_name}...")
                self.s3.create_bucket(Bucket=self.bucket_name)
                if self.verbose:
                    print(f"[SDK_SUCCESS] Bucket created")
            elif self.verbose:
                print(f"[SDK_SUCCESS] Bucket exists")
        except ClientError as e:
            raise ValueError(f"Failed to ensure bucket: {e}")

    def check_connection(self):
        try:
            self.s3.list_buckets()
            if self.verbose:
                print("[SDK_SUCCESS] Connection established")
            return True
        except Exception as e:
            if self.verbose:
                print(f"[SDK_FAIL] Connection error: {e}")
            return False

    def check_auth(self):
        try:
            self.s3.list_buckets()
            if self.verbose:
                print("[SDK_SUCCESS] Authentication valid")
            return True
        except Exception as e:
            if self.verbose:
                print(f"[SDK_FAIL] Auth error: {e}")
            return False

    def check_if_exists(self, key):
        if self.verbose:
            print(f"[SDK_DEBUG] Checking existence: {key}")
        try:
            resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=key, MaxKeys=1)
            exists = "Contents" in resp and len(resp["Contents"]) > 0
            if self.verbose:
                print(f"[SDK_DEBUG] Exists: {exists}")
            return exists
        except Exception:
            return False

    def get_uri_size(self, uri):
        if self.verbose:
            print(f"[SDK_DEBUG] Calculating size for {uri}...")
        try:
            pattern = r"^s3://([^/]+)/(.+)$"
            match = re.match(pattern, uri)
            if not match:
                key = uri if not uri.startswith("s3://") else uri
            else:
                _, key = match.groups()

            try:
                response = self.s3.head_object(Bucket=self.bucket_name, Key=key)
                return response["ContentLength"] / (1024**2)
            except self.s3.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    if not key.endswith("/"):
                        key += "/"
                else:
                    raise

            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=key)
            total_size = 0
            
            # Silent scanning unless verbose
            iterator = tqdm(pages, desc="Scanning size", leave=False) if self.verbose else pages
            
            for page in iterator:
                contents = page.get("Contents", [])
                if contents:
                    for obj in contents:
                        total_size += obj["Size"]
            
            return total_size / (1024**2)
        except Exception as e:
            if self.verbose:
                print(f"[SDK_WARN] Size calc failed: {e}")
            return 0.0

    def list_buckets(self):
        if self.verbose:
            print("[SDK_INFO] Listing buckets...")
        try:
            response = self.s3.list_buckets()
            buckets = response.get("Buckets", [])
            data = [{"Name": b["Name"], "CreationDate": str(b["CreationDate"])} for b in buckets]
            if self.verbose:
                for b in data:
                    print(f"  - {b['Name']}")
            return data
        except Exception as e:
            raise ValueError(f"List buckets failed: {e}")

    def list_folder_contents(self, folder_prefix):
        if self.verbose:
            print(f"[SDK_INFO] Listing folder: {folder_prefix}")
        try:
            if not folder_prefix.endswith("/"): folder_prefix += "/"
            
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=folder_prefix)
            
            files = []
            for page in pages:
                if "Contents" in page:
                    files.extend([obj['Key'] for obj in page["Contents"]])
            
            if not files and self.verbose:
                print("[SDK_WARN] Folder empty or not found")
            elif self.verbose:
                for f in files: print(f"  - {f}")
            
            return files
        except Exception as e:
            raise ValueError(f"List folder failed: {e}")

    def list_available_buckets(self):
        data = self.list_buckets()
        return [b["Name"] for b in data]

    def print_bucket_full_detail(self):
        if self.verbose:
            print(json.dumps(self.s3.list_buckets(), indent=4, default=str))

    def print_bucket_short_detail(self):
        if self.verbose:
            self.list_buckets()

    def find_file(self, name):
        if self.verbose:
            print(f"[SDK_INFO] Finding: {name}")
        try:
            if name.endswith("/") or "." not in name:
                return self.list_folder_contents(name)
            else:
                return self.read_file_from_s3(name)
        except Exception as e:
            raise ValueError(f"Find failed: {e}")

    def list_model_classes(self):
        if self.verbose:
            print("[SDK_INFO] Listing model classes...")
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix="_models/", Delimiter="/")
            classes = [p["Prefix"].split("/")[1] for p in response.get("CommonPrefixes", [])]
            if self.verbose:
                print(f"[SDK_SUCCESS] Classes: {classes}")
            return classes
        except Exception as e:
            raise ValueError(f"List classes failed: {e}")

    def list_buckets_and_model_classes(self):
        if self.verbose:
            print("[SDK_INFO] Listing buckets and classes...")
        try:
            buckets = self.list_available_buckets()
            result = {}
            for b in buckets:
                try:
                    resp = self.s3.list_objects_v2(Bucket=b, Prefix="_models/", Delimiter="/")
                    classes = [p["Prefix"].split("/")[1] for p in resp.get("CommonPrefixes", [])]
                    result[b] = classes
                    if self.verbose:
                        print(f"  Bucket {b}: {classes}")
                except:
                    result[b] = []
            return result
        except Exception as e:
            raise ValueError(f"List buckets/classes failed: {e}")

    def list_models_and_versions(self):
        if self.verbose:
            print("[SDK_INFO] Listing models and versions...")
        try:
            all_models = {}
            resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix="_models/", Delimiter="/")
            classes = [p["Prefix"].split("/")[1] for p in resp.get("CommonPrefixes", [])]
            
            for cls in classes:
                all_models[cls] = {}
                resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=f"_models/{cls}/", Delimiter="/")
                models = [p["Prefix"].split("/")[2] for p in resp.get("CommonPrefixes", [])]
                
                for m in models:
                    v_resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=f"_models/{cls}/{m}/", Delimiter="/")
                    vers = [p["Prefix"].split("/")[-2] for p in v_resp.get("CommonPrefixes", [])]
                    all_models[cls][m] = vers
                    if self.verbose:
                        print(f"  {cls}/{m}: {vers}")
            return all_models
        except Exception as e:
            raise ValueError(f"List models/versions failed: {e}")

    def is_folder(self, key):
        if key.endswith("/"): return True
        try:
            resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=key + "/", MaxKeys=1)
            return "Contents" in resp and len(resp["Contents"]) > 0
        except:
            return False

    def _download_file_with_progress_bar(self, remote_path, local_path):
        try:
            meta = self.s3.head_object(Bucket=self.bucket_name, Key=remote_path)
            total = int(meta.get("ContentLength", 0))
        except:
            total = None

        try:
            # Force show progress bar even if not verbose, as it is a visual indicator of work
            # Using ascii=True for compatibility
            with tqdm(
                total=total,
                desc=os.path.basename(remote_path),
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                leave=False,
                ascii=True,
            ) as pbar, open(local_path, "wb") as f:
                self.s3.download_fileobj(self.bucket_name, remote_path, f, Callback=pbar.update)
        except Exception as e:
            raise ValueError(f"Download failed: {e}")

    def download_file(self, remote_path, local_path):
        if self.verbose:
            print(f"[SDK_INFO] Downloading file: {remote_path}")
        try:
            if os.path.isdir(local_path):
                local_path = os.path.join(local_path, os.path.basename(remote_path))
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self._download_file_with_progress_bar(remote_path, local_path)
            
            if self.verbose:
                print(f"[SDK_SUCCESS] Downloaded: {local_path}")
        except Exception as e:
            raise ValueError(f"Download file failed: {e}")

    def download_folder(self, remote_folder, local_folder, keep_folder=False, exclude=[], overwrite=False):
        if self.verbose:
            print(f"[SDK_INFO] Downloading folder: {remote_folder}")
        try:
            if not remote_folder.endswith("/"): remote_folder += "/"
            
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=remote_folder)
            
            all_objs = []
            for page in pages:
                if "Contents" in page:
                    all_objs.extend(page["Contents"])
            
            if not all_objs:
                raise ValueError("Folder not found or empty")

            if keep_folder:
                local_folder = os.path.join(local_folder, remote_folder.split("/")[-2])
            os.makedirs(local_folder, exist_ok=True)

            # Always show progress bar for folder download
            with tqdm(total=len(all_objs), desc="Downloading", unit="file", ascii=True) as pbar:
                for obj in all_objs:
                    key = obj["Key"]
                    rel = key[len(remote_folder):]
                    
                    if not rel or any(x in rel for x in exclude):
                        pbar.update(1)
                        continue
                    
                    dest = os.path.join(local_folder, rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    
                    if not overwrite and os.path.exists(dest):
                        pbar.update(1)
                        continue
                    
                    self.s3.download_file(self.bucket_name, key, dest)
                    pbar.update(1)
            
            if self.verbose:
                print(f"[SDK_SUCCESS] Folder downloaded")
        except Exception as e:
            raise ValueError(f"Download folder failed: {e}")

    def download(self, remote_path, local_path, keep_folder=False, exclude=[], overwrite=False):
        if self.verbose:
            print(f"[SDK_INFO] Starting download: {remote_path}")
        try:
            if self.is_folder(remote_path):
                self.download_folder(remote_path, local_path, keep_folder, exclude, overwrite)
            else:
                self.download_file(remote_path, local_path)
        except Exception as e:
            print(f"[SDK_FAIL] Download failed: {e}")
            raise ValueError(f"Download failed: {e}")

    def upload_file(self, local_file_path, remote_path):
        if self.verbose:
            print(f"[SDK_DEBUG] Uploading file: {local_file_path}")
        try:
            self.s3.upload_file(local_file_path, self.bucket_name, remote_path)
            if self.verbose:
                print(f"[SDK_SUCCESS] Uploaded file")
        except Exception as e:
            raise ValueError(f"Upload file failed: {e}")

    def upload(self, local_path, remote_path):
        if self.verbose:
            print(f"[SDK_INFO] Starting upload: {local_path} -> {remote_path}")
        
        try:
            if os.path.isfile(local_path) and self.is_folder(remote_path):
                raise ValueError("Cannot upload file to folder path")

            if self.check_s5cmd() and os.path.isdir(local_path):
                if self.verbose:
                    print("[SDK_INFO] Optimizing upload with s5cmd...")
                if not remote_path.endswith('/'): remote_path += '/'
                
                cmd = ["s5cmd", "--endpoint-url", self.s3.meta.endpoint_url, "cp", f"{local_path}/*", f"s3://{self.bucket_name}/{remote_path}"]
                env = os.environ.copy()
                env["AWS_ACCESS_KEY_ID"] = self.s3.meta.client._request_signer._credentials.access_key
                env["AWS_SECRET_ACCESS_KEY"] = self.s3.meta.client._request_signer._credentials.secret_key
                
                subprocess.run(cmd, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if self.verbose:
                    print("[SDK_SUCCESS] s5cmd upload completed")
            
            elif os.path.isdir(local_path):
                # Recursive upload with progress
                files = []
                for root, _, fs in os.walk(local_path):
                    for f in fs:
                        lf = os.path.join(root, f)
                        rk = os.path.join(remote_path, os.path.relpath(lf, local_path)).replace("\\", "/")
                        files.append((lf, rk))
                
                # Always show progress bar
                with tqdm(total=len(files), desc="Uploading", unit="file", ascii=True) as pbar:
                    for lf, rk in files:
                        self.s3.upload_file(lf, self.bucket_name, rk)
                        pbar.update(1)
            
            else:
                self.upload_file(local_path, remote_path)

            size = self.get_uri_size(f"s3://{self.bucket_name}/{remote_path}")
            if self.verbose:
                print(f"[SDK_SUCCESS] Upload complete ({size:.2f} MB)")
            return size

        except Exception as e:
            print(f"[SDK_FAIL] Upload failed: {e}")
            raise ValueError(f"Upload failed: {e}")

    def delete_folder(self, prefix):
        if self.verbose:
            print(f"[SDK_INFO] Deleting folder: {prefix}")
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            objs = []
            for page in pages:
                if "Contents" in page:
                    objs.extend([{"Key": o["Key"]} for o in page["Contents"]])
            
            if not objs:
                if self.verbose:
                    print("[SDK_WARN] Folder empty or not found")
                return

            for i in range(0, len(objs), 1000):
                chunk = objs[i:i+1000]
                self.s3.delete_objects(Bucket=self.bucket_name, Delete={"Objects": chunk})
            
            if self.verbose:
                print("[SDK_SUCCESS] Folder deleted")
        except Exception as e:
            raise ValueError(f"Delete folder failed: {e}")

    def move_folder(self, src_prefix, dest_prefix):
        if self.verbose:
            print(f"[SDK_INFO] Moving: {src_prefix} -> {dest_prefix}")
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=src_prefix)
            
            keys = []
            for page in pages:
                if "Contents" in page:
                    keys.extend([o["Key"] for o in page["Contents"]])
            
            if not keys:
                raise ValueError("Source folder empty")

            # Progress bar for moving
            with tqdm(total=len(keys), desc="Moving", unit="file", ascii=True, disable=not self.verbose) as pbar:
                for src in keys:
                    dest = src.replace(src_prefix, dest_prefix, 1)
                    self.s3.copy_object(Bucket=self.bucket_name, CopySource={"Bucket": self.bucket_name, "Key": src}, Key=dest)
                    pbar.update(1)
            
            self.delete_folder(src_prefix)
            if self.verbose:
                print("[SDK_SUCCESS] Move completed")
        except Exception as e:
            print(f"[SDK_FAIL] Move failed: {e}")
            raise ValueError(f"Move failed: {e}")
    
    def server_side_copy(self, src_bucket, src_key, dest_key):
        """
        Copies a file directly from source bucket to current bucket using Server-Side Copy.
        """
        if self.verbose:
            print(f"[SDK_DEBUG] Server-side copy: {src_bucket}/{src_key} -> {self.bucket_name}/{dest_key}")
        try:
            copy_source = {
                'Bucket': src_bucket,
                'Key': src_key
            }
            # client.copy handles large files (multipart) automatically
            self.s3.copy(copy_source, self.bucket_name, dest_key)
        except Exception as e:
            raise ValueError(f"Server-side copy failed: {e}")