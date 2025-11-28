# SKS Configuration Variables

variable "sks_enabled" {
  description = "Enable SKS cluster creation"
  type        = bool
  default     = false
}

variable "sks_k8s_version" {
  description = "Kubernetes version for SKS cluster"
  type        = string
  default     = "1.34.2"
}

variable "sks_service_level" {
  description = "SKS service level (starter or pro)"
  type        = string
  default     = "starter"
  
  validation {
    condition     = contains(["starter", "pro"], var.sks_service_level)
    error_message = "SKS service level must be 'starter' or 'pro'"
  }
}

variable "sks_cni" {
  description = "CNI plugin for SKS cluster"
  type        = string
  default     = "calico"
  
  validation {
    condition     = contains(["calico", "cilium"], var.sks_cni)
    error_message = "CNI must be 'calico' or 'cilium'"
  }
}

variable "sks_node_instance_type" {
  description = "Instance type for SKS nodes"
  type        = string
  default     = "standard.medium"
}

variable "sks_node_count" {
  description = "Number of nodes in the SKS node pool"
  type        = number
  default     = 2
  
  validation {
    condition     = var.sks_node_count >= 1 && var.sks_node_count <= 10
    error_message = "Node count must be between 1 and 10"
  }
}

variable "sks_auto_upgrade" {
  description = "Enable automatic upgrade of control plane"
  type        = bool
  default     = false
}

variable "sks_anti_affinity" {
  description = "Enable anti-affinity for nodes (spread across physical hosts)"
  type        = bool
  default     = true
}

