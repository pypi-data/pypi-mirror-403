from .config import DATA_FILE
import json
import time

# registration system function for keeping track of the cloned and forked repositories
def registration_sys(method, repo_type, repo, user, remove=False):
    
    if not DATA_FILE.exists():
        DATA_FILE.write_text(
            json.dumps({"cloned": [], "forked": []}, indent=4)
        )

    data = json.loads(DATA_FILE.read_text())

    if not remove:
        data[repo_type].append({
            "Name": repo,
            "Owner": user,
            "Date": time.strftime("%A, %d %b,%Y at %l:%M:%S %P %Z%z"),
            "Method": method
        })
    else:
        data[repo_type] = [
            item for item in data[repo_type]
            if item["Name"] != repo
        ]

    DATA_FILE.write_text(json.dumps(data, indent=4))
    
# listing function to show about the corresponding type of repositories

def zlist(kind: str):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if kind == "a":  # all
        for section in data:
            print(f"\n[{section.upper()}]")
            for item in data[section]:
                print(f"- {item['Owner']}/{item['Name']} ({item['Date']})")

    elif kind == "in":  # installed / cloned
        print("\n[INSTALLED]")
        for item in data.get("cloned", []):
            print(f"- {item['Owner']}/{item['Name']} ({item['Date']})")

    elif kind == "f":  # forked
        print("\n[FORKED]")
        for item in data.get("forked", []):
            print(f"- {item['Owner']}/{item['Name']} ({item['Date']})")

    else:
        print("Invalid list command. Use: a | in | f")

# repository information showing function 
def info(target):

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for section, items in data.items():
        for item in items:
            full_name = f"{item['Owner']}/{item['Name']}"
            if target == item["Name"] or target == full_name:
                print("\nRepository Info")
                print("---------------")
                print(f"Name   : {item['Name']}")
                print(f"Owner  : {item['Owner']}")
                print(f"Type   : {section}")
                print(f"Date   : {item['Date']}")
                print(f"Method : {item['Method']}")
                return

    print("Repository not found in registry")


# command map
COMMANDS = {
    "l": lambda arg1, url: zlist(arg1),
    "info": lambda arg1, url: info(arg1)
    
}
