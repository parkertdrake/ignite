# ignite — secrets

The chart references one pre-existing Secret per namespace:

- `harbor-pull` — dockerconfigjson pull secret for the private ignite
  images on Harbor. Created by `create-secret.sh` (one time per cluster).

The backend stub currently needs no application secrets. When it grows
credentials (database URL, Plaid keys, etc.), add an `ignite-secrets`
Secret and wire it into the chart via a `secretName` + `envFrom` on the
backend Deployment — mirror cairn's `cairn-secrets` pattern.

```sh
HARBOR_PULL_USERNAME='robot$ignite+pull' \
HARBOR_PULL_PASSWORD='...' \
./create-secret.sh
```
