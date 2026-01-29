from . import gitops, registry
import sys
from .version import get_version

# command map
COMMANDS = {}
COMMANDS.update(gitops.COMMANDS)
COMMANDS.update(registry.COMMANDS)

# command handler 
def handle_command(command: str, arg1: str):
    if command not in COMMANDS:
        print("Unknown command")
        sys.exit(1)

    url = "https://github.com/" + arg1
    COMMANDS[command](arg1, url)

def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("version","v","-v","--version"):
        return get_version()
    elif len(sys.argv) != 3:
        print(
            """Usage:
              zyt in <username/reponame>  - clone a repositories
              zyt un <reponame>           - delete a cloned repositories
              zyt up <username/reponame>  - update a cloned repositories
              zyt f <username/reponame>   - fork a repositories
              zyt sync <username/reponame>- to fetch+ rebase upstream
              zyt l <command> - to see installed or forked repositories
              zyt info <repo> - to check about a cloned or forked repo"""
              )
        sys.exit(1)

    command = sys.argv[1]
    arg1 = sys.argv[2]
    handle_command(command, arg1)

