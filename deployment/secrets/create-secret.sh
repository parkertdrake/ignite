#!/usr/bin/env bash
# Bootstrap the harbor-pull image-pull secret for ignite. Run once per
# cluster (or after rotating the Harbor robot creds). The ignite images
# are private on Harbor, so the namespace needs a dockerconfigjson secret
# to pull them.
#
# Usage:
#   HARBOR_PULL_USERNAME=robot$ignite+pull \
#   HARBOR_PULL_PASSWORD=... \
#   ./create-secret.sh
set -euo pipefail

NAMESPACE="${NAMESPACE:-ignite}"
HARBOR_REGISTRY="${HARBOR_REGISTRY:-harbor.cluster.brindledev.com}"
: "${HARBOR_PULL_USERNAME:?set HARBOR_PULL_USERNAME}"
: "${HARBOR_PULL_PASSWORD:?set HARBOR_PULL_PASSWORD}"

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "$NAMESPACE" create secret docker-registry harbor-pull \
    --docker-server="$HARBOR_REGISTRY" \
    --docker-username="$HARBOR_PULL_USERNAME" \
    --docker-password="$HARBOR_PULL_PASSWORD" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "harbor-pull secret applied to namespace '$NAMESPACE'."
