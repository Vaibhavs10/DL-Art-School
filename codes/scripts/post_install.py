import filecmp
import os
import shutil
import sys
import sysconfig
import subprocess
from pathlib import Path
import requests
import zipfile

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata


def run(command, desc=None, errdesc=None, custom_env=None):
    if desc is not None:
        print(desc)

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        env=os.environ if custom_env is None else custom_env,
    )

    if result.returncode != 0:
        message = f"""{errdesc or 'Error running command'}.
Command: {command}
Error code: {result.returncode}
stdout: {result.stdout.decode(encoding="utf8", errors="ignore") if len(result.stdout)>0 else '<empty>'}
stderr: {result.stderr.decode(encoding="utf8", errors="ignore") if len(result.stderr)>0 else '<empty>'}
"""
        raise RuntimeError(message)

    return result.stdout.decode(encoding="utf8", errors="ignore")


print("Fixing Tensorboard...")
# uninstall tensorboard so it works
run("pip uninstall tensorboard -y")
run("pip uninstall tensorboard-data-server -y")
run("pip uninstall tensorboard-plugin-wit -y")
run("pip uninstall tb-nightly -y")
run("pip install tensorboard")
if not os.path.exists("experiments/dvae.pth"):
    print("Downloading DVAE...")
    r = requests.get(
        "https://huggingface.co/jbetker/tortoise-tts-v2/resolve/3704aea61678e7e468a06d8eea121dba368a798e/.models/dvae.pth",
        allow_redirects=True,
    )
    # save to experiments
    open("experiments/dvae.pth", "wb").write(r.content)
if not os.path.exists("experiments/autoregressive.pth"):
    print("Downloading Autoregressive Model...")
    r = requests.get(
        "https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/autoregressive.pth",
        allow_redirects=True,
    )
    # save to experiments
    open("experiments/autoregressive.pth", "wb").write(r.content)

# run("pip uninstall tensorboard -y", "Uninstalling Tensorboard")

base_dir = os.path.dirname(os.getcwd())
# Check for "different" B&B Files and copy only if necessary
if os.name == "nt":
    run(
        f"pip install https://huggingface.co/r4ziel/xformers_pre_built/resolve/main/triton-2.0.0-cp310-cp310-win_amd64.whl",
        "Installing Triton",
        "Couldn't install triton",
    )
    run("pip install -U bitsandbytes==0.35.0", "Installing B&B for Windows")
    bnb_src = os.path.join(os.getcwd(), "resources/bitsandbytes_windows")
    bnb_dest = os.path.join(sysconfig.get_paths()["purelib"], "bitsandbytes")
    cudnn_src = os.path.join(os.getcwd(), "resources/cudnn_windows")
    # check if chudnn is in cwd
    if not os.path.exists(cudnn_src):
        print("Can't find CUDNN in resources, trying main folder...")
        cudnn_src = os.path.join(os.getcwd(), "cudnn_windows")
        if not os.path.exists(cudnn_src):
            cudnn_url = "https://developer.download.nvidia.com/compute/redist/cudnn/v8.6.0/local_installers/11.8/cudnn-windows-x86_64-8.6.0.163_cuda11-archive.zip"
            print(f"Downloading CUDNN 8.6")
            # download with requests
            r = requests.get(cudnn_url, allow_redirects=True)
            # save to cwd
            open("cudnn_windows.zip", "wb").write(r.content)
            # unzip
            with zipfile.ZipFile("cudnn_windows.zip", "r") as zip_ref:
                zip_ref.extractall(os.path.join(os.getcwd(), "resources/"))
            # remove zip
            os.remove("cudnn_windows.zip")
            cudnn_src = os.path.join(
                os.getcwd(),
                "resources/cudnn-windows-x86_64-8.6.0.163_cuda11-archive/bin",
            )
    cudnn_dest = os.path.join(sysconfig.get_paths()["purelib"], "torch", "lib")
    print(f"Checking for CUDNN files in {cudnn_dest}")
    if os.path.exists(cudnn_src):
        if os.path.exists(cudnn_dest):
            # check for different files
            filecmp.clear_cache()
            for file in os.listdir(cudnn_src):
                src_file = os.path.join(cudnn_src, file)
                dest_file = os.path.join(cudnn_dest, file)
                # if dest file exists, check if it's different
                if os.path.exists(dest_file):
                    status = shutil.copy2(src_file, cudnn_dest)
            if status:
                print("Copied CUDNN 8.6 files to destination")
    print(f"Checking for B&B files in {bnb_dest}")
    if not os.path.exists(bnb_dest):
        # make destination directory
        os.makedirs(bnb_dest, exist_ok=True)
    printed = False
    filecmp.clear_cache()
    for file in os.listdir(bnb_src):
        src_file = os.path.join(bnb_src, file)
        if file == "main.py":
            dest = os.path.join(bnb_dest, "cuda_setup")
            if not os.path.exists(dest):
                os.mkdir(dest)
        else:
            dest = bnb_dest
            if not os.path.exists(dest):
                os.mkdir(dest)
        dest_file = os.path.join(dest, file)
        status = shutil.copy2(src_file, dest)
    if status:
        print("Copied B&B files to destination")
