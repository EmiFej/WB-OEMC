
# Goal
-  We want to create a repeatable environment.
- ✅ We use [`uv`](https://docs.astral.sh/uv/) for fast installing + managing dependencies automatically.

# Actions for First time use:

These instructions assumes that the user is using Linux OS (or WSL), has `pip` installed and familiar using bash commands. It is recommended to use vscode for versatile adaptability.

> To check if uv is installed in your system, try

```bash
uv --version
```
if fails, install pip :

```bash
sudo apt install python3-pip  # or your distro's package manager
```

## 1. Clone the repo : 

```bash
git clone https://github.com/EmiFej/WB-OEMC
```

Change directory to your "WB-OEMC" folder and setup the environment manager as following: 

```bash
cd <your-project-folder>
```
## 2. 😎 The simplest command to do everything for you !
- A `Makefile` is provided to do the environment setup for you.
  
```bash
make it
```

- It does the 3 core things:
  - Activates the `uv` env `wb_oemc` from `.venv` directory
  - Installs the dependencies (as listed in `pyproject.toml`) in your environment `wb_oemc`
  - Activates the env `wb_oemc` as a default when you open-up this folder in vscode.


## 4 🎯 Managing Dependencies

| You want to...        | Command               |
|-----------------------|------------------------|
| Add a dependency      | `uv add package-name`   |
| Remove a dependency   | `uv remove package-name`|
| Lock all dependencies   | `uv lock`|

- `uv add` or `remove` auto updates _pyproject.toml_
- For more : check [uv_features](https://docs.astral.sh/uv/getting-started/features/)
---

# Actions for  later usage:

just activate the uv env using one of the following cmds (whatever is easier for your to remember)


```bash
./activate.sh
```
or
```bash
bash activate.sh
```
or
```bash
source .venv/bin/activate
```

🔥 __Ensruing Repeatability tips__: 
- 
- If you want other developers/contributors to repeat your project, then remember to use the `uv.lock` command and make sure `pyproject.lock` file gets uploaded to git-repo.
  - `uv.lock` will generate or update the `pyproject.lock` file with your latest `pyproject.toml`. Make sure to commit the lock file to version control.
  - when the user uses `uv pip install` (via the `Make it` command), the uv installer respects the `pyproject.lock` file for installing exact version of dependencies.  

---

# 🔥 Bonus Tip:
- If you name your environment `.venv` (standard), VS Code and PyCharm automatically detect it and activate it when opening the folder — no need to run activating env cmd.
You just need a `.vscode/settings.json` like:

```bash
{
  "python.defaultInterpreterPath": ".venv/bin/python"
}

> ✨ With our makefile, We have already added this setup for you.
```
- If yoour bash looks like `(wb_oemce) (base) your_linux_user_id` or  `(wb_oemce) (your_conda_env_name) your_linux_user_id`, then deactivate the conda env `deactivate base` or `deactivate your_env_name` to make sure everything is synced in `uv` ecosystem only.


  
# 🎉 Enough for now

You're all set to dive in! 🚀 Happy coding and have fun with modelling ! 💻✨



