# Example: Use the CloudPulse Terraform provider to manage integrations as code.
#
# This file shows how you would declare CloudPulse integrations in Terraform,
# using the CloudPulse Terraform provider (published separately).
#
# If the provider isn't published yet, you can use the `restapi` provider
# or curl-based provisioners as a workaround.

terraform {
  required_providers {
    # Option A: Use the CloudPulse Terraform provider (when published)
    # cloudpulse = {
    #   source  = "abhineetsood21/cloudpulse"
    #   version = "~> 0.1"
    # }

    # Option B: Use the generic REST API provider
    restapi = {
      source  = "Mastercard/restapi"
      version = "~> 1.18"
    }
  }
}

# Configure the REST API provider to talk to CloudPulse
provider "restapi" {
  uri                  = "http://localhost:8000/api/v2"
  write_returns_object = true
  headers = {
    Content-Type = "application/json"
  }
}

# Connect Datadog as an integration
resource "restapi_object" "datadog_integration" {
  path         = "/integrations/connect"
  create_method = "POST"
  
  data = jsonencode({
    provider     = "datadog"
    display_name = "Production Datadog"
    credentials = {
      api_key = var.datadog_api_key
      app_key = var.datadog_app_key
      site    = "datadoghq.com"
    }
  })
}

# Register a webhook for cost events
resource "restapi_object" "slack_webhook" {
  path         = "/webhooks"
  create_method = "POST"
  
  data = jsonencode({
    url         = var.slack_webhook_url
    events      = ["sync.completed", "anomaly.detected", "budget.exceeded"]
    secret      = var.webhook_secret
    description = "Slack cost alerts"
  })
}

# Variables
variable "datadog_api_key" {
  type      = string
  sensitive = true
}

variable "datadog_app_key" {
  type      = string
  sensitive = true
}

variable "slack_webhook_url" {
  type = string
}

variable "webhook_secret" {
  type      = string
  sensitive = true
}

# Outputs
output "datadog_integration_id" {
  value = jsondecode(restapi_object.datadog_integration.api_response).id
}
