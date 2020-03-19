import os
import json
import time
import subprocess
import sys
import shlex
import boto3
import hashlib
from datetime import datetime


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def download(
    execution_id: int,
    org: str,
    repo_name: str,
    file_path: str,
    target_dir: str,
    out_file: str,
    commit: str,
):
    print(repo_name, file_path, target_dir, commit)
    token = os.getenv("GITHUB_TOKEN")
    if token is None:
        print(
            "Warning: Environment Var GITHUB_TOKEN does not exist, set this variable to access private GitHub repos"
        )

    cmd = "curl"
    if token is not None:
        cmd = cmd + f" -H 'Authorization: token {token}'"
    cmd = (
        cmd + " -H 'Accept: application/vnd.github.v3.raw' "
        "-L https://raw.githubusercontent.com/{org}/"
        "{repo_name}/{commit}/{file_path} -o {out_file}".format(
            out_file=out_file,
            org=org,
            token=token,
            repo_name=repo_name,
            commit=commit,
            file_path=file_path,
        )
    )

    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)

    with cd(target_dir):
        shcmd(cmd)


def shcmd(cmd, ignore_error=False):
    print("Doing:", cmd)
    try:
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            shell=True,
            timeout=900,
            universal_newlines=True,
        )
    except subprocess.CalledProcessError as exc:
        print("Status : FAIL", exc.returncode, exc.output)
    else:
        print("Output: \n{}\n".format(output))


def download_notebook_and_return_path(request) -> str:
    org = request.args.get("org")
    repo = request.args.get("repo")
    nb_path = request.args.get("nb_path")
    params = request.args.get("params")

    execution_id = time.time() * 1000
    base_file_name = f"{org}.{repo}.{nb_path}".replace("/", "_")

    download(
        execution_id,
        org,
        repo,
        nb_path,
        "/tmp",
        f"{base_file_name}_{execution_id}.ipynb",
        "master",
    )

    out_format = "ipynb"
    input = f"/tmp/{base_file_name}_{execution_id}.{out_format}"
    return input


def execute_notebook(downloaded_nb_path: str, request):
    org = request.args.get("org")
    repo = request.args.get("repo")
    nb_path = request.args.get("nb_path")
    params = request.args.get("params")

    execution_id = time.time() * 1000
    base_file_name = f"{org}.{repo}.{nb_path}".replace("/", "_")

    out_format = "ipynb"
    input = downloaded_nb_path
    output = f"/tmp/{base_file_name}_{execution_id}_out.{out_format}"

    papermill(input, output, params)
    nbconvert(output)

    output = output[: len(output) - 5] + "html"

    store(output)
    return readHTML(output)


def readHTML(file: str):
    with open(file, "r") as content_file:
        return content_file.read()


def nbconvert(report: str):
    shcmd(f"jupyter nbconvert --to html {report}")


def papermill(input: str, output: str, params: str):
    params_s = ""
    if params is not None:
        d = json.loads(params)
        for param in d:
            val = d[param]
            if is_number(val):
                params_s = f"{params_s} -p {param} {val}"
            else:
                params_s = f'{params_s} -p {param} "{val}"'
    cmd = f"papermill {input} {output} {params_s}".strip()
    shcmd(cmd)


def is_number(s):
    try:
        float(s)
        return True
    except:
        return False


def store(output_filename: str):
    bucket_name = os.getenv("S3_BUCKET")
    if bucket_name is None:
        print(
            "Warning: Environment Var S3_BUCKET does not exist, set this variable to save generated reports on S3"
        )
        return

    d = datetime.now()
    obj_name = f'nb_to_html/{d.year}/{d.month}/{output_filename.split("/tmp/")[1]}'
    s3 = boto3.client("s3")
    with open(output_filename, "rb") as f:
        s3.upload_fileobj(f, bucket_name, obj_name)


def hash_file(file_path: str) -> str:
    """
    return sha1 hash of the file
    """
    with open(file_path, "r") as content_file:
        hash_object = hashlib.sha1(content_file.read().encode("utf-8"))
        return hash_object.hexdigest()


def hash_string(str_to_hash: str) -> str:
    hash_object = hashlib.sha1(str_to_hash.encode("utf-8"))
    return hash_object.hexdigest()
