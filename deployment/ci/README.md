# ignite — CI

Concourse pipeline for ignite. Self-deploying via the `set-pipeline`
job (triggers on `deployment/ci/**` changes).

## Jobs

| Job             | Gate                     | Does                                        |
|-----------------|--------------------------|---------------------------------------------|
| `set-pipeline`  | `deployment/ci/**`       | Re-applies this pipeline to itself          |
| `test-backend`  | any source change        | `pytest` in a fresh venv                     |
| `test-frontend` | any source change        | `npm ci` + `vitest`                          |
| `build-backend` | `test-backend` passed    | kaniko → `harbor/ignite/backend:<sha>`       |
| `build-frontend`| `test-frontend` passed   | kaniko → `harbor/ignite/frontend:<sha>`      |
| `publish-chart` | both builds passed       | helm package + push chart to Harbor OCI      |

## Credentials

Resolved at build time from the Concourse credential manager
(`brindle-concourse-main` namespace):

- `((gitea-pat))` — source checkout.
- `((harbor-chart-robot.username/password))` — image + chart push
  (needs push on the `ignite` Harbor project).

## First-time setup

1. Create the `ignite` project in Harbor.
2. Create a robot account with push access; stage its creds as
   `harbor-chart-robot` in the credential manager (reuse the existing
   one if it already spans projects).
3. Ensure the Gitea repo `parkertdrake/ignite` exists on `main`.
4. `fly -t brindle set-pipeline -p ignite -c deployment/ci/pipeline.yml`.
