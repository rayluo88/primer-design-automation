# AWS Elastic Beanstalk Deployment Guide
## Primer Design Automation Pipeline

**✅ VERIFIED WORKING** - Successfully deployed on 2026-01-03

This guide provides step-by-step instructions for deploying the Primer Design Automation Pipeline to AWS Elastic Beanstalk using Docker containers.

---

## Why Elastic Beanstalk?

**Advantages over App Runner:**
- ✅ **Compatible with Streamlit** - Handles long container startup times
- ✅ **Free tier eligible** - t2.micro instance (750 hours/month for 12 months)
- ✅ **More control** - Full access to EC2 instances, logs, and configuration
- ✅ **Proven reliability** - Mature service with extensive documentation

**Working deployment:**
- **Live URL:** http://primer-design-env.eba-ak2qz6v5.ap-southeast-1.elasticbeanstalk.com
- **Instance:** t2.micro (1 vCPU, 1 GB RAM)
- **Cost:** FREE (if within 12-month free tier)

---

## Prerequisites

1. **AWS Account** with free tier eligibility (optional but recommended)
2. **AWS CLI** installed and configured (`aws configure`)
3. **EB CLI** installed (`pip install awsebcli`)
4. **Docker image** pushed to Amazon ECR (see [deploy-to-aws.sh](deploy-to-aws.sh))

---

## Quick Start (3 Commands)

```bash
# 1. Push Docker image to ECR (if not already done)
./deploy-to-aws.sh

# 2. Initialize Elastic Beanstalk
eb init -p docker -r ap-southeast-1 primer-design

# 3. Create environment and deploy
eb create primer-design-env --instance-type t2.micro
```

**That's it!** Your app will be live in ~10 minutes.

---

## Detailed Step-by-Step Guide

### Step 1: Install EB CLI

```bash
# Install EB CLI
pip install awsebcli

# Verify installation
eb --version
# Expected: EB CLI 3.x.x (Python 3.x.x)
```

### Step 2: Ensure Docker Image is in ECR

```bash
# If you haven't pushed to ECR yet:
cd /Users/raymondluo/Documents/jobs/tf-senior-ds/projects/primer-design-automation
./deploy-to-aws.sh

# Verify image exists
aws ecr describe-images \
    --repository-name primer-design \
    --region ap-southeast-1
```

**Expected output:**
```json
{
    "imageDetails": [
        {
            "imageDigest": "sha256:...",
            "imageTags": ["latest"],
            "imageSizeInBytes": 1330000000
        }
    ]
}
```

### Step 3: Initialize Elastic Beanstalk Application

```bash
# Navigate to project directory
cd /Users/raymondluo/Documents/jobs/tf-senior-ds/projects/primer-design-automation

# Initialize EB (creates .elasticbeanstalk/ directory)
eb init -p docker -r ap-southeast-1 primer-design
```

**What this does:**
- Creates EB application named "primer-design"
- Sets platform to Docker
- Configures Singapore region (ap-southeast-1)
- Uses your AWS credentials from `aws configure`

**Expected output:**
```
Application primer-design has been created.
```

**Files created:**
- `.elasticbeanstalk/config.yml` - EB configuration
- Uses existing `Dockerrun.aws.json` for container config

### Step 4: Create EB Environment and Deploy

```bash
# Create environment with t2.micro (FREE tier)
eb create primer-design-env \
    --instance-type t2.micro \
    --region ap-southeast-1 \
    --elb-type application

# Alternative (let EB choose defaults):
# eb create primer-design-env --instance-type t2.micro
```

**What happens:**
1. **Creating application version** (~30 seconds)
   - Packages Dockerrun.aws.json
   - Uploads to S3
2. **Launching EC2 instance** (~2 minutes)
   - Provisions t2.micro instance
   - Configures security groups
3. **Setting up load balancer** (~3 minutes)
   - Creates Application Load Balancer
   - Configures target groups
4. **Deploying Docker container** (~3 minutes)
   - Pulls image from ECR
   - Starts container
   - Maps port 8080
5. **Running health checks** (~2 minutes)
   - Waits for container to be healthy
   - Verifies app is responding

**Total time:** ~8-10 minutes

**Expected final output:**
```
2026-01-03 13:05:35    INFO    Instance deployment completed successfully.
2026-01-03 13:05:49    INFO    Application available at primer-design-env.eba-ak2qz6v5.ap-southeast-1.elasticbeanstalk.com.
2026-01-03 13:05:50    INFO    Successfully launched environment: primer-design-env
```

### Step 5: Access Your Application

```bash
# Open in browser
eb open

# Or get the URL
eb status
```

**Your app is now live at:**
```
http://primer-design-env.<random-id>.ap-southeast-1.elasticbeanstalk.com
```

---

## Instance Type Options

| Instance Type | vCPU | RAM | Cost/Month | Recommendation |
|--------------|------|-----|------------|----------------|
| **t2.micro** ⭐ | 1 | 1 GB | **FREE** (750h/month) | ✅ Best for demo |
| t3.micro | 2 | 1 GB | ~$7.50 | Good alternative |
| t3.small | 2 | 2 GB | ~$15 | Production-ready |
| t3.medium | 2 | 4 GB | ~$30 | High traffic |

**Recommendation for interview demo:** **t2.micro** (free tier)

---

## Configuration Files

### Dockerrun.aws.json

This file tells Elastic Beanstalk how to run your Docker container:

```json
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "377133361984.dkr.ecr.ap-southeast-1.amazonaws.com/primer-design:latest",
    "Update": "true"
  },
  "Ports": [
    {
      "ContainerPort": 8080,
      "HostPort": 8080
    }
  ],
  "Logging": "/var/log/nginx"
}
```

**Key fields:**
- `Image.Name`: Your ECR image URI
- `ContainerPort`: Port app listens on (8080 for Streamlit)
- `HostPort`: Port exposed to load balancer
- `Update`: Auto-pull latest image on deployment

---

## Managing Your Deployment

### View Environment Status

```bash
# Check environment health
eb health

# View detailed status
eb status

# Monitor in real-time
eb health --refresh
```

### View Logs

```bash
# Download all logs
eb logs

# Stream logs in real-time
eb logs --stream

# View specific log file
eb ssh
# Then: tail -f /var/log/eb-engine.log
```

### Update Application

```bash
# After pushing new image to ECR:
eb deploy

# Force rebuild
eb deploy --staged
```

### SSH into Instance

```bash
# Connect to EC2 instance
eb ssh

# Once connected, check Docker container
sudo docker ps
sudo docker logs <container_id>
```

---

## Scaling and Auto-Scaling

### Manual Scaling

```bash
# Scale to 2 instances
eb scale 2

# Scale back to 1
eb scale 1
```

### Auto-Scaling Configuration

Edit `.elasticbeanstalk/config.yml`:

```yaml
deploy:
  artifact: Dockerrun.aws.json

autoscaling:
  MinSize: 1
  MaxSize: 4
  Cooldown: 360
  Triggers:
    CPUUtilization:
      UpperThreshold: 80
      LowerThreshold: 20
```

Apply changes:
```bash
eb config save
eb deploy
```

---

## Cost Management

### Current Deployment Cost (t2.micro)

**Free tier eligible (first 12 months):**
- EC2 t2.micro: **FREE** (750 hours/month)
- Elastic Load Balancer: **FREE** (750 hours/month + 15 GB data)
- S3 storage: **FREE** (5 GB)

**After free tier expires:**
- EC2 t2.micro: ~$7.50/month
- Application Load Balancer: ~$16/month
- **Total: ~$23/month**

### Cost Optimization Tips

1. **Use t2.micro during demo period**
   ```bash
   eb create primer-design-env --instance-type t2.micro
   ```

2. **Delete environment after interview**
   ```bash
   eb terminate primer-design-env
   ```

3. **Use single instance (no auto-scaling) for demo**
   ```bash
   eb scale 1
   ```

4. **Monitor costs**
   - Set up billing alerts in AWS Console
   - Use AWS Cost Explorer

---

## Troubleshooting

### Issue: Environment creation fails

**Solution:**
```bash
# Check logs
eb logs

# View events
eb events

# Common issue: Insufficient permissions
# Ensure IAM user has ElasticBeanstalkFullAccess policy
```

### Issue: Health check failing

**Solution:**
```bash
# Check if container is running
eb ssh
sudo docker ps

# View container logs
sudo docker logs <container_id>

# Verify port 8080 is listening
curl http://localhost:8080/_stcore/health
```

### Issue: Cannot pull from ECR

**Error:** `Error pulling image: authorization token has expired`

**Solution:**
```bash
# Create/update IAM instance profile with ECR permissions
# EB should auto-create this, but verify in IAM console:
# Role: aws-elasticbeanstalk-ec2-role
# Policy: AmazonEC2ContainerRegistryReadOnly
```

### Issue: Deployment takes too long

**Solution:**
```bash
# Increase deployment timeout
eb config
# Edit: aws:elasticbeanstalk:command
# Set: Timeout: 600
```

---

## Cleanup After Interview

### Terminate Environment (Stop Charges)

```bash
# This deletes:
# - EC2 instances
# - Load balancer
# - Security groups
# - Auto-scaling groups

eb terminate primer-design-env
```

**Confirmation required:** Type environment name to confirm

### Delete Application (Optional)

```bash
# This also deletes all environments
eb terminate --all

# Or use AWS Console:
# Elastic Beanstalk → Applications → primer-design → Delete
```

### Delete ECR Image (Optional)

```bash
# Delete ECR repository and all images
aws ecr delete-repository \
    --repository-name primer-design \
    --force \
    --region ap-southeast-1
```

**Total cleanup time:** ~5 minutes

---

## Interview Talking Points

### Technical Architecture

**"I deployed the primer design application to AWS using Elastic Beanstalk with a Docker container:"**

1. **Containerization:**
   - "Packaged as Docker container following production best practices"
   - "Non-root user, health checks, optimized layers"
   - "1.33GB final image size"

2. **AWS Service Selection:**
   - "Initially attempted App Runner but discovered Streamlit incompatibility"
   - "Pivoted to Elastic Beanstalk which better supports Docker containers"
   - "Shows real-world debugging and AWS service trade-off analysis"

3. **Cost Optimization:**
   - "Deployed on t2.micro free tier for cost efficiency"
   - "Can easily scale to t3.medium or larger for production"
   - "Auto-scaling configured for variable workloads"

4. **Production Readiness:**
   - "Application Load Balancer for high availability"
   - "CloudWatch logging for monitoring"
   - "Can add RDS database, ElastiCache, or CloudFront CDN as needed"

5. **CI/CD Ready:**
   - "Deployment automated with EB CLI"
   - "Can integrate with CodePipeline for continuous deployment"
   - "Single command updates: `eb deploy`"

### Deployment Journey

**"The deployment process demonstrated real-world problem-solving:"**

1. **Initial Attempt:** App Runner (failed due to Streamlit incompatibility)
2. **Debugging:** Analyzed CloudWatch logs, tested health checks
3. **Root Cause:** App Runner's runtime restrictions prevent Streamlit startup
4. **Solution:** Elastic Beanstalk (Docker-friendly, more flexible)
5. **Result:** Successful deployment in 10 minutes

**"This mirrors production scenarios where initial approaches need adjustment based on real constraints."**

---

## Additional Resources

- [AWS Elastic Beanstalk Documentation](https://docs.aws.amazon.com/elasticbeanstalk/)
- [EB CLI Documentation](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html)
- [Docker Platform Documentation](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/docker.html)
- [Pricing Calculator](https://calculator.aws/)

---

## Quick Reference Commands

```bash
# Deploy workflow
./deploy-to-aws.sh              # Push to ECR
eb init -p docker primer-design # Initialize
eb create primer-design-env     # Deploy

# Management
eb open                         # Open in browser
eb status                       # Check status
eb health                       # View health
eb logs                         # Download logs

# Updates
eb deploy                       # Deploy changes
eb scale 2                      # Scale instances

# Cleanup
eb terminate primer-design-env  # Delete everything
```

---

## Summary

**Deployment Status:** ✅ **WORKING**

**Live URL:** http://primer-design-env.eba-ak2qz6v5.ap-southeast-1.elasticbeanstalk.com

**Configuration:**
- Platform: Docker on Amazon Linux 2023
- Instance: t2.micro (FREE tier)
- Region: ap-southeast-1 (Singapore)
- Auto-scaling: 1-4 instances
- Load Balancer: Application Load Balancer

**Cost:** $0/month (free tier) or ~$23/month (after free tier)

**Deployment Time:** ~10 minutes

**Interview Ready:** ✅ YES
