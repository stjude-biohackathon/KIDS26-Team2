#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==========================================
# CONFIGURATION VARIABLES
# ==========================================
ACR_SERVER="biohackacr20147.azurecr.io"
RESOURCE_GROUP="biohackathon-clinical-rag"
BACKEND_APP="clinical-backend"
FRONTEND_APP="clinical-data-assistant"

# Generate a unique tag using the current date and time (e.g., v-20260918-094000)
TAG="v-$(date +%Y%m%d-%H%M%S)"

# --- IMPORTANT: UPDATE THESE BEFORE RUNNING ---
LANGSMITH_API_KEY="lsv2_pt_PASTE_YOUR_PERSONAL_TOKEN_HERE"
BACKEND_URL="https://clinical-backend.victoriousbush-7b0515a9.westus2.azurecontainerapps.io"
# ==========================================

echo "🚀 Starting Full System Deployment: Tag $TAG"

# ==========================================
# 1. DEPLOY BACKEND
# ==========================================
echo "⚙️ Building Backend Image..."
docker build --platform linux/amd64 -t $ACR_SERVER/$BACKEND_APP:$TAG .

echo "☁️ Pushing Backend to Azure Container Registry..."
docker push $ACR_SERVER/$BACKEND_APP:$TAG

echo "🔄 Updating Backend Azure Container App..."
az containerapp update \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_SERVER/$BACKEND_APP:$TAG \
  --set-env-vars "LANGSMITH_TRACING=true" "LANGSMITH_API_KEY=$LANGSMITH_API_KEY" "LANGSMITH_PROJECT=MIMIC-IV-Clinical-Agent"

cd ..
echo "✅ Backend Deployment Complete!"

# ==========================================
# 2. DEPLOY FRONTEND
# ==========================================
echo "🎨 Building Frontend Image..."
cd frontend
docker build --platform linux/amd64 -t $ACR_SERVER/$FRONTEND_APP:$TAG .

echo "☁️ Pushing Frontend to Azure Container Registry..."
docker push $ACR_SERVER/$FRONTEND_APP:$TAG

echo "🔄 Updating Frontend Azure Container App..."
az containerapp update \
  --name $FRONTEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_SERVER/$FRONTEND_APP:$TAG \
  --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL"

cd ..
echo "✅ Frontend Deployment Complete!"

echo "🎉 FULL SYSTEM DEPLOYMENT SUCCESSFUL!"