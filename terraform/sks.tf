# SKS Cluster Configuration for HaqNow
# This creates the Kubernetes infrastructure for containerized deployment

# Security Group for SKS Nodes
resource "exoscale_security_group" "sks_nodes" {
  count = var.sks_enabled ? 1 : 0
  name        = "${var.project_name}-sks-nodes-${var.environment}"
  description = "Security group for SKS production nodes"
  
  lifecycle {
    create_before_destroy = true
  }
}

# Security Group Rules for SKS Nodes
# Allow all traffic between nodes (required for Kubernetes)
resource "exoscale_security_group_rule" "sks_nodes_inter_node" {
  count                  = var.sks_enabled ? 1 : 0
  security_group_id      = exoscale_security_group.sks_nodes[0].id
  user_security_group_id = exoscale_security_group.sks_nodes[0].id
  type                   = "INGRESS"
  protocol               = "TCP"
  start_port             = 1
  end_port               = 65535
  description            = "Allow all TCP traffic between SKS nodes"
}

resource "exoscale_security_group_rule" "sks_nodes_inter_node_udp" {
  count                  = var.sks_enabled ? 1 : 0
  security_group_id      = exoscale_security_group.sks_nodes[0].id
  user_security_group_id = exoscale_security_group.sks_nodes[0].id
  type                   = "INGRESS"
  protocol               = "UDP"
  start_port             = 1
  end_port               = 65535
  description            = "Allow all UDP traffic between SKS nodes"
}

# Allow kubelet API (required for node communication)
resource "exoscale_security_group_rule" "sks_nodes_kubelet" {
  count             = var.sks_enabled ? 1 : 0
  security_group_id = exoscale_security_group.sks_nodes[0].id
  type              = "INGRESS"
  protocol          = "TCP"
  start_port        = 10250
  end_port          = 10250
  cidr              = "0.0.0.0/0"
  description       = "Allow kubelet API access"
}

# Allow NodePort services (30000-32767)
resource "exoscale_security_group_rule" "sks_nodes_nodeport" {
  count             = var.sks_enabled ? 1 : 0
  security_group_id = exoscale_security_group.sks_nodes[0].id
  type              = "INGRESS"
  protocol          = "TCP"
  start_port        = 30000
  end_port          = 32767
  cidr              = "0.0.0.0/0"
  description       = "Allow NodePort services"
}

# SKS Cluster
resource "exoscale_sks_cluster" "haqnow" {
  count         = var.sks_enabled ? 1 : 0
  zone          = var.zone
  name          = "${var.project_name}-sks-${var.environment}"
  description   = "HaqNow production Kubernetes cluster"
  version       = var.sks_k8s_version
  service_level = var.sks_service_level
  cni           = var.sks_cni
  
  # Enable Exoscale addons (using new attributes instead of deprecated addons)
  exoscale_ccm = true
  exoscale_csi = true
  metrics_server = true
  
  auto_upgrade = var.sks_auto_upgrade
  
  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# Anti-Affinity Group (optional, for HA)
resource "exoscale_anti_affinity_group" "haqnow" {
  count       = var.sks_enabled && var.sks_anti_affinity ? 1 : 0
  name        = "${var.project_name}-anti-affinity-${var.environment}"
  description = "Anti-affinity group for SKS nodes"
}

# SKS Node Pool
resource "exoscale_sks_nodepool" "haqnow_nodes" {
  count              = var.sks_enabled ? 1 : 0
  zone               = var.zone
  cluster_id         = exoscale_sks_cluster.haqnow[0].id
  name               = "${var.project_name}-nodes-${var.environment}"
  instance_type      = var.sks_node_instance_type
  size               = var.sks_node_count
  security_group_ids = [exoscale_security_group.sks_nodes[0].id]
  description        = "Production node pool for HaqNow"
  
  # Anti-affinity for high availability
  anti_affinity_group_ids = var.sks_anti_affinity && length(exoscale_anti_affinity_group.haqnow) > 0 ? [exoscale_anti_affinity_group.haqnow[0].id] : []
  
  labels = {
    environment = var.environment
    project     = var.project_name
    role        = "worker"
  }
}

# Network Load Balancer for SKS
resource "exoscale_nlb" "haqnow" {
  count       = var.sks_enabled ? 1 : 0
  zone        = var.zone
  name        = "${var.project_name}-nlb-${var.environment}"
  description = "Network Load Balancer for HaqNow SKS cluster"
  
  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# Note: NLB Services will be configured after Kubernetes deployment
# They need to point to NodePort services or use Exoscale CCM integration
# For now, we'll create the NLB and configure services manually or via Kubernetes

# Generate kubeconfig for cluster access
resource "exoscale_sks_kubeconfig" "haqnow" {
  count       = var.sks_enabled ? 1 : 0
  cluster_id  = exoscale_sks_cluster.haqnow[0].id
  zone        = exoscale_sks_cluster.haqnow[0].zone
  user        = "kubernetes-admin"
  groups      = ["system:masters"]
}

# Save kubeconfig to local file
resource "local_sensitive_file" "haqnow_kubeconfig" {
  count            = var.sks_enabled ? 1 : 0
  filename         = "${path.module}/../k8s/kubeconfig"
  content          = exoscale_sks_kubeconfig.haqnow[0].kubeconfig
  file_permission  = "0600"
  
  depends_on = [exoscale_sks_cluster.haqnow]
}

# Note: Node IPs will be retrieved via kubectl after cluster is created
# The update-database-ips-terraform.sh script will use kubectl to get node IPs
# We can't use Terraform data sources for this as node IPs are dynamic

