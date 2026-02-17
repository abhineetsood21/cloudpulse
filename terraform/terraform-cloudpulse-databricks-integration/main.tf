# CloudPulse Databricks Integration Module
#
# Configures Databricks workspace billing access for CloudPulse cost monitoring.
#
# Usage:
#   module "cloudpulse_databricks" {
#     source              = "cloudpulse/databricks-integration/cloudpulse"
#     cloudpulse_api_token = var.cloudpulse_api_token
#     workspace_token      = "ws_abc123"
#     databricks_host      = "https://accounts.cloud.databricks.com"
#     databricks_account_id = "your-account-id"
#   }

variable "cloudpulse_api_token" {
  description = "CloudPulse API token for registering the integration"
  type        = string
  sensitive   = true
}

variable "workspace_token" {
  description = "CloudPulse workspace token to associate with the Databricks account"
  type        = string
}

variable "databricks_host" {
  description = "Databricks accounts console URL"
  type        = string
  default     = "https://accounts.cloud.databricks.com"
}

variable "databricks_account_id" {
  description = "Databricks account ID"
  type        = string
}

variable "enable_usage_export" {
  description = "Enable automatic usage data export from Databricks to CloudPulse"
  type        = bool
  default     = true
}

# Store integration configuration
# In production this would use the CloudPulse Terraform provider
# to create an integration resource. For now, output config for manual setup.

output "integration_config" {
  description = "Configuration to enter in CloudPulse for Databricks integration"
  value = {
    provider            = "databricks"
    workspace_token     = var.workspace_token
    databricks_host     = var.databricks_host
    account_id          = var.databricks_account_id
    usage_export        = var.enable_usage_export
  }
}
