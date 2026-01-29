# France Travail API Python SDK

[![Continuous Integration](https://github.com/cmnemoi/france-travail-api/actions/workflows/continuous_integration.yaml/badge.svg)](https://github.com/cmnemoi/france-travail-api/actions/workflows/continuous_integration.yaml)
[![Continuous Delivery](https://github.com/cmnemoi/france-travail-api/actions/workflows/create_github_release.yaml/badge.svg)](https://github.com/cmnemoi/france-travail-api/actions/workflows/create_github_release.yaml)
[![codecov](https://codecov.io/gh/cmnemoi/france-travail-api/graph/badge.svg?token=FLAARH38AG)](https://codecov.io/gh/cmnemoi/france-travail-api)
[![PyPI version](https://badge.fury.io/py/france-travail-api.svg)](https://badge.fury.io/py/france-travail-api)

A high-level Python SDK to interact with the [France Travail API](https://francetravail.io/data/api).

# Quick start

## Installation

```bash
python3 venv .france-travail-api
source .france-travail-api/bin/activate
pip install france-travail-api
```

## Authentication

The SDK handles the OAuth2 Client Credentials Grant flow to authenticate with the API.

Get your API credentials (`FRANCE_TRAVAIL_CLIENT_ID` and `FRANCE_TRAVAIL_CLIENT_SECRET`) from the [France Travail API developer portal](https://francetravail.io/data/api).

## Usage

```python
from france_travail_api.client import FranceTravailClient
from france_travail_api.auth.scope import Scope

with FranceTravailClient(
    client_id="your_id",
    client_secret="your_secret",
    scopes=[Scope.OFFRES]
) as client:
    job_offers =client.offres.search(mots_cles="developpeur")
```

# Contributing

## Unix-like systems (GNU/Linux, macOS, etc.)

You need to have `curl` and [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed on your system.

Then run the following command : `curl -sSL https://raw.githubusercontent.com/cmnemoi/france-travail-api/main/clone-and-install | bash`

## Development

You can run tests with `make test`.

To run integration tests, you need to set `FRANCE_TRAVAIL_CLIENT_ID` and `FRANCE_TRAVAIL_CLIENT_SECRET` environment variables.

# License

The source code of this repository is licensed under the [Apache License 2.0](LICENSE).