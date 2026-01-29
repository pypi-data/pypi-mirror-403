all: setup-git-hooks install check test 

check: check-format check-lint check-types

check-format:
	uv run ruff format . --diff

check-lint:
	uv run ruff check .

check-types:
	uv run mypy . --exclude=tests

clean:
	find . -name '*.pyc' -delete

install:
	uv lock --locked
	uv sync --locked --group dev --group lint --group test --group docs

lint:
	uv run ruff format .
	uv run ruff check . --fix

semantic-release:
	uv run semantic-release version --no-changelog --no-push --no-vcs-release --skip-build --no-commit --no-tag
	uv lock
	git add pyproject.toml uv.lock
	git commit --allow-empty --amend --no-edit 

setup-env-variables:
	cp .env.example .env

setup-git-hooks:
	chmod +x hooks/pre-commit
	chmod +x hooks/pre-push
	chmod +x hooks/post-commit
	git config core.hooksPath hooks

test:
	uv run pytest -v --cov=france_travail_api --cov-report=xml

upgrade-dependencies:
	uv lock --upgrade

.PHONY: all check check-format check-lint check-types clean install lint semantic-release setup-git-hooks test upgrade-dependencies