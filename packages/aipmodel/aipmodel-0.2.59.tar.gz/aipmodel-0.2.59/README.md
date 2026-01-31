#AIP Model SDKThis SDK provides a robust interface for registering, uploading, downloading, listing, and deleting machine learning models using ClearML and S3 (Ceph) as storage. It supports **automatic versioning**, **categorization**, **tagging**, **metadata transparency**, **web link generation**, and fail-fast connectivity checks.

---

##InstallationInstall from PyPI:

```bash
pip install aipmodel

```

---

##Configuration & AuthenticationTo use the SDK, you must set up your environment variables. You can create a `.env` file in your project root:

```env
# ClearML API Credentials
CLEARML_API_HOST="http://your-clearml-server:8008"
CLEARML_WEB_HOST="http://your-clearml-web-ui:8080"  # Required for generating model web links
CLEARML_ACCESS_KEY="your_access_key"
CLEARML_SECRET_KEY="your_secret_key"

# Ceph / S3 Storage
CEPH_ENDPOINT_URL="https://your-ceph-endpoint.com"

# User Management (Internal)
USER_MANAGEMENT_API="http://your-user-manager:30009"
USER_TOKEN="your_bearer_token" # Or pass explicitly in code

```

> **Note:** `CLEARML_WEB_HOST` is new. If not provided, the SDK will default to the API host, which might result in incorrect clickable links in the output.

---

##Example UsageThis example demonstrates how to use the new features: **Auto-Versioning**, **Categories**, **Tags**, and **Web Links**.

```python
import os
from dotenv import load_dotenv
from aipmodel.model_registry import MLOpsManager

load_dotenv()

# --- STEP 1: Initialize MLOps Manager ---
print("\n[STEP 1] Initialize MLOps Manager")
# verbose=True enables detailed logging and transparency mode.
manager = MLOpsManager(
    user_token=os.getenv("USER_TOKEN"), 
    CLEARML_API_HOST=os.getenv("CLEARML_API_HOST"),
    CLEARML_WEB_HOST=os.getenv("CLEARML_WEB_HOST"), # New: For generating UI links
    CEPH_ENDPOINT_URL=os.getenv("CEPH_ENDPOINT_URL"),
    USER_MANAGEMENT_API=os.getenv("USER_MANAGEMENT_API"),
    verbose=True 
)

# --- STEP 2: Add Local Model (Full Metadata) ---
print("\n[STEP 2] Add Local Model (Explicit Version + Category + Tags)")
local_model_id = manager.add_model(
    source_type="local",
    model_name="demo_model_local",
    version="v1.0", 
    source_path="./my_models/v1",       
    code_path="./my_models/train.py",   
    category="Text Generation",         # Supported: "Text Generation", "Image Classification"
    tags=["production", "base-model"]   # List of string tags
)
print(f" -> Registered ID: {local_model_id}")

# --- STEP 3: Add Local Model (Auto-Versioning) ---
print("\n[STEP 3] Add Local Model (Auto-Versioning)")
# Passing version=None triggers auto-generation (e.g., _v1, _v2 based on history)
auto_ver_id = manager.add_model(
    source_type="local",
    model_name="demo_model_local",
    version=None, 
    source_path="./my_models/v2_finetuned",
    tags=["experimental", "auto-versioned"]
)
print(f" -> Registered ID: {auto_ver_id}")

# --- STEP 4: Add Hugging Face Model ---
print("\n[STEP 4] Add Model from Hugging Face")
hf_model_id = manager.add_model(
    source_type="hf",
    model_name="demo_model_hf",
    version="v1", 
    source_path="facebook/wav2vec2-base-960h",
    category="Image Classification", 
    tags=["imported", "audio"]
)
print(f" -> Registered ID: {hf_model_id}")

# --- STEP 5: Add S3 Model (Auto-Auth) ---
print("\n[STEP 5] Add Model from S3 (Internal)")
s3_model_id = manager.add_model(
    source_type="s3",
    model_name="demo_model_s3",
    version="v1",
    source_path="training_jobs/checkpoint-500",
    tags=["internal-training"]
)
print(f" -> Registered ID: {s3_model_id}")

# --- STEP 6: Get Detailed Info (With Web Link) ---
print("\n[STEP 6] Get Detailed Model Info")
# Displays ID, Name, Category, Tags, Total Versions, and the ClearML Web Link
manager.get_model_info("demo_model_local")

# --- STEP 7: List All Models ---
print("\n[STEP 7] List All Models (Verbose)")
# Lists models with their latest version, size, and version count
manager.list_models(verbose=True)

# --- STEP 8: Management Operations ---
print("\n[STEP 8] Management Operations")

# Download latest version
manager.get_model(model_name="demo_model_local", local_dest="./downloads/latest")

# Set a specific version as 'latest' without deleting others
manager.set_latest_version(model_name="demo_model_local", version="v1.0")

# Delete a specific version
manager.delete_model(model_name="demo_model_local", version="v1.0")

# Delete the entire model (when all versions are gone or by name)
manager.delete_model(model_name="demo_model_hf")

```

---

##API Reference###`MLOpsManager` Methods| Function | Input Arguments | Description |
| --- | --- | --- |
| **`__init__`** | `user_token`, `CLEARML_API_HOST`, `CLEARML_WEB_HOST`, `CEPH_ENDPOINT_URL`, `USER_MANAGEMENT_API`, `verbose` | Initializes connections. Performs fail-fast health checks. |
| **`add_model`** | `source_type`, `model_name`, `version`, `source_path`, `code_path`, `category`, `tags`, `external_ceph_*` | Uploads a model. <br>

<br>• **`version`**: If `None`, generates `_v{n}` automatically.<br>

<br>• **`category`**: "Text Generation" or "Image Classification".<br>

<br>• **`tags`**: List of strings. |
| **`get_model`** | `model_name`, `local_dest`, `version` | Downloads model files. If `version` is omitted, downloads the version marked as 'latest'. |
| **`get_model_info`** | `identifier` (Name or ID) | Prints detailed info including **Web Link**, Tags, Category, and Version History. |
| **`list_models`** | `verbose` | Lists all models. `verbose=True` shows full JSON metadata for transparency. |
| **`set_latest_version`** | `model_name`, `version` | Updates the 'latest' pointer to a specific version without modifying files. |
| **`delete_model`** | `model_name`, `version` | • If `version` provided: Deletes that version.<br>

<br>• If `version` is the *last one*, deletes the model container.<br>

<br>• If `version` omitted: Deletes the entire model. |

---

##Constraints & Validations1. **Model Names:** Cannot start with `tmp_`, `_tmp_`, or `#`.
2. **Version Names:**
* Manual versions cannot start with `_` (reserved for auto-generated versions).
* Auto-generated versions follow the pattern `_v1`, `_v2`, etc.


3. **Categories:** Only the following categories are allowed:
* `Text Generation`
* `Image Classification`



---

##Admin Instructions: Auto-Publishing to PyPIThis SDK uses a GitHub Actions workflow (`.github/workflows/publish.yaml`) for automatic versioning and PyPI publishing.

###Trigger Conditions* Push to `main` branch.
* Commit message contains `pipy commit -push`.
* GitHub variable `PUBLISH_TO_PYPI` is set to `true`.

###Commit Message Format| Keyword | Action |
| --- | --- |
| `pipy commit -push major` | Increments **Major** version (e.g., 1.0.0 -> 2.0.0) |
| `pipy commit -push minor` | Increments **Minor** version (e.g., 0.1.0 -> 0.2.0) |
| `pipy commit -push` | Increments **Patch** version (e.g., 0.1.1 -> 0.1.2) |