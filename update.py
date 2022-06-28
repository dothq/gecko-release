#!/usr/bin/env python3

import re
import subprocess
import requests
import os
import lzma
import tarfile
import glob
import shutil

def download_file(url):
    local_filename = url.split('/')[-1]

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)

    return local_filename

def main():
    current_ff_version = requests.get("https://download.mozilla.org/?product=firefox-latest-ssl&os=linux", allow_redirects=False)
    current_ff_version = current_ff_version.headers['Location']
    current_ff_version = current_ff_version.split("firefox/releases/")[1].split("/linux-")[0]

    branches = subprocess.check_output(["git", "branch", "-l", "--color=never"])
    branches = re.sub(r'\* ', '', str(branches, 'utf-8'))
    branches = [i for i in branches.split("\n") if i]

    if f"release-{current_ff_version}" in branches:
        print("Version already pushed.")
        quit()
    
    print("Creating orphaned Git branch...")
    os.system(f"git checkout --orphan release-{current_ff_version}")
    os.system("git rm -rf .")

    print(f"Downloading tarball for version {current_ff_version}...")
    tar_url_prefix = "https://archive.mozilla.org/pub/firefox/releases"
    tar_url = f"{tar_url_prefix}/{current_ff_version}/source/firefox-{current_ff_version}.source.tar.xz"
    tar_filename = download_file(tar_url)

    print("Extracting tarball...")
    with lzma.open(tar_filename) as fd:
        with tarfile.open(fileobj=fd) as tar:
            content = tar.extractall(".")

    print("Removing tarball...")
    os.system(f"rm -f {tar_filename}")

    print("Moving files outside parent directory...")
    os.system(f"rsync -ua --remove-source-files firefox-{current_ff_version}/ .")
    os.system(f"rm -rf firefox-{current_ff_version}")

    print("Pushing to Git...")
    os.system("git add .")
    os.system(f"git commit -m \"Firefox Release {current_ff_version}\"")
    os.system(f"git push -u origin release-{current_ff_version}")
    os.system("git checkout latest")
    os.system(f"git pull origin release-{current_ff_version}")

    print("All done.")

if __name__ == "__main__":
    main()