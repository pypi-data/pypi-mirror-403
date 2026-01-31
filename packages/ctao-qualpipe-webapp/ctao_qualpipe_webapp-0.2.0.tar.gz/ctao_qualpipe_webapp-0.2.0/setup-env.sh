#!/bin/sh

# Setup variable if not existing yet (POSIX-compliant):
KIND_CLUSTER_NAME=${KIND_CLUSTER_NAME:-dpps-local-qualpipe-webapp}
NAMESPACE=${NAMESPACE:-default}
BACKEND_REPO=${BACKEND_REPO:-harbor.cta-observatory.org/dpps/qualpipe-webapp-backend}
FRONTEND_REPO=${FRONTEND_REPO:-harbor.cta-observatory.org/dpps/qualpipe-webapp-frontend}

# Generate git-based tags
GIT_VERSION=$(git describe --tags --always 2>/dev/null || echo "dev")
GIT_TAG_LATEST=$(git describe --tags --abbrev=0 2>/dev/null || echo "latest")

TAG=${TAG:-$GIT_VERSION}
TAG_LATEST=${TAG_LATEST:-$GIT_TAG_LATEST}

export KUBECONFIG=~/.kube/config
export KIND_CLUSTER_NAME
export NAMESPACE
export BACKEND_REPO
export FRONTEND_REPO
export TAG
export TAG_LATEST

# Image full names (for kind load)
BACKEND_IMAGE=${BACKEND_IMAGE:-$BACKEND_REPO:$TAG}
FRONTEND_IMAGE=${FRONTEND_IMAGE:-$FRONTEND_REPO:$TAG}

BACKEND_DEV_IMAGE=${BACKEND_DEV_IMAGE:-$BACKEND_REPO:$TAG}
FRONTEND_DEV_IMAGE=${FRONTEND_DEV_IMAGE:-$FRONTEND_REPO:$TAG}

export BACKEND_IMAGE
export FRONTEND_IMAGE
export BACKEND_DEV_IMAGE
export FRONTEND_DEV_IMAGE
