from pathlib import Path
import subprocess
import os
import shutil
from .registry import registration_sys
from .auth import detect_auth_method

def install(url):
    method = detect_auth_method()
    repo_name = url.strip().strip("/").split("/")[-1]
    user = url.strip().strip("/").split("/")[-2]
    subprocess.run(["git", "clone", url])
    registration_sys(method, "cloned", repo_name, user)

def uninstall(repo):
    repo_path = Path(repo)
    if repo_path.is_dir():
        consent = input(f"Are you sure you want to uninstall {repo}? (Y/n): ")
        if consent == "Y":
            shutil.rmtree(repo)
            registration_sys(None, "cloned", repo, None, remove=True)
        else:
            print("Cancelled")
    else:
        print(f"No directory named {repo}")

def update(repo, url):
	repo_path = Path(repo)
	if repo_path.is_dir():
	       consent = input(f"Are you sure you want to update {repo}?\n (updating will delete all old data)? (Y/n): ")
	       if consent == "Y":
	           trash = repo_path.with_name(repo_name + "_trash")
	           repo_path.rename(trash)
	           subprocess.run(["git", "clone", url])
	           #delete directory if cloning successful 
	           shutil.rmtree(trash_dir)
	       else:
	       	print("Cancelled")
	else:
		print(f"No directory named {repo_name}")


def sync(repo):
    repo_name = repo.split("/")[1]
    repo_path = Path(repo_name)

    if not repo_path.is_dir():
        print("Repository not found locally")
        return

    os.chdir(repo_path)
    subprocess.run(["git", "fetch", "upstream"])

    branch = subprocess.check_output(
        ["git", "branch", "--show-current"],
        text=True
    ).strip()

    result = subprocess.run(
        ["git", "rebase", f"upstream/{branch}"]
    )

    if result.returncode != 0:
        subprocess.run(["git", "rebase", "--abort"])
        subprocess.run(["git", "merge", f"upstream/{branch}"])

def fork(repo):
    user, repo_name = repo.split("/")
    method = detect_auth_method()
    repo_path = Path(repo_name)

    if method == "gh":
        subprocess.run(["gh", "repo", "fork", repo, "--clone"])
        Path.cwd().joinpath(repo_name)
        subprocess.run([
            "git", "remote", "add",
            "upstream",
            f"https://github.com/{user}/{repo_name}.git"
        ])
        return

    if method == "ssh":
        url = f"git@github.com:{user}/{repo_name}.git"
    else:
        url = f"https://github.com/{user}/{repo_name}.git"

    subprocess.run(["git", "clone", url])
    repo_path.chdir()
    subprocess.run(["git", "remote", "add", "upstream", url])
    registration_sys(method, "forked", repo_name, owner=user)

# command map 
COMMANDS = {
    "in": lambda arg1, url: install(url),
    "un": lambda arg1, url: uninstall(arg1),
    "up": lambda arg1, url: update(arg1, url),
    "f":  lambda arg1, url: fork(arg1),
    "sync": lambda arg1, url: sync(arg1)
    }