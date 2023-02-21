import json
import os
import subprocess
from pathlib import Path

from invoke import task

PERSISTENT_WORKSPACES = ["dev", "prod"]
ROOT_ZONE = "vajeh.co.uk"

default_conf = {
    "PROJECT": os.getenv("PROJECT", Path(os.getcwd()).stem),
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "dev"),
    "WORKSPACE": os.getenv("WORKSPACE", "dev"),
    "TERRAFORM_DIR": os.getenv("TERRAFORM_DIR", "terraform"),
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
}


def load_project_conf():
    with open(f"{os.getcwd()}/project.env.json", 'r') as public_conf_file:
        public_conf = json.load(public_conf_file)

    try:
        with open(f"{os.getcwd()}/project.private.env.json", 'r') as private_conf_file:
            private_conf = json.load(private_conf_file)
    except FileNotFoundError:
        print(
            "Private environment file not found. "
            "Using only default values and environment variables for private settings.")
        private_conf = default_conf

    return default_conf | public_conf | private_conf


config = load_project_conf()
# config will overwrite environment variables
os.environ.update(config)
# DO NOT print the whole config. There are secrets in there
print("Settings:")
print(
    f"PROJECT: {config['PROJECT']}\nENVIRONMENT: {config['ENVIRONMENT']}\n"
    f"WORKSPACE: {config['WORKSPACE']}\nTERRAFORM_DIR: {config['TERRAFORM_DIR']}\n")

ACCOUNT = "ptl" if config['ENVIRONMENT'] != "prod" else "prod"
TERRAFORM_STATE_S3 = f"{config['PROJECT']}-{ACCOUNT}-terraform-state"


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


def get_tf_vars(_dir):
    (_, ws) = get_terraform_workspaces(_dir)
    workspace_tag = ws
    if ws not in PERSISTENT_WORKSPACES and not ws.startswith("pr-"):
        workspace_tag = f"user-{ws}"

    account_zone = f"{ACCOUNT}.{ROOT_ZONE}"

    all_vars = {"project": config["PROJECT"], "workspace_tag": workspace_tag, "account_zone": account_zone}

    tf_vars = ""
    for k, v in all_vars.items():
        tf_vars += f"-var=\"{k}={v}\" "

    return tf_vars


@task(help={"dir": "Directory where terraform files are located. Set default via TERRAFORM_DIR in env var or .env file",
            "ws": "Terraform workspace. Set default via WORKSPACE in env var or .env file"})
def workspace(c, dir=config["TERRAFORM_DIR"], ws=config["WORKSPACE"]):
    (wss, current_ws) = get_terraform_workspaces(dir)
    if ws not in wss:
        create_workspace(dir, ws)
    elif ws != current_ws:
        switch_workspace(dir, ws)


@task(help={"dir": "Directory where terraform files are located. "
                   "Set default via TERRAFORM_DIR in env var or .env file"})
def init(c, dir=config["TERRAFORM_DIR"]):
    c.run(f"terraform -chdir={dir} init -backend-config=\"bucket={TERRAFORM_STATE_S3}\"", in_stream=False)
    print("DO NOT FORGET to run `provider-lock` task if, you added new provider/plugin.")


@task(workspace)
def plan(c, dir=config["TERRAFORM_DIR"]):
    tf_vars = get_tf_vars(dir)
    c.run(f"terraform -chdir={dir} plan {tf_vars}", in_stream=False)


@task(workspace)
def apply(c, dir=config["TERRAFORM_DIR"]):
    tf_vars = get_tf_vars(dir)
    c.run(f"terraform -chdir={dir} apply {tf_vars} -auto-approve", in_stream=False)


@task(workspace)
def destroy(c, dir=config["TERRAFORM_DIR"], dryrun=True):
    (_, ws) = get_terraform_workspaces(dir)
    tf_vars = get_tf_vars(dir)
    if dryrun:
        c.run(f"terraform -chdir={dir} plan {tf_vars} -destroy", in_stream=False)
    else:
        c.run(f"terraform -chdir={dir} destroy {tf_vars} -auto-approve", in_stream=False)
        delete_workspace(dir, ws)


@task(workspace)
def output(c, dir=config["TERRAFORM_DIR"]):
    c.run("mkdir -p build", in_stream=False)
    c.run(f"terraform -chdir={dir} output -json", in_stream=False)


@task(workspace)
def lock_provider(c, dir=config["TERRAFORM_DIR"]):
    print("This will take a while. Be patient!")
    c.run(f"terraform -chdir={dir} providers lock "
          f"-platform=darwin_arm64 -platform=darwin_amd64 -platform=linux_amd64 -platform=windows_amd64",
          in_stream=False)
