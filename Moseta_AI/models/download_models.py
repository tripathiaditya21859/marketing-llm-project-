
from huggingface_hub import snapshot_download

print("Downloading Qwen2.5-0.5B-Instruct...")

model_path = snapshot_download(
    repo_id="Qwen/Qwen2.5-0.5B-Instruct",
    local_dir="models/Qwen2.5-0.5B-Instruct"
)

print("\nDownload completed!")
print("Model location:", model_path)
