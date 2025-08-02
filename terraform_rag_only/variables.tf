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

variable "zone" {
  description = "Exoscale zone"
  type        = string
  default     = "ch-dk-2"
}

variable "postgres_plan" {
  description = "PostgreSQL database plan"
  type        = string
  default     = "hobbyist-2"
}

variable "postgres_user" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "rag_user"
}

variable "postgres_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}