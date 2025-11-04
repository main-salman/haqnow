terraform {
  required_providers {
    exoscale = {
      source  = "exoscale/exoscale"
      version = "~> 0.64"
    }
  }
  required_version = ">= 1.3"
}

provider "exoscale" {
  key    = var.exoscale_api_key
  secret = var.exoscale_secret_key
}

# PostgreSQL Database for RAG Vector Storage
resource "exoscale_dbaas" "foi_postgres_rag" {
  name                   = "foi-archive-postgres-rag-production"
  type                   = "pg"
  plan                   = var.postgres_plan
  zone                   = var.zone
  termination_protection = true

  pg {
    admin_username    = var.postgres_user
    admin_password    = var.postgres_password
    version          = "15"
    backup_schedule  = "03:00"
    ip_filter        = [var.server_ip_cidr]
  }
}

# Get database connection information
data "exoscale_database_uri" "foi_postgres_rag_uri" {
  zone = var.zone
  name = exoscale_dbaas.foi_postgres_rag.name
  type = "pg"
}

# Outputs
output "postgres_rag_uri" {
  description = "PostgreSQL RAG database connection URI"
  value       = data.exoscale_database_uri.foi_postgres_rag_uri.uri
  sensitive   = true
}

output "postgres_rag_host" {
  description = "PostgreSQL RAG database host"
  value       = data.exoscale_database_uri.foi_postgres_rag_uri.host
  sensitive   = true
}