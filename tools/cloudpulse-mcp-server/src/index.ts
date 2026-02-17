/**
 * CloudPulse MCP Server
 *
 * Model Context Protocol server that allows AI assistants to
 * query and manage cloud cost data via the CloudPulse API.
 *
 * Tools provided:
 * - list_workspaces: List all workspaces
 * - get_cost_report: Get cost report details
 * - list_cost_reports: List cost reports in a workspace
 * - create_cost_report: Create a new cost report with CQL filter
 * - list_segments: List cost segments
 * - query_costs: Run a CQL query against cost data
 * - get_recommendations: Get cost optimization recommendations
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const API_BASE = process.env.CLOUDPULSE_API_URL || 'https://api.cloudpulse.dev';
const API_TOKEN = process.env.CLOUDPULSE_API_TOKEN || '';

async function apiRequest(method: string, path: string, body?: unknown) {
  const res = await fetch(`${API_BASE}/api/v2${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(`API error ${res.status}: ${err.detail}`);
  }
  return res.json();
}

const server = new Server(
  { name: 'cloudpulse-mcp-server', version: '0.1.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'list_workspaces',
      description: 'List all CloudPulse workspaces',
      inputSchema: { type: 'object', properties: {} },
    },
    {
      name: 'list_cost_reports',
      description: 'List cost reports, optionally filtered by workspace',
      inputSchema: {
        type: 'object',
        properties: {
          workspace_token: { type: 'string', description: 'Filter by workspace token' },
        },
      },
    },
    {
      name: 'get_cost_report',
      description: 'Get details of a specific cost report',
      inputSchema: {
        type: 'object',
        properties: { token: { type: 'string' } },
        required: ['token'],
      },
    },
    {
      name: 'create_cost_report',
      description: 'Create a new cost report with optional CQL filter',
      inputSchema: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          workspace_token: { type: 'string' },
          filter: { type: 'string', description: 'CQL filter expression' },
          groupings: { type: 'string', default: 'service' },
          date_interval: { type: 'string', default: 'last_30_days' },
        },
        required: ['title', 'workspace_token'],
      },
    },
    {
      name: 'list_segments',
      description: 'List cost segments in a workspace',
      inputSchema: {
        type: 'object',
        properties: {
          workspace_token: { type: 'string' },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result: unknown;

    switch (name) {
      case 'list_workspaces':
        result = await apiRequest('GET', '/workspaces');
        break;
      case 'list_cost_reports': {
        const qs = args?.workspace_token ? `?workspace_token=${args.workspace_token}` : '';
        result = await apiRequest('GET', `/cost_reports${qs}`);
        break;
      }
      case 'get_cost_report':
        result = await apiRequest('GET', `/cost_reports/${args?.token}`);
        break;
      case 'create_cost_report':
        result = await apiRequest('POST', '/cost_reports', args);
        break;
      case 'list_segments': {
        const qs = args?.workspace_token ? `?workspace_token=${args.workspace_token}` : '';
        result = await apiRequest('GET', `/segments${qs}`);
        break;
      }
      default:
        return { content: [{ type: 'text', text: `Unknown tool: ${name}` }], isError: true };
    }

    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error: ${error instanceof Error ? error.message : String(error)}` }],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('CloudPulse MCP server running on stdio');
}

main().catch(console.error);
