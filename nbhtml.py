import os
import json
import time
import subprocess
import sys
import shlex
import time


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def download(execution_id: int, org: str, repo_name: str, file_path: str, target_dir: str, commit: str):
    print(repo_name, file_path, target_dir, commit)
    token = os.getenv("GITHUB_TOKEN")
    if token == None:
        raise RuntimeError("Environment Var GITHUB_TOKEN does not exist")

    cmd = "curl -H 'Authorization: token {token}' "\
        "-H 'Accept: application/vnd.github.v3.raw' "\
        "-L https://raw.githubusercontent.com/{org}/"\
        "{repo_name}/{commit}/{file_path} -o nb_{execution_id}.ipynb".format(execution_id=execution_id, org=org, token=token,
                                                                             repo_name=repo_name, commit=commit, file_path=file_path)

    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)

    with cd(target_dir):
        shcmd(cmd)


def shcmd(cmd, ignore_error=False):
    print('Doing:', cmd)
    try:
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=True, timeout=900,
            universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        print("Status : FAIL", exc.returncode, exc.output)
    else:
        print("Output: \n{}\n".format(output))


def execute_notebook(request):
    org = request.args.get('org')
    repo = request.args.get('repo')
    nb_path = request.args.get('nb_path')
    params = request.args.get('params')
    
    execution_id = time.time()*1000
    download(execution_id, org, repo, nb_path, '/tmp',
             'master')

    input = f'/tmp/nb_{execution_id}.ipynb'
    output = f'/tmp/nb_{execution_id}_out.ipynb'
    papermill(input, output, params)
    nbconvert(output)

    return readHTML(output)


def readHTML(file: str):
    with open(file.replace('ipynb', 'html'), 'r') as content_file:
        return content_file.read()


def nbconvert(report: str):
    shcmd(f'jupyter nbconvert --to html {report}')


def papermill(input: str, output: str, params: str):
    params_s = ''
    if params is not None:
        d = json.loads(params)
        for param in d:
            params_s = f'{params_s} -p {param} {d[param]}'
    cmd = f'papermill {input} {output} {params_s}'.strip()
    shcmd(cmd)