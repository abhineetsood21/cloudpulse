# CloudPulse AWS Integration Module
#
# Creates an IAM role with read-only Cost Explorer and CUR access
# that CloudPulse can assume to monitor your AWS costs.
#
# Usage:
#   module "cloudpulse" {
#     source              = "cloudpulse/aws-integration/cloudpulse"
#     cloudpulse_account_id = "123456789012"  # CloudPulse's AWS account
#     external_id          = "cpls_abc123"     # From CloudPulse dashboard
#   }

variable "cloudpulse_account_id" {
  description = "CloudPulse's AWS account ID for cross-account access"
  type        = string
  default     = "000000000000" # Placeholder — set to actual CloudPulse account
}

variable "external_id" {
  description = "External ID from your CloudPulse workspace for secure cross-account access"
  type        = string
}

variable "role_name" {
  description = "Name of the IAM role to create"
  type        = string
  default     = "CloudPulseCostAccess"
}

variable "enable_cur_access" {
  description = "Whether to grant access to Cost and Usage Reports S3 bucket"
  type        = bool
  default     = false
}

variable "cur_bucket_arn" {
  description = "ARN of the S3 bucket containing CUR data (required if enable_cur_access is true)"
  type        = string
  default     = ""
}

# IAM Role
resource "aws_iam_role" "cloudpulse" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.cloudpulse_account_id}:root"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.external_id
          }
        }
      }
    ]
  })

  tags = {
    ManagedBy = "CloudPulse"
    Purpose   = "Cost monitoring read-only access"
  }
}

# Cost Explorer read-only policy
resource "aws_iam_role_policy" "cost_explorer" {
  name = "CloudPulseCostExplorerRead"
  role = aws_iam_role.cloudpulse.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast",
          "ce:GetReservationUtilization",
          "ce:GetSavingsPlansUtilization",
          "ce:GetDimensionValues",
          "ce:GetTags",
          "ce:GetRightsizingRecommendation",
          "ce:GetAnomalies",
          "ce:GetAnomalyMonitors",
          "ce:GetAnomalySubscriptions",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "organizations:DescribeOrganization",
          "organizations:ListAccounts",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeRegions",
          "rds:DescribeDBInstances",
          "elasticache:DescribeCacheClusters",
          "es:DescribeElasticsearchDomains",
          "eks:ListClusters",
          "eks:DescribeCluster",
        ]
        Resource = "*"
      }
    ]
  })
}

# Optional CUR S3 access
resource "aws_iam_role_policy" "cur_access" {
  count = var.enable_cur_access ? 1 : 0
  name  = "CloudPulseCURRead"
  role  = aws_iam_role.cloudpulse.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = [var.cur_bucket_arn, "${var.cur_bucket_arn}/*"]
      }
    ]
  })
}

output "role_arn" {
  description = "ARN of the CloudPulse IAM role — enter this in CloudPulse settings"
  value       = aws_iam_role.cloudpulse.arn
}

output "external_id" {
  description = "External ID used for secure cross-account access"
  value       = var.external_id
}
