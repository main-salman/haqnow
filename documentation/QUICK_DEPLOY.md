# 🚀 Quick Deploy Guide

## ⚡ 5-Minute Setup

### Step 1: Get Exoscale API Credentials
1. **Go to**: [Exoscale Console](https://portal.exoscale.com) → **IAM** → **API Keys**
2. **Click**: "Create API Key"
3. **Name**: `foi-archive-terraform`
4. **Permissions** (select these):
   - ✅ **Compute** (for instances, security groups)
   - ✅ **Database** (for MySQL database)
   - ✅ **Network** (for elastic IPs)
   - ✅ **Storage** (for S3 access)
5. **Click**: "Create"
6. **Copy**: Both the API Key and Secret Key (save them!)

### Step 2: Configure Terraform
```bash
# Copy the template file
cp terraform/terraform.tfvars.template terraform/terraform.tfvars

# Edit the file and add your API credentials
nano terraform/terraform.tfvars
```

**Just fill in these 5 values:**
```hcl
exoscale_api_key    = "EXO..."  # 👈 Your API key from step 1
exoscale_secret_key = "..."     # 👈 Your secret key from step 1
admin_password      = "SecurePass123!"  # 👈 Choose admin password
jwt_secret_key      = "super-secret-jwt-key-here"  # 👈 Random string
mysql_password      = "SecureDB123!"  # 👈 Choose DB password
```

### Step 3: Deploy to Exoscale
```bash
# Run the deployment script
./scripts/deploy.sh

# Select option 2: "Deploy infrastructure and application"
```

### Step 4: Test Locally (Optional)
```bash
# First update your .env with the MySQL host from deployment
./scripts/run-local.sh
```

## 🎯 What Gets Created

- **Compute Instance** (standard.medium - 2 vCPU, 4GB RAM)
- **MySQL Database** (managed by Exoscale)
- **Elastic IP** (public IP for your app)
- **Security Groups** (firewall rules)
- **S3 Storage** (uses your existing bucket)

## 📱 Access Your App

After deployment, you'll get:
- **Frontend**: `http://YOUR-IP/`
- **Backend API**: `http://YOUR-IP/api/`
- **Admin Login**: Use your admin_email and admin_password

## 🔧 Update App Code

```bash
# Make your code changes, then:
./scripts/deploy.sh

# Select option 3: "Update application code only"
```

## 💡 All Variables Pre-configured

Everything is already set up from your `.env` file:
- ✅ S3 credentials from your .env
- ✅ Admin email: salman.naqvi@gmail.com
- ✅ SendGrid API key from your .env
- ✅ Region: ch-dk-2 (matches your S3)

**You only need to add 5 values to get started!** 🎉 