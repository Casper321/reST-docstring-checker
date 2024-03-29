FROM python:3.12 AS base_bare

LABEL NAME=docstring_checker
LABEL VERSION=1.0.0

WORKDIR /app

# Install poetry, do this before copying files for caching purposes.
RUN pip install poetry==1.8.2

# Copy pyproject.toml, poetry.lock and README.md files.
COPY pyproject.toml poetry.lock README.md ./
COPY rest_docstring_checker/__init__.py rest_docstring_checker/__init__.py

# Install dependencies.
RUN poetry config virtualenvs.create false && poetry install

ENTRYPOINT [ "bash" ]

FROM base_bare AS test

# Required for pre-commit.
RUN apt-get update \
    && apt-get install git build-essential shellcheck -y \
    && apt-get clean
RUN poetry install --with dev
COPY .pre-commit-config.yaml .pre-commit-config.yaml
RUN git init . && pre-commit install-hooks
RUN git config --global --add safe.directory /app
