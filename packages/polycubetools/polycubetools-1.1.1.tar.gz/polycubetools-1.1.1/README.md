# polycube-framework

### Workflows

These are **only** available on github, not locally

1. lint workflow (runs automatically on PR, required for merging in main:
    - runs pyright with the config in pyproject.toml (pyright strict)
    - runs `black --check --line-length 120 "./src/polycubetools"`
2. format workflow (can be run manually)
    - runs `black --line-length 120 "./src/polycubetools"`
    - commits and push to the chosen branch

### Recommendations

1. PyCharm IDE
    - EAP (EARLY ACCESS PRODUCT) version: has pyright and black tools integrated
    - alternatively: `pip install pyright black`

### Getting started

1. Have a look at pyproject.toml
2. Configure a virtual environment (use python `>=3.12`)
3. For quick testing, feel free to create a script in `scripts/`
