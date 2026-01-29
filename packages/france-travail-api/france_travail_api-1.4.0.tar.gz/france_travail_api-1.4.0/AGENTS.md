# Guidelines for AI Agents - France Travail API

This document outlines coding standards and repository interaction guidelines for AI agents working on the `france_travail_api` project, a Python SDK for France Travail API.

Work exclusively in [TDD](.ai/docs/rules/tdd.md).

## Documentation and Resources

- SDK design best practices: [.ai/docs/sdk-design-best-practices](.ai/docs/sdk-design-best-practices)
- France Travail API documentation: [.ai/docs/france-travail-.ai/docs](.ai/docs/france-travail-.ai/docs)
- Coding standards: [.ai/docs/rules](.ai/docs/rules)

## Repository Interaction

- Use the provided `Makefile` commands to interact with the repository. All commands use `uv` for dependency management.
- Always run `make check` and `make test` before committing changes to ensure code quality.