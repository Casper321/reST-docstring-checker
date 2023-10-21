# reST-docstring-checker

This repository contains a Python utility tool for checking adherence
 to PEP 287 – reStructuredText (reST) Docstring Format.
It validates docstrings in Python files against the reST format.
It's a handy tool for developers seeking to maintain docstring
 readability and consistency with function headers.

## Usage

```yaml
repos:
  - repo: https://github.com/Casper321/reST-docstring-checker
    rev: v0.0.1
    hooks:
      - id: rest-docstring-checker
        additional_dependencies: [ "docstring-parser==0.15" ]
```

## Setup

### Requirements

Ensure you have the following installed:

- Python 3.10 or later
- Pip

### Installation

1. Install the project and its dependencies with Poetry:

```bash
make install
```

If you will be contributing to the project, install the development dependencies:

```bash
make install_dev
```

This includes additional tools like `pre-commit` that help to keep the codebase consistent.

### Running the Tests

After installation, you can run the tests using:

```bash
make run_tests
```

This will run all the tests in the project using `pytest`.

### Using Pre-commit

The project uses `pre-commit` to enforce a variety of community-agreed standards.

Run it with:

```bash
make run_pre_commit
```

This runs pre-commit on all the files in the project. It will also automatically
fix some of the common issues, like whitespace, end of file settings etc.
Make sure you add these changes to your commit.
