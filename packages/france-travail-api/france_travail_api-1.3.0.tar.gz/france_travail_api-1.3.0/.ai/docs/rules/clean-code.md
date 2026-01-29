Code Quality:
- Maintain strict typing.
- Disallow untyped values and magic numbers.
- Use explicit enums for possible values.
- Avoid double negatives and ensure conditions are self-documenting.
- Use long, readable variable names reflecting domain concepts.
- Write the simplest code possible.
- Eliminate duplication (DRY).

Length Limits:
- Max 20 lines per function : extract until you drop.
- Max 3 parameters per function.
- Max 300 lines per file.
- Max 10 sub-files per folder.

Responsibilities:
- One responsibility per file.
- Organize code by domain concepts.

Functions:
- No flag parameters; split into multiple functions if needed.
- Follow command-query separation.
- Use verbs for service methods that perform actions.

Errors:
- Fail fast and throw errors early.
- Use custom domain errors and translate errors to user language.
- Log errors in English with error codes.

Code Organization:
- Follow Ports & Adapters pattern.
- Favor composition over inheritance.

Documentation:
- Use Numpy-style docstrings for all public modules, types, constants, and functions (not for private ones).