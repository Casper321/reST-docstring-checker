.PHONY:
	install_poetry
	install
	install_dev
	run_pre_commit
	run_tests

install_poetry:
	pip install --upgrade pip
	# Installing poetry if not installed...
	@python -m poetry --version || \
		pip install poetry==1.5.1

install: install_poetry
	poetry install

install_dev: install_poetry
	poetry install --with dev
	# Installing pre-commit dependencies...
	pre-commit install

run_pre_commit:
	poetry run pre-commit run --all-files

run_tests:
	poetry run python -m pytest
