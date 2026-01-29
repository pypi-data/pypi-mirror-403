# zyt   
*A simple GitHub repository manager and git command wrapper from the terminal*

---

## 📖 About

**zyt** is a lightweight command-line tool that simplifies common GitHub workflows such as cloning, forking, updating, syncing, and managing repositories.  
It acts as a small wrapper around `git`, `ssh`, and (optionally) the GitHub CLI (`gh`) to reduce repetitive commands and decision-making.

The goal of **zyt** is to let you work with repositories using **short, memorable commands** while automatically choosing the best authentication method available.

---

## 🔧 The Problem It Solves

Working with GitHub repositories often involves:

- Remembering and typing long `git` commands
- Manually setting `upstream` for forks
- Handling SSH vs HTTPS vs GitHub CLI
- Keeping forks up-to-date with upstream
- Cloning private repositories reliably
- Managing cloned and forked repositories

**zyt** solves these by:

- Auto-detecting authentication (GitHub CLI → SSH → HTTPS)
- Automatically configuring `origin` and `upstream`
- Providing one-command workflows for common tasks
- Keeping track of cloned and forked repositories


---

## ✨ Features

- 📥 Clone public and private repositories
- 🍴 Fork repositories with upstream automatically configured
- 🔄 Sync forks with upstream (rebase → merge fallback)
- ⬆️ Update repositories safely
- 🗑️ Uninstall cloned repositories
- 🔐 Authentication auto-detection
- ⚙️ Minimal dependencies
- ⏱ Track cloned and forked repositories with timestamp and auth method 

---

## 🛠 Requirements

- Python **>=3.8**
- `git`
- One of the following for authentication:
  - **GitHub CLI (`gh`)** *(recommended)*
  - **SSH key configured with GitHub**
  - **HTTPS credentials / token**

Optional but recommended:
- `gh` authenticated via:
  ```bash
  gh auth login

## 🚀 Getting started

- Install with pipx:
	```bash
	pipx install zyt-si
	```

>[!NOTE]
>*`zyt` hasn't yet tested on Windows, if any error   occurs, please notify by creating an issue or start a pull request.*
     
     
## 🔥 Usage

```
zyt <command> <username/repository>
```
- Commands
  - clone a repository
    ```
    zyt in <username/repository>
    ```
    - Works for public repositories
    - Works for private repositories if authenticated

  - delete a repository
    ```
    zyt un <username/repository>
    ```
    - Removes the local directory after confirmation

  - update a repository (re-clone)
    ```
    zyt up <username/repository>
    ```
    - Deletes old local copy
    - Clones a fresh copy
    - Useful for corrupted or outdated directories
    - works if in the directory that contains the repo's directory
  - fork a repository 
    ```
    zyt f <username/repository>
    ```
    Automatically:
    - Forks the repository
    - Clones your fork
    - Sets:
      - `origin` → your fork
      - `upstream` → original repository
  - sync fork with upstream 
    ```
    zyt sync <username/repository>
    ```
    Performs:
    - `git fetch upstream`
    - Attempts `git rebase upstream/<branch>`
    - Falls back to `git merge` if rebase fails
  - see cloned(in), forked(f) or all(a) repositories
    ```
    zyt l <cmd(in/f/a)>
    ```
  - see info of a repository
    ```
    zyt info <repo>
    ```


##📂 Project structure:

```
zyt/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
│
├── src/
│   └── zyt/
│       ├── __init__.py
│       ├── __main__.py        ← python -m zit
│       ├── cli.py             ← argument parsing, command dispatch
│       ├── config.py          ← config paths (XDG / AppData)
│       ├── registry.py        ← JSON registry (cloned/forked)
│       ├── auth.py            ← auth detection (gh / ssh / https)
│       ├── gitops.py          ← clone, fork, sync etc. git based operations
│       
│
└── .github/
    └── workflows/
        ├── release.yaml

```

---

## 💻 Updating zyt
- Zyt would get updates in future with new features.
- When new versions of zyt would be available, it can be updated by `pipx upgrade zyt-si`.
  ```
    pipx upgrade zyt-si
  ```
---

## 📄 License

**Zyt** is licensed under the *GNU General Public License v3*

