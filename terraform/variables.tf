variable "exoscale_api_key" {
  description = "Exoscale API key"
  type        = string
  sensitive   = true
}

variable "exoscale_secret_key" {
  description = "Exoscale secret key"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "foi-archive"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "zone" {
  description = "Exoscale zone"
  type        = string
  default     = "ch-dk-2"
}

variable "instance_type" {
  description = "Instance type"
  type        = string
  default     = "standard.medium"
}

variable "disk_size" {
  description = "Root disk size in GB"
  type        = number
  default     = 50
}

variable "ssh_key_name" {
  description = "SSH key pair name"
  type        = string
  default     = "foi-archive-key"
}

variable "s3_access_key" {
  description = "S3 access key"
  type        = string
  sensitive   = true
}

variable "s3_secret_key" {
  description = "S3 secret key"
  type        = string
  sensitive   = true
}

variable "s3_endpoint" {
  description = "S3 endpoint"
  type        = string
  default     = "sos-ch-dk-2.exo.io"
}

variable "s3_region" {
  description = "S3 region"
  type        = string
  default     = "ch-dk-2"
}

variable "s3_bucket_name" {
  description = "S3 bucket name"
  type        = string
  default     = "foi-archive-terraform"
}

variable "admin_email" {
  description = "Admin email address"
  type        = string
}

variable "admin_password" {
  description = "Admin password"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true
}

variable "sendgrid_api_key" {
  description = "SendGrid API key for email notifications"
  type        = string
  sensitive   = true
}

variable "from_email" {
  description = "From email address for notifications"
  type        = string
  default     = "noreply@fadih.org"
}

variable "custom_domain" {
  description = "Custom domain for the application (optional)"
  type        = string
  default     = ""
} 