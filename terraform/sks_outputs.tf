# SKS Outputs

output "sks_cluster_id" {
  description = "SKS cluster ID"
  value       = var.sks_enabled ? exoscale_sks_cluster.haqnow[0].id : null
}

output "sks_cluster_name" {
  description = "SKS cluster name"
  value       = var.sks_enabled ? exoscale_sks_cluster.haqnow[0].name : null
}

output "sks_nodepool_id" {
  description = "SKS node pool ID"
  value       = var.sks_enabled ? exoscale_sks_nodepool.haqnow_nodes[0].id : null
}

output "sks_security_group_id" {
  description = "SKS nodes security group ID"
  value       = var.sks_enabled ? exoscale_security_group.sks_nodes[0].id : null
}

output "sks_node_ips" {
  description = "SKS node IP addresses (retrieved via kubectl after deployment)"
  value       = "Use 'kubectl get nodes -o jsonpath=\"{.items[*].status.addresses[?(@.type==\\\"ExternalIP\\\")].address}\"' to get node IPs"
}

output "sks_nlb_ip" {
  description = "Network Load Balancer IP address"
  value       = var.sks_enabled ? exoscale_nlb.haqnow[0].ip_address : null
}

output "sks_kubeconfig_path" {
  description = "Path to kubeconfig file (gitignored, contains sensitive credentials)"
  value       = var.sks_enabled ? local_sensitive_file.haqnow_kubeconfig[0].filename : null
  sensitive   = false
}

output "sks_kubectl_command" {
  description = "Command to set KUBECONFIG and access cluster"
  value       = var.sks_enabled ? "export KUBECONFIG=${abspath(local_sensitive_file.haqnow_kubeconfig[0].filename)} && kubectl get nodes" : null
}

