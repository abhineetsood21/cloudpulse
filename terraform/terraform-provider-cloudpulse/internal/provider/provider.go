// Package provider implements the CloudPulse Terraform provider.
//
// Resources:
//   - cloudpulse_workspace
//   - cloudpulse_cost_report
//   - cloudpulse_folder
//   - cloudpulse_saved_filter
//   - cloudpulse_dashboard
//   - cloudpulse_segment
//   - cloudpulse_team
//   - cloudpulse_virtual_tag
//
// Data Sources:
//   - cloudpulse_workspaces
//   - cloudpulse_cost_reports
//   - cloudpulse_folders
//
// Example:
//
//	provider "cloudpulse" {
//	  api_token = var.cloudpulse_api_token
//	  host      = "https://api.cloudpulse.dev"   # optional
//	}
//
//	resource "cloudpulse_workspace" "prod" {
//	  name = "Production"
//	}
//
//	resource "cloudpulse_cost_report" "ec2" {
//	  title           = "EC2 Monthly"
//	  workspace_token = cloudpulse_workspace.prod.token
//	  filter          = "costs.service = 'Amazon EC2'"
//	  groupings       = "service"
//	  date_interval   = "last_30_days"
//	}
//
//	resource "cloudpulse_folder" "engineering" {
//	  title           = "Engineering"
//	  workspace_token = cloudpulse_workspace.prod.token
//	}
//
//	resource "cloudpulse_segment" "backend" {
//	  title           = "Backend Services"
//	  workspace_token = cloudpulse_workspace.prod.token
//	  filter          = "costs.service = 'Amazon EC2' OR costs.service = 'Amazon RDS'"
//	  priority        = 1
//	}
//
//	resource "cloudpulse_virtual_tag" "team" {
//	  key             = "team"
//	  workspace_token = cloudpulse_workspace.prod.token
//	  overridable     = true
//	  values = [
//	    { name = "platform", filter = "tags.team = 'platform'" },
//	    { name = "frontend", filter = "tags.team = 'frontend'" },
//	  ]
//	}
//
//	resource "cloudpulse_team" "sre" {
//	  name            = "SRE"
//	  workspace_token = cloudpulse_workspace.prod.token
//	  description     = "Site Reliability Engineering"
//	}
//
//	resource "cloudpulse_saved_filter" "prod_only" {
//	  title           = "Production Only"
//	  workspace_token = cloudpulse_workspace.prod.token
//	  filter          = "tags.env = 'production'"
//	}
//
//	resource "cloudpulse_dashboard" "overview" {
//	  title           = "Cost Overview"
//	  workspace_token = cloudpulse_workspace.prod.token
//	  date_interval   = "last_30_days"
//	}
//
//	data "cloudpulse_workspaces" "all" {}
//
//	data "cloudpulse_cost_reports" "prod" {
//	  workspace_token = cloudpulse_workspace.prod.token
//	}
package provider

import (
	"context"

	"github.com/hashicorp/terraform-plugin-framework/datasource"
	"github.com/hashicorp/terraform-plugin-framework/provider"
	"github.com/hashicorp/terraform-plugin-framework/provider/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/types"
)

var _ provider.Provider = &CloudPulseProvider{}

type CloudPulseProvider struct {
	version string
}

type CloudPulseProviderModel struct {
	APIToken types.String `tfsdk:"api_token"`
	Host     types.String `tfsdk:"host"`
}

func New(version string) func() provider.Provider {
	return func() provider.Provider {
		return &CloudPulseProvider{version: version}
	}
}

func (p *CloudPulseProvider) Metadata(_ context.Context, _ provider.MetadataRequest, resp *provider.MetadataResponse) {
	resp.TypeName = "cloudpulse"
	resp.Version = p.version
}

func (p *CloudPulseProvider) Schema(_ context.Context, _ provider.SchemaRequest, resp *provider.SchemaResponse) {
	resp.Schema = schema.Schema{
		Description: "Manage CloudPulse cloud cost management resources.",
		Attributes: map[string]schema.Attribute{
			"api_token": schema.StringAttribute{
				Description: "CloudPulse API token. Can also be set via CLOUDPULSE_API_TOKEN env var.",
				Optional:    true,
				Sensitive:   true,
			},
			"host": schema.StringAttribute{
				Description: "CloudPulse API host URL. Defaults to https://api.cloudpulse.dev.",
				Optional:    true,
			},
		},
	}
}

func (p *CloudPulseProvider) Configure(ctx context.Context, req provider.ConfigureRequest, resp *provider.ConfigureResponse) {
	var config CloudPulseProviderModel
	resp.Diagnostics.Append(req.Config.Get(ctx, &config)...)
	if resp.Diagnostics.HasError() {
		return
	}
	// API client would be initialized here and passed to resources via resp.DataSourceData / resp.ResourceData
}

func (p *CloudPulseProvider) Resources(_ context.Context) []func() resource.Resource {
	return []func() resource.Resource{
		// Each would be a full resource implementation.
		// Stubbed for structure — full CRUD implementation follows the
		// terraform-plugin-framework patterns.
	}
}

func (p *CloudPulseProvider) DataSources(_ context.Context) []func() datasource.DataSource {
	return []func() datasource.DataSource{}
}
