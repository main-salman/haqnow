terraform {
  required_providers {
    exoscale = {
      source  = "exoscale/exoscale"
      version = "~> 0.62"
    }
  }
  required_version = ">= 1.0"
}

# Configure the Exoscale Provider
provider "exoscale" {
  key    = var.exoscale_api_key
  secret = var.exoscale_secret_key
}

# Security Group for web traffic
resource "exoscale_security_group" "foi_web" {
  name        = "${var.project_name}-web-${var.environment}"
  description = "Security group for FOI Archive web traffic"
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

# MySQL Database using dbaas
resource "exoscale_dbaas" "foi_mysql" {
  name = "${var.project_name}-mysql-${var.environment}"
  type = "mysql"
  plan = "hobbyist-2"
  zone = var.zone

  mysql {
    # MySQL specific configuration can go here
    # For basic setup, this block can be empty
  }
}

# Data source to get database connection info
data "exoscale_database_uri" "foi_mysql" {
  name = exoscale_dbaas.foi_mysql.name
  type = exoscale_dbaas.foi_mysql.type
  zone = exoscale_dbaas.foi_mysql.zone
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

  user_data = base64encode(templatefile("${path.module}/cloud-init.yml", {
    project_name     = var.project_name
    environment      = var.environment
    s3_bucket        = var.s3_bucket_name
    s3_access_key    = var.s3_access_key
    s3_secret_key    = var.s3_secret_key
    s3_endpoint      = var.s3_endpoint
    s3_region        = var.s3_region
    admin_email      = var.admin_email
    admin_password   = var.admin_password
    jwt_secret       = var.jwt_secret_key
    mysql_host       = data.exoscale_database_uri.foi_mysql.host
    mysql_user       = var.mysql_user
    mysql_password   = var.mysql_password
    mysql_database   = var.mysql_database
    sendgrid_api_key = var.sendgrid_api_key
  }))
}

# Outputs
output "instance_ip" {
  description = "Public IP of the FOI Archive instance"
  value       = exoscale_compute_instance.foi_app.public_ip_address
}

output "instance_id" {
  description = "Instance ID"
  value       = exoscale_compute_instance.foi_app.id
}

output "mysql_host" {
  description = "MySQL database host"
  value       = data.exoscale_database_uri.foi_mysql.host
}

output "mysql_connection_info" {
  description = "MySQL connection information"
  value = {
    host     = data.exoscale_database_uri.foi_mysql.host
    port     = data.exoscale_database_uri.foi_mysql.port
    database = var.mysql_database
  }
  sensitive = true
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh ubuntu@${exoscale_compute_instance.foi_app.public_ip_address}"
} 