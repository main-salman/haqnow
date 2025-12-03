terraform {
  required_providers {
    exoscale = {
      source  = "exoscale/exoscale"
      version = "~> 0.64"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

# Configure the Exoscale Provider
provider "exoscale" {
  key    = var.exoscale_api_key
  secret = var.exoscale_secret_key
}

# AWS Provider configured for Exoscale SOS (S3-compatible) - Primary Region (Zurich)
# Using main Exoscale API credentials (work across all regions)
provider "aws" {
  alias                       = "exoscale_primary"
  region                      = "us-east-1"  # Required but not used by Exoscale
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  skip_requesting_account_id  = true
  
  access_key = var.exoscale_api_key
  secret_key = var.exoscale_secret_key
  
  endpoints {
    s3 = "https://sos-${var.zone}.exo.io"
  }
}

# AWS Provider configured for Exoscale SOS (S3-compatible) - DR Region (Vienna)
# Using main Exoscale API credentials (work across all regions)
provider "aws" {
  alias                       = "exoscale_dr"
  region                      = "us-east-1"  # Required but not used by Exoscale
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  skip_requesting_account_id  = true
  
  access_key = var.exoscale_api_key
  secret_key = var.exoscale_secret_key
  
  endpoints {
    s3 = "https://sos-${var.dr_zone}.exo.io"
  }
}

# EXOscale Database as a Service (DBaaS) - MySQL
resource "exoscale_dbaas" "foi_mysql" {
  zone = var.zone
  name = "${var.project_name}-mysql-${var.environment}"
  type = "mysql"
  plan = var.mysql_plan
  
  mysql {
    admin_username   = var.mysql_user
    admin_password   = var.mysql_password
    # IP filter: Start with VM IP, will be updated after SKS nodes are created
    ip_filter        = [var.server_ip_cidr]
    backup_schedule  = "02:00"  # Daily backup at 2 AM UTC
  }
  
  lifecycle {
    ignore_changes = [mysql]  # Allow manual updates during migration
  }
}

# Data source to get database connection URI
data "exoscale_database_uri" "foi_mysql_uri" {
  name = exoscale_dbaas.foi_mysql.name
  zone = var.zone
  type = "mysql"
}

# EXOscale Database as a Service (DBaaS) - PostgreSQL for RAG/Vector Operations
resource "exoscale_dbaas" "foi_postgres_rag" {
  zone = var.zone
  name = "${var.project_name}-postgres-rag-${var.environment}"
  type = "pg"
  plan = var.postgres_plan
  
  pg {
    admin_username   = var.postgres_user
    admin_password   = var.postgres_password
    # IP filter: Start with VM IP, will be updated after SKS nodes are created
    ip_filter        = [var.server_ip_cidr]
    backup_schedule  = "03:00"  # Daily backup at 3 AM UTC
    version         = "15"      # PostgreSQL 15 supports pgvector
  }
  
  lifecycle {
    ignore_changes = [pg]  # Allow manual updates during migration
  }
}

# Data source to get PostgreSQL connection URI
data "exoscale_database_uri" "foi_postgres_rag_uri" {
  name = exoscale_dbaas.foi_postgres_rag.name
  zone = var.zone
  type = "pg"
}

# Security Group for web traffic
resource "exoscale_security_group" "foi_web" {
  name        = "${var.project_name}-web-${var.environment}-v3"
  description = "Security group for HaqNow.com web traffic"
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "exoscale_security_group_rule" "foi_web_http" {
  security_group_id = exoscale_security_group.foi_web.id
  type              = "INGRESS"
  protocol          = "TCP"
  start_port        = 80
  end_port          = 80
  cidr              = "0.0.0.0/0"
}

resource "exoscale_security_group_rule" "foi_web_https" {
  security_group_id = exoscale_security_group.foi_web.id
  type              = "INGRESS"
  protocol          = "TCP"
  start_port        = 443
  end_port          = 443
  cidr              = "0.0.0.0/0"
}

resource "exoscale_security_group_rule" "foi_web_ssh" {
  security_group_id = exoscale_security_group.foi_web.id
  type              = "INGRESS"
  protocol          = "TCP"
  start_port        = 22
  end_port          = 22
  cidr              = "0.0.0.0/0"
}

resource "exoscale_security_group_rule" "foi_web_api" {
  security_group_id = exoscale_security_group.foi_web.id
  type              = "INGRESS"
  protocol          = "TCP"
  start_port        = 8000
  end_port          = 8000
  cidr              = "0.0.0.0/0"
}

# SSH Key Pair
resource "exoscale_ssh_key" "foi_key" {
  name       = var.ssh_key_name
  public_key = file("~/.ssh/id_rsa.pub") # Adjust path as needed
}

# Compute Instance for the application (disabled after SKS migration)
resource "exoscale_compute_instance" "foi_app" {
  count              = var.vm_enabled ? 1 : 0
  zone               = var.zone
  name               = "${var.project_name}-app-${var.environment}"
  template_id        = "c71eb1d9-e537-4f92-9832-7089e6e45fae" # Ubuntu 24.04 LTS
  type               = var.instance_type
  disk_size          = var.disk_size
  ssh_keys           = [exoscale_ssh_key.foi_key.name]
  security_group_ids = [exoscale_security_group.foi_web.id]

  lifecycle {
    ignore_changes = [user_data]
  }

  user_data = base64encode(templatefile("${path.module}/cloud-init.yml", {
    project_name       = var.project_name
    environment        = var.environment
    s3_bucket          = var.s3_bucket_name
    s3_access_key      = var.s3_access_key
    s3_secret_key      = var.s3_secret_key
    s3_endpoint        = var.s3_endpoint
    s3_region          = var.s3_region
    admin_email        = var.admin_email
    admin_password     = var.admin_password
    jwt_secret         = var.jwt_secret_key
    sendgrid_api_key   = var.sendgrid_api_key
    mysql_host         = data.exoscale_database_uri.foi_mysql_uri.uri
    mysql_user         = var.mysql_user
    mysql_password     = var.mysql_password
    mysql_database     = var.mysql_database
    postgres_rag_uri   = data.exoscale_database_uri.foi_postgres_rag_uri.uri
    postgres_user      = var.postgres_user
    postgres_password  = var.postgres_password
    postgres_database  = var.postgres_database
    mysql_root_password = var.mysql_root_password
  }))
}

# Outputs
output "instance_ip" {
  description = "Public IP of the HaqNow.com instance (null if VM disabled)"
  value       = var.vm_enabled ? exoscale_compute_instance.foi_app[0].public_ip_address : null
}

output "instance_id" {
  description = "Instance ID (null if VM disabled)"
  value       = var.vm_enabled ? exoscale_compute_instance.foi_app[0].id : null
}

output "database_uri" {
  description = "Database connection URI"
  value       = data.exoscale_database_uri.foi_mysql_uri.uri
  sensitive   = true
}

output "database_host" {
  description = "Database host"
  value       = data.exoscale_database_uri.foi_mysql_uri.uri
  sensitive   = true
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = var.vm_enabled ? "ssh root@${exoscale_compute_instance.foi_app[0].public_ip_address}" : null
}

output "application_url" {
  description = "URL to access the HaqNow.com application"
  value       = var.vm_enabled ? "http://${exoscale_compute_instance.foi_app[0].public_ip_address}" : "http://www.haqnow.com (via SKS)"
}

output "postgres_rag_uri" {
  description = "PostgreSQL RAG database connection URI"
  value       = data.exoscale_database_uri.foi_postgres_rag_uri.uri
  sensitive   = true
}

output "postgres_rag_host" {
  description = "PostgreSQL RAG database host"
  value       = data.exoscale_database_uri.foi_postgres_rag_uri.uri
  sensitive   = true
}

# ============================================
# Disaster Recovery - S3 Bucket in Vienna
# ============================================

# SOS Bucket for cross-region backups (Vienna, Austria)
# Using AWS provider since Exoscale SOS is S3-compatible
resource "aws_s3_bucket" "foi_dr_bucket" {
  count    = var.dr_enabled ? 1 : 0
  provider = aws.exoscale_dr
  
  bucket = var.dr_bucket_name
  
  tags = {
    Name        = var.dr_bucket_name
    Environment = var.environment
    Purpose     = "disaster-recovery"
    Region      = var.dr_zone
  }
}

# Outputs for DR configuration
output "dr_bucket_name" {
  description = "Disaster recovery S3 bucket name"
  value       = var.dr_enabled ? aws_s3_bucket.foi_dr_bucket[0].bucket : null
}

output "dr_bucket_endpoint" {
  description = "Disaster recovery S3 bucket endpoint"
  value       = var.dr_enabled ? "sos-${var.dr_zone}.exo.io" : null
}

output "dr_bucket_url" {
  description = "Disaster recovery S3 bucket URL"
  value       = var.dr_enabled ? "https://sos-${var.dr_zone}.exo.io/${var.dr_bucket_name}" : null
} 