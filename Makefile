.PHONY:
	build_test
	build_base_bare
	install_poetry
	install
	install_dev
	run_pre_commit
	run_tests

install_poetry:
	pip install --upgrade pip
	# Installing poetry if not installed...
	@python -m poetry --version || \
		pip install poetry==1.8.2

install: install_poetry
	poetry install

install_dev: install_poetry
	poetry install --with dev
	# Installing pre-commit dependencies...
	pre-commit install

build_base_bare:
	docker build \
		--file Dockerfile \
		--target base_bare \
		--tag docstring-checker-bare \
		--cache-from=docstring-checker-bare \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		${PWD}


build_test:
	docker build \
		--file Dockerfile \
		--target test \
		--tag docstring-checker-test  \
		--cache-from=docstring-checker-bare \
		--cache-from=docstring-checker-test \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		${PWD}

run_pre_commit: build_test
	docker run --rm \
		--volume ${PWD}:/app \
		docstring-checker-test \
		-c "pre-commit run --all-files"


run_tests: build_test
	docker run --rm \
		--volume ${PWD}:/app \
		docstring-checker-test \
		-c "python -m pytest"
