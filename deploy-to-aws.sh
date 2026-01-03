#!/bin/bash
# AWS Deployment Script for Primer Design Automation Pipeline
# This script deploys the containerized app to AWS App Runner via Amazon ECR Elastic Container Registry

set -e  # Exit on error

echo "=========================================="
echo "Primer Design - AWS Deployment Script"
echo "=========================================="
echo ""

# Configuration
export AWS_REGION=ap-southeast-1
export ECR_REPO_NAME=primer-design
export APP_NAME=primer-design

# Get AWS account ID
echo "Fetching AWS account ID..."
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Configuration:"
echo "  Region: $AWS_REGION"
echo "  Repository: $ECR_REPO_NAME"
echo "  Account ID: $AWS_ACCOUNT_ID"
echo ""

# Step 1: Verify ECR repository exists (skipping creation - repo already exists)
echo "Step 1: Verifying ECR repository..."
aws ecr describe-repositories \
    --repository-names $ECR_REPO_NAME \
    --region $AWS_REGION > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ ECR repository found: $ECR_REPO_NAME"
else
    echo "✗ ERROR: ECR repository '$ECR_REPO_NAME' not found"
    echo "  Please create it manually in AWS Console or run create-repository command"
    exit 1
fi
echo ""

# Step 2: Authenticate Docker to ECR
echo "Step 2: Authenticating Docker to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "✓ Docker authenticated"
echo ""

# Step 3: Build Docker image
echo "Step 3: Building Docker image..."
docker build -t $ECR_REPO_NAME:latest .

echo "✓ Docker image built"
echo ""

# Step 4: Tag image for ECR
echo "Step 4: Tagging image for ECR..."
docker tag $ECR_REPO_NAME:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

echo "✓ Image tagged"
echo ""

# Step 5: Push image to ECR
echo "Step 5: Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

echo "✓ Image pushed to ECR"
echo ""

# Step 6: Display next steps
echo "=========================================="
echo "✓ Deployment to ECR Complete!"
echo "=========================================="
echo ""
echo "Image URI:"
echo "  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest"
echo ""
echo "Next Steps:"
echo "1. Create App Runner service (choose one method):"
echo ""
echo "   Method A - AWS Console (Recommended):"
echo "   - Go to: https://console.aws.amazon.com/apprunner"
echo "   - Click 'Create service'"
echo "   - Select ECR image above"
echo "   - Configure: Port 8080, 1 vCPU, 2 GB RAM"
echo "   - Health check: /_stcore/health"
echo ""
echo "   Method B - AWS CLI:"
echo "   - Run: ./create-apprunner-service.sh"
echo ""
echo "For detailed instructions, see: AWS_DEPLOYMENT.md"
echo ""
