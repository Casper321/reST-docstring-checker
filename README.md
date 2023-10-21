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
