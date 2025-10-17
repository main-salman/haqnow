terraform {
  required_providers {
    exoscale = {
      source  = "exoscale/exoscale"
      version = "~> 0.64"
    }
  }
  required_version = ">= 1.0"
}

# Configure the Exoscale Provider
provider "exoscale" {
  key    = var.exoscale_api_key
  secret = var.exoscale_secret_key
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
    ip_filter        = ["159.100.250.145/32"]  # Allow access from our server
    backup_schedule  = "02:00"  # Daily backup at 2 AM UTC
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
    ip_filter        = ["159.100.250.145/32"]  # Allow access from our server
    backup_schedule  = "03:00"  # Daily backup at 3 AM UTC
    version         = "15"      # PostgreSQL 15 supports pgvector
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

# Compute Instance for the application
resource "exoscale_compute_instance" "foi_app" {
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
  description = "Public IP of the HaqNow.com instance"
  value       = exoscale_compute_instance.foi_app.public_ip_address
}

output "instance_id" {
  description = "Instance ID"
  value       = exoscale_compute_instance.foi_app.id
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
  value       = "ssh root@${exoscale_compute_instance.foi_app.public_ip_address}"
}

output "application_url" {
  description = "URL to access the HaqNow.com application"
  value       = "http://${exoscale_compute_instance.foi_app.public_ip_address}"
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