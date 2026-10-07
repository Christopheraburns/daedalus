import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { ReactFlow, Background, Controls, Handle, Position, applyNodeChanges, useReactFlow, type Node, type NodeProps, type OnConnect, type NodeChange } from '@xyflow/react';
import { ArrowRight, ArrowUpRight, Box, Braces, Check, CheckCheck, ChevronDown, ChevronRight, CircleHelp, Database, FlaskConical, GitBranch, GripVertical, History, LayoutGrid, List, LoaderCircle, LogOut, Network, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, Play, Plus, Radio, Rocket, Save, Search, Server, Settings2, ShieldCheck, Trash2, Undo2, Unplug, X } from 'lucide-react';
import { type ApiOrigin, type Connection, type Deployment, type OpenAPIOperation, type Parameter, type Preview, type ServerSummary, type Tool, type ToolSpec, type Workspace, specOf } from './types';

type CardData = { kind: 'server' | 'tool' | 'connection'; title: string; subtitle: string; status?: string; method?: string; count?: number; selected?: boolean; [key: string]: unknown };
type CardNode = Node<CardData>;
const openAdmin = import.meta.env.VITE_FACTORY_OPEN_ADMIN === 'true';

function CanvasCard({ data }: NodeProps<CardNode>) {
  const Icon = data.kind === 'server' ? Server : data.kind === 'connection' ? Database : Braces;
  return <div className={`canvas-card ${data.kind} ${data.selected ? 'selected' : ''}`}>
    {data.kind !== 'server' && <Handle type="target" position={Position.Left} />}
    <div className="card-kicker">{data.kind === 'server' ? 'MCP SERVER' : data.kind === 'connection' ? 'API CONNECTION' : 'REST TOOL'}<span className={`status-dot ${data.status === 'Active' || data.status === 'Tested' ? 'green' : ''}`} /></div>
    <div className="card-title"><span className="node-icon"><Icon size={17} /></span><strong>{data.title}</strong></div>
    <div className="card-subtitle">{data.method && <span className={`method ${data.method.toLowerCase()}`}>{data.method}</span>}{data.subtitle}</div>
    <div className="card-footer"><span>{data.kind === 'tool' ? data.status : `${data.count ?? 0} tools`}</span>{data.kind === 'tool' ? <ChevronRight size={14} /> : <span className="tiny-tag">{data.kind === 'server' ? 'agentgateway' : 'REST / JSON'}</span>}</div>
    {data.kind !== 'connection' && <Handle type="source" position={Position.Right} />}
  </div>;
}
const nodeTypes = { card: CanvasCard };

function Modal({ title, subtitle, children, close }: { title: string; subtitle?: string; children: ReactNode; close: () => void }) {
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
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) close(); }}><div ref={panel} className="modal" role="dialog" aria-modal="true" aria-label={title}><button className="icon-button close-modal" aria-label="Close dialog" onClick={close}><X size={19} /></button><p className="eyebrow">DAEDALUS BUILDER</p><h2>{title}</h2>{subtitle && <p className="muted">{subtitle}</p>}{children}</div></div>;
}

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem('factory-token') || (openAdmin ? 'development-open' : ''));
  const [loginToken, setLoginToken] = useState('');
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
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
  async function removeOrigin(origin: ApiOrigin) { if (origin.bootstrap || !window.confirm(`Remove ${origin.origin} from the approved API origins?`)) return; await run('Removing policy', async () => { await api(`/policies/origins/${origin.id}`, { method: 'DELETE', headers: { 'If-Match': String(origin.revision) } }); await loadPolicies(); await refresh(); }); }
  useEffect(() => {
    if (!token) return;
    let alive = true;
    const load = () => Promise.all([api<Workspace>('/workspace'), api<ServerSummary[]>('/servers')]).then(([data, choices]) => { if (alive) { setWorkspace(data); setServers(choices); } }).catch(e => { if (alive) setError(e.message); });
    void load(); const timer = setInterval(load, 2500);
    return () => { alive = false; clearInterval(timer); };
  }, [api, token]);

  async function run(name: string, action: () => Promise<void>) {
    setBusy(name); setError(''); setNotice('');
    try { await action(); } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(''); }
  }

  function status(tool: Tool) {
    if (!tool.enabled) return 'Excluded';
    if (workspace?.tools.find(t => t.id === tool.id)?.published) return 'Active';
    if (tool.tested) return 'Tested';
    if (tool.validated) return 'Validated';
    return 'Draft';
  }

  const choose = useCallback((id: string) => {
    if (dirty && id !== selected) { setError('Save or discard your inspector changes before selecting another item.'); return; }
    setSelected(id);
    const tool = latest.current?.tools.find(t => t.id === id) || null;
    setEditor(tool); setBodyText(tool?.body_schema ? JSON.stringify(tool.body_schema, null, 2) : ''); setDirty(false);
    setTestOpen(false); setTestResult(null); setConfirmWrite(false);
  }, [dirty, selected]);

  useEffect(() => {
    if (!workspace) return;
    const saved = workspace.layout.positions;
    const make = (id: string, x: number, y: number, data: CardData): CardNode => ({ id, type: 'card', position: positions.current[id] || saved[id] || { x, y }, data: { ...data, selected: id === selected } });
    const visible = workspace.tools.filter(t => `${t.name} ${t.description}`.toLowerCase().includes(query.toLowerCase()));
    setNodes([
      make(workspace.server.id, 30, 120, { kind: 'server', title: workspace.server.name, subtitle: 'Your agent’s tool catalog', count: workspace.tools.length, status: workspace.server.runtime.ready && workspace.server.runtime.online ? 'Active' : 'Draft' }),
      ...visible.map((t, i) => make(t.id, 355, 40 + i * 190, { kind: 'tool', title: t.name, subtitle: t.path, method: t.method, status: status(t) })),
      ...workspace.connections.map((c, i) => make(c.id, 685, 120 + i * 220, { kind: 'connection', title: c.name, subtitle: c.base_url, count: workspace.tools.filter(t => t.connection_id === c.id).length })),
    ]);
  }, [workspace, selected, query]);
  useEffect(() => { if (policiesOpen && token) void loadPolicies().catch(e => setError(e instanceof Error ? e.message : String(e))); }, [policiesOpen, token, serverId]);

  const edges = useMemo(() => workspace ? workspace.tools.filter(t => nodes.some(n => n.id === t.id)).flatMap(t => [
    { id: `server-${t.id}`, source: workspace.server.id, target: t.id, type: 'smoothstep', style: { stroke: '#abb6c5', strokeWidth: 1.5 } },
    { id: `api-${t.id}`, source: t.id, target: t.connection_id, type: 'smoothstep', style: { stroke: t.id === selected ? '#087f8c' : '#abb6c5', strokeWidth: t.id === selected ? 2 : 1.5 } },
  ]) : [], [workspace, nodes, selected]);

  function edit(patch: Partial<ToolSpec>) { if (editor) { setEditor({ ...editor, ...patch }); setDirty(true); } }
  function editParameter(index: number, patch: Partial<Parameter>) { if (editor) edit({ parameters: editor.parameters.map((p, i) => i === index ? { ...p, ...patch } : p) }); }

  async function saveEditor() {
    if (!editor) return;
    await run('Saving', async () => {
      const body = bodyText.trim() ? JSON.parse(bodyText) : null;
      const saved = await api<Tool>(`/tools/${editor.id}`, { method: 'PATCH', headers: { 'If-Match': String(editor.revision) }, body: JSON.stringify({ ...specOf(editor), body_schema: body }) });
      setEditor(saved); setDirty(false); await refresh(); setNotice('Draft saved. The live catalog is unchanged.');
    });
  }

  async function removeNode(kind: 'tool' | 'connection', id: string, name: string, revision: number) {
    if (!canAuthor || busy || !window.confirm(`Remove ${kind} “${name}” from this workspace?`)) return;
    await run(`Removing ${kind}`, async () => {
      await api(`/${kind === 'tool' ? 'tools' : 'connections'}/${id}`, { method: 'DELETE', headers: { 'If-Match': String(revision) } });
      setSelected(''); setEditor(null); setBodyText(''); setTestOpen(false); setTestResult(null);
      await refresh();
      setNotice(`${name} removed from the canvas.`);
    });
  }

  async function addTool(connectionId?: string, template?: string, position?: { x: number; y: number }) {
    if (!workspace) return;
    if (dirty) { setError('Save or discard your inspector changes first.'); return; }
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
      await refresh(); setNotice('Connection saved to the draft. Retest before publishing.');
    });
  };

  function openTest() {
    if (!editor) return;
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
    if (operation.supported === false) { setNotice(`${operation.method} operations are visible for discovery but are not supported by the current tool profile.`); return; }
    const existing = workspace?.connections.find(c => c.base_url === openapi?.base_url);
    if (existing) { await addImportedTool(existing.id, operation); return; }
    setPendingOperation(operation); setConnectionModal({ name: openapi?.title || 'Imported API', base_url: openapi?.base_url || '' }); setOpenapiOpen(false);
  }
  async function addImportedTool(connectionId: string, operation: OpenAPIOperation) { await run('Adding imported tool', async () => { const { supported, ...toolSpec } = operation; void supported; await api('/tools', { method: 'POST', body: JSON.stringify({ ...toolSpec, connection_id: connectionId, enabled: true }) }); await refresh(); setOpenapiOpen(false); setPendingOperation(null); setNotice(`${operation.name} added as a draft tool.`); }); }

  if (!workspace) return <main className="login-page"><div className="login-identity"><span className="brand-mark"><GitBranch size={25} /></span><span>daedalus<span className="brand-period">.</span></span></div><div className="login-grid"><section><p className="eyebrow">THE MCP FACTORY</p><h1>Your APIs.<br />Your tools.<br /><span>One connected canvas.</span></h1><p className="login-description">Build the tools your agents need. Connect an API, shape its capabilities, and publish with confidence.</p><div className="login-flow"><span><Database size={20} /> Connect</span><ChevronRight /><span><Braces size={20} /> Build</span><ChevronRight /><span><Radio size={20} /> Publish</span></div></section><form className="login-card" onSubmit={e => { e.preventDefault(); setError(''); sessionStorage.setItem('factory-token', loginToken); setToken(loginToken); }}><span className="icon-tile"><ShieldCheck size={26} /></span><h2>Open your workspace</h2><p className="muted">Use a management token from your local <code>.env</code> file. Your role determines what you can change.</p><label>Management token<input type="password" value={loginToken} onChange={e => setLoginToken(e.target.value)} placeholder="Paste your development token" required autoComplete="off" /></label>{error && <p className="error" role="alert">{error}</p>}<button className="button primary" type="submit" disabled={!loginToken || Boolean(token)}>{token ? <LoaderCircle className="spin" size={17} /> : <>Enter workspace <ArrowRight size={17} /></>}</button><p className="login-footnote"><span className="status-dot" /> Local development · Token authentication</p></form></div><footer>DAEDALUS / BUILDER <span>Make capability tangible.</span></footer></main>;

  const selectedConnection = workspace.connections.find(c => c.id === selected);
  const runtime = workspace.server.runtime;
  const activeCount = workspace.active_tools.length;
  const pendingRelease = workspace.releases.find(r => ['pending', 'applying'].includes(r.status));

  return <div className="application">
    <header className="topbar"><a className="brand" href="/" aria-label="Daedalus home"><span className="brand-mark"><GitBranch size={22} /></span>daedalus<span className="brand-period">.</span></a><span className="header-divider" /><span className="breadcrumb">Project <ChevronRight size={14} /><strong>Server workspace</strong></span><select aria-label="MCP server workspace" className="server-picker" value={serverId || workspace.server.id} onChange={e => setServerId(e.target.value)}>{servers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select><button className="text-button" disabled={!canAuthor} onClick={() => setServerModal(true)}>New server</button><span className="topbar-spacer" /><span className="environment-pill"><span className="status-dot" /> {openAdmin ? 'Open local admin' : 'Local evaluation'}</span><button className="role-chip" title={`Signed in as ${role}`}><span className="avatar">{role?.slice(0, 1).toUpperCase()}</span>{role}</button>{!openAdmin && <button className="icon-button" title="Sign out" aria-label="Sign out" onClick={() => { sessionStorage.removeItem('factory-token'); setToken(''); setWorkspace(null); }}><LogOut size={17} /></button>}</header>
    <div className="workspace-heading"><div><div className="heading-eyebrow"><span>SERVER WORKSPACE</span><span className="slash">/</span><span>{workspace.server.id.slice(0, 8)}</span></div><h1>{workspace.server.name}<span className="version-pill">{workspace.server.active_release_id ? `v${workspace.releases.filter(r => ['active', 'superseded'].includes(r.status)).length}` : 'Unpublished'}</span></h1><p>Design, test, publish, and deploy a dedicated MCP server application.</p></div><div className="heading-actions"><span className={`runtime-status ${runtime.online && runtime.ready ? 'online' : ''}`}><span className="status-dot" />{runtime.online && runtime.ready ? 'Server online' : 'Server offline'}</span><button className="button" onClick={() => setPoliciesOpen(true)}><ShieldCheck size={16} /> Policies</button><button className="button" onClick={() => setDeploymentOpen(true)}><Radio size={16} /> Deploy</button><button className="button" onClick={() => setHistory(true)}><History size={16} /> Releases</button><button className="button primary" disabled={!canPublish || !!busy || !!pendingRelease || dirty} onClick={() => void run('Preparing review', async () => setPreview(await api<Preview>('/releases/preview')))}>{pendingRelease ? <LoaderCircle className="spin" size={16} /> : <Rocket size={16} />}{pendingRelease ? 'Applying release' : 'Review & publish'}</button></div></div>
    {(error || notice || runtime.last_error) && <div className={`message-bar ${error || runtime.last_error ? 'failure' : ''}`} role={error ? 'alert' : 'status'}><span>{error || runtime.last_error || notice}</span><button className="icon-button" aria-label="Dismiss message" onClick={() => { setError(''); setNotice(''); }}><X size={15} /></button></div>}
    <div className={`workbench ${leftOpen ? '' : 'left-collapsed'} ${rightOpen ? '' : 'right-collapsed'}`}>
      <aside className="palette"><div className="palette-title"><span>BUILDING BLOCKS</span><Box size={15} /></div><div className="panel-toggle-row"><button className="icon-button" aria-label="Collapse building blocks" onClick={() => setLeftOpen(false)}><PanelLeftClose size={16} /></button></div><div className="search-box"><Search size={15} /><input aria-label="Search tools" placeholder="Find a tool…" value={query} onChange={e => setQuery(e.target.value)} /><kbd>⌕</kbd></div><button className="openapi-button" disabled={!canAuthor} onClick={() => setOpenapiOpen(true)}><span><strong>Import OpenAPI</strong><small>Browse available API operations</small></span><ArrowUpRight size={14} /></button><p className="section-label">COMPONENTS</p><button className="component-button" disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({}))} onClick={() => void addTool()}><span className="component-icon"><Braces size={18} /></span><span><strong>REST tool</strong><small>Turn an endpoint into a tool</small></span><GripVertical size={15} className="muted" /></button><p className="section-label connection-label">CONNECTIONS <button className="icon-button" aria-label="Add connection" disabled={role !== 'administrator'} onClick={() => setConnectionModal({ name: '', base_url: workspace.allowed_api_origins[0] })}><Plus size={15} /></button></p>{workspace.connections.length === 0 ? <div className="empty-connections"><Unplug size={20} /><p>No APIs connected yet.</p><button className="text-button" disabled={role !== 'administrator'} onClick={() => setConnectionModal({ name: '', base_url: workspace.allowed_api_origins[0] })}>Add a connection <Plus size={13} /></button></div> : workspace.connections.map(c => <div className="connection-group" key={c.id}><button className="connection-heading" onClick={() => choose(c.id)}><Database size={15} /><strong>{c.name}</strong><ChevronDown size={13} /></button><div className="operation-list">{[{ key: 'inventory', label: 'Find inventory item', method: 'GET' }, { key: 'ticket', label: 'Get support ticket', method: 'GET' }, { key: 'write', label: 'Create support ticket', method: 'POST' }].filter(() => c.base_url === 'http://mock-api:8080').map(op => <button key={op.key} disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({ connectionId: c.id, template: op.key }))} onClick={() => void addTool(c.id, op.key)} title="Click or drag onto the canvas"><span className={`method ${op.method.toLowerCase()}`}>{op.method}</span><span>{op.label}</span><Plus size={12} /></button>)}<button className="custom-operation" disabled={!canAuthor || !!busy} onClick={() => void addTool(c.id)}><Plus size={13} /> Custom operation</button></div></div>)}<div className="palette-bottom"><span className="icon-tile small"><CircleHelp size={17} /></span><strong>A canvas for capabilities</strong><p>Click or drag a tool to begin. Connect it to an API, then configure it in the inspector.</p><div className="legend"><span><i className="legend-line" /> Relationship</span><span><i className="legend-dot" /> Draft</span></div></div></aside>
      <main className="canvas-area"><div className="canvas-toolbar"><div className="view-switch"><button className={view === 'canvas' ? 'active' : ''} onClick={() => setView('canvas')}><LayoutGrid size={14} /> Canvas</button><button className={view === 'list' ? 'active' : ''} onClick={() => setView('list')}><List size={15} /> List</button></div><button className="button small-button canvas-import-button" disabled={!canAuthor} onClick={() => setOpenapiOpen(true)}><Search size={14} />Import OpenAPI</button>{!leftOpen && <button className="icon-button canvas-panel-toggle" aria-label="Show building blocks" onClick={() => setLeftOpen(true)}><PanelLeftOpen size={16} /></button>}<span className="canvas-count">{workspace.tools.length} tools <span>·</span> {workspace.connections.length} connections</span><span className="toolbar-spacer" /><span className="save-indicator">{layoutSaving ? <LoaderCircle size={13} className="spin" /> : <CheckCheck size={14} />}{layoutSaving ? 'Saving layout' : 'Layout saved'}</span>{!rightOpen && <button className="icon-button canvas-panel-toggle" aria-label="Show inspector" onClick={() => setRightOpen(true)}><PanelRightOpen size={16} /></button>}</div>
        <div className={`graph-container ${testOpen ? 'with-test' : ''}`} onDragOver={e => { if (canAuthor) { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; } }} onDrop={e => { e.preventDefault(); if (!canAuthor) return; try { const data = JSON.parse(e.dataTransfer.getData('application/daedalus')); void addTool(data.connectionId, data.template, flow.screenToFlowPosition({ x: e.clientX, y: e.clientY })); } catch { setError('Drag an operation from the building blocks panel.'); } }}>
          {view === 'canvas' ? <ReactFlow<CardNode> nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.23 }} minZoom={0.3} maxZoom={1.4} nodesDraggable={canAuthor && !layoutSaving} nodesConnectable={canAuthor && !dirty && !busy} deleteKeyCode={null} onNodesChange={(changes: NodeChange<CardNode>[]) => setNodes(n => applyNodeChanges(changes, n))} onNodeClick={(_, node) => choose(node.id)} onNodeDragStop={(_, node) => { positions.current[node.id] = node.position; void savePositions({ ...workspace.layout.positions, [node.id]: node.position }); }} onConnect={connect} isValidConnection={c => Boolean(workspace.tools.some(t => t.id === c.source) && workspace.connections.some(a => a.id === c.target))}><Background color="#d1d8df" gap={22} size={1} /><Controls showInteractive={false} /></ReactFlow> : <div className="tool-table"><div className="table-head"><span>TOOL</span><span>ENDPOINT</span><span>STATUS</span></div>{workspace.tools.filter(t => `${t.name} ${t.description}`.toLowerCase().includes(query.toLowerCase())).map(t => <button className={`table-row ${selected === t.id ? 'selected' : ''}`} key={t.id} onClick={() => choose(t.id)}><span><Braces size={16} /><strong>{t.name}</strong></span><span><b className={`method ${t.method.toLowerCase()}`}>{t.method}</b>{t.path}</span><span className={`tool-status ${status(t).toLowerCase()}`}>{status(t)}</span></button>)}</div>}
          {workspace.tools.length === 0 && <div className="canvas-welcome"><div className="welcome-symbol"><Network size={35} strokeWidth={1.4} /></div><p className="eyebrow">A BLANK CANVAS. ENDLESS CAPABILITY.</p><h2>What will your server do?</h2><p>Bring an API into your workspace,<br />then turn its operations into useful tools.</p><button className="button primary" disabled={!!busy || (!workspace.connections.length ? role !== 'administrator' : !canAuthor)} onClick={() => workspace.connections.length ? void addTool(workspace.connections[0].id, 'inventory') : setConnectionModal({ name: 'Demo APIs', base_url: workspace.allowed_api_origins[0] })}><Plus size={16} />{workspace.connections.length ? 'Add your first tool' : 'Connect your first API'}</button><span className="welcome-hint">Start with the included inventory and support APIs.</span></div>}
        </div>
        {testOpen && editor && <section className="test-drawer"><div className="drawer-heading"><FlaskConical size={17} /><strong>Tool playground</strong><span className="tiny-tag">Isolated draft test</span><span className="toolbar-spacer" /><button className="icon-button" aria-label="Close playground" onClick={() => setTestOpen(false)}><X size={17} /></button></div><div className="test-columns"><div><label htmlFor="arguments">Arguments <span>path / query / body</span></label><textarea id="arguments" spellCheck={false} value={argumentsText} onChange={e => setArgumentsText(e.target.value)} />{editor.effect === 'write' && <label className="checkbox-row"><input type="checkbox" checked={confirmWrite} onChange={e => setConfirmWrite(e.target.checked)} />I authorize this live write to the selected API.</label>}<button className="button primary small-button" disabled={!canAuthor || !!busy || dirty || (editor.effect === 'write' && !confirmWrite)} onClick={() => void run('Testing', async () => { const result = await api<Record<string, unknown>>(`/tools/${editor.id}/test`, { method: 'POST', headers: { 'If-Match': String(editor.revision) }, body: JSON.stringify({ arguments: JSON.parse(argumentsText), confirm_write: confirmWrite }) }); setTestResult(result); const w = await refresh(); setEditor(w.tools.find(t => t.id === editor.id) || null); })}>{busy === 'Testing' ? <LoaderCircle size={14} className="spin" /> : <Play size={14} />}Run test</button></div><div><label>Result {testResult && <span className={testResult.success ? 'success-text' : 'error'}>{testResult.success ? 'Passed' : 'Failed'} · {String(testResult.duration_ms)} ms</span>}</label>{testResult ? <pre className="result-output">{JSON.stringify(testResult.result || testResult.error, null, 2)}</pre> : <div className="result-placeholder"><Braces size={24} /><p>Your API response will appear here.</p><small>Tests use agentgateway without publishing the draft.</small></div>}</div></div></section>}
        <div className="canvas-footer"><span><GitBranch size={13} /> Working draft</span><span>Layout changes never affect the live server.</span><span className="toolbar-spacer" /><span>{activeCount} published tools</span></div>
      </main>
      <aside className="inspector"><div className="inspector-heading"><Settings2 size={16} /><span>INSPECTOR</span>{editor && <span className={`tool-status ${dirty ? 'draft' : status(editor).toLowerCase()}`}>{dirty ? 'Unsaved' : status(editor)}</span>}<button className="icon-button panel-heading-toggle" aria-label="Collapse inspector" onClick={() => setRightOpen(false)}><PanelRightClose size={16} /></button></div>
        {editor ? <><div className="inspector-body"><div className="inspector-intro"><span className="icon-tile small"><Braces size={20} /></span><div><h2>Configure tool</h2><p>Shape what your agent can do.</p></div></div><fieldset disabled={!canAuthor || !!busy}><label>Tool name<input value={editor.name} onChange={e => edit({ name: e.target.value })} placeholder="get_inventory_item" /></label><label>Description<textarea rows={3} value={editor.description} onChange={e => edit({ description: e.target.value })} placeholder="Explain when and how to use this tool…" /></label><div className="form-divider" /><p className="section-label">API OPERATION</p><label>Connection<select value={editor.connection_id} onChange={e => edit({ connection_id: e.target.value })}>{workspace.connections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><div className="endpoint-input"><label>Method<select value={editor.method} onChange={e => edit({ method: e.target.value as 'GET' | 'POST', effect: e.target.value === 'POST' ? 'write' : editor.effect })}><option>GET</option><option>POST</option></select></label><label>Path<input value={editor.path} onChange={e => edit({ path: e.target.value })} placeholder="/items/{item_id}" /></label></div><label>Side effects<select value={editor.effect} onChange={e => edit({ effect: e.target.value as 'read' | 'write' })}><option value="read">Read data</option><option value="write">Write or change data</option></select></label><p className="field-help">Classify the actual API behavior. Write tests require explicit confirmation.</p><div className="form-divider" /><div className="parameters-heading"><p className="section-label">INPUT PARAMETERS <span>{editor.parameters.length}</span></p><button className="icon-button" aria-label="Add parameter" onClick={() => edit({ parameters: [...editor.parameters, { name: `parameter_${editor.parameters.length + 1}`, location: 'query', type: 'string', required: false, description: '' }] })}><Plus size={16} /></button></div>{editor.parameters.map((p, i) => <div className="parameter-card" key={i}><div className="parameter-top"><input aria-label={`Parameter ${i + 1} name`} value={p.name} onChange={e => editParameter(i, { name: e.target.value })} /><button className="icon-button" aria-label={`Remove parameter ${i + 1}`} onClick={() => edit({ parameters: editor.parameters.filter((_, j) => i !== j) })}><Trash2 size={14} /></button></div><div className="parameter-options"><select aria-label={`Parameter ${i + 1} location`} value={p.location} onChange={e => editParameter(i, { location: e.target.value as 'path' | 'query', required: e.target.value === 'path' ? true : p.required })}><option value="path">Path</option><option value="query">Query</option></select><select aria-label={`Parameter ${i + 1} type`} value={p.type} onChange={e => editParameter(i, { type: e.target.value as Parameter['type'] })}>{['string', 'integer', 'number', 'boolean'].map(t => <option key={t}>{t}</option>)}</select><label className="checkbox-row"><input type="checkbox" checked={p.required} onChange={e => editParameter(i, { required: e.target.checked })} />Required</label></div></div>)}{editor.parameters.length === 0 && <p className="field-help">No parameters yet. Add path or query inputs above.</p>}{editor.method === 'POST' && <label>JSON body schema<textarea className="code-input" rows={7} value={bodyText} onChange={e => { setBodyText(e.target.value); setDirty(true); }} placeholder={'{"type":"object","properties":{}}'} /></label>}<div className="form-divider" /><label className="checkbox-row include-tool"><input type="checkbox" checked={editor.enabled} onChange={e => edit({ enabled: e.target.checked })} /><span>Include in next release<small>Excluding a tool takes effect when published.</small></span></label></fieldset></div><div className="inspector-actions"><div><button className="button" disabled={!!busy || dirty || !canAuthor} onClick={() => void run('Validating', async () => { await api(`/tools/${editor.id}/validate`, { method: 'POST', headers: { 'If-Match': String(editor.revision) } }); const w = await refresh(); setEditor(w.tools.find(t => t.id === editor.id) || null); setNotice('Tool definition validated. Run a test before publishing.'); })}><Check size={15} />Validate</button><button className="button" disabled={!!busy || dirty || !canAuthor} onClick={openTest}><FlaskConical size={15} />Test tool</button></div><button className="button primary full-width" disabled={!dirty || !!busy || !canAuthor} onClick={() => void saveEditor()}>{busy === 'Saving' ? <LoaderCircle className="spin" size={16} /> : <Save size={16} />}Save draft</button>{dirty && <button className="text-button discard" onClick={() => { setDirty(false); const tool = workspace.tools.find(t => t.id === editor.id)!; setEditor(tool); setBodyText(tool.body_schema ? JSON.stringify(tool.body_schema, null, 2) : ''); }}>Discard changes</button>}<button className="text-button danger" disabled={!!busy || dirty || !canAuthor} onClick={() => void removeNode('tool', editor.id, editor.name, editor.revision)}><Trash2 size={14} />Remove tool</button></div></> : selectedConnection ? <div className="inspector-body"><span className="icon-tile"><Database size={26} /></span><h2>{selectedConnection.name}</h2><p className="muted">A reusable connection for your REST tools.</p><label>Approved base URL<code className="endpoint-display">{selectedConnection.base_url}</code></label><div className="detail-row"><span>Authentication</span><strong>None · evaluation</strong></div><div className="detail-row"><span>Revision</span><strong>{selectedConnection.revision}</strong></div><button className="button full-width" disabled={role !== 'administrator'} onClick={() => setConnectionModal(selectedConnection)}><Settings2 size={16} />Edit connection</button><button className="text-button danger" disabled={!!busy || !canAuthor} onClick={() => void removeNode('connection', selectedConnection.id, selectedConnection.name, selectedConnection.revision)}><Trash2 size={14} />Remove connection</button><p className="field-help">Changing a connection requires affected tools to be tested again. Published releases retain their original connection.</p></div> : <div className="inspector-overview"><span className="icon-tile"><Server size={25} /></span><h2>Your server, at a glance.</h2><p>Choose a tool or connection on the canvas to configure its details.</p><div className="overview-stat"><span>Draft tools</span><strong>{workspace.tools.length}</strong></div><div className="overview-stat"><span>Published tools</span><strong>{activeCount}</strong></div><div className="overview-stat"><span>Connections</span><strong>{workspace.connections.length}</strong></div><div className="overview-endpoint"><p className="section-label">MCP ENDPOINT</p><code>{workspace.server.mcp_url}</code><small>Use your separate MCP token to connect a client.</small></div><div className="workflow-steps"><p className="section-label">FROM IDEA TO CAPABILITY</p>{['Connect an API', 'Configure a tool', 'Validate and test', 'Review and publish'].map((label, i) => <div key={label}><span>{i + 1}</span>{label}</div>)}</div></div>}
      </aside>
    </div>
    {policiesOpen && <Modal title="API access policies" subtitle="Approved origins are enforced by the Builder and generated MCP Server." close={() => setPoliciesOpen(false)}><div className="policy-list">{origins.map(origin => <div className="policy-row" key={origin.id}><div><strong>{origin.origin}</strong><small>{origin.description || 'No description'}{origin.bootstrap ? ' · bootstrap' : ''}</small></div>{origin.bootstrap ? <span className="tiny-tag">Environment</span> : <button className="icon-button" aria-label={`Remove ${origin.origin}`} onClick={() => void removeOrigin(origin)}><Trash2 size={15} /></button>}</div>)}</div><form onSubmit={addOrigin} className="policy-form"><label>API origin<input required type="url" value={originDraft.origin} onChange={e => setOriginDraft({ ...originDraft, origin: e.target.value })} placeholder="https://api.example.com" /></label><label>Description<input value={originDraft.description} onChange={e => setOriginDraft({ ...originDraft, description: e.target.value })} placeholder="Customer support API" /></label><button className="button primary full-width" disabled={!!busy}><Plus size={15} />Approve origin</button></form><p className="field-help">Origins must be scheme and host only. Changes apply to new validation and the next server release reconciliation.</p></Modal>}{openapiOpen && <Modal title="Import an OpenAPI document" subtitle="Preview every documented operation, then add supported GET or POST operations as draft tools." close={() => setOpenapiOpen(false)}><form onSubmit={e => { e.preventDefault(); void discoverOpenAPI(); }}><label>Swagger or OpenAPI URL<input autoFocus required type="url" value={openapiUrl} onChange={e => setOpenapiUrl(e.target.value)} placeholder="https://api.example.com/openapi.json" /></label><p className="field-help">The Builder fetches the document server-side. Credentials, query strings, and private network destinations are rejected.</p><button className="button primary full-width" disabled={openapiBusy || !openapiUrl.trim()} type="submit">{openapiBusy ? <LoaderCircle className="spin" size={16} /> : <Search size={16} />}Find API operations</button></form>{openapi && <><div className="detail-row"><span>{openapi.title} {openapi.version && `· v${openapi.version}`}</span><code>{openapi.base_url}</code></div>{openapi.truncated && <p className="field-help">Showing the first 200 operations.</p>}<div className="openapi-results">{openapi.operations.length ? openapi.operations.map((operation, index) => <button className="openapi-operation" disabled={operation.supported === false} key={`${operation.method}-${operation.path}-${index}`} onClick={() => void selectOperation(operation)}><b className={`method ${operation.method.toLowerCase()}`}>{operation.method}</b><code>{operation.path}</code><small>{operation.supported === false ? 'Not supported by current profile' : operation.name}</small>{operation.supported === false ? <span className="tiny-tag">Preview</span> : <Plus size={14} />}</button>) : <p className="openapi-empty">No operations were found.</p>}</div></>}</Modal>}
    {connectionModal && <Modal title={connectionModal.id ? 'Edit API connection' : 'Connect an API'} subtitle="Connections are reusable across tools. Only administrator-approved origins can be used." close={closeConnection}><form onSubmit={(e: FormEvent) => { e.preventDefault(); void run('Saving connection', async () => { const data = { name: connectionModal.name, base_url: connectionModal.base_url, auth_mode: 'none' }; const saved = await api<Connection>(connectionModal.id ? `/connections/${connectionModal.id}` : '/connections', { method: connectionModal.id ? 'PATCH' : 'POST', headers: connectionModal.id ? { 'If-Match': String(connectionModal.revision) } : {}, body: JSON.stringify(data) }); setConnectionModal(null); setSelected(saved.id); setEditor(null); await refresh(); if (pendingOperation) await addImportedTool(saved.id, pendingOperation); else setNotice('API connection saved. Add an operation from the sidebar.'); }); }}><label>Connection name<input autoFocus required maxLength={80} value={connectionModal.name || ''} onChange={e => setConnectionModal({ ...connectionModal, name: e.target.value })} placeholder="Inventory API" /></label><label>Base URL<input required value={connectionModal.base_url || ''} onChange={e => setConnectionModal({ ...connectionModal, base_url: e.target.value })} placeholder="http://mock-api:8080" /></label><p className="field-help">Approved origins: {workspace.allowed_api_origins.join(', ')}</p><div className="inline-info"><ShieldCheck size={19} /><p>This first profile connects to APIs without backend credentials. Management and MCP access use separate tokens.</p></div>{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy} type="submit">{busy ? <LoaderCircle className="spin" size={16} /> : <Plus size={16} />}Save connection</button></form></Modal>}
    {serverModal && <Modal title="Create MCP server" subtitle="This creates an isolated server workspace in the current project. Publish a release, then deploy it as its dedicated Server Application." close={() => setServerModal(false)}><form onSubmit={e => { e.preventDefault(); void createServer(); }}><label>Server name<input autoFocus required value={newServerName} onChange={e => setNewServerName(e.target.value)} placeholder="Customer support MCP" /></label><button className="button primary full-width" disabled={!!busy || !newServerName.trim()} type="submit"><Plus size={16} />Create server</button></form></Modal>}
    {deploymentOpen && <Modal title="Deployment & monitoring" subtitle="Each MCP server deploys to its own Server Application in this project." close={() => setDeploymentOpen(false)}><div className="deployment-card"><div><span className={`tool-status ${workspace.deployment.status}`}>{workspace.deployment.status.replaceAll('_', ' ')}</span><strong>{workspace.deployment.application_name || 'Application not provisioned'}</strong></div><p className="muted">Provider: {workspace.deployment.provider}. {workspace.deployment.message || 'Publish an active release, then deploy.'}</p><div className="detail-row"><span>Active release</span><code>{workspace.server.active_release_id?.slice(0, 8) || 'None'}</code></div><div className="detail-row"><span>Deployed release</span><code>{workspace.deployment.deployed_release_id?.slice(0, 8) || 'None'}</code></div>{workspace.deployment.endpoint && <div className="detail-row"><span>Endpoint</span><code>{workspace.deployment.endpoint}</code></div>}<div className="deployment-actions"><button className="button primary" disabled={!canPublish || !!busy || !workspace.server.active_release_id} onClick={() => void deploy()}><Rocket size={15} />Deploy release</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('refresh')}>Refresh</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('stop')}>Stop</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('delete')}>Delete</button></div><p className="field-help">Gateway health appears in the workspace header after the dedicated application starts. Call/error/latency metrics are supplied by the configured deployment bridge.</p></div></Modal>}
    {preview && <Modal title="Review your release" subtitle="Only tested, included tools enter the live catalog. The Server will verify activation before marking this release active." close={closePreview}><div className="release-diff">{(['added', 'changed', 'removed'] as const).map(kind => <div key={kind}><p className="section-label">{kind} <span>{preview[kind].length}</span></p>{preview[kind].length ? preview[kind].map(name => <div className={`diff-item ${kind}`} key={name}>{kind === 'added' ? <Plus size={15} /> : kind === 'removed' ? <X size={15} /> : <Settings2 size={15} />}<code>{name}</code></div>) : <p className="field-help">No {kind} tools</p>}</div>)}</div>{preview.problems.length > 0 && <div className="publish-problems"><strong>Before you publish</strong><ul>{preview.problems.map(p => <li key={p}>{p}</li>)}</ul></div>}{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy || !!preview.problems.length || !canPublish} onClick={() => void run('Publishing', async () => { await api('/releases', { method: 'POST', body: JSON.stringify({ revision: preview.revision }) }); setPreview(null); await refresh(); setNotice('Release submitted. Waiting for the Server to verify the live catalog.'); })}>{busy === 'Publishing' ? <LoaderCircle className="spin" size={16} /> : <Rocket size={16} />}Publish release</button></Modal>}
    {history && <Modal title="Release history" subtitle="Each release is an immutable snapshot. Restoring creates a new release and preserves your working draft." close={closeHistory}><div className="runtime-detail"><Radio size={16} /><span>{runtime.online && runtime.ready ? 'Gateway ready' : 'Gateway unavailable'}</span>{runtime.gateway_pid && <code>PID {runtime.gateway_pid}</code>}</div>{workspace.releases.length === 0 ? <div className="history-empty"><History size={30} /><p>Your first release starts here.</p><small>Validate and test a tool, then review and publish.</small></div> : <div className="release-list">{workspace.releases.map(r => <article key={r.id}><div><span className={`tool-status ${r.status}`}>{r.status}</span><code>{r.id.slice(0, 8)}</code><time>{new Date(r.created_at).toLocaleString()}</time></div><p>{r.tool_names.length ? r.tool_names.join(', ') : 'Empty catalog'}</p>{r.error && <p className="error">{r.error}</p>}{r.status === 'superseded' && <button className="text-button" disabled={!canPublish || !!busy || !!pendingRelease} onClick={() => void run('Restoring', async () => { await api('/releases/rollback', { method: 'POST', body: JSON.stringify({ revision: workspace.server.revision, release_id: r.id }) }); await refresh(); setNotice('Restore submitted for Server verification.'); })}><Undo2 size={14} />Restore this release</button>}</article>)}</div>}{error && <p className="error" role="alert">{error}</p>}</Modal>}
  </div>;
}
