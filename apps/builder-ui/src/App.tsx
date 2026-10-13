import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { ReactFlow, Background, Controls, Handle, Position, applyNodeChanges, useReactFlow, type Node, type NodeProps, type OnConnect, type NodeChange } from '@xyflow/react';
import { ArrowRight, ArrowUpRight, Box, Braces, Check, CheckCheck, ChevronDown, ChevronRight, CircleHelp, Database, FlaskConical, GitBranch, GripVertical, History, LayoutGrid, List, LoaderCircle, LogOut, Network, Package, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, Play, Plus, Radio, Rocket, Save, Search, Server, Settings2, ShieldCheck, Trash2, Undo2, Unplug, X } from 'lucide-react';
import { statusLabel, useI18n } from './i18n';
import { type ApiOrigin, type Connection, type Deployment, type OpenAPIOperation, type Pack, type PackTool, type Parameter, type Preview, type ServerSummary, type Tool, type ToolSpec, type Workspace, specOf, toolLabel } from './types';

type CardData = { kind: 'server' | 'tool' | 'connection'; title: string; subtitle: string; status?: string; method?: string; count?: number; selected?: boolean; [key: string]: unknown };
type CardNode = Node<CardData>;
const openAdmin = import.meta.env.VITE_FACTORY_OPEN_ADMIN === 'true';
const PACK_TEMPLATE = `"""Describe what this pack is for; it appears in the Builder palette."""
from factory.packs import ToolContext, pack_tool


@pack_tool(effect="read", requires_connection=False)
def hello(ctx: ToolContext, name: str) -> dict:
    """Greet someone by name. Explain here when an agent should use this tool."""
    return {"greeting": f"Hello, {name}", "user": ctx.caller.username}
`;

function CanvasCard({ data }: NodeProps<CardNode>) {
  const { tr } = useI18n();
  const Icon = data.kind === 'server' ? Server : data.kind === 'connection' ? Database : Braces;
  return <div className={`canvas-card ${data.kind} ${data.selected ? 'selected' : ''}`}>
    {data.kind !== 'server' && <Handle type="target" position={Position.Left} />}
    <div className="card-kicker">{data.kind === 'server' ? tr('kicker_server') : data.kind === 'connection' ? tr('kicker_connection') : tr('kicker_tool')}<span className={`status-dot ${data.status === 'Active' || data.status === 'Tested' ? 'green' : ''}`} /></div>
    <div className="card-title"><span className="node-icon"><Icon size={17} /></span><strong>{data.title}</strong></div>
    <div className="card-subtitle">{data.method && <span className={`method ${data.method.toLowerCase()}`}>{data.method}</span>}{data.subtitle}</div>
    <div className="card-footer"><span>{data.kind === 'tool' ? statusLabel(tr, data.status) : tr('n_tools', { count: data.count ?? 0 })}</span>{data.kind === 'tool' ? <ChevronRight size={14} /> : <span className="tiny-tag">{data.kind === 'server' ? 'agentgateway' : 'REST / JSON'}</span>}</div>
    {data.kind !== 'connection' && <Handle type="source" position={Position.Right} />}
  </div>;
}
const nodeTypes = { card: CanvasCard };

function Modal({ title, subtitle, children, close }: { title: string; subtitle?: string; children: ReactNode; close: () => void }) {
  const { tr } = useI18n();
  const panel = useRef<HTMLDivElement>(null);
  const closeRef = useRef(close);
  closeRef.current = close;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const element = panel.current;
    element?.querySelector<HTMLElement>('input, button, textarea, select')?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeRef.current();
      if (event.key === 'Tab' && element) {
        const focusable = Array.from(element.querySelectorAll<HTMLElement>('button:not(:disabled), input, textarea, select, [tabindex="0"]'));
        const first = focusable[0], last = focusable.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', key);
    return () => { document.removeEventListener('keydown', key); previous?.focus(); };
  }, []);
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) close(); }}><div ref={panel} className="modal" role="dialog" aria-modal="true" aria-label={title}><button className="icon-button close-modal" aria-label={tr('close_dialog')} onClick={close}><X size={19} /></button><p className="eyebrow">{tr('daedalus_builder')}</p><h2>{title}</h2>{subtitle && <p className="muted">{subtitle}</p>}{children}</div></div>;
}

export default function App() {
  const { tr, language, setLanguage, translateError } = useI18n();
  const helpUrl = `${language === 'ko' ? '/help/ko' : '/help'}/tool-packs.html`;
  const [token, setToken] = useState(() => sessionStorage.getItem('factory-token') || (openAdmin ? 'development-open' : ''));
  const [loginToken, setLoginToken] = useState('');
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const locale = language === 'ko' ? 'ko-KR' : 'en-US';
  const [servers, setServers] = useState<ServerSummary[]>([]);
  const [serverId, setServerId] = useState('');
  const [serverModal, setServerModal] = useState(false);
  const [newServerName, setNewServerName] = useState('');
  const [deploymentOpen, setDeploymentOpen] = useState(false);
  const [policiesOpen, setPoliciesOpen] = useState(false);
  const [origins, setOrigins] = useState<ApiOrigin[]>([]);
  const [originDraft, setOriginDraft] = useState({ origin: '', description: '' });
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [openapiOpen, setOpenapiOpen] = useState(false);
  const [openapiUrl, setOpenapiUrl] = useState('');
  const [openapi, setOpenapi] = useState<{ title: string; version: string; base_url: string; operations: OpenAPIOperation[]; truncated: boolean } | null>(null);
  const [openapiBusy, setOpenapiBusy] = useState(false);
  const [pendingOperation, setPendingOperation] = useState<OpenAPIOperation | null>(null);
  const [packs, setPacks] = useState<Pack[]>([]);
  const [pendingPackTool, setPendingPackTool] = useState<{ pack: string; tool: PackTool } | null>(null);
  const [configText, setConfigText] = useState('{}');
  const [packEditor, setPackEditor] = useState<{ name: string; source: string; existing: boolean } | null>(null);
  const [sourceView, setSourceView] = useState<{ title: string; subtitle: string; source: string } | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState('');
  const [selected, setSelected] = useState('');
  const [editor, setEditor] = useState<Tool | null>(null);
  const [dirty, setDirty] = useState(false);
  const [bodyText, setBodyText] = useState('');
  const [nodes, setNodes] = useState<CardNode[]>([]);
  const [query, setQuery] = useState('');
  const [view, setView] = useState<'canvas' | 'list'>('canvas');
  const [connectionModal, setConnectionModal] = useState<Partial<Connection> | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [history, setHistory] = useState(false);
  const [testOpen, setTestOpen] = useState(false);
  const [argumentsText, setArgumentsText] = useState('{}');
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
  const [confirmWrite, setConfirmWrite] = useState(false);
  const [layoutSaving, setLayoutSaving] = useState(false);
  const flow = useReactFlow<CardNode>();
  const latest = useRef(workspace); latest.current = workspace;
  const positions = useRef<Record<string, { x: number; y: number }>>({});
  const role = workspace?.identity.role;
  const canAuthor = role === 'administrator' || role === 'author';
  const canPublish = role === 'administrator' || role === 'publisher';

  const api = useCallback(async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
    const scoped = path.startsWith('/servers') || !serverId ? path : `${path}${path.includes('?') ? '&' : '?'}server_id=${encodeURIComponent(serverId)}`;
    const response = await fetch(`/api${scoped}`, { ...options, headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...options.headers } });
    const value = response.status === 204 ? undefined : await response.json();
    if (!response.ok) {
      if (response.status === 401) { sessionStorage.removeItem('factory-token'); setToken(openAdmin ? 'development-open' : ''); setWorkspace(null); }
      throw new Error(typeof value.detail === 'string' ? value.detail : JSON.stringify(value.detail));
    }
    return value as T;
  }, [token, serverId]);

  const refresh = useCallback(async () => { const data = await api<Workspace>('/workspace'); setWorkspace(data); return data; }, [api]);
  async function loadPolicies() { const data = await api<ApiOrigin[]>('/policies/origins'); setOrigins(data); }
  async function addOrigin(e: FormEvent) { e.preventDefault(); await run('Adding policy', async () => { await api('/policies/origins', { method: 'POST', body: JSON.stringify({ ...originDraft, enabled: true }) }); setOriginDraft({ origin: '', description: '' }); await loadPolicies(); await refresh(); }); }
  async function removeOrigin(origin: ApiOrigin) { if (origin.bootstrap || !window.confirm(tr('confirm_remove_origin', { origin: origin.origin }))) return; await run('Removing policy', async () => { await api(`/policies/origins/${origin.id}`, { method: 'DELETE', headers: { 'If-Match': String(origin.revision) } }); await loadPolicies(); await refresh(); }); }
  useEffect(() => {
    if (!token) return;
    let alive = true;
    const load = () => Promise.all([api<Workspace>('/workspace'), api<ServerSummary[]>('/servers')]).then(([data, choices]) => { if (alive) { setWorkspace(data); setServers(choices); } }).catch(e => { if (alive) setError(translateError(e.message)); });
    void load(); const timer = setInterval(load, 2500);
    return () => { alive = false; clearInterval(timer); };
  }, [api, token]);
  // Built-in packs come from the runtime image and project packs from project storage; reload after edits.
  const loadPacks = useCallback(() => api<Pack[]>('/packs').then(setPacks), [api]);
  useEffect(() => { if (token) void loadPacks().catch(e => setError(e instanceof Error ? e.message : String(e))); }, [loadPacks, token]);

  async function run(name: string, action: () => Promise<void>) {
    setBusy(name); setError(''); setNotice('');
    try { await action(); } catch (e) { setError(translateError(e instanceof Error ? e.message : String(e))); }
    finally { setBusy(''); }
  }

  function status(tool: Tool) {
    if (!tool.enabled) return 'Excluded';
    if (workspace?.tools.find(t => t.id === tool.id)?.published) return 'Active';
    if (tool.tested) return 'Tested';
    if (tool.validated) return 'Validated';
    return 'Draft';
  }

  function packToolOf(tool: Tool | null): PackTool | undefined {
    return tool?.kind === 'python' ? packs.find(p => p.name === tool.pack)?.tools.find(t => t.function === tool.function) : undefined;
  }

  const choose = useCallback((id: string) => {
    if (dirty && id !== selected) { setError(tr('save_or_discard_your_inspector_changes')); return; }
    setSelected(id);
    const tool = latest.current?.tools.find(t => t.id === id) || null;
    setEditor(tool); setBodyText(tool?.body_schema ? JSON.stringify(tool.body_schema, null, 2) : ''); setConfigText(JSON.stringify(tool?.config ?? {}, null, 2)); setDirty(false);
    setTestOpen(false); setTestResult(null); setConfirmWrite(false);
  }, [dirty, selected]);

  useEffect(() => {
    if (!workspace) return;
    const saved = workspace.layout.positions;
    const make = (id: string, x: number, y: number, data: CardData): CardNode => ({ id, type: 'card', position: positions.current[id] || saved[id] || { x, y }, data: { ...data, selected: id === selected } });
    const visible = workspace.tools.filter(t => `${t.name} ${t.description}`.toLowerCase().includes(query.toLowerCase()));
    setNodes([
      make(workspace.server.id, 30, 120, { kind: 'server', title: workspace.server.name, subtitle: tr('agents_tool_catalog'), count: workspace.tools.length, status: workspace.server.runtime.ready && workspace.server.runtime.online ? 'Active' : 'Draft' }),
      ...visible.map((t, i) => make(t.id, 355, 40 + i * 190, { kind: 'tool', title: t.name, ...toolLabel(t), status: status(t) })),
      ...workspace.connections.map((c, i) => make(c.id, 685, 120 + i * 220, { kind: 'connection', title: c.name, subtitle: c.base_url, count: workspace.tools.filter(t => t.connection_id === c.id).length })),
    ]);
  }, [workspace, selected, query]);
  useEffect(() => { if (policiesOpen && token) void loadPolicies().catch(e => setError(e instanceof Error ? e.message : String(e))); }, [policiesOpen, token, serverId]);

  const edges = useMemo(() => workspace ? workspace.tools.filter(t => nodes.some(n => n.id === t.id)).flatMap(t => [
    { id: `server-${t.id}`, source: workspace.server.id, target: t.id, type: 'smoothstep', style: { stroke: '#abb6c5', strokeWidth: 1.5 } },
    // Python tools without a connection have no API edge.
    ...(t.connection_id ? [{ id: `api-${t.id}`, source: t.id, target: t.connection_id, type: 'smoothstep', style: { stroke: t.id === selected ? '#087f8c' : '#abb6c5', strokeWidth: t.id === selected ? 2 : 1.5 } }] : []),
  ]) : [], [workspace, nodes, selected]);

  function edit(patch: Partial<ToolSpec>) { if (editor) { setEditor({ ...editor, ...patch }); setDirty(true); } }
  function editParameter(index: number, patch: Partial<Parameter>) { if (editor) edit({ parameters: editor.parameters.map((p, i) => i === index ? { ...p, ...patch } : p) }); }

  async function saveEditor() {
    if (!editor) return;
    await run('Saving', async () => {
      const body = bodyText.trim() ? JSON.parse(bodyText) : null;
      const config = editor.kind === 'python' ? JSON.parse(configText.trim() || '{}') : editor.config;
      const saved = await api<Tool>(`/tools/${editor.id}`, { method: 'PATCH', headers: { 'If-Match': String(editor.revision) }, body: JSON.stringify({ ...specOf(editor), body_schema: body, config }) });
      setEditor(saved); setDirty(false); await refresh(); setNotice(tr('draft_saved_the_live_catalog_is'));
    });
  }

  async function removeNode(kind: 'tool' | 'connection', id: string, name: string, revision: number) {
    if (!canAuthor || busy || !window.confirm(tr('confirm_remove', { kind: tr(kind === 'tool' ? 'kind_tool' : 'kind_connection'), name }))) return;
    await run(`Removing ${kind}`, async () => {
      await api(`/${kind === 'tool' ? 'tools' : 'connections'}/${id}`, { method: 'DELETE', headers: { 'If-Match': String(revision) } });
      setSelected(''); setEditor(null); setBodyText(''); setTestOpen(false); setTestResult(null);
      await refresh();
      setNotice(tr('notice_removed', { name }));
    });
  }

  async function addTool(connectionId?: string, template?: string, position?: { x: number; y: number }) {
    if (!workspace) return;
    if (dirty) { setError(tr('save_or_discard_your_inspector_changes_2')); return; }
    const connection = connectionId || workspace.connections[0]?.id;
    if (!connection) { setConnectionModal({ name: '', base_url: workspace.allowed_api_origins[0] }); return; }
    const prefix = template === 'inventory' ? 'get_inventory_item' : template === 'ticket' ? 'get_ticket' : template === 'write' ? 'create_ticket' : 'new_tool';
    let name = prefix; let i = 2; while (workspace.tools.some(t => t.name === name)) name = `${prefix}_${i++}`;
    const parameterName = template === 'ticket' ? 'ticket_id' : 'item_id';
    const spec: ToolSpec = { name, description: template === 'inventory' ? 'Look up stock availability for an inventory item.' : template === 'ticket' ? 'Retrieve the current status of a support ticket.' : template === 'write' ? 'Create a new support ticket.' : '', connection_id: connection, method: template === 'write' ? 'POST' : 'GET', path: template === 'inventory' ? '/inventory/items/{item_id}' : template === 'ticket' ? '/tickets/{ticket_id}' : template === 'write' ? '/tickets' : '/', parameters: template && template !== 'write' ? [{ name: parameterName, location: 'path', type: 'string', required: true, description: 'The unique identifier' }] : [], body_schema: template === 'write' ? { type: 'object', properties: { title: { type: 'string', minLength: 1 } }, required: ['title'], additionalProperties: false } : null, effect: template === 'write' ? 'write' : 'read', enabled: true };
    await run('Adding tool', async () => {
      const tool = await api<Tool>('/tools', { method: 'POST', body: JSON.stringify(spec) });
      if (position) positions.current[tool.id] = position;
      const data = await refresh();
      setSelected(tool.id); setEditor(tool); setBodyText(tool.body_schema ? JSON.stringify(tool.body_schema, null, 2) : ''); setDirty(false); setTestOpen(false); setTestResult(null);
      if (position) await savePositions({ ...data.layout.positions, [tool.id]: position }, data.layout.revision);
      setTimeout(() => void flow.fitView({ duration: 350, padding: 0.2 }), 50);
    });
  }

  /** Create a tool record for one pack function. Tools that call an API need a connection; without one the connection modal opens first. */
  async function addPackTool(pack: string, tool: PackTool, position?: { x: number; y: number }, connectionId?: string) {
    const current = latest.current;
    if (!current) return;
    if (dirty) { setError(tr('save_or_discard_your_inspector_changes_2')); return; }
    const connection = tool.requires_connection ? connectionId || current.connections[0]?.id : null;
    if (tool.requires_connection && !connection) { setPendingPackTool({ pack, tool }); setConnectionModal({ name: '', base_url: current.allowed_api_origins[0] }); return; }
    let name = tool.function; let i = 2; while (current.tools.some(t => t.name === name)) name = `${tool.function}_${i++}`;
    const spec: ToolSpec = { name, description: tool.description, kind: 'python', pack, function: tool.function, connection_id: connection, method: 'GET', path: '/', parameters: [], body_schema: null, config: {}, effect: tool.effect, enabled: true };
    await run('Adding pack tool', async () => {
      const created = await api<Tool>('/tools', { method: 'POST', body: JSON.stringify(spec) });
      if (position) positions.current[created.id] = position;
      const data = await refresh();
      setSelected(created.id); setEditor(created); setBodyText(''); setConfigText('{}'); setDirty(false); setTestOpen(false); setTestResult(null);
      if (position) await savePositions({ ...data.layout.positions, [created.id]: position }, data.layout.revision);
      setTimeout(() => void flow.fitView({ duration: 350, padding: 0.2 }), 50);
    });
  }

  async function viewSource(packName: string, fn?: string) {
    await run('Loading source', async () => {
      const pack = await api<Pack>(`/packs/${packName}`);
      const tool = fn ? pack.tools.find(t => t.function === fn) : undefined;
      setSourceView({ title: tool ? `${packName}.${fn}` : tr('pack_title', { name: packName }), subtitle: pack.origin === 'builtin' ? tr('source_builtin') : tr('source_project'), source: (tool?.source ?? pack.source) || '' });
    });
  }

  async function openPackEditor(pack?: Pack) {
    if (!pack) { setPackEditor({ name: '', source: PACK_TEMPLATE, existing: false }); return; }
    await run('Loading pack', async () => { const full = await api<Pack>(`/packs/${pack.name}`); setPackEditor({ name: pack.name, source: full.source || '', existing: true }); });
  }

  async function savePack() {
    if (!packEditor) return;
    await run('Saving pack', async () => {
      const saved = await api<Pack>(`/packs/${packEditor.name.trim()}`, { method: 'PUT', body: JSON.stringify({ source: packEditor.source }) });
      setPackEditor(null); await loadPacks(); const data = await refresh();
      // Tools served by this pack lost their test evidence; show that on the selected tool too.
      if (editor && !dirty) setEditor(data.tools.find(t => t.id === editor.id) || null);
      setNotice(tr('notice_pack_saved', { name: saved.name, tools: saved.tools.map(t => t.function).join(', ') }));
    });
  }

  async function deletePack(pack: Pack) {
    if (!window.confirm(tr('confirm_delete_pack', { name: pack.name }))) return;
    await run('Deleting pack', async () => { await api(`/packs/${pack.name}`, { method: 'DELETE' }); await loadPacks(); setNotice(tr('notice_pack_deleted', { name: pack.name })); });
  }

  async function addAllPackTools(pack: Pack) {
    const current = latest.current;
    if (!current || dirty) { setError(tr('save_or_discard_your_inspector_changes_2')); return; }
    const missing = pack.tools.filter(t => !current.tools.some(existing => existing.kind === 'python' && existing.pack === pack.name && existing.function === t.function));
    const skipped = missing.filter(t => t.requires_connection && !current.connections.length);
    await run('Adding pack', async () => {
      for (const tool of missing.filter(t => !skipped.includes(t))) {
        await api<Tool>('/tools', { method: 'POST', body: JSON.stringify({ name: tool.function, description: tool.description, kind: 'python', pack: pack.name, function: tool.function, connection_id: tool.requires_connection ? current.connections[0].id : null, effect: tool.effect, enabled: true }) });
      }
      await refresh();
      setNotice(skipped.length ? tr('notice_pack_added_skipped', { count: missing.length - skipped.length, names: skipped.map(t => t.function).join(', ') }) : missing.length ? tr('notice_pack_added', { count: missing.length, pack: pack.name }) : tr('notice_pack_all_present', { pack: pack.name }));
      setTimeout(() => void flow.fitView({ duration: 350, padding: 0.2 }), 50);
    });
  }

  async function savePositions(value: Workspace['layout']['positions'], revision = latest.current?.layout.revision) {
    setLayoutSaving(true);
    try {
      const layout = await api<Workspace['layout']>('/layout', { method: 'PUT', headers: { 'If-Match': String(revision) }, body: JSON.stringify({ positions: value }) });
      setWorkspace(w => w ? { ...w, layout } : w); positions.current = {};
    } catch (e) { positions.current = {}; setError(String(e)); await refresh(); }
    finally { setLayoutSaving(false); }
  }

  const connect: OnConnect = edge => {
    if (!canAuthor || dirty || !workspace) return;
    const tool = workspace.tools.find(t => t.id === edge.source);
    if (!tool || !workspace.connections.some(c => c.id === edge.target)) return;
    void run('Connecting', async () => {
      const saved = await api<Tool>(`/tools/${tool.id}`, { method: 'PATCH', headers: { 'If-Match': String(tool.revision) }, body: JSON.stringify({ ...specOf(tool), connection_id: edge.target }) });
      if (selected === tool.id) setEditor(saved);
      await refresh(); setNotice(tr('connection_saved_to_the_draft_retest'));
    });
  };

  function openTest() {
    if (!editor) return;
    if (editor.kind === 'python') {
      const body: Record<string, unknown> = {};
      for (const p of packToolOf(editor)?.parameters ?? []) body[p.name] = p.type === 'boolean' ? true : p.type === 'string' ? (p.name === 'path' ? '/' : 'example') : 1;
      setArgumentsText(JSON.stringify(Object.keys(body).length ? { body } : {}, null, 2)); setTestOpen(true); setTestResult(null); setConfirmWrite(false);
      return;
    }
    const args: Record<string, Record<string, unknown>> = {};
    for (const p of editor.parameters) { args[p.location] ||= {}; args[p.location][p.name] = p.type === 'boolean' ? true : p.type === 'string' ? (p.name.includes('ticket') ? 'T-101' : 'SKU-001') : 1; }
    if (editor.body_schema) args.body = { title: 'Replace workstation' };
    setArgumentsText(JSON.stringify(args, null, 2)); setTestOpen(true); setTestResult(null); setConfirmWrite(false);
  }

  const closeConnection = useCallback(() => setConnectionModal(null), []);
  const closePreview = useCallback(() => setPreview(null), []);
  const closeHistory = useCallback(() => setHistory(false), []);
  async function createServer() { await run('Creating server', async () => { const server = await api<{ id: string }>('/servers', { method: 'POST', body: JSON.stringify({ name: newServerName }) }); setServerModal(false); setNewServerName(''); setServerId(server.id); }); }
  async function deploy(action = '') { await run(action ? `${action} deployment` : 'Deploying server', async () => { const path = action ? `/deployments/${action}` : '/deployments'; await api<Deployment>(path, { method: 'POST', body: JSON.stringify({ revision: workspace!.server.revision }) }); await refresh(); await api<ServerSummary[]>('/servers').then(setServers); }); }
  async function discoverOpenAPI() { await run('Loading OpenAPI', async () => { setOpenapiBusy(true); try { const result = await api<typeof openapi>('/openapi/preview', { method: 'POST', body: JSON.stringify({ url: openapiUrl }) }); setOpenapi(result); } finally { setOpenapiBusy(false); } }); }
  async function selectOperation(operation: OpenAPIOperation) {
    if (operation.supported === false) { setNotice(tr('notice_unsupported_method', { method: operation.method })); return; }
    const existing = workspace?.connections.find(c => c.base_url === openapi?.base_url);
    if (existing) { await addImportedTool(existing.id, operation); return; }
    setPendingOperation(operation); setConnectionModal({ name: openapi?.title || 'Imported API', base_url: openapi?.base_url || '' }); setOpenapiOpen(false);
  }
  async function addImportedTool(connectionId: string, operation: OpenAPIOperation) { await run('Adding imported tool', async () => { const { supported, ...toolSpec } = operation; void supported; await api('/tools', { method: 'POST', body: JSON.stringify({ ...toolSpec, connection_id: connectionId, enabled: true }) }); await refresh(); setOpenapiOpen(false); setPendingOperation(null); setNotice(tr('notice_imported', { name: operation.name })); }); }

  if (!workspace) return <main className="login-page"><div className="login-identity"><span className="brand-mark"><GitBranch size={25} /></span><span>daedalus<span className="brand-period">.</span></span></div><div className="login-grid"><section><p className="eyebrow">{tr('the_mcp_factory')}</p><h1>{tr('your_apis')}<br />{tr('your_tools')}<br /><span>{tr('one_connected_canvas')}</span></h1><p className="login-description">{tr('build_the_tools_your_agents_need')}</p><div className="login-flow"><span><Database size={20} /> {tr('connect')}</span><ChevronRight /><span><Braces size={20} /> {tr('build')}</span><ChevronRight /><span><Radio size={20} /> {tr('publish')}</span></div></section><form className="login-card" onSubmit={e => { e.preventDefault(); setError(''); sessionStorage.setItem('factory-token', loginToken); setToken(loginToken); }}><span className="icon-tile"><ShieldCheck size={26} /></span><h2>{tr('open_your_workspace')}</h2><p className="muted">{tr('use_a_management_token_from_your')} <code>.env</code> {tr('file_your_role_determines_what_you')}</p><label>{tr('management_token')}<input type="password" value={loginToken} onChange={e => setLoginToken(e.target.value)} placeholder={tr('paste_your_development_token')} required autoComplete="off" /></label>{error && <p className="error" role="alert">{error}</p>}<button className="button primary" type="submit" disabled={!loginToken || Boolean(token)}>{token ? <LoaderCircle className="spin" size={17} /> : <>{tr('enter_workspace')} <ArrowRight size={17} /></>}</button><p className="login-footnote"><span className="status-dot" /> {tr('local_development_token_authentication')}</p></form></div><footer>DAEDALUS / BUILDER <span>{tr('make_capability_tangible')}</span></footer></main>;

  const selectedConnection = workspace.connections.find(c => c.id === selected);
  const runtime = workspace.server.runtime;
  const activeCount = workspace.active_tools.length;
  const pendingRelease = workspace.releases.find(r => ['pending', 'applying'].includes(r.status));

  return <div className="application">
    <header className="topbar"><a className="brand" href="/" aria-label={tr('daedalus_home')}><span className="brand-mark"><GitBranch size={22} /></span>daedalus<span className="brand-period">.</span></a><span className="header-divider" /><span className="breadcrumb">{tr('project')} <ChevronRight size={14} /><strong>{tr('server_workspace')}</strong></span><select aria-label={tr('mcp_server_workspace')} className="server-picker" value={serverId || workspace.server.id} onChange={e => setServerId(e.target.value)}>{servers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select><button className="text-button" disabled={!canAuthor} onClick={() => setServerModal(true)}>{tr('new_server')}</button><span className="topbar-spacer" /><a className="icon-button" href={helpUrl} target="_blank" rel="noreferrer" title={tr('help_writing_a_tool_pack')} aria-label={tr('help')}><CircleHelp size={17} /></a><span className="environment-pill"><span className="status-dot" /> {openAdmin ? tr('open_local_admin') : tr('local_evaluation')}</span><select aria-label={tr('language')} className="language-picker" value={language} onChange={e => setLanguage(e.target.value as 'en' | 'ko')}><option value="en">English</option><option value="ko">한국어</option></select><button className="role-chip" title={tr('signed_in_as', { role: role ? tr(`role_${role}`) : '' })}><span className="avatar">{role?.slice(0, 1).toUpperCase()}</span>{role ? tr(`role_${role}`) : ''}</button>{!openAdmin && <button className="icon-button" title={tr('sign_out')} aria-label={tr('sign_out')} onClick={() => { sessionStorage.removeItem('factory-token'); setToken(''); setWorkspace(null); }}><LogOut size={17} /></button>}</header>
    <div className="workspace-heading"><div><div className="heading-eyebrow"><span>{tr('server_workspace_2')}</span><span className="slash">/</span><span>{workspace.server.id.slice(0, 8)}</span></div><h1>{workspace.server.name}<span className="version-pill">{workspace.server.active_release_id ? `v${workspace.releases.filter(r => ['active', 'superseded'].includes(r.status)).length}` : tr('unpublished')}</span></h1><p>{tr('design_test_publish_and_deploy_a')}</p></div><div className="heading-actions"><span className={`runtime-status ${runtime.online && runtime.ready ? 'online' : ''}`}><span className="status-dot" />{runtime.online && runtime.ready ? tr('server_online') : tr('server_offline')}</span><button className="button" onClick={() => setPoliciesOpen(true)}><ShieldCheck size={16} /> {tr('policies')}</button><button className="button" onClick={() => setDeploymentOpen(true)}><Radio size={16} /> {tr('deploy')}</button><button className="button" onClick={() => setHistory(true)}><History size={16} /> {tr('releases')}</button><button className="button primary" disabled={!canPublish || !!busy || !!pendingRelease || dirty} onClick={() => void run('Preparing review', async () => setPreview(await api<Preview>('/releases/preview')))}>{pendingRelease ? <LoaderCircle className="spin" size={16} /> : <Rocket size={16} />}{pendingRelease ? tr('applying_release') : tr('review_publish')}</button></div></div>
    {(error || notice || runtime.last_error) && <div className={`message-bar ${error || runtime.last_error ? 'failure' : ''}`} role={error ? 'alert' : 'status'}><span>{error || runtime.last_error || notice}</span><button className="icon-button" aria-label={tr('dismiss_message')} onClick={() => { setError(''); setNotice(''); }}><X size={15} /></button></div>}
    <div className={`workbench ${leftOpen ? '' : 'left-collapsed'} ${rightOpen ? '' : 'right-collapsed'}`}>
      <aside className="palette"><div className="palette-title"><span>{tr('building_blocks')}</span><Box size={15} /></div><div className="panel-toggle-row"><button className="icon-button" aria-label={tr('collapse_building_blocks')} onClick={() => setLeftOpen(false)}><PanelLeftClose size={16} /></button></div><div className="search-box"><Search size={15} /><input aria-label={tr('search_tools')} placeholder={tr('find_a_tool')} value={query} onChange={e => setQuery(e.target.value)} /><kbd>⌕</kbd></div><button className="openapi-button" disabled={!canAuthor} onClick={() => setOpenapiOpen(true)}><span><strong>{tr('import_openapi')}</strong><small>{tr('browse_available_api_operations')}</small></span><ArrowUpRight size={14} /></button><p className="section-label">{tr('components')}</p><button className="component-button" disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({}))} onClick={() => void addTool()}><span className="component-icon"><Braces size={18} /></span><span><strong>{tr('rest_tool')}</strong><small>{tr('turn_an_endpoint_into_a_tool')}</small></span><GripVertical size={15} className="muted" /></button><p className="section-label connection-label">{tr('connections')} <button className="icon-button" aria-label={tr('add_connection')} disabled={role !== 'administrator'} onClick={() => setConnectionModal({ name: '', base_url: workspace.allowed_api_origins[0] })}><Plus size={15} /></button></p>{workspace.connections.length === 0 ? <div className="empty-connections"><Unplug size={20} /><p>{tr('no_apis_connected_yet')}</p><button className="text-button" disabled={role !== 'administrator'} onClick={() => setConnectionModal({ name: '', base_url: workspace.allowed_api_origins[0] })}>{tr('add_a_connection')} <Plus size={13} /></button></div> : workspace.connections.map(c => <div className="connection-group" key={c.id}><button className="connection-heading" onClick={() => choose(c.id)}><Database size={15} /><strong>{c.name}</strong><ChevronDown size={13} /></button><div className="operation-list">{[{ key: 'inventory', label: tr('op_find_inventory'), method: 'GET' }, { key: 'ticket', label: tr('op_get_ticket'), method: 'GET' }, { key: 'write', label: tr('op_create_ticket'), method: 'POST' }].filter(() => c.base_url === 'http://mock-api:8080').map(op => <button key={op.key} disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({ connectionId: c.id, template: op.key }))} onClick={() => void addTool(c.id, op.key)} title={tr('click_or_drag_onto_the_canvas')}><span className={`method ${op.method.toLowerCase()}`}>{op.method}</span><span>{op.label}</span><Plus size={12} /></button>)}<button className="custom-operation" disabled={!canAuthor || !!busy} onClick={() => void addTool(c.id)}><Plus size={13} /> {tr('custom_operation')}</button></div></div>)}<p className="section-label connection-label">{tr('tool_packs')} <button className="icon-button" aria-label={tr('new_pack')} title={tr('write_a_new_tool_pack')} disabled={role !== 'administrator' || !!busy} onClick={() => void openPackEditor()}><Plus size={15} /></button></p>{packs.length === 0 ? <p className="field-help">{tr('no_tool_packs_yet_administrators_can')}</p> : packs.map(p => <div className="connection-group pack-group" key={p.name}><div className="connection-heading"><Package size={15} /><strong>{p.name}</strong>{p.origin === 'project' && <span className="tiny-tag">{tr('project_2')}</span>}<button className="text-button" disabled={!canAuthor || !!busy || !!p.error} onClick={() => void addAllPackTools(p)}>{tr('add_all')}</button></div><small className="pack-description">{p.error ? <span className="error">{tr('cannot_load', { error: p.error ?? '' })}</span> : p.description}</small><div className="pack-actions"><button className="text-button" disabled={!!busy} onClick={() => void viewSource(p.name)}><Braces size={12} /> {tr('view_code')}</button>{p.editable && <button className="text-button" disabled={role !== 'administrator' || !!busy} onClick={() => void openPackEditor(p)}><Settings2 size={12} /> {tr('edit')}</button>}{p.editable && <button className="text-button danger" disabled={role !== 'administrator' || !!busy} onClick={() => void deletePack(p)}><Trash2 size={12} /> {tr('delete')}</button>}</div><div className="operation-list">{p.tools.map(t => <button key={t.function} disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({ pack: p.name, tool: t }))} onClick={() => void addPackTool(p.name, t)} title={t.description}><span className={`method ${t.effect}`}>{t.effect.toUpperCase()}</span><span>{t.function}{t.requires_connection ? <small> {tr('uses_an_api')}</small> : null}</span><Plus size={12} /></button>)}</div></div>)}<div className="palette-bottom"><span className="icon-tile small"><CircleHelp size={17} /></span><strong>{tr('a_canvas_for_capabilities')}</strong><p>{tr('click_or_drag_a_tool_to')} <a href={helpUrl} target="_blank" rel="noreferrer">{tr('write_a_tool_pack')}</a>.</p><div className="legend"><span><i className="legend-line" /> {tr('relationship')}</span><span><i className="legend-dot" /> {tr('draft')}</span></div></div></aside>
      <main className="canvas-area"><div className="canvas-toolbar"><div className="view-switch"><button className={view === 'canvas' ? 'active' : ''} onClick={() => setView('canvas')}><LayoutGrid size={14} /> {tr('canvas')}</button><button className={view === 'list' ? 'active' : ''} onClick={() => setView('list')}><List size={15} /> {tr('list')}</button></div><button className="button small-button canvas-import-button" disabled={!canAuthor} onClick={() => setOpenapiOpen(true)}><Search size={14} />{tr('import_openapi')}</button>{!leftOpen && <button className="icon-button canvas-panel-toggle" aria-label={tr('show_building_blocks')} onClick={() => setLeftOpen(true)}><PanelLeftOpen size={16} /></button>}<span className="canvas-count">{tr('n_tools', { count: workspace.tools.length })} <span>·</span> {tr('n_connections', { count: workspace.connections.length })}</span><span className="toolbar-spacer" /><span className="save-indicator">{layoutSaving ? <LoaderCircle size={13} className="spin" /> : <CheckCheck size={14} />}{layoutSaving ? tr('saving_layout') : tr('layout_saved')}</span>{!rightOpen && <button className="icon-button canvas-panel-toggle" aria-label={tr('show_inspector')} onClick={() => setRightOpen(true)}><PanelRightOpen size={16} /></button>}</div>
        <div className={`graph-container ${testOpen ? 'with-test' : ''}`} onDragOver={e => { if (canAuthor) { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; } }} onDrop={e => { e.preventDefault(); if (!canAuthor) return; try { const data = JSON.parse(e.dataTransfer.getData('application/daedalus')); const at = flow.screenToFlowPosition({ x: e.clientX, y: e.clientY }); if (data.pack) void addPackTool(data.pack, data.tool, at); else void addTool(data.connectionId, data.template, at); } catch { setError(tr('drag_an_operation_from_the_building')); } }}>
          {view === 'canvas' ? <ReactFlow<CardNode> nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.23 }} minZoom={0.3} maxZoom={1.4} nodesDraggable={canAuthor && !layoutSaving} nodesConnectable={canAuthor && !dirty && !busy} deleteKeyCode={null} onNodesChange={(changes: NodeChange<CardNode>[]) => setNodes(n => applyNodeChanges(changes, n))} onNodeClick={(_, node) => choose(node.id)} onNodeDragStop={(_, node) => { positions.current[node.id] = node.position; void savePositions({ ...workspace.layout.positions, [node.id]: node.position }); }} onConnect={connect} isValidConnection={c => Boolean(workspace.tools.some(t => t.id === c.source) && workspace.connections.some(a => a.id === c.target))}><Background color="#d1d8df" gap={22} size={1} /><Controls showInteractive={false} /></ReactFlow> : <div className="tool-table"><div className="table-head"><span>{tr('tool')}</span><span>{tr('endpoint')}</span><span>{tr('status')}</span></div>{workspace.tools.filter(t => `${t.name} ${t.description}`.toLowerCase().includes(query.toLowerCase())).map(t => <button className={`table-row ${selected === t.id ? 'selected' : ''}`} key={t.id} onClick={() => choose(t.id)}><span><Braces size={16} /><strong>{t.name}</strong></span><span><b className={`method ${toolLabel(t).method.toLowerCase()}`}>{toolLabel(t).method}</b>{toolLabel(t).subtitle}</span><span className={`tool-status ${status(t).toLowerCase()}`}>{statusLabel(tr, status(t))}</span></button>)}</div>}
          {workspace.tools.length === 0 && <div className="canvas-welcome"><div className="welcome-symbol"><Network size={35} strokeWidth={1.4} /></div><p className="eyebrow">{tr('a_blank_canvas_endless_capability')}</p><h2>{tr('what_will_your_server_do')}</h2><p>{tr('bring_an_api_into_your_workspace')}<br />{tr('then_turn_its_operations_into_useful')}</p><button className="button primary" disabled={!!busy || (!workspace.connections.length ? role !== 'administrator' : !canAuthor)} onClick={() => workspace.connections.length ? void addTool(workspace.connections[0].id, 'inventory') : setConnectionModal({ name: 'Demo APIs', base_url: workspace.allowed_api_origins[0] })}><Plus size={16} />{workspace.connections.length ? tr('add_your_first_tool') : tr('connect_your_first_api')}</button><span className="welcome-hint">{tr('start_with_the_included_inventory_and')}</span></div>}
        </div>
        {testOpen && editor && <section className="test-drawer"><div className="drawer-heading"><FlaskConical size={17} /><strong>{tr('tool_playground')}</strong><span className="tiny-tag">{tr('isolated_draft_test')}</span><span className="toolbar-spacer" /><button className="icon-button" aria-label={tr('close_playground')} onClick={() => setTestOpen(false)}><X size={17} /></button></div><div className="test-columns"><div><label htmlFor="arguments">{tr('arguments')} <span>{tr('path_query_body')}</span></label><textarea id="arguments" spellCheck={false} value={argumentsText} onChange={e => setArgumentsText(e.target.value)} />{editor.effect === 'write' && <label className="checkbox-row"><input type="checkbox" checked={confirmWrite} onChange={e => setConfirmWrite(e.target.checked)} />{tr('i_authorize_this_live_write_to')}</label>}<button className="button primary small-button" disabled={!canAuthor || !!busy || dirty || (editor.effect === 'write' && !confirmWrite)} onClick={() => void run('Testing', async () => { const result = await api<Record<string, unknown>>(`/tools/${editor.id}/test`, { method: 'POST', headers: { 'If-Match': String(editor.revision) }, body: JSON.stringify({ arguments: JSON.parse(argumentsText), confirm_write: confirmWrite }) }); setTestResult(result); const w = await refresh(); setEditor(w.tools.find(t => t.id === editor.id) || null); })}>{busy === 'Testing' ? <LoaderCircle size={14} className="spin" /> : <Play size={14} />}{tr('run_test')}</button></div><div><label>{tr('result')} {testResult &&<span className={testResult.success ? 'success-text' : 'error'}>{testResult.success ? tr('passed') : tr('failed')} · {String(testResult.duration_ms)} ms</span>}</label>{testResult ? <pre className="result-output">{JSON.stringify(testResult.result || testResult.error, null, 2)}</pre> : <div className="result-placeholder"><Braces size={24} /><p>{tr('your_api_response_will_appear_here')}</p><small>{tr('tests_use_agentgateway_without_publishing_the')}</small></div>}</div></div></section>}
        <div className="canvas-footer"><span><GitBranch size={13} /> {tr('working_draft')}</span><span>{tr('layout_changes_never_affect_the_live')}</span><span className="toolbar-spacer" /><span>{tr('n_published_tools', { count: activeCount })}</span></div>
      </main>
      <aside className="inspector"><div className="inspector-heading"><Settings2 size={16} /><span>{tr('inspector')}</span>{editor && <span className={`tool-status ${dirty ? 'draft' : status(editor).toLowerCase()}`}>{dirty ? tr('unsaved') : statusLabel(tr, status(editor))}</span>}<button className="icon-button panel-heading-toggle" aria-label={tr('collapse_inspector')} onClick={() => setRightOpen(false)}><PanelRightClose size={16} /></button></div>
        {editor ? <><div className="inspector-body"><div className="inspector-intro"><span className="icon-tile small"><Braces size={20} /></span><div><h2>{tr('configure_tool')}</h2><p>{tr('shape_what_your_agent_can_do')}</p></div></div><fieldset disabled={!canAuthor || !!busy}><label>{tr('tool_name')}<input value={editor.name} onChange={e => edit({ name: e.target.value })} placeholder="get_inventory_item" /></label><label>{tr('description')}<textarea rows={3} value={editor.description} onChange={e => edit({ description: e.target.value })} placeholder={tr('explain_when_and_how_to_use')} /></label>{editor.kind === 'python' ? <><div className="form-divider" /><p className="section-label">{tr('python_tool')}</p><div className="detail-row"><span>{tr('pack_function')}</span><code>{editor.pack}.{editor.function}</code></div><button className="text-button" type="button" disabled={!!busy} onClick={() => void viewSource(editor.pack!, editor.function)}><Braces size={13} /> {tr('view_source')}</button><div className="detail-row"><span>{tr('side_effects')}</span><strong>{editor.effect === 'write' ? tr('write_or_change_data') : tr('read_data')}</strong></div>{packToolOf(editor)?.requires_connection ? <label>{tr('connection')}<select value={editor.connection_id ?? ''} onChange={e => edit({ connection_id: e.target.value })}><option value="" disabled>{tr('choose_a_connection')}</option>{workspace.connections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label> : <p className="field-help">{tr('this_tool_runs_in_the_python')}</p>}<div className="form-divider" /><p className="section-label">{tr('input_parameters')} <span>{packToolOf(editor)?.parameters.length ?? 0}</span></p>{packToolOf(editor)?.parameters.length ? packToolOf(editor)!.parameters.map(p => <div className="detail-row" key={p.name}><span>{p.name}{p.required ? '' : tr('optional_suffix')}</span><code>{p.type}</code></div>) : <p className="field-help">{tr('no_inputs_agents_call_this_tool')}</p>}<p className="field-help">{tr('inputs_are_defined_by_the_pack')} <code>body</code>.</p><label>{tr('configuration_json')}<textarea className="code-input" rows={4} spellCheck={false} value={configText} onChange={e => { setConfigText(e.target.value); setDirty(true); }} placeholder="{}" /></label></> : <><div className="form-divider" /><p className="section-label">{tr('api_operation')}</p><label>{tr('connection')}<select value={editor.connection_id ?? ''} onChange={e => edit({ connection_id: e.target.value })}>{workspace.connections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><div className="endpoint-input"><label>{tr('method')}<select value={editor.method} onChange={e => edit({ method: e.target.value as 'GET' | 'POST', effect: e.target.value === 'POST' ? 'write' : editor.effect })}><option>GET</option><option>POST</option></select></label><label>{tr('path')}<input value={editor.path} onChange={e => edit({ path: e.target.value })} placeholder="/items/{item_id}" /></label></div><label>{tr('side_effects')}<select value={editor.effect} onChange={e => edit({ effect: e.target.value as 'read' | 'write' })}><option value="read">{tr('read_data')}</option><option value="write">{tr('write_or_change_data')}</option></select></label><p className="field-help">{tr('classify_the_actual_api_behavior_write')}</p><div className="form-divider" /><div className="parameters-heading"><p className="section-label">{tr('input_parameters')} <span>{editor.parameters.length}</span></p><button className="icon-button" aria-label={tr('add_parameter')} onClick={() => edit({ parameters: [...editor.parameters, { name: `parameter_${editor.parameters.length + 1}`, location: 'query', type: 'string', required: false, description: '' }] })}><Plus size={16} /></button></div>{editor.parameters.map((p, i) => <div className="parameter-card" key={i}><div className="parameter-top"><input aria-label={tr('parameter_n_name', { n: i + 1 })} value={p.name} onChange={e => editParameter(i, { name: e.target.value })} /><button className="icon-button" aria-label={tr('remove_parameter_n', { n: i + 1 })} onClick={() => edit({ parameters: editor.parameters.filter((_, j) => i !== j) })}><Trash2 size={14} /></button></div><div className="parameter-options"><select aria-label={tr('parameter_n_location', { n: i + 1 })} value={p.location} onChange={e => editParameter(i, { location: e.target.value as 'path' | 'query', required: e.target.value === 'path' ? true : p.required })}><option value="path">{tr('path')}</option><option value="query">{tr('query')}</option></select><select aria-label={tr('parameter_n_type', { n: i + 1 })} value={p.type} onChange={e => editParameter(i, { type: e.target.value as Parameter['type'] })}>{['string', 'integer', 'number', 'boolean'].map(t => <option key={t}>{t}</option>)}</select><label className="checkbox-row"><input type="checkbox" checked={p.required} onChange={e => editParameter(i, { required: e.target.checked })} />{tr('required')}</label></div></div>)}{editor.parameters.length === 0 && <p className="field-help">{tr('no_parameters_yet_add_path_or')}</p>}{editor.method === 'POST' && <label>{tr('json_body_schema')}<textarea className="code-input" rows={7} value={bodyText} onChange={e => { setBodyText(e.target.value); setDirty(true); }} placeholder={'{"type":"object","properties":{}}'} /></label>}</>}<div className="form-divider" /><label className="checkbox-row include-tool"><input type="checkbox" checked={editor.enabled} onChange={e => edit({ enabled: e.target.checked })} /><span>{tr('include_in_next_release')}<small>{tr('excluding_a_tool_takes_effect_when')}</small></span></label></fieldset></div><div className="inspector-actions"><div><button className="button" disabled={!!busy || dirty || !canAuthor} onClick={() => void run('Validating', async () => { await api(`/tools/${editor.id}/validate`, { method: 'POST', headers: { 'If-Match': String(editor.revision) } }); const w = await refresh(); setEditor(w.tools.find(t => t.id === editor.id) || null); setNotice(tr('tool_definition_validated_run_a_test')); })}><Check size={15} />{tr('validate')}</button><button className="button" disabled={!!busy || dirty || !canAuthor} onClick={openTest}><FlaskConical size={15} />{tr('test_tool')}</button></div><button className="button primary full-width" disabled={!dirty || !!busy || !canAuthor} onClick={() => void saveEditor()}>{busy === 'Saving' ? <LoaderCircle className="spin" size={16} /> : <Save size={16} />}{tr('save_draft')}</button>{dirty && <button className="text-button discard" onClick={() => { setDirty(false); const tool = workspace.tools.find(t => t.id === editor.id)!; setEditor(tool); setBodyText(tool.body_schema ? JSON.stringify(tool.body_schema, null, 2) : ''); setConfigText(JSON.stringify(tool.config ?? {}, null, 2)); }}>{tr('discard_changes')}</button>}<button className="text-button danger" disabled={!!busy || dirty || !canAuthor} onClick={() => void removeNode('tool', editor.id, editor.name, editor.revision)}><Trash2 size={14} />{tr('remove_tool')}</button></div></> : selectedConnection ? <div className="inspector-body"><span className="icon-tile"><Database size={26} /></span><h2>{selectedConnection.name}</h2><p className="muted">{tr('a_reusable_connection_for_your_rest')}</p><label>{tr('approved_base_url')}<code className="endpoint-display">{selectedConnection.base_url}</code></label><div className="detail-row"><span>{tr('authentication')}</span><strong>{tr('none_evaluation')}</strong></div><div className="detail-row"><span>{tr('revision')}</span><strong>{selectedConnection.revision}</strong></div><button className="button full-width" disabled={role !== 'administrator'} onClick={() => setConnectionModal(selectedConnection)}><Settings2 size={16} />{tr('edit_connection')}</button><button className="text-button danger" disabled={!!busy || !canAuthor} onClick={() => void removeNode('connection', selectedConnection.id, selectedConnection.name, selectedConnection.revision)}><Trash2 size={14} />{tr('remove_connection')}</button><p className="field-help">{tr('changing_a_connection_requires_affected_tools')}</p></div> : <div className="inspector-overview"><span className="icon-tile"><Server size={25} /></span><h2>{tr('your_server_at_a_glance')}</h2><p>{tr('choose_a_tool_or_connection_on')}</p><div className="overview-stat"><span>{tr('draft_tools')}</span><strong>{workspace.tools.length}</strong></div><div className="overview-stat"><span>{tr('published_tools')}</span><strong>{activeCount}</strong></div><div className="overview-stat"><span>{tr('connections_2')}</span><strong>{workspace.connections.length}</strong></div><div className="overview-endpoint"><p className="section-label">{tr('mcp_endpoint')}</p><code>{workspace.server.mcp_url}</code><small>{tr('use_your_separate_mcp_token_to')}</small></div><div className="workflow-steps"><p className="section-label">{tr('from_idea_to_capability')}</p>{[tr('step_connect'), tr('step_configure'), tr('step_validate'), tr('step_review')].map((label, i) => <div key={label}><span>{i + 1}</span>{label}</div>)}</div></div>}
      </aside>
    </div>
    {policiesOpen && <Modal title={tr('api_access_policies')} subtitle={tr('policies_subtitle')} close={() => setPoliciesOpen(false)}><div className="policy-list">{origins.map(origin => <div className="policy-row" key={origin.id}><div><strong>{origin.origin}</strong><small>{origin.description || tr('no_description')}{origin.bootstrap ? ' · bootstrap' : ''}</small></div>{origin.bootstrap ? <span className="tiny-tag">{tr('environment')}</span> : <button className="icon-button" aria-label={tr('remove_x', { name: origin.origin })} onClick={() => void removeOrigin(origin)}><Trash2 size={15} /></button>}</div>)}</div><form onSubmit={addOrigin} className="policy-form"><label>{tr('api_origin')}<input required type="url" value={originDraft.origin} onChange={e => setOriginDraft({ ...originDraft, origin: e.target.value })} placeholder="https://api.example.com" /></label><label>{tr('description')}<input value={originDraft.description} onChange={e => setOriginDraft({ ...originDraft, description: e.target.value })} placeholder={tr('customer_support_api')} /></label><button className="button primary full-width" disabled={!!busy}><Plus size={15} />{tr('approve_origin')}</button></form><p className="field-help">{tr('origins_must_be_scheme_and_host')}</p></Modal>}{openapiOpen && <Modal title={tr('import_an_openapi_document')} subtitle={tr('openapi_subtitle')} close={() => setOpenapiOpen(false)}><form onSubmit={e => { e.preventDefault(); void discoverOpenAPI(); }}><label>{tr('swagger_or_openapi_url')}<input autoFocus required type="url" value={openapiUrl} onChange={e => setOpenapiUrl(e.target.value)} placeholder="https://api.example.com/openapi.json" /></label><p className="field-help">{tr('the_builder_fetches_the_document_server')}</p><button className="button primary full-width" disabled={openapiBusy || !openapiUrl.trim()} type="submit">{openapiBusy ? <LoaderCircle className="spin" size={16} /> : <Search size={16} />}{tr('find_api_operations')}</button></form>{openapi && <><div className="detail-row"><span>{openapi.title} {openapi.version && `· v${openapi.version}`}</span><code>{openapi.base_url}</code></div>{openapi.truncated && <p className="field-help">{tr('showing_the_first_200_operations')}</p>}<div className="openapi-results">{openapi.operations.length ? openapi.operations.map((operation, index) => <button className="openapi-operation" disabled={operation.supported === false} key={`${operation.method}-${operation.path}-${index}`} onClick={() => void selectOperation(operation)}><b className={`method ${operation.method.toLowerCase()}`}>{operation.method}</b><code>{operation.path}</code><small>{operation.supported === false ? tr('not_supported_profile') : operation.name}</small>{operation.supported === false ? <span className="tiny-tag">{tr('preview')}</span> : <Plus size={14} />}</button>) : <p className="openapi-empty">{tr('no_operations_were_found')}</p>}</div></>}</Modal>}
    {connectionModal && <Modal title={connectionModal.id ? tr('edit_api_connection') : tr('connect_an_api')} subtitle={tr('connection_subtitle')} close={closeConnection}><form onSubmit={(e: FormEvent) => { e.preventDefault(); void run('Saving connection', async () => { const data = { name: connectionModal.name, base_url: connectionModal.base_url, auth_mode: 'none' }; const saved = await api<Connection>(connectionModal.id ? `/connections/${connectionModal.id}` : '/connections', { method: connectionModal.id ? 'PATCH' : 'POST', headers: connectionModal.id ? { 'If-Match': String(connectionModal.revision) } : {}, body: JSON.stringify(data) }); setConnectionModal(null); setSelected(saved.id); setEditor(null); await refresh(); if (pendingOperation) await addImportedTool(saved.id, pendingOperation); else if (pendingPackTool) { const pending = pendingPackTool; setPendingPackTool(null); await addPackTool(pending.pack, pending.tool, undefined, saved.id); } else setNotice(tr('api_connection_saved_add_an_operation')); }); }}><label>{tr('connection_name')}<input autoFocus required maxLength={80} value={connectionModal.name || ''} onChange={e => setConnectionModal({ ...connectionModal, name: e.target.value })} placeholder={tr('inventory_api')} /></label><label>{tr('base_url')}<input required value={connectionModal.base_url || ''} onChange={e => setConnectionModal({ ...connectionModal, base_url: e.target.value })} placeholder="http://mock-api:8080" /></label><p className="field-help">{tr('approved_origins', { origins: workspace.allowed_api_origins.join(', ') })}</p><div className="inline-info"><ShieldCheck size={19} /><p>{tr('this_first_profile_connects_to_apis')}</p></div>{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy} type="submit">{busy ? <LoaderCircle className="spin" size={16} /> : <Plus size={16} />}{tr('save_connection')}</button></form></Modal>}
    {sourceView && <Modal title={sourceView.title} subtitle={sourceView.subtitle} close={() => setSourceView(null)}><pre className="result-output source-view">{sourceView.source}</pre></Modal>}
    {packEditor && <Modal title={packEditor.existing ? tr('edit_pack_title', { name: packEditor.name }) : tr('new_tool_pack')} subtitle={tr('pack_editor_subtitle')} close={() => setPackEditor(null)}><form onSubmit={e => { e.preventDefault(); void savePack(); }}>{!packEditor.existing && <label>{tr('pack_name')}<input autoFocus required pattern="[a-z][a-z0-9_]{0,29}" title={tr('lowercase_letters_digits_and_underscores_starts')} value={packEditor.name} onChange={e => setPackEditor({ ...packEditor, name: e.target.value })} placeholder="hdfs_files" /></label>}<label>{tr('python_source')}<textarea className="code-input source-editor" rows={18} spellCheck={false} value={packEditor.source} onChange={e => setPackEditor({ ...packEditor, source: e.target.value })} /></label><p className="field-help">{tr('each_tool_is_a_function_decorated')} <code>@pack_tool(effect=…, requires_connection=…)</code> {tr('whose_first_parameter_is')} <code>ctx: ToolContext</code>. Typed parameters (str, int, float, bool) become the tool's inputs; the docstring becomes its description. <a href={helpUrl} target="_blank" rel="noreferrer">{tr('read_the_how_to_guide')}</a>.</p>{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy || !packEditor.name.trim() || !packEditor.source.trim()} type="submit">{busy === 'Saving pack' ? <LoaderCircle className="spin" size={16} /> : <Save size={16} />}{tr('save_pack')}</button></form></Modal>}
    {serverModal && <Modal title={tr('create_mcp_server')} subtitle={tr('server_subtitle')} close={() => setServerModal(false)}><form onSubmit={e => { e.preventDefault(); void createServer(); }}><label>{tr('server_name')}<input autoFocus required value={newServerName} onChange={e => setNewServerName(e.target.value)} placeholder={tr('customer_support_mcp')} /></label><button className="button primary full-width" disabled={!!busy || !newServerName.trim()} type="submit"><Plus size={16} />{tr('create_server')}</button></form></Modal>}
    {deploymentOpen && <Modal title={tr('deployment_monitoring')} subtitle={tr('deployment_subtitle')} close={() => setDeploymentOpen(false)}><div className="deployment-card"><div><span className={`tool-status ${workspace.deployment.status}`}>{workspace.deployment.status.replaceAll('_', ' ')}</span><strong>{workspace.deployment.application_name || tr('application_not_provisioned')}</strong></div><p className="muted">{tr('provider_line', { provider: workspace.deployment.provider })} {workspace.deployment.message || tr('publish_then_deploy')}</p><div className="detail-row"><span>{tr('active_release')}</span><code>{workspace.server.active_release_id?.slice(0, 8) || tr('none')}</code></div><div className="detail-row"><span>{tr('deployed_release')}</span><code>{workspace.deployment.deployed_release_id?.slice(0, 8) || tr('none')}</code></div>{workspace.deployment.endpoint && <div className="detail-row"><span>{tr('endpoint_2')}</span><code>{workspace.deployment.endpoint}</code></div>}<div className="deployment-actions"><button className="button primary" disabled={!canPublish || !!busy || !workspace.server.active_release_id} onClick={() => void deploy()}><Rocket size={15} />{tr('deploy_release')}</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('refresh')}>{tr('refresh')}</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('stop')}>{tr('stop')}</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('delete')}>{tr('delete')}</button></div><p className="field-help">{tr('gateway_health_appears_in_the_workspace')}</p></div></Modal>}
    {preview && <Modal title={tr('review_your_release')} subtitle={tr('preview_subtitle')} close={closePreview}><div className="release-diff">{(['added', 'changed', 'removed'] as const).map(kind => <div key={kind}><p className="section-label">{tr(`diff_${kind}`)} <span>{preview[kind].length}</span></p>{preview[kind].length ? preview[kind].map(name => <div className={`diff-item ${kind}`} key={name}>{kind === 'added' ? <Plus size={15} /> : kind === 'removed' ? <X size={15} /> : <Settings2 size={15} />}<code>{name}</code></div>) : <p className="field-help">{tr('no_kind_tools', { kind: tr(`diff_${kind}`) })}</p>}</div>)}</div>{preview.problems.length > 0 && <div className="publish-problems"><strong>{tr('before_you_publish')}</strong><ul>{preview.problems.map(p => <li key={p}>{p}</li>)}</ul></div>}{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy || !!preview.problems.length || !canPublish} onClick={() => void run('Publishing', async () => { await api('/releases', { method: 'POST', body: JSON.stringify({ revision: preview.revision }) }); setPreview(null); await refresh(); setNotice(tr('release_submitted_waiting_for_the_server')); })}>{busy === 'Publishing' ? <LoaderCircle className="spin" size={16} /> : <Rocket size={16} />}{tr('publish_release')}</button></Modal>}
    {history && <Modal title={tr('release_history')} subtitle={tr('history_subtitle')} close={closeHistory}><div className="runtime-detail"><Radio size={16} /><span>{runtime.online && runtime.ready ? tr('gateway_ready') : tr('gateway_unavailable')}</span>{runtime.gateway_pid && <code>PID {runtime.gateway_pid}</code>}</div>{workspace.releases.length === 0 ? <div className="history-empty"><History size={30} /><p>{tr('your_first_release_starts_here')}</p><small>{tr('validate_and_test_a_tool_then')}</small></div> : <div className="release-list">{workspace.releases.map(r => <article key={r.id}><div><span className={`tool-status ${r.status}`}>{r.status}</span><code>{r.id.slice(0, 8)}</code><time>{new Date(r.created_at).toLocaleString(locale)}</time></div><p>{r.tool_names.length ? r.tool_names.join(', ') : tr('empty_catalog')}</p>{r.error && <p className="error">{r.error}</p>}{r.status === 'superseded' && <button className="text-button" disabled={!canPublish || !!busy || !!pendingRelease} onClick={() => void run('Restoring', async () => { await api('/releases/rollback', { method: 'POST', body: JSON.stringify({ revision: workspace.server.revision, release_id: r.id }) }); await refresh(); setNotice(tr('restore_submitted_for_server_verification')); })}><Undo2 size={14} />{tr('restore_this_release')}</button>}</article>)}</div>}{error && <p className="error" role="alert">{error}</p>}</Modal>}
  </div>;
}
