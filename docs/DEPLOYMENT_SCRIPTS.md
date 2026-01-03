# AWS Deployment Scripts

Automated scripts for deploying the Primer Design Automation app to AWS.

**✅ RECOMMENDED:** Use AWS Elastic Beanstalk for deploying this application. See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for the complete deployment guide.

---

## Quick Start (Working Method - Elastic Beanstalk)

```bash
# 1. Deploy to ECR (build & push Docker image)
./deploy-to-aws.sh

# 2. Deploy to Elastic Beanstalk
eb init -p docker -r ap-southeast-1 primer-design
eb create primer-design-env --instance-type t2.micro

# 3. When done, cleanup resources to avoid costs
eb terminate primer-design-env
```

---

## Alternative (App Runner - NOT WORKING)

```bash
# ❌ This approach DOES NOT WORK due to Streamlit incompatibility
# Kept for reference only

# Method A: AWS Console
# Follow the on-screen instructions after deploy-to-aws.sh completes

# Method B: AWS CLI (Automated)
./create-apprunner-service.sh
```

## Scripts Overview

### `deploy-to-aws.sh`
**Purpose:** Builds Docker image and pushes to Amazon ECR

**What it does:**
1. Sets up AWS environment variables
2. Creates ECR repository (if doesn't exist)
3. Authenticates Docker to ECR
4. Builds Docker image locally
5. Tags and pushes image to ECR

**Runtime:** ~3-5 minutes (depending on image caching)

**Requirements:**
- AWS CLI configured (`aws configure`)
- Docker running locally
- Internet connection

**Cost:** $0 (ECR storage is free for first 500 MB)

---

### `create-apprunner-service.sh`
**Purpose:** Creates and configures AWS App Runner service

**What it does:**
1. Creates IAM role for App Runner ECR access (if needed)
2. Creates App Runner service with proper configuration:
   - 1 vCPU, 2 GB RAM
   - Port 8080
   - Health check at `/_stcore/health`
   - Manual deployment (not automatic)
3. Waits for service to be running (~5 minutes)
4. Returns the public HTTPS URL

**Runtime:** ~5-7 minutes

**Requirements:**
- `deploy-to-aws.sh` must be run first
- AWS CLI configured
- IAM permissions to create roles and App Runner services

**Cost:** ~$0-5/month for demo usage (pay-per-use)

---

### `cleanup-aws.sh`
**Purpose:** Deletes all AWS resources to avoid ongoing costs

**What it does:**
1. Deletes App Runner service
2. Deletes ECR repository and all images

**Runtime:** ~1-2 minutes

**Use when:**
- After interview/demo is complete
- Want to avoid any ongoing charges
- Need to redeploy from scratch

**Safety:** Prompts for confirmation before deletion

---

## Deployment Workflow

### For Interview Demo

```bash
# 1-2 days before interview
./deploy-to-aws.sh
./create-apprunner-service.sh

# During interview, show the live URL
# After interview
./cleanup-aws.sh  # To avoid costs
```

### For Testing/Development

```bash
# Deploy
./deploy-to-aws.sh

# Test locally first (optional)
docker run -p 8080:8080 primer-design:latest

# Then create App Runner service
./create-apprunner-service.sh

# Make changes, redeploy
./deploy-to-aws.sh  # Rebuilds and pushes
# Manually trigger App Runner deployment in AWS Console
```

---

## Cost Breakdown

| Resource | Cost | Notes |
|----------|------|-------|
| ECR Storage | Free (< 500 MB) | First 500 MB free |
| ECR Data Transfer | $0.09/GB | Only when pulling images |
| App Runner Compute | $0.064/vCPU-hour | Only when running |
| App Runner Memory | $0.007/GB-hour | Only when running |

**Typical demo cost:** $0-5 for entire interview period

**Cost optimization:**
- Run `cleanup-aws.sh` after demo
- Use manual deployment (not automatic)
- App Runner scales to zero when idle (minimal cost)

---

## Troubleshooting

### Error: "repository already exists"
**Solution:** This is normal, script handles it automatically

### Error: "Access denied to ECR"
**Solution:**
```bash
# Re-authenticate
aws ecr get-login-password --region ap-southeast-1 | \
    docker login --username AWS --password-stdin \
    <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com
```

### Error: "IAM role propagation"
**Solution:** Wait 30 seconds and retry `create-apprunner-service.sh`

### Health check failing
**Solution:**
```bash
# Test locally first
docker run -p 8080:8080 primer-design:latest
curl http://localhost:8080/_stcore/health

# Should return 200 OK
```

### Can't access app URL
**Solution:**
- Wait 5 minutes after deployment (App Runner needs time)
- Check service status in AWS Console
- View logs in CloudWatch

---

## Manual Deployment (Alternative)

If scripts fail, follow `AWS_DEPLOYMENT.md` for manual step-by-step instructions.

---

## Environment Variables

Scripts use these variables (automatically set):

```bash
AWS_REGION=ap-southeast-1        # Singapore
ECR_REPO_NAME=primer-design
AWS_ACCOUNT_ID=<auto-detected>
SERVICE_NAME=primer-design
```

To customize, edit the scripts before running.

---

## Security Notes

- Scripts run with your AWS credentials (from `aws configure`)
- IAM role created has minimal ECR read permissions only
- App Runner service runs as non-root user (from Dockerfile)
- All images are encrypted at rest in ECR
- HTTPS enabled by default on App Runner

---

## Interview Talking Points

When demonstrating deployment:

1. **"I automated the entire deployment with shell scripts"**
   - Shows DevOps/automation skills

2. **"The app runs in AWS App Runner for automatic scaling"**
   - Demonstrates cloud-native architecture knowledge

3. **"I use ECR for container registry with image scanning enabled"**
   - Shows security awareness

4. **"Total cost for this demo is under $5/month with pay-per-use pricing"**
   - Demonstrates cost consciousness

5. **"The cleanup script ensures no surprise charges after the demo"**
   - Shows production/operational awareness

---

## Related Documentation

- **AWS_DEPLOYMENT.md** - Detailed manual deployment guide
- **Dockerfile** - Container configuration
- **buildspec.yml** - CI/CD configuration for AWS CodeBuild
- **DEV_PROGRESS.md** - Development progress tracking
