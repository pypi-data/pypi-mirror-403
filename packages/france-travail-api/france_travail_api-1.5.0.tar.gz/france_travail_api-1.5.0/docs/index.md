# France Travail API

A high-level Python SDK to interact with the [France Travail API](https://francetravail.io/data/api).

The SDK handles the OAuth2 Client Credentials Grant flow to authenticate with the API.

Get your API credentials (`FRANCE_TRAVAIL_CLIENT_ID` and `FRANCE_TRAVAIL_CLIENT_SECRET`) from the [France Travail API developer portal](https://francetravail.io/data/api) and use them with the SDK :

```python
from france_travail_api import FranceTravailClient, Scope

with FranceTravailClient(
    client_id="your_id",
    client_secret="your_secret",
    scopes=[Scope.OFFRES]
) as client:
    job_offers = client.offres.search(mots_cles="développeur Python")
```