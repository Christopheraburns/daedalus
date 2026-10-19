export type Parameter = { name: string; location: 'path' | 'query'; type: 'string' | 'integer' | 'number' | 'boolean'; required: boolean; description: string };
export type ToolKind = 'http' | 'python' | 'mcp';
export type ToolSpec = { name: string; description: string; kind?: ToolKind; connection_id: string | null; method: 'GET' | 'POST'; path: string; parameters: Parameter[]; body_schema: Record<string, unknown> | null; pack?: string; function?: string; config?: Record<string, unknown>; upstream_tool?: string; input_schema?: JsonSchema; wrap_body?: boolean; effect: 'read' | 'write'; enabled: boolean };
export type PackTool = { function: string; description: string; effect: 'read' | 'write'; requires_connection: boolean; parameters: { name: string; type: string; required: boolean }[]; source?: string };
export type Pack = { name: string; description: string; origin: 'builtin' | 'project'; editable: boolean; error: string | null; protocol: Protocol; tools: PackTool[]; source?: string };
/** What the canvas and lists show for a tool: method and path for HTTP tools, pack.function for Python tools. */
export function toolLabel(tool: ToolSpec): { method: string; subtitle: string } {
  if (tool.kind === 'mcp') return { method: 'MCP', subtitle: tool.upstream_tool ?? '' };
  return tool.kind === 'python' ? { method: 'PY', subtitle: `${tool.pack}.${tool.function}` } : { method: tool.method, subtitle: tool.path };
}
export type Tool = ToolSpec & { id: string; revision: number; validated: boolean; tested: boolean; published: boolean; test_summary: { success: boolean; duration_ms: number; tested_at: string } | null };
export type AuthMode = 'none' | 'static' | 'forward-token' | 'proxy-doas' | 's3-sigv4';
export type Protocol = 'rest' | 'webhdfs' | 's3' | 'mcp';
export type ProbeSummary = { success: boolean; message: string; pack: string | null; checked_at: string; duration_ms: number };
export type JsonSchema = { type?: string; properties?: Record<string, JsonSchema & { description?: string }>; required?: string[]; [key: string]: unknown };
export type DiscoveredTool = { name: string; description: string; input_schema: JsonSchema; read_only: boolean };
export type Connection = { id: string; revision: number; name: string; base_url: string; protocol?: Protocol; federate?: boolean; probe_summary?: ProbeSummary | null; discovered?: DiscoveredTool[] | null; auth_mode: AuthMode; secret_ref?: string; proxy_principal?: string; keytab_ref?: string; doas_parameter?: string };
export type ApiOrigin = { id: string; server_id: string; revision: number; origin: string; description: string; enabled: boolean; bootstrap?: boolean; created_at?: string };
export type Release = { id: string; status: string; checksum: string; error: string | null; created_at: string; created_by: string; tool_names: string[] };
export type Deployment = { id: string; revision: number; status: string; desired_release_id: string | null; deployed_release_id: string | null; application_name: string | null; application_id: string | null; endpoint: string | null; provider: string; message: string | null; metrics: Record<string, unknown>; updated_at: string };
export type ServerSummary = { id: string; name: string; revision: number; active_release_id: string | null; deployment: Deployment; tools?: number; connections?: number;
  owner?: { process: string | null; address: string | null; since: string | null } | null;
  contender?: { host: string | null; revision: string | null; owner: string | null; at: string } | null;
  runtime?: { online: boolean; ready: boolean; heartbeat_age: number | null; host: string | null; revision: string | null; effective_release_id: string | null } };
export type Workspace = {
  identity: { role: string; mode: string };
  server: { id: string; name: string; revision: number; active_release_id: string | null; desired_release_id: string | null; mcp_url: string; runtime: { online: boolean; ready?: boolean; gateway_pid?: number; gateway_started_at?: string; effective_release_id?: string | null; last_error?: string | null; revision?: string; host?: string } };
  connections: Connection[]; tools: Tool[];
  layout: { revision: number; positions: Record<string, { x: number; y: number }> };
  active_tools: { id: string; revision: number; spec: ToolSpec; fingerprint: string }[];
  releases: Release[]; allowed_api_origins: string[];
  deployment: Deployment;
};
export type Preview = { revision: number; added: string[]; changed: string[]; removed: string[]; problems: string[] };
export type OpenAPIOperation = { method: string; path: string; name: string; description: string; parameters: Parameter[]; body_schema: Record<string, unknown> | null; effect: 'read' | 'write'; supported?: boolean };
export function specOf(tool: Tool): ToolSpec {
  const { name, description, kind, connection_id, method, path, parameters, body_schema, pack, function: fn, config, upstream_tool, effect, enabled } = tool;
  return { name, description, kind, connection_id, method, path, parameters, body_schema, pack, function: fn, config, upstream_tool, effect, enabled };
}
