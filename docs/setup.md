# WB-OEMC Modelling Environment Setup Instructions:

- This instruction assumes that the :
  - user is using __Linux__ (or __WSL in Windows Machine__) or __MAC-OS__
  - has `conda` and `pip` installed and familiar using bash/terminal commands. 
- It is recommended to use `vscode` for versatile adaptability and the `ruff` extension for linting and code quality checks.


## Clone the repo : 

```bash
git clone https://github.com/EmiFej/WB-OEMC
```

## Change directory to your __"WB-OEMC"__ folder 

```bash
cd <your-project-folder>
```
## Use the action items for the environment manager as following: 

| **Action**                          | **Command**                                                                                     | **Description**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Set up the environment**          | `make setup`                                                                                    | Initializes the environment using the provided `Makefile`.                                          |
| **Export dependencies**             | `make export` <br> or  <br>`conda env export --name wb_oemc > env/environment.yml`                        | Saves the current environment's dependencies to `environment.yml` for reproducibility.              |
| **Update environment**              | `make update` <br> or  <br>`conda env update -f env/environment.yml`                                      | Updates the environment with the latest dependencies from `environment.yml`.                        |
| **Deactivate conda environment**    | `conda deactivate`                                                                              | Deactivates the current conda environment to ensure proper syncing within the `uv` ecosystem only.  |

# 🔥 Tip:

- Update the __[Makefile](https://github.com/EmiFej/WB-OEMC/blob/main/Makefile)__ with your frequent use commands to handle the commands gracefully !
- Use `make` commands to simplify repetitive tasks and ensure consistency.
---

# 🎉 Enough for now

You're all set to dive in! 🚀 Happy coding and have fun with modelling ! 💻✨
