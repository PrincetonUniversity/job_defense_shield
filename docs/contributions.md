# Contributions

Contributions to the Jobstats platform and its tools are welcome. To work with the code, build a Conda environment:

```
$ conda create --name jds-env python=3.12     \
                              pandas          \
                              pyarrow         \
                              pytest-mock     \
                              ruff            \
                              blessed         \
                              requests        \
                              pyyaml          \
                              mkdocs-material \
                              -c conda-forge -y
```

## Testing

Be sure that the tests are passing before making a pull request:

```
(jds-env) $ pytest

```

There are additional options for development:

```
(jds-env) $ pytest  --cov=. --capture=tee-sys tests
(jds-env) $ pytest -s tests  # use the -s option to run print statements
```

## Static Checking

Run `ruff` and make sure it is passing for each source file modified:

```
(jds-env) $ ruff check myfile.py
```


## Documentation

The documentation is generated with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). To build and
serve the documentation:

```
(jds-env) $ mkdocs build
(jds-env) $ mkdocs serve
# open a web browser
```
