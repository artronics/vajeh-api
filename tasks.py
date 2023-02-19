import os
import subprocess
from pathlib import Path

from invoke import task

ENV_FILE = ".env"
PERSISTENT_WORKSPACES = ["dev", "prod"]
ROOT_ZONE = "vajeh.co.uk"

default_kvm = {
    "PROJECT": os.getenv("PROJECT", Path(os.getcwd()).stem),
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "dev"),
    "WORKSPACE": os.getenv("WORKSPACE", "dev"),
    "TERRAFORM_DIR": os.getenv("TERRAFORM_DIR", "terraform"),
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
}


def update_kvm():
    try:
        with open(ENV_FILE) as f:
            kv = {k.strip(): v.strip() for k, v in (line.split('=') for line in f if line.strip())}
    except ValueError:
        print("Parse error. Format file like key=value")
        exit(1)
    except FileNotFoundError:
        print("Environment file not found. Using only default values and environment variables.")
        return default_kvm
    return default_kvm | kv


kvm = update_kvm()
# .env kvm will overwrite environment variables
os.environ.update(kvm)
# DO NOT print the whole kvm. There are secrets in there
print("Settings:")
print(
    f"PROJECT: {kvm['PROJECT']}\nENVIRONMENT: {kvm['ENVIRONMENT']}\nWORKSPACE: {kvm['WORKSPACE']}\nTERRAFORM_DIR: {kvm['TERRAFORM_DIR']}\n")

ACCOUNT = "ptl" if kvm['ENVIRONMENT'] != "prod" else "prod"


def get_state_s3_name():
    prj = kvm['PROJECT']
    return f"{prj}-{ACCOUNT}-terraform-state"


TERRAFORM_STATE_S3 = get_state_s3_name()


def get_tf_vars(ws):
    workspace_tag = ws
    if ws not in PERSISTENT_WORKSPACES and not ws.startswith("pr-"):
        workspace_tag = f"user-{ws}"

    account_zone = f"{ACCOUNT}.{ROOT_ZONE}"

    all_vars = {"project": kvm["PROJECT"], "workspace_tag": workspace_tag, "account_zone": account_zone}

    tf_vars = ""
    for k, v in all_vars.items():
        tf_vars += f"-var=\"{k}={v}\" "

    return tf_vars


def parse_workspace_list(output):
    workspaces = []
    current_ws = None
    for ws in output.split("\n"):
        _ws = ws.strip()
        if _ws.startswith("*"):
            current_ws = _ws.lstrip("*").strip()
            workspaces.append(current_ws)
        elif _ws != "":
            workspaces.append(_ws)
    return workspaces, current_ws


def get_terraform_workspaces(_dir) -> (list[str], str):
    s = subprocess.check_output(["terraform", f"-chdir={_dir}", "workspace", "list"])
    return parse_workspace_list(s.decode("utf-8"))


def switch_workspace(_dir, ws):
    subprocess.run(["terraform", f"-chdir={_dir}", "workspace", "select", ws])


def create_workspace(_dir, ws):
    subprocess.run(["terraform", f"-chdir={_dir}", "workspace", "new", ws])


def delete_workspace(_dir, ws):
    (_, current) = get_terraform_workspaces(_dir)
    if ws == "default" or current == "default":
        return
    switch_workspace(_dir, "default")
    subprocess.run(["terraform", f"-chdir={_dir}", "workspace", "delete", ws])


@task(help={"dir": "Directory where terraform files are located. Set default via TERRAFORM_DIR in env var or .env file",
            "ws": "Terraform workspace. Set default via WORKSPACE in env var or .env file"})
def workspace(c, dir=kvm["TERRAFORM_DIR"], ws=kvm["WORKSPACE"]):
    (wss, current_ws) = get_terraform_workspaces(dir)
    if ws not in wss:
        create_workspace(dir, ws)
    elif ws != current_ws:
        switch_workspace(dir, ws)


@task(help={"dir": "Directory where terraform files are located. "
                   "Set default via TERRAFORM_DIR in env var or .env file"})
def init(c, dir=kvm["TERRAFORM_DIR"]):
    c.run(f"terraform -chdir={dir} init -backend-config=\"bucket={TERRAFORM_STATE_S3}\"", in_stream=False)


@task(workspace)
def plan(c, dir=kvm["TERRAFORM_DIR"]):
    (_, ws) = get_terraform_workspaces(dir)
    tf_vars = get_tf_vars(ws)
    c.run(f"terraform -chdir={dir} plan {tf_vars}", in_stream=False)


@task(workspace)
def apply(c, dir=kvm["TERRAFORM_DIR"]):
    (_, ws) = get_terraform_workspaces(dir)
    tf_vars = get_tf_vars(ws)
    c.run(f"terraform -chdir={dir} apply {tf_vars} -auto-approve", in_stream=False)


@task(workspace)
def destroy(c, dir=kvm["TERRAFORM_DIR"], dryrun=True):
    (_, ws) = get_terraform_workspaces(dir)
    tf_vars = get_tf_vars(ws)
    if dryrun:
        c.run(f"terraform -chdir={dir} plan {tf_vars} -destroy", in_stream=False)
    else:
        c.run(f"terraform -chdir={dir} destroy {tf_vars} -auto-approve", in_stream=False)
        delete_workspace(dir, ws)


@task(workspace)
def output(c, dir=kvm["TERRAFORM_DIR"]):
    c.run("mkdir -p build", in_stream=False)
    c.run(f"terraform -chdir={dir} output -json", in_stream=False)
