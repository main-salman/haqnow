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
  name        = "${var.project_name}-web-${var.environment}-v2"
  description = "Security group for Fadih.org web traffic"
  
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
    sendgrid_api_key = var.sendgrid_api_key
  }))
}

# Outputs
output "instance_ip" {
  description = "Public IP of the Fadih.org instance"
  value       = exoscale_compute_instance.foi_app.public_ip_address
}

output "instance_id" {
  description = "Instance ID"
  value       = exoscale_compute_instance.foi_app.id
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh ubuntu@${exoscale_compute_instance.foi_app.public_ip_address}"
}

output "application_url" {
  description = "URL to access the Fadih.org application"
  value       = "http://${exoscale_compute_instance.foi_app.public_ip_address}"
} 