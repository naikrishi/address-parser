#!/usr/bin/env bash
# Day 23 — Deploy address-parser backend to Azure
# Run this in Azure Cloud Shell: https://shell.azure.com  (Bash mode)
#
# Usage:
#   1. Open https://shell.azure.com and choose Bash
#   2. Clone or upload this repo, then run:
#      chmod +x deploy-azure.sh && ./deploy-azure.sh
#
# What it creates (all in one resource group):
#   • Azure Container Registry (Basic)
#   • Azure Database for PostgreSQL Flexible Server 16 + pgvector
#   • Azure Container Apps environment + web app
#
# After it finishes it prints:
#   • The public API URL  (verify /health)
#   • The GitHub Actions secrets you need to enable CD
# ---------------------------------------------------------------------------

set -euo pipefail

# ── Configuration — edit these if you want different names ──────────────────
RG="address-parser-rg"
LOCATION="centralus"
ACR_NAME="addressparseracr"        # globally unique; if taken, add a suffix e.g. addressparseracr42
PG_SERVER="address-parser-db"      # globally unique subdomain
PG_ADMIN_USER="appadmin"
DB_NAME="address_parser"
ACA_ENV="address-parser-env"
ACA_APP="address-parser-backend"
# ---------------------------------------------------------------------------

echo "=== Generating secrets ==="
# These are stored only in Azure; print them at the end for safekeeping.
DB_PASS="$(openssl rand -base64 18 | tr -d '+/=' | head -c 20)Aa1!"
JWT_SECRET="$(openssl rand -base64 40 | tr -d '\n')"
ADMIN_PASS="$(openssl rand -base64 14 | tr -d '+/=' | head -c 16)Aa1!"

echo "=== Creating resource group (skipped if it already exists) ==="
az group create --name "$RG" --location "$LOCATION" --output none 2>/dev/null || \
  echo "  Resource group '$RG' already exists — continuing."

echo "=== Creating Container Registry ==="
az acr create \
  --name "$ACR_NAME" \
  --resource-group "$RG" \
  --sku Basic \
  --admin-enabled true \
  --output none

ACR_SERVER="$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)"
ACR_USER="$(az acr credential show --name "$ACR_NAME" --query username -o tsv)"
ACR_PASS="$(az acr credential show --name "$ACR_NAME" --query 'passwords[0].value' -o tsv)"

echo "=== Building and pushing backend image to ACR ==="
# Cloud Shell builds inside Azure — no corporate proxy or local Docker needed.
az acr build \
  --registry "$ACR_NAME" \
  --image "address-parser-backend:latest" \
  ./backend

echo "=== Creating PostgreSQL Flexible Server (this takes ~5 min) ==="
az postgres flexible-server create \
  --name "$PG_SERVER" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --admin-user "$PG_ADMIN_USER" \
  --admin-password "$DB_PASS" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 16 \
  --storage-size 32 \
  --public-access 0.0.0.0 \
  --output none

echo "=== Allowing pgvector extension ==="
az postgres flexible-server parameter set \
  --resource-group "$RG" \
  --server-name "$PG_SERVER" \
  --name azure.extensions \
  --value vector \
  --output none

echo "=== Creating app database ==="
az postgres flexible-server db create \
  --database-name "$DB_NAME" \
  --resource-group "$RG" \
  --server-name "$PG_SERVER" \
  --output none

echo "=== Creating Container Apps environment ==="
az containerapp env create \
  --name "$ACA_ENV" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --output none

DATABASE_URL="postgresql+psycopg://${PG_ADMIN_USER}:${DB_PASS}@${PG_SERVER}.postgres.database.azure.com/${DB_NAME}?sslmode=require"

echo "=== Deploying Container App ==="
# APP_ENV=development so /docs is accessible for the initial smoke test.
# After verifying, run:  az containerapp update -n $ACA_APP -g $RG --set-env-vars APP_ENV=production
az containerapp create \
  --name "$ACA_APP" \
  --resource-group "$RG" \
  --environment "$ACA_ENV" \
  --image "${ACR_SERVER}/address-parser-backend:latest" \
  --registry-server "$ACR_SERVER" \
  --registry-username "$ACR_USER" \
  --registry-password "$ACR_PASS" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --env-vars \
    APP_ENV=development \
    DATABASE_URL="$DATABASE_URL" \
    JWT_SECRET_KEY="$JWT_SECRET" \
    JWT_ALGORITHM=HS256 \
    ACCESS_TOKEN_EXPIRE_MINUTES=15 \
    REFRESH_TOKEN_EXPIRE_DAYS=7 \
    AUTH_BCRYPT_ROUNDS=12 \
    AUTH_RATE_LIMIT_PER_MINUTE=10 \
    AUTH_RATE_LIMIT_WINDOW_SECONDS=60 \
    CORS_ALLOW_METHODS=GET,POST,OPTIONS \
    CORS_ALLOW_HEADERS=Authorization,Content-Type,Accept \
    EMBEDDINGS_PROVIDER=local \
    EMBEDDINGS_MODEL=all-MiniLM-L6-v2 \
    EMBEDDINGS_DIMENSION=384 \
    EMBEDDINGS_FALLBACK_ENABLED=true \
    SEED_ADMIN_EMAIL=admin@example.com \
    SEED_ADMIN_PASSWORD="$ADMIN_PASS" \
  --output none

FQDN="$(az containerapp show \
  --name "$ACA_APP" \
  --resource-group "$RG" \
  --query properties.configuration.ingress.fqdn -o tsv)"

echo ""
echo "============================================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================================"
echo "  API URL:    https://${FQDN}"
echo "  Health:     https://${FQDN}/health"
echo "  Docs:       https://${FQDN}/docs   (visible while APP_ENV=development)"
echo ""
echo "  Admin login:"
echo "    Email:    admin@example.com"
echo "    Password: ${ADMIN_PASS}"
echo ""
echo "--- GitHub Actions secrets (add in repo Settings → Secrets) ---"
echo "  AZURE_RESOURCE_GROUP=${RG}"
echo "  ACR_NAME=${ACR_NAME}"
echo "  ACR_LOGIN_SERVER=${ACR_SERVER}"
echo "  AZURE_CONTAINER_APP_NAME=${ACA_APP}"
echo ""
echo "  AZURE_CREDENTIALS → run this in Cloud Shell to generate:"
echo "    SUBID=\$(az account show --query id -o tsv)"
echo "    az ad sp create-for-rbac --name address-parser-ci \\"
echo "      --role contributor \\"
echo "      --scopes /subscriptions/\$SUBID/resourceGroups/${RG} \\"
echo "      --sdk-auth"
echo ""
echo "  After CI is wired up, gate the docs:"
echo "    az containerapp update -n ${ACA_APP} -g ${RG} \\"
echo "      --set-env-vars APP_ENV=production"
echo "============================================================"
