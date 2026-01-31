import os
from dotenv import load_dotenv
from aipmodel.model_registry import MLOpsManager

load_dotenv()

# ==========================================
# 1. INITIALIZATION
# ==========================================
print("\n[STEP 1] Initialize MLOps Manager")
# verbose=True enables detailed logging (Transparency Mode)
manager = MLOpsManager(
    user_token=os.getenv("USER_TOKEN"), 
    CLEARML_API_HOST=os.getenv("CLEARML_API_HOST"),
    CEPH_ENDPOINT_URL=os.getenv("CEPH_ENDPOINT_URL"),
    USER_MANAGEMENT_API=os.getenv("USER_MANAGEMENT_API"),
    verbose=True 
)

# ==========================================
# 2. ADD MODEL SCENARIOS
# ==========================================

# --- A. Local Source (Full Features) ---
print("\n[STEP 2A] Add Local Model (Explicit Version + Category + Tags)")
# Best practice: Provide all metadata for better organization
local_model_id = manager.add_model(
    source_type="local",
    model_name="demo_model_local",
    version="v1.0", 
    source_path="./my_models/v1",       # Local folder to upload
    code_path="./my_models/train.py",   # Optional: Upload training code
    category="Text Generation",         # Supported: "Text Generation", "Image Classification"
    tags=["production", "base-model", "qwen"]
)
print(f" -> Registered ID: {local_model_id}")

# --- B. Local Source (Auto-Versioning) ---
print("\n[STEP 2B] Add Local Model (Auto-Versioning)")
# Passing version=None triggers auto-generation (e.g., _v2, _v3 based on history)
auto_ver_id = manager.add_model(
    source_type="local",
    model_name="demo_model_local",
    version=None, 
    source_path="./my_models/v2_finetuned",
    tags=["experimental", "auto-versioned"]
)
print(f" -> Registered ID: {auto_ver_id}")

# --- C. Hugging Face Source ---
print("\n[STEP 2C] Add Model from Hugging Face")
# Downloads directly from HF Hub to S3
hf_model_id = manager.add_model(
    source_type="hf",
    model_name="demo_model_hf",
    version="v1", 
    source_path="facebook/wav2vec2-base-960h",
    category="Image Classification", # Using supported category as example
    tags=["imported", "audio-processing"]
)
print(f" -> Registered ID: {hf_model_id}")

# --- D. S3 Source (Auto-Auth / Internal Bucket) ---
print("\n[STEP 2D] Add Model from S3 (Internal/Auto-Auth)")
# Uses your user credentials automatically to fetch from internal S3
s3_model_id = manager.add_model(
    source_type="s3",
    model_name="demo_model_s3",
    version="v1",
    source_path="training_jobs/checkpoint-500", # Path inside your bucket
    tags=["internal-training"]
)
print(f" -> Registered ID: {s3_model_id}")

# --- E. S3 Source (External Bucket) ---
print("\n[STEP 2E] Add Model from External S3 (Explicit Creds)")
# Useful for importing models from partners or public buckets
ext_s3_id = manager.add_model(
    source_type="s3",
    model_name="demo_model_external",
    version="v1",
    source_path="shared/models/bert-large",
    external_ceph_endpoint_url="https://external-s3.example.com",
    external_ceph_bucket_name="partner-bucket",
    external_ceph_access_key="ACCESS_KEY",
    external_ceph_secret_key="SECRET_KEY"
)
print(f" -> Registered ID: {ext_s3_id}")


# ==========================================
# 3. MANAGEMENT OPERATIONS
# ==========================================

# --- A. List Models (Transparency Check) ---
print("\n[STEP 3A] List All Models (Verbose Mode)")
# verbose=True prints the full raw metadata JSON for verification
manager.list_models(verbose=True)

# --- B. Get Model Info (Detailed View) ---
print("\n[STEP 3B] Get Detailed Model Info")
# Shows ID, Name, Category, Tags, Web Link, and sorted Version History
manager.get_model_info("demo_model_local")

# --- C. Set Latest Version ---
print("\n[STEP 3C] Manually Set Latest Version")
# Points the 'latest' tag to a specific version without deleting others
manager.set_latest_version(model_name="demo_model_local", version="v1.0")


# ==========================================
# 4. DOWNLOAD OPERATIONS
# ==========================================

# --- A. Download Specific Version ---
print("\n[STEP 4A] Download Specific Version (v1.0)")
manager.get_model(
    model_name="demo_model_local",
    version="v1.0", 
    local_dest="./downloads/demo_v1"
)

# --- B. Download Latest Version ---
print("\n[STEP 4B] Download Latest Version (Implicit)")
# If version is omitted, downloads the version marked as 'latest'
manager.get_model(
    model_name="demo_model_local",
    local_dest="./downloads/demo_latest"
)


# ==========================================
# 5. DELETION SCENARIOS
# ==========================================

# --- A. Delete Specific Version ---
print("\n[STEP 5A] Delete Specific Version (v1.0)")
# Only removes the files for this version. The model container remains if other versions exist.
manager.delete_model(
    model_name="demo_model_local", 
    version="v1.0"
)

# --- B. Delete Entire Model ---
print("\n[STEP 5B] Delete Entire Model")
# 1. You can delete by name (removes all versions and the model entry)
manager.delete_model(model_name="demo_model_hf")

# 2. Or if you delete the LAST remaining version, the model is auto-deleted
# manager.delete_model(model_name="demo_model_local", version="_v2") # Assuming _v2 is the only one left

print("\n[INFO] All scenarios executed.")