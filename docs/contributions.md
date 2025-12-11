# Contributions

Contributions to the Jobstats platform and its tools are welcome. To work with the code, build a Conda environment:

```
$ conda create --name jds-dev python=3.12     \
                              pandas          \
                              pyarrow         \
                              pytest-mock     \
                              ruff            \
                              blessed         \
                              requests        \
                              pyyaml          \
                              mkdocs-material \
                              -c conda-forge -y
$ conda activate jds-dev
# clone from your fork of the repo
(jds-dev) $ git clone git@github.com:<YourUserName>/job_defense_shield.git
(jds-dev) $ cd job_defense_shield
(jds-dev) $ pip install -e .
```

## Testing

Be sure that the tests are passing before making a pull request:

```
(jds-dev) $ pytest
```

There are additional options for development:

```
(jds-dev) $ pytest  --cov=. --capture=tee-sys tests
(jds-dev) $ pytest -s tests  # use the -s option to run print statements
```

## Static Checking

Run `ruff` and make sure it is passing for each source file modified:

```
(jds-dev) $ ruff check myfile.py
```


## Documentation

The documentation is generated with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). To build and
serve the documentation:

```
(jds-dev) $ mkdocs build
(jds-dev) $ mkdocs serve
# open a web browser
```
