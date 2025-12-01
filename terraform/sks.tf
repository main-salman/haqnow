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

# NLB Service for HTTP (port 80 → NodePort 31621)
resource "exoscale_nlb_service" "http" {
  count            = var.sks_enabled ? 1 : 0
  zone             = var.zone
  nlb_id           = exoscale_nlb.haqnow[0].id
  name             = "http"
  description      = "HTTP traffic to ingress controller"
  port             = 80
  target_port      = 31621
  protocol         = "tcp"
  strategy         = "round-robin"
  
  healthcheck {
    mode     = "http"
    port     = 31621
    uri      = "/health"
    interval = 10
    timeout  = 5
    retries  = 3
  }
  
  instance_pool_id = exoscale_sks_nodepool.haqnow_nodes[0].instance_pool_id
}

# NLB Service for HTTPS (port 443 → NodePort 31993)
resource "exoscale_nlb_service" "https" {
  count            = var.sks_enabled ? 1 : 0
  zone             = var.zone
  nlb_id           = exoscale_nlb.haqnow[0].id
  name             = "https"
  description      = "HTTPS traffic to ingress controller"
  port             = 443
  target_port      = 31993
  protocol         = "tcp"
  strategy         = "round-robin"
  
  healthcheck {
    mode     = "tcp"
    port     = 31993
    interval = 10
    timeout  = 5
    retries  = 3
  }
  
  instance_pool_id = exoscale_sks_nodepool.haqnow_nodes[0].instance_pool_id
}

# Generate kubeconfig for cluster access
resource "exoscale_sks_kubeconfig" "haqnow" {
  count       = var.sks_enabled ? 1 : 0
  cluster_id  = exoscale_sks_cluster.haqnow[0].id
  zone        = exoscale_sks_cluster.haqnow[0].zone
  user        = "kubernetes-admin"
  groups      = ["system:masters"]
}

# Save kubeconfig to local file (in gitignored location)
resource "local_sensitive_file" "haqnow_kubeconfig" {
  count            = var.sks_enabled ? 1 : 0
  filename         = "${path.module}/../k8s/.kubeconfig"  # .kubeconfig is gitignored
  content          = exoscale_sks_kubeconfig.haqnow[0].kubeconfig
  file_permission  = "0600"
  
  depends_on = [exoscale_sks_cluster.haqnow]
}

# Note: Node IPs will be retrieved via kubectl after cluster is created
# The update-database-ips-terraform.sh script will use kubectl to get node IPs
# We can't use Terraform data sources for this as node IPs are dynamic

