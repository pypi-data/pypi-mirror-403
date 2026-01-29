import subprocess
import os
import sys
import re

REPO = "Qarvexium-Ops/Qarvexium"
TAG  = "v0.1.2"
PATTERN = r"extras\.zip\.\d{3}$"
CLOBBER = True
FILES_DIR = os.path.dirname(os.path.abspath(__file__))
RETRIES = 3

def run(cmd):
    try:
        subprocess.run(cmd, check=True);return True
    except subprocess.CalledProcessError:
        return False

def release_exists(tag):
    success = run(["gh", "release", "view", tag, "--repo", REPO])
    return success

def create_release(tag):
    print(f"Creating release {tag}")
    success = run(["gh", "release", "create", tag,"--title", tag,"--notes", "Split extras.zip parts","--repo", REPO])
    if not success:
        print("Failed to create release")
        sys.exit(1)

def upload_file(file_path, index, total):
    size = os.path.getsize(file_path)
    print(f"[{index}/{total}] Uploading {os.path.basename(file_path)} ({size/1e6:.1f} MB)...")
    for attempt in range(RETRIES):
        cmd = ["gh", "release", "upload", TAG, file_path, "--repo", REPO]
        if CLOBBER:
            cmd.append("--clobber")
        success = run(cmd)
        if success:
            print(f"Uploaded {os.path.basename(file_path)} ✅\n")
            return
        print(f"Attempt {attempt+1} failed. Retrying...")
    print(f"Failed to upload {file_path} after {RETRIES} attempts")
    sys.exit(1)

def main():
    split_files = sorted([os.path.join(FILES_DIR, f) for f in os.listdir(FILES_DIR)if re.match(PATTERN, f)])
    if not split_files:
        print(f"No sp files found in '{FILES_DIR}' with pattern '{PATTERN}'")
        sys.exit(1)

    total = len(split_files)
    print(f"Found {total} split files:")
    for f in split_files:
        print("  -", os.path.basename(f))

    if not release_exists(TAG):
        create_release(TAG)
    else:
        print(f"Release {TAG} already exists, skipping.\n")

    for i, f in enumerate(split_files, start=1):
        upload_file(f, i, total)

    print("Done.")

if __name__ == "__main__":
    main()
