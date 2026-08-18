# Contributions

Contributions to Job Defense Shield are welcome. The software has benefitted from these code submissions:

- improved cleaning of `sacct` data (P. Edmon, Harvard Univ.)
- querying LDAP for user email addresses (T. Langford, Yale Univ.)

## Development Environment

To work with the code, build a Conda environment:

```bash
$ conda create --name jds-dev python=3.14     \
                              pandas          \
                              pyarrow         \
                              blessed         \
                              requests        \
                              pyyaml          \
                              pytest          \
                              pytest-mock     \
                              ruff            \
                              mypy            \
                              pre-commit      \
                              mkdocs-material \
                              cffconvert      \
                              -c conda-forge -y
$ conda activate jds-dev
# clone from your fork of the repo
(jds-dev) $ git clone git@github.com:<YourFork>/job_defense_shield.git
(jds-dev) $ cd job_defense_shield
(jds-dev) $ pip install -e .
```

## Testing

Be sure that the tests are passing before making a pull request:

```bash
(jds-dev) $ pytest
```

There are additional options for development:

```bash
(jds-dev) $ pytest  --cov=. --capture=tee-sys tests
(jds-dev) $ pytest -s tests  # use the -s option to run print statements
```

## Static Checking

Run `ruff` and make sure it is passing for each source file modified:

```bash
(jds-dev) $ ruff check myfile.py
```

Run `mypy` to check type hints:

```bash
(jds-dev) $ mypy myfile.py
```

## Pre-commit Hooks

Set up the backend script to intercept your commits by executing the installation command inside your repository:

```bash
(jds-dev) $ pre-commit install
```

When it makes sense to ignore the hooks:

```
(jds-dev) $ git commit -m "Message" --no-verify
```

Or on push:

```
(jds-dev) $ git push --no-verify
```

## Documentation

The documentation is generated with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). To build and
serve the documentation:

```bash
(jds-dev) $ mkdocs build
(jds-dev) $ mkdocs serve
# open a web browser
```
