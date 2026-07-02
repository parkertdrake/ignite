# ignite — deployment

Everything needed to build, package, and ship ignite to the
brindle-cluster. Modeled on cairn's deployment layout.

## Layout

- `chart/` — Helm chart (frontend + backend Deployments/Services + a
  single HTTPRoute). Source of truth for the chart; published to Harbor
  OCI on every green CI build.
- `ci/` — Concourse pipeline + tasks. Tests → kaniko image builds →
  helm chart push.
- `secrets/` — one-time `harbor-pull` image-pull secret bootstrap.

## Flow

1. Push to `main` → Gitea → Concourse `ignite` pipeline triggers.
2. `test-backend` / `test-frontend` run pytest / vitest.
3. `build-backend` / `build-frontend` kaniko-build both images to
   `harbor.cluster.brindledev.com/ignite/{backend,frontend}:<short-sha>`.
4. `publish-chart` packages the chart as `ignite-<major>.<minor>.<revcount>`
   and pushes to `oci://harbor.cluster.brindledev.com/ignite/ignite`.
5. home-kubernetes `deploy-ignite` job watches that OCI tag and runs
   `helm upgrade` against the `ignite` namespace.

## Images

- `harbor.cluster.brindledev.com/ignite/backend` — FastAPI (`python:3.12-slim`).
- `harbor.cluster.brindledev.com/ignite/frontend` — Vite build served by nginx.

Both private; `harbor-pull` secret required in the namespace (see
`secrets/`).

## Local build sanity

```sh
docker build -t ignite-backend:dev  backend  -f backend/deployment/Dockerfile
docker build -t ignite-frontend:dev frontend -f frontend/deployment/Dockerfile
helm template ignite deployment/chart | kubectl apply --dry-run=client -f -
```

> The frontend image build (`npm ci`) requires `frontend/package-lock.json`.
> Run `npm install` in `frontend/` once to generate it before the first CI run.

## Set the pipeline (break-glass)

```sh
fly -t brindle set-pipeline -p ignite -c deployment/ci/pipeline.yml
```

Normally the `set-pipeline` job self-updates on any `deployment/ci/**` change.
