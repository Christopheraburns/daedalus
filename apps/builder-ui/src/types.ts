export type Parameter = { name: string; location: 'path' | 'query'; type: 'string' | 'integer' | 'number' | 'boolean'; required: boolean; description: string };
export type ToolSpec = { name: string; description: string; connection_id: string; method: 'GET' | 'POST'; path: string; parameters: Parameter[]; body_schema: Record<string, unknown> | null; effect: 'read' | 'write'; enabled: boolean };
export type Tool = ToolSpec & { id: string; revision: number; validated: boolean; tested: boolean; published: boolean; test_summary: { success: boolean; duration_ms: number; tested_at: string } | null };
export type Connection = { id: string; revision: number; name: string; base_url: string; auth_mode: 'none' };
export type Release = { id: string; status: string; checksum: string; error: string | null; created_at: string; created_by: string; tool_names: string[] };
export type Deployment = { id: string; revision: number; status: string; desired_release_id: string | null; deployed_release_id: string | null; application_name: string | null; application_id: string | null; endpoint: string | null; provider: string; message: string | null; metrics: Record<string, unknown>; updated_at: string };
export type ServerSummary = { id: string; name: string; revision: number; active_release_id: string | null; deployment: Deployment };
export type Workspace = {
  identity: { role: string; mode: string };
  server: { id: string; name: string; revision: number; active_release_id: string | null; desired_release_id: string | null; mcp_url: string; runtime: { online: boolean; ready?: boolean; gateway_pid?: number; gateway_started_at?: string; last_error?: string | null } };
  connections: Connection[]; tools: Tool[];
  layout: { revision: number; positions: Record<string, { x: number; y: number }> };
  active_tools: { id: string; revision: number; spec: ToolSpec; fingerprint: string }[];
  releases: Release[]; allowed_api_origins: string[];
  deployment: Deployment;
};
export type Preview = { revision: number; added: string[]; changed: string[]; removed: string[]; problems: string[] };
export type OpenAPIOperation = { method: string; path: string; name: string; description: string; parameters: Parameter[]; body_schema: Record<string, unknown> | null; effect: 'read' | 'write'; supported?: boolean };
export function specOf(tool: Tool): ToolSpec {
  const { name, description, connection_id, method, path, parameters, body_schema, effect, enabled } = tool;
  return { name, description, connection_id, method, path, parameters, body_schema, effect, enabled };
}
