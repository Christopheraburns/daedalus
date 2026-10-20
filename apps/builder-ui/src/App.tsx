import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { ReactFlow, Background, Controls, Handle, Position, applyNodeChanges, useReactFlow, type Node, type NodeProps, type OnConnect, type NodeChange } from '@xyflow/react';
import { ArrowRight, ArrowUpRight, Box, Braces, Check, CheckCheck, ChevronDown, ChevronRight, CircleHelp, Copy, Database, Download, FlaskConical, GitBranch, GripVertical, History, LayoutGrid, List, LoaderCircle, LogOut, Network, Package, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, Play, Plus, Radio, Rocket, Save, Search, Server, Settings2, ShieldCheck, Square, Trash2, Undo2, Unplug, Upload, X } from 'lucide-react';
import { statusLabel, useI18n } from './i18n';
import { type ApiOrigin, type Connection, type Deployment, type OpenAPIOperation, type Pack, type PackTool, type DiscoveredTool, type Parameter, type Preview, type Protocol, type ServerSummary, type Tool, type ToolSpec, type Workspace, specOf, toolLabel } from './types';

type CardData = { kind: 'server' | 'tool' | 'connection'; title: string; subtitle: string; status?: string; method?: string; count?: number; tag?: string; toolKind?: string; selected?: boolean; [key: string]: unknown };
type CardNode = Node<CardData>;
type LogEntry = { at: number; level: 'info' | 'error' | 'success'; code: string; values?: Record<string, string | number> };
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
    <div className="card-kicker">{data.kind === 'server' ? tr('kicker_server') : data.kind === 'connection' ? tr('kicker_connection') : tr(data.toolKind === 'mcp' ? 'kicker_mcp' : data.toolKind === 'python' ? 'kicker_python' : 'kicker_tool')}<span className={`status-dot ${data.status === 'Active' || data.status === 'Tested' || data.status === 'Checked' ? 'green' : data.status === 'Failed' ? 'red' : ''}`} /></div>
    <div className="card-title"><span className="node-icon"><Icon size={17} /></span><strong>{data.title}</strong></div>
    <div className="card-subtitle">{data.method && <span className={`method ${data.method.toLowerCase()}`}>{data.method}</span>}{data.subtitle}</div>
    <div className="card-footer"><span>{data.kind === 'tool' ? statusLabel(tr, data.status) : tr('n_tools', { count: data.count ?? 0 })}</span>{data.kind === 'tool' ? <ChevronRight size={14} /> : <span className="tiny-tag">{data.tag ?? (data.kind === 'server' ? 'agentgateway' : 'REST / JSON')}</span>}</div>
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
  const [serversOpen, setServersOpen] = useState(false);
  const [deleteDraft, setDeleteDraft] = useState<{ confirm: string; deleteApplication: boolean } | null>(null);
  type ImportResult = { server: { id: string; name: string }; tools: number; connections: number; packs_written: string[]; required_secrets: string[]; missing_secrets: string[] };
  const [importDraft, setImportDraft] = useState<{ document: Record<string, unknown>; fileName: string; name: string; replacePacks: boolean; result?: ImportResult } | null>(null);
  const importInput = useRef<HTMLInputElement>(null);
  const [newServerName, setNewServerName] = useState('');
  const [deploymentOpen, setDeploymentOpen] = useState(false);
  // While the dialog is open and the application is starting or stopping, follow it in Workbench.
  const [liveStarted, setLiveStarted] = useState<number | null>(null);
  const [liveCheck, setLiveCheck] = useState<{ at: number; error: string } | null>(null);
  const [deployName, setDeployName] = useState('');
  const [builderCode, setBuilderCode] = useState<{ revision: string; started_at: string } | null>(null);
  const [errorAt, setErrorAt] = useState<number | null>(null);
  const [policiesOpen, setPoliciesOpen] = useState(false);
  const [origins, setOrigins] = useState<ApiOrigin[]>([]);
  const [originDraft, setOriginDraft] = useState({ origin: '', description: '' });
  const [originNote, setOriginNote] = useState('');
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
  // Packs start collapsed to keep the palette short; the open ones are remembered per browser.
  // The empty-canvas welcome can be closed per server; remembered per browser.
  const [welcomeHidden, setWelcomeHidden] = useState<string[]>(() => { try { return JSON.parse(localStorage.getItem('factory-welcome-hidden') || '[]'); } catch { return []; } });
  const hideWelcome = (id: string) => setWelcomeHidden(current => { const next = [...new Set([...current, id])]; try { localStorage.setItem('factory-welcome-hidden', JSON.stringify(next)); } catch { /* per-viewer convenience only */ } return next; });
  const [openPacks, setOpenPacks] = useState<string[]>(() => { try { return JSON.parse(localStorage.getItem('factory-open-packs') || '[]'); } catch { return []; } });
  const togglePack = (name: string) => setOpenPacks(current => { const next = current.includes(name) ? current.filter(n => n !== name) : [...current, name]; try { localStorage.setItem('factory-open-packs', JSON.stringify(next)); } catch { /* per-viewer convenience only */ } return next; });
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
  // The playground's right side: a running log of validation and test events, and the result once one arrives.
  const [testLog, setTestLog] = useState<LogEntry[]>([]);
  const [drawerTab, setDrawerTab] = useState<'logs' | 'result'>('logs');
  const logRef = useRef<HTMLDivElement>(null);
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
  async function addOrigin(e: FormEvent) {
    e.preventDefault(); setOriginNote('');
    // A policy approves an origin (scheme + host + port). People paste full URLs, so keep just the origin and say so.
    let origin = originDraft.origin.trim();
    try { const url = new URL(origin); if (!url.username && !url.password && url.origin !== 'null') origin = url.origin; } catch { /* the API reports malformed values */ }
    const shortened = origin !== originDraft.origin.trim().replace(/\/$/, '');
    await run('Adding policy', async () => { await api('/policies/origins', { method: 'POST', body: JSON.stringify({ ...originDraft, origin, enabled: true }) }); if (shortened) setOriginNote(tr('origin_normalized', { origin, url: originDraft.origin.trim() })); setOriginDraft({ origin: '', description: '' }); await loadPolicies(); await refresh(); });
  }
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

  // A different server workspace starts with nothing selected: the inspector, playground and drafts belong to the old one.
  useEffect(() => {
    setSelected(''); setEditor(null); setDirty(false); setBodyText(''); setConfigText('{}');
    setTestOpen(false); setTestResult(null); setConfirmWrite(false); setTestLog([]); setDrawerTab('logs'); setDeployName(''); positions.current = {};
  }, [serverId]);

  const appendLog = (code: string, level: LogEntry['level'] = 'info', values?: LogEntry['values'], at = Date.now()) => setTestLog(current => [...current.slice(-299), { at, level, code, values }]);
  const logText = (entry: LogEntry) => tr(`log_${entry.code}`, entry.values);
  useEffect(() => { const panel = logRef.current; if (panel) panel.scrollTop = panel.scrollHeight; }, [testLog, drawerTab]);

  async function validateTool() {
    if (!editor) return;
    if (!testOpen) openTest();
    setDrawerTab('logs');
    appendLog('client_validating', 'info', { name: editor.name });
    await run('Validating', async () => {
      try {
        const verdict = await api<{ profile: string }>(`/tools/${editor.id}/validate`, { method: 'POST', headers: { 'If-Match': String(editor.revision) } });
        appendLog('client_valid', 'success', { profile: verdict.profile });
      } catch (e) { appendLog('client_invalid', 'error', { message: translateError(e instanceof Error ? e.message : String(e)) }); throw e; }
      const w = await refresh(); setEditor(w.tools.find(t => t.id === editor.id) || null); setNotice(tr('tool_definition_validated_run_a_test'));
    });
  }

  async function runTest() {
    if (!editor) return;
    setDrawerTab('logs'); setTestResult(null);
    appendLog('client_testing', 'info', { name: editor.name });
    let args: unknown;
    try { args = JSON.parse(argumentsText); } catch (e) { appendLog('client_bad_json', 'error', { message: e instanceof Error ? e.message : String(e) }); return; }
    appendLog('client_arguments', 'info', { args: JSON.stringify(args) });
    await run('Testing', async () => {
      const sent = Date.now();
      let result: { success: boolean; duration_ms: number; log?: { t: number; level: LogEntry['level']; code: string; values: Record<string, string> }[] } & Record<string, unknown>;
      try {
        result = await api(`/tools/${editor.id}/test`, { method: 'POST', headers: { 'If-Match': String(editor.revision) }, body: JSON.stringify({ arguments: args, confirm_write: confirmWrite }) });
      } catch (e) { appendLog('client_request_failed', 'error', { message: translateError(e instanceof Error ? e.message : String(e)) }); throw e; }
      for (const entry of result.log ?? []) appendLog(entry.code, entry.level, entry.values, sent + entry.t);
      appendLog(result.success ? 'client_passed' : 'client_failed', result.success ? 'success' : 'error', { ms: result.duration_ms });
      setTestResult(result); setDrawerTab('result');
      const w = await refresh(); setEditor(w.tools.find(t => t.id === editor.id) || null);
    });
  }

  const deploymentStatus = workspace?.deployment.status;
  useEffect(() => {
    if (!deploymentOpen || !deploymentStatus || !['provisioning', 'stopping', 'unknown'].includes(deploymentStatus)) { setLiveStarted(null); setLiveCheck(null); return; }
    setLiveStarted(started => started ?? Date.now());
    let alive = true;
    const tick = async () => {
      try {
        const live = await api<Deployment & { live_error?: string }>('/deployments/live');
        if (!alive) return;
        setLiveCheck({ at: Date.now(), error: live.live_error ?? '' });
        if (live.status !== deploymentStatus) await refresh();
      } catch (e) {
        if (!alive) return;
        const message = e instanceof Error ? e.message : String(e);
        // An API without this route means the page was updated but the Builder process was not restarted.
        if (/^(Method Not Allowed|Not Found)$/.test(message)) { setLiveCheck({ at: Date.now(), error: tr('api_older_than_ui') }); clearInterval(timer); return; }
        setLiveCheck({ at: Date.now(), error: message });
      }
    };
    const timer = setInterval(() => void tick(), 5000); void tick();
    return () => { alive = false; clearInterval(timer); };
  }, [deploymentOpen, deploymentStatus, api, refresh]);

  async function exportServer() {
    await run('Exporting', async () => {
      const exported = await api<{ server: { name: string } }>('/export');
      const fileName = `${exported.server.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'mcp-server'}.daedalus.json`;
      const link = document.createElement('a');
      link.href = URL.createObjectURL(new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' }));
      link.download = fileName;
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
      setNotice(tr('notice_exported', { name: exported.server.name, file: fileName }));
    });
  }

  async function deleteServer() {
    if (!deleteDraft || !workspace) return;
    const name = workspace.server.name;
    await run('Deleting server', async () => {
      await api(`/servers/${workspace.server.id}?delete_application=${deleteDraft.deleteApplication}`, { method: 'DELETE', headers: { 'If-Match': String(workspace.server.revision) } });
      setDeleteDraft(null); setServerId('');
      await api<ServerSummary[]>('/servers').then(setServers);
      setNotice(tr('notice_server_deleted', { name }));
    });
  }

  async function readImport(file: File) {
    setError('');
    try {
      const parsed = JSON.parse(await file.text()) as Record<string, unknown>;
      setImportDraft({ document: parsed, fileName: file.name, name: String((parsed.server as { name?: string } | undefined)?.name ?? ''), replacePacks: false });
      if (parsed.format !== 'daedalus-server/v1') setError(tr('import_wrong_format'));
    } catch (e) { setError(tr('import_bad_file', { message: e instanceof Error ? e.message : String(e) })); }
  }

  async function submitImport() {
    if (!importDraft) return;
    await run('Importing', async () => {
      const result = await api<ImportResult>('/servers/import', { method: 'POST', body: JSON.stringify({ document: importDraft.document, name: importDraft.name, replace_packs: importDraft.replacePacks }) });
      setImportDraft({ ...importDraft, result });
      await api<ServerSummary[]>('/servers').then(setServers);
      await loadPacks();
    });
  }

  useEffect(() => { setErrorAt(error ? Date.now() : null); }, [error]);
  const clock = (value: number | string) => new Date(value).toLocaleTimeString(locale, { hour12: false });
  const suggestedName = (name: string) => (name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^[^a-z]+|-+$/g, '') || 'mcp-server').slice(0, 63);
  function openDeployment() {
    setError(''); setDeploymentOpen(true);
    setDeployName('');
    void fetch('/healthz').then(r => r.json()).then(setBuilderCode).catch(() => setBuilderCode(null));
  }

  useEffect(() => { if (!notice) return; const timer = setTimeout(() => setNotice(''), 6000); return () => clearTimeout(timer); }, [notice]);

  async function run(name: string, action: () => Promise<void>) {
    setBusy(name); setError(''); setNotice('');
    try { await action(); } catch (e) { setError(translateError(e instanceof Error ? e.message : String(e))); }
    finally { setBusy(''); }
  }

  function status(tool: Tool) {
    if (!tool.enabled) return 'Excluded';
    if (workspace?.tools.find(t => t.id === tool.id)?.published) return 'Active';
    if (tool.tested) return 'Tested';
    if (tool.test_summary && !tool.test_summary.success) return 'Failed';
    if (tool.validated) return 'Validated';
    return 'Draft';
  }

  /** One server's live state, from its deployment record, heartbeat and ownership. */
  function liveState(s: ServerSummary | undefined): { state: 'running' | 'starting' | 'stopped' | 'failed' | 'offline' | 'not_deployed'; warning: string } {
    if (!s) return { state: 'not_deployed', warning: '' };
    const pod = (s.owner?.process ?? '').match(/ on (\S+)$/)?.[1];
    const warning = s.contender ? tr('server_contended', { host: s.contender.host ?? '?', revision: (s.contender.revision ?? '?').slice(0, 8), time: new Date(s.contender.at).toLocaleTimeString(locale, { hour12: false }), owner: s.contender.owner ?? '?' })
      : s.owner && !s.runtime?.online ? tr('server_owner_silent', { pod: pod ?? '?' }) : '';
    const status = s.deployment.status;
    if (s.runtime?.online && s.runtime.ready) return { state: 'running', warning };
    if (s.runtime?.online || ['provisioning', 'starting'].includes(status)) return { state: 'starting', warning };
    if (status === 'failed') return { state: 'failed', warning };
    if (status === 'stopped' || status === 'stopping') return { state: 'stopped', warning };
    if (status === 'not_deployed' || status === 'ready_to_deploy') return { state: s.runtime?.host ? 'offline' : 'not_deployed', warning };
    return { state: 'offline', warning };
  }

  function packToolOf(tool: Tool | null): PackTool | undefined {
    return tool?.kind === 'python' ? packs.find(p => p.name === tool.pack)?.tools.find(t => t.function === tool.function) : undefined;
  }

  /** The four setup steps, derived from what is on the canvas now, so removing a tool or connection unchecks them. */
  function progress(w: Workspace) {
    const linked = (t: Tool) => t.enabled && (t.kind !== 'python' || !packToolOf(t)?.requires_connection || Boolean(t.connection_id));
    return [
      { key: 'connect', done: w.connections.length > 0 },
      { key: 'configure', done: w.tools.some(linked) },
      { key: 'validate', done: w.tools.some(t => linked(t) && t.tested) },
      { key: 'review', done: w.tools.some(t => linked(t) && t.published) },
    ];
  }

  /** The protocol a tool needs from its connection: the pack's protocol for Python tools, REST for HTTP tools. */
  function requiredProtocol(tool: Pick<ToolSpec, 'kind' | 'pack'>): Protocol {
    if (tool.kind === 'mcp') return 'mcp';
    return tool.kind === 'python' ? (packs.find(p => p.name === tool.pack)?.protocol ?? 'rest') : 'rest';
  }
  function compatible(tool: Pick<ToolSpec, 'kind' | 'pack'>, connection: Connection) {
    return (connection.protocol ?? 'rest') === requiredProtocol(tool);
  }

  const choose = useCallback((id: string) => {
    if (dirty && id !== selected) { setError(tr('save_or_discard_your_inspector_changes')); return; }
    setSelected(id);
    const tool = latest.current?.tools.find(t => t.id === id) || null;
    setEditor(tool); setBodyText(tool?.body_schema ? JSON.stringify(tool.body_schema, null, 2) : ''); setConfigText(JSON.stringify(tool?.config ?? {}, null, 2)); setDirty(false);
    setTestOpen(false); setTestResult(null); setConfirmWrite(false); setTestLog([]); setDrawerTab('logs');
  }, [dirty, selected]);

  useEffect(() => {
    if (!workspace) return;
    const saved = workspace.layout.positions;
    const make = (id: string, x: number, y: number, data: CardData): CardNode => ({ id, type: 'card', position: positions.current[id] || saved[id] || { x, y }, data: { ...data, selected: id === selected } });
    const visible = workspace.tools.filter(t => `${t.name} ${t.description}`.toLowerCase().includes(query.toLowerCase()));
    setNodes([
      make(workspace.server.id, 30, 120, { kind: 'server', title: workspace.server.name, subtitle: tr('agents_tool_catalog'), count: workspace.tools.length, status: workspace.server.runtime.ready && workspace.server.runtime.online ? 'Active' : 'Draft' }),
      ...visible.map((t, i) => make(t.id, 355, 40 + i * 190, { kind: 'tool', title: t.name, ...toolLabel(t), toolKind: t.kind ?? 'http', status: status(t) })),
      ...workspace.connections.map((c, i) => make(c.id, 685, 120 + i * 220, { kind: 'connection', title: c.name, subtitle: c.base_url, count: c.protocol === 'mcp' ? (c.discovered?.length ?? 0) : workspace.tools.filter(t => t.connection_id === c.id).length, tag: c.protocol === 'mcp' ? 'MCP' : c.protocol === 'webhdfs' ? 'WebHDFS' : c.protocol === 's3' ? 'S3' : 'REST / JSON', status: c.probe_summary ? (c.probe_summary.success ? 'Checked' : 'Failed') : undefined })),
    ]);
  }, [workspace, selected, query]);
  useEffect(() => { if (policiesOpen && token) void loadPolicies().catch(e => setError(e instanceof Error ? e.message : String(e))); }, [policiesOpen, token, serverId]);

  const edges = useMemo(() => workspace ? workspace.tools.filter(t => nodes.some(n => n.id === t.id)).flatMap(t => [
    { id: `server-${t.id}`, source: workspace.server.id, target: t.id, type: 'smoothstep', style: { stroke: '#abb6c5', strokeWidth: 1.5 } },
    // Python tools without a connection have no API edge.
    ...(t.connection_id ? [{ id: `api-${t.id}`, source: t.id, target: t.connection_id, type: 'smoothstep', style: { stroke: status(t) === 'Failed' ? '#c0392b' : t.id === selected ? '#087f8c' : '#abb6c5', strokeWidth: t.id === selected || status(t) === 'Failed' ? 2 : 1.5, strokeDasharray: status(t) === 'Failed' ? '6 4' : undefined } }] : []),
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
    const protocol = packs.find(p => p.name === pack)?.protocol ?? 'rest';
    const connection = tool.requires_connection ? connectionId || current.connections.find(c => (c.protocol ?? 'rest') === protocol)?.id : null;
    if (tool.requires_connection && !connection) { setPendingPackTool({ pack, tool }); setConnectionModal({ name: '', base_url: current.allowed_api_origins[0], protocol, auth_mode: protocol === 's3' ? 's3-sigv4' : 'none' }); return; }
    let name = tool.function; let i = 2; while (current.tools.some(t => t.name === name)) name = `${tool.function}_${i++}`;
    const spec: ToolSpec = { name, description: tool.description, kind: 'python', pack, function: tool.function, connection_id: connection ?? null, method: 'GET', path: '/', parameters: [], body_schema: null, config: {}, effect: tool.effect, enabled: true };
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

  /** Probe the endpoint (or discover an MCP server's tools) through an isolated candidate and show the verdict. */
  async function checkConnection(connection: Connection) {
    await run('Checking connection', async () => {
      const checked = await api<Connection>(`/connections/${connection.id}/check`, { method: 'POST', headers: { 'If-Match': String(connection.revision) } });
      await refresh();
      if (checked.probe_summary?.success) setNotice(tr('notice_check_passed', { name: checked.name, message: translateError(checked.probe_summary.message) }));
      else setError(tr('notice_check_failed', { name: checked.name, message: translateError(checked.probe_summary?.message ?? '') }));
    });
  }

  /** Add one tool of an upstream MCP server as a tool node; the server copies its input schema from discovery. */
  async function addMcpTool(connection: Connection, tool: DiscoveredTool, position?: { x: number; y: number }) {
    const current = latest.current;
    if (!current) return;
    if (dirty) { setError(tr('save_or_discard_your_inspector_changes_2')); return; }
    const base = /^[A-Za-z]/.test(tool.name) ? tool.name.replace(/[^A-Za-z0-9_]/g, '_') : `mcp_${tool.name.replace(/[^A-Za-z0-9_]/g, '_')}`;
    let name = base.slice(0, 60); let i = 2; while (current.tools.some(t => t.name === name)) name = `${base.slice(0, 56)}_${i++}`;
    await run('Adding MCP tool', async () => {
      const created = await api<Tool>('/tools', { method: 'POST', body: JSON.stringify({ name, description: tool.description || tr('mcp_default_description', { tool: tool.name, server: connection.name }), kind: 'mcp', connection_id: connection.id, upstream_tool: tool.name, effect: tool.read_only ? 'read' : 'write', enabled: true }) });
      if (position) positions.current[created.id] = position;
      const data = await refresh();
      setSelected(created.id); setEditor(created); setBodyText(''); setDirty(false); setTestOpen(false); setTestResult(null);
      if (position) await savePositions({ ...data.layout.positions, [created.id]: position }, data.layout.revision);
      setTimeout(() => void flow.fitView({ duration: 350, padding: 0.2 }), 50);
    });
  }

  async function addAllMcpTools(connection: Connection) {
    const current = latest.current;
    if (!current || dirty) { setError(tr('save_or_discard_your_inspector_changes_2')); return; }
    const missing = (connection.discovered ?? []).filter(d => !current.tools.some(t => t.kind === 'mcp' && t.connection_id === connection.id && t.upstream_tool === d.name));
    for (const tool of missing) await addMcpTool(connection, tool);
    setNotice(missing.length ? tr('notice_mcp_added', { count: missing.length, server: connection.name }) : tr('notice_mcp_all_present', { server: connection.name }));
  }

  async function addAllPackTools(pack: Pack) {
    const current = latest.current;
    if (!current || dirty) { setError(tr('save_or_discard_your_inspector_changes_2')); return; }
    const missing = pack.tools.filter(t => !current.tools.some(existing => existing.kind === 'python' && existing.pack === pack.name && existing.function === t.function));
    const target = current.connections.find(c => (c.protocol ?? 'rest') === pack.protocol);
    const skipped = missing.filter(t => t.requires_connection && !target);
    await run('Adding pack', async () => {
      for (const tool of missing.filter(t => !skipped.includes(t))) {
        await api<Tool>('/tools', { method: 'POST', body: JSON.stringify({ name: tool.function, description: tool.description, kind: 'python', pack: pack.name, function: tool.function, connection_id: tool.requires_connection ? target!.id : null, effect: tool.effect, enabled: true }) });
      }
      await refresh();
      setNotice(skipped.length ? tr('notice_pack_needs_protocol', { count: missing.length - skipped.length, names: skipped.map(t => t.function).join(', '), protocol: tr(`protocol_${pack.protocol}`) }) : missing.length ? tr('notice_pack_added', { count: missing.length, pack: pack.name }) : tr('notice_pack_all_present', { pack: pack.name }));
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
    const target = workspace.connections.find(c => c.id === edge.target);
    if (!tool || !target) return;
    if (!compatible(tool, target)) { setError(tr('incompatible_connection', { protocol: tr(`protocol_${requiredProtocol(tool)}`), name: target.name })); return; }
    void run('Connecting', async () => {
      const saved = await api<Tool>(`/tools/${tool.id}`, { method: 'PATCH', headers: { 'If-Match': String(tool.revision) }, body: JSON.stringify({ ...specOf(tool), connection_id: edge.target }) });
      if (selected === tool.id) setEditor(saved);
      await refresh(); setNotice(tr('connection_saved_to_the_draft_retest'));
    });
  };

  function openTest() {
    if (!editor) return;
    if (editor.kind === 'mcp') {
      const body: Record<string, unknown> = {};
      const schema = editor.input_schema ?? {};
      for (const name of schema.required ?? []) { const type = schema.properties?.[name]?.type; body[name] = type === 'integer' || type === 'number' ? 1 : type === 'boolean' ? true : type === 'object' ? {} : type === 'array' ? [] : 'example'; }
      setArgumentsText(JSON.stringify(Object.keys(schema.properties ?? {}).length ? { body } : {}, null, 2)); setTestOpen(true); setTestResult(null); setConfirmWrite(false);
      return;
    }
    if (editor.kind === 'python') {
      const body: Record<string, unknown> = {};
      // Required inputs get a sample value; optional ones are left to their defaults.
      for (const p of (packToolOf(editor)?.parameters ?? []).filter(p => p.required)) body[p.name] = p.type === 'boolean' ? true : p.type === 'string' ? (p.name === 'path' ? '/' : 'example') : 1;
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
  async function deploy(action = '') { await run(action ? `${action} deployment` : 'Deploying server', async () => { const path = action ? `/deployments/${action}` : '/deployments'; await api<Deployment>(path, { method: 'POST', body: JSON.stringify({ revision: workspace!.server.revision, ...(action || workspace!.deployment.application_id ? {} : { application_name: deployName.trim() || suggestedName(workspace!.server.name) }) }) }); await refresh(); await api<ServerSummary[]>('/servers').then(setServers); }); }
  async function stopServer() {
    const deployment = workspace!.deployment; const name = deployment.application_name ?? '';
    if (!window.confirm(tr('stop_server_confirm', { name, endpoint: deployment.endpoint ?? '/mcp' }))) return;
    await run('stop deployment', async () => {
      const result = await api<Deployment>('/deployments/stop', { method: 'POST', body: JSON.stringify({ revision: workspace!.server.revision }) });
      await refresh(); await api<ServerSummary[]>('/servers').then(setServers);
      setNotice(tr('notice_server_stopped', { name, status: tr(`deploy_status_${result.status}`) }));
    });
  }
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
  const apiConnections = workspace.connections.filter(c => c.protocol !== 'mcp');
  const mcpConnections = workspace.connections.filter(c => c.protocol === 'mcp');
  const openMcpModal = () => setConnectionModal({ name: '', base_url: '', protocol: 'mcp', auth_mode: 'none' });
  const runtime = workspace.server.runtime;
  const activeCount = workspace.active_tools.length;
  const pendingRelease = workspace.releases.find(r => ['pending', 'applying'].includes(r.status));

  return <div className="application">
    <header className="topbar"><a className="brand" href="/" aria-label={tr('daedalus_home')}><span className="brand-mark"><GitBranch size={22} /></span>daedalus<span className="brand-period">.</span></a><span className="header-divider" /><select aria-label={tr('mcp_server_workspace')} className="server-picker" value={serverId || workspace.server.id} onChange={e => { if (dirty && !window.confirm(tr('confirm_switch_server'))) { e.target.value = serverId || workspace.server.id; return; } setServerId(e.target.value); }}>{servers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>{(() => { const states = servers.map(s => liveState(s)); const running = states.filter(s => s.state === 'running').length; const problem = states.some(s => s.warning || s.state === 'failed'); const down = states.some(s => ['starting', 'offline', 'stopped'].includes(s.state)); const tone = problem ? 'red' : down ? 'amber' : running ? 'green' : ''; const label = tr('servers_running_summary', { running, total: servers.length }); return <button className={`servers-summary ${tone}`} title={tr('all_servers')} aria-label={`${tr('all_servers')}: ${label}`} onClick={() => setServersOpen(true)}><span className={`status-dot ${tone}`} />{label}</button>; })()}<button className="text-button" disabled={!canAuthor} onClick={() => setServerModal(true)}>{tr('new_server')}</button>{(() => { const d = workspace.deployment; const reason = !d.application_id ? tr('stop_server_none') : d.provider === 'manual' ? tr('stop_server_manual', { name: d.application_name ?? '' }) : d.status === 'stopped' && !runtime.online ? tr('stop_server_already', { name: d.application_name ?? '' }) : ''; return <button className="text-button" disabled={!canPublish || !!busy || !!reason} title={reason || tr('stop_server_title', { name: d.application_name ?? '' })} onClick={() => void stopServer()}>{busy === 'stop deployment' ? <LoaderCircle className="spin" size={14} /> : <Square size={13} />}{tr('stop_server')}</button>; })()}<button className="text-button" disabled={!!busy} title={tr('export_title')} onClick={() => void exportServer()}><Download size={14} />{tr('export_server')}</button><button className="text-button" disabled={role !== 'administrator' || !!busy} title={tr('import_title')} onClick={() => importInput.current?.click()}><Upload size={14} />{tr('import_server')}</button><button className="text-button danger" disabled={role !== 'administrator' || !!busy || workspace.server.is_default} title={workspace.server.is_default ? tr('delete_server_default') : tr('delete_server_title')} onClick={() => { setError(''); setDeleteDraft({ confirm: '', deleteApplication: true }); }}><Trash2 size={14} />{tr('delete_server')}</button><input ref={importInput} type="file" accept=".json,application/json" hidden aria-label={tr('import_server')} onChange={e => { const file = e.target.files?.[0]; e.target.value = ''; if (file) void readImport(file); }} /><span className="topbar-spacer" /><a className="icon-button" href={helpUrl} target="_blank" rel="noreferrer" title={tr('help_writing_a_tool_pack')} aria-label={tr('help')}><CircleHelp size={17} /></a><select aria-label={tr('language')} className="language-picker" value={language} onChange={e => setLanguage(e.target.value as 'en' | 'ko')}><option value="en">English</option><option value="ko">한국어</option></select><button className="role-chip" title={tr('signed_in_as', { role: role ? tr(`role_${role}`) : '' })}><span className="avatar">{role?.slice(0, 1).toUpperCase()}</span>{role ? tr(`role_${role}`) : ''}</button>{!openAdmin && <button className="icon-button" title={tr('sign_out')} aria-label={tr('sign_out')} onClick={() => { sessionStorage.removeItem('factory-token'); setToken(''); setWorkspace(null); }}><LogOut size={17} /></button>}</header>
    <div className="workspace-heading"><div><div className="heading-eyebrow"><span>{workspace.server.id.slice(0, 8)}</span></div><h1>{workspace.server.name}<span className="version-pill">{workspace.server.active_release_id ? `v${workspace.releases.filter(r => ['active', 'superseded'].includes(r.status)).length}` : tr('unpublished')}</span></h1><p>{tr('design_test_publish_and_deploy_a')}</p></div><div className="heading-actions"><span className={`runtime-status ${runtime.online && runtime.ready ? 'online' : ''}`}><span className="status-dot" />{runtime.online && runtime.ready ? tr('server_online') : tr('server_offline')}</span><button className="button" onClick={() => { setError(''); setOriginNote(''); setPoliciesOpen(true); }}><ShieldCheck size={16} /> {tr('policies')}</button><button className="button" onClick={openDeployment}><Radio size={16} /> {tr('deploy')}</button><button className="button" onClick={() => setHistory(true)}><History size={16} /> {tr('releases')}</button><button className="button primary" disabled={!canPublish || !!busy || !!pendingRelease || dirty} onClick={() => void run('Preparing review', async () => setPreview(await api<Preview>('/releases/preview')))}>{pendingRelease ? <LoaderCircle className="spin" size={16} /> : <Rocket size={16} />}{pendingRelease ? tr('applying_release') : tr('review_publish')}</button></div></div>
    
    <div className={`workbench ${leftOpen ? '' : 'left-collapsed'} ${rightOpen ? '' : 'right-collapsed'}`}>
      <aside className="palette"><div className="palette-title"><span>{tr('building_blocks')}</span><Box size={15} /></div><div className="panel-toggle-row"><button className="icon-button" aria-label={tr('collapse_building_blocks')} onClick={() => setLeftOpen(false)}><PanelLeftClose size={16} /></button></div><div className="search-box"><Search size={15} /><input aria-label={tr('search_tools')} placeholder={tr('find_a_tool')} value={query} onChange={e => setQuery(e.target.value)} /><kbd>⌕</kbd></div><button className="openapi-button" disabled={!canAuthor} onClick={() => setOpenapiOpen(true)}><span><strong>{tr('import_openapi')}</strong><small>{tr('browse_available_api_operations')}</small></span><ArrowUpRight size={14} /></button><p className="section-label">{tr('components')}</p><button className="component-button" disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({}))} onClick={() => void addTool()}><span className="component-icon"><Braces size={18} /></span><span><strong>{tr('rest_tool')}</strong><small>{tr('turn_an_endpoint_into_a_tool')}</small></span><GripVertical size={15} className="muted" /></button><p className="section-label connection-label">{tr('connections')} <button className="icon-button" aria-label={tr('add_connection')} disabled={role !== 'administrator'} onClick={() => setConnectionModal({ name: '', base_url: workspace.allowed_api_origins[0] })}><Plus size={15} /></button></p>{apiConnections.length === 0 ? <div className="empty-connections"><Unplug size={20} /><p>{tr('no_apis_connected_yet')}</p><button className="text-button" disabled={role !== 'administrator'} onClick={() => setConnectionModal({ name: '', base_url: workspace.allowed_api_origins[0] })}>{tr('add_a_connection')} <Plus size={13} /></button></div> : apiConnections.map(c => <div className="connection-group" key={c.id}><div className="connection-heading"><button className="pack-toggle" onClick={() => choose(c.id)}><Database size={15} /><strong>{c.name}</strong>{c.protocol && c.protocol !== 'rest' && <span className="tiny-tag">{c.protocol === 'mcp' ? 'MCP' : c.protocol === 'webhdfs' ? 'WebHDFS' : 'S3'}</span>}</button>{c.protocol === 'mcp' && (c.discovered?.length ?? 0) > 0 && <button className="text-button" disabled={!canAuthor || !!busy} onClick={() => void addAllMcpTools(c)}>{tr('add_all')}</button>}</div>{c.protocol === 'mcp' ? <div className="operation-list">{c.discovered?.length ? c.discovered.map(d => <button key={d.name} disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({ mcp: { connectionId: c.id, tool: d } }))} onClick={() => void addMcpTool(c, d)} title={d.description}><span className={`method ${d.read_only ? 'read' : 'write'}`}>{d.read_only ? 'READ' : 'WRITE'}</span><span>{d.name}</span><Plus size={12} /></button>) : <p className="field-help">{tr('mcp_discover_hint')}</p>}</div> : (c.protocol ?? 'rest') === 'rest' ? <div className="operation-list">{[{ key: 'inventory', label: tr('op_find_inventory'), method: 'GET' }, { key: 'ticket', label: tr('op_get_ticket'), method: 'GET' }, { key: 'write', label: tr('op_create_ticket'), method: 'POST' }].filter(() => c.base_url === 'http://mock-api:8080').map(op => <button key={op.key} disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({ connectionId: c.id, template: op.key }))} onClick={() => void addTool(c.id, op.key)} title={tr('click_or_drag_onto_the_canvas')}><span className={`method ${op.method.toLowerCase()}`}>{op.method}</span><span>{op.label}</span><Plus size={12} /></button>)}<button className="custom-operation" disabled={!canAuthor || !!busy} onClick={() => void addTool(c.id)}><Plus size={13} /> {tr('custom_operation')}</button></div> : null}</div>)}<p className="section-label connection-label">{tr('mcp_servers')} <button className="icon-button" aria-label={tr('connect_mcp_server')} title={tr('connect_mcp_server')} disabled={role !== 'administrator'} onClick={openMcpModal}><Plus size={15} /></button></p>{mcpConnections.length === 0 ? <div className="empty-connections"><Network size={20} /><p>{tr('no_mcp_servers')}</p><button className="text-button" disabled={role !== 'administrator'} onClick={openMcpModal}>{tr('connect_mcp_server')} <Plus size={13} /></button></div> : mcpConnections.map(c => <div className="connection-group" key={c.id}><div className="connection-heading"><button className="pack-toggle" onClick={() => choose(c.id)}><Database size={15} /><strong>{c.name}</strong>{c.protocol && c.protocol !== 'rest' && <span className="tiny-tag">{c.protocol === 'mcp' ? 'MCP' : c.protocol === 'webhdfs' ? 'WebHDFS' : 'S3'}</span>}</button>{c.protocol === 'mcp' && (c.discovered?.length ?? 0) > 0 && <button className="text-button" disabled={!canAuthor || !!busy} onClick={() => void addAllMcpTools(c)}>{tr('add_all')}</button>}</div>{c.protocol === 'mcp' ? <div className="operation-list">{c.discovered?.length ? c.discovered.map(d => <button key={d.name} disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({ mcp: { connectionId: c.id, tool: d } }))} onClick={() => void addMcpTool(c, d)} title={d.description}><span className={`method ${d.read_only ? 'read' : 'write'}`}>{d.read_only ? 'READ' : 'WRITE'}</span><span>{d.name}</span><Plus size={12} /></button>) : <p className="field-help">{tr('mcp_discover_hint')}</p>}</div> : (c.protocol ?? 'rest') === 'rest' ? <div className="operation-list">{[{ key: 'inventory', label: tr('op_find_inventory'), method: 'GET' }, { key: 'ticket', label: tr('op_get_ticket'), method: 'GET' }, { key: 'write', label: tr('op_create_ticket'), method: 'POST' }].filter(() => c.base_url === 'http://mock-api:8080').map(op => <button key={op.key} disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({ connectionId: c.id, template: op.key }))} onClick={() => void addTool(c.id, op.key)} title={tr('click_or_drag_onto_the_canvas')}><span className={`method ${op.method.toLowerCase()}`}>{op.method}</span><span>{op.label}</span><Plus size={12} /></button>)}<button className="custom-operation" disabled={!canAuthor || !!busy} onClick={() => void addTool(c.id)}><Plus size={13} /> {tr('custom_operation')}</button></div> : null}</div>)}<p className="section-label connection-label">{tr('tool_packs')} <button className="icon-button" aria-label={tr('new_pack')} title={tr('write_a_new_tool_pack')} disabled={role !== 'administrator' || !!busy} onClick={() => void openPackEditor()}><Plus size={15} /></button></p>{packs.length === 0 ? <p className="field-help">{tr('no_tool_packs_yet_administrators_can')}</p> : packs.filter(p => p.tools.length || p.error || p.editable).map(p => <div className={`connection-group pack-group ${openPacks.includes(p.name) ? 'open' : ''}`} key={p.name}><div className="connection-heading"><button className="pack-toggle" aria-expanded={openPacks.includes(p.name)} aria-label={tr('toggle_pack', { name: p.name })} onClick={() => togglePack(p.name)}><ChevronRight size={13} className="pack-chevron" /><Package size={15} /><strong>{p.name}</strong><span className="pack-count">{p.tools.length}</span></button>{p.origin === 'project' && <span className="tiny-tag">{tr('project_2')}</span>}<button className="text-button" disabled={!canAuthor || !!busy || !!p.error} onClick={() => void addAllPackTools(p)}>{tr('add_all')}</button></div>{openPacks.includes(p.name) && <><small className="pack-description">{p.error ? <span className="error">{tr('cannot_load', { error: p.error ?? '' })}</span> : p.description}{!p.error && p.tools.some(t => t.requires_connection) && !workspace.connections.some(c => (c.protocol ?? 'rest') === p.protocol) && <span className="pack-hint"> {tr('needs_protocol_connection', { protocol: tr(`protocol_${p.protocol}`) })}</span>}</small><div className="pack-actions"><button className="text-button" disabled={!!busy} onClick={() => void viewSource(p.name)}><Braces size={12} /> {tr('view_code')}</button>{p.editable && <button className="text-button" disabled={role !== 'administrator' || !!busy} onClick={() => void openPackEditor(p)}><Settings2 size={12} /> {tr('edit')}</button>}{p.editable && <button className="text-button danger" disabled={role !== 'administrator' || !!busy} onClick={() => void deletePack(p)}><Trash2 size={12} /> {tr('delete')}</button>}</div><div className="operation-list">{p.tools.map(t => <button key={t.function} disabled={!canAuthor || !!busy} draggable={canAuthor} onDragStart={e => e.dataTransfer.setData('application/daedalus', JSON.stringify({ pack: p.name, tool: t }))} onClick={() => void addPackTool(p.name, t)} title={t.description}><span className={`method ${t.effect}`}>{t.effect.toUpperCase()}</span><span>{t.function}{t.requires_connection ? <small> {tr('uses_an_api')}</small> : null}</span><Plus size={12} /></button>)}</div></>}</div>)}<div className="palette-bottom"><div className="legend"><span><i className="legend-line" /> {tr('relationship')}</span><span><i className="legend-dot" /> {tr('draft')}</span></div></div></aside>
      <main className="canvas-area">{(error || notice || runtime.last_error) && <div key={error || runtime.last_error || notice} className={`message-bar ${error || runtime.last_error ? 'failure' : ''}`} role={error ? 'alert' : 'status'}><span>{error || runtime.last_error || notice}</span><button className="icon-button" aria-label={tr('dismiss_message')} onClick={() => { setError(''); setNotice(''); }}><X size={15} /></button></div>}<div className="canvas-toolbar"><div className="view-switch"><button className={view === 'canvas' ? 'active' : ''} onClick={() => setView('canvas')}><LayoutGrid size={14} /> {tr('canvas')}</button><button className={view === 'list' ? 'active' : ''} onClick={() => setView('list')}><List size={15} /> {tr('list')}</button></div>{!leftOpen && <button className="icon-button canvas-panel-toggle" aria-label={tr('show_building_blocks')} onClick={() => setLeftOpen(true)}><PanelLeftOpen size={16} /></button>}<span className="canvas-count">{tr('n_tools', { count: workspace.tools.length })} <span>·</span> {tr('n_connections', { count: workspace.connections.length })}</span><span className="toolbar-spacer" />{!editor && selectedConnection && <button className="button small-button danger-button" disabled={!!busy || !canAuthor} onClick={() => void removeNode('connection', selectedConnection.id, selectedConnection.name, selectedConnection.revision)}><Trash2 size={14} />{tr('remove_connection')}</button>}{editor && <button className="button small-button danger-button" disabled={!!busy || dirty || !canAuthor} title={dirty ? tr('save_or_discard_your_inspector_changes_2') : undefined} onClick={() => void removeNode('tool', editor.id, editor.name, editor.revision)}><Trash2 size={14} />{tr('remove_tool')}</button>}<span className="save-indicator">{layoutSaving ? <LoaderCircle size={13} className="spin" /> : <CheckCheck size={14} />}{layoutSaving ? tr('saving_layout') : tr('layout_saved')}</span>{!rightOpen && <button className="icon-button canvas-panel-toggle" aria-label={tr('show_inspector')} onClick={() => setRightOpen(true)}><PanelRightOpen size={16} /></button>}</div>
        <div className={`graph-container ${testOpen ? 'with-test' : ''}`} onDragOver={e => { if (canAuthor) { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; } }} onDrop={e => { e.preventDefault(); if (!canAuthor) return; try { const data = JSON.parse(e.dataTransfer.getData('application/daedalus')); const at = flow.screenToFlowPosition({ x: e.clientX, y: e.clientY }); if (data.mcp) { const target = latest.current?.connections.find(c => c.id === data.mcp.connectionId); if (target) void addMcpTool(target, data.mcp.tool, at); } else if (data.pack) void addPackTool(data.pack, data.tool, at); else void addTool(data.connectionId, data.template, at); } catch { setError(tr('drag_an_operation_from_the_building')); } }}>
          {view === 'canvas' ? <ReactFlow<CardNode> nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.23 }} minZoom={0.3} maxZoom={1.4} nodesDraggable={canAuthor && !layoutSaving} nodesConnectable={canAuthor && !dirty && !busy} deleteKeyCode={null} onNodesChange={(changes: NodeChange<CardNode>[]) => setNodes(n => applyNodeChanges(changes, n))} onNodeClick={(_, node) => choose(node.id)} onNodeDragStop={(_, node) => { positions.current[node.id] = node.position; void savePositions({ ...workspace.layout.positions, [node.id]: node.position }); }} onConnect={connect} isValidConnection={c => { const tool = workspace.tools.find(t => t.id === c.source); const target = workspace.connections.find(a => a.id === c.target); return Boolean(tool && target && compatible(tool, target)); }}><Background color="#d1d8df" gap={22} size={1} /><Controls showInteractive={false} /></ReactFlow> : <div className="tool-table"><div className="table-head"><span>{tr('tool')}</span><span>{tr('endpoint')}</span><span>{tr('status')}</span></div>{workspace.tools.filter(t => `${t.name} ${t.description}`.toLowerCase().includes(query.toLowerCase())).map(t => <button className={`table-row ${selected === t.id ? 'selected' : ''}`} key={t.id} onClick={() => choose(t.id)}><span><Braces size={16} /><strong>{t.name}</strong></span><span><b className={`method ${toolLabel(t).method.toLowerCase()}`}>{toolLabel(t).method}</b>{toolLabel(t).subtitle}</span><span className={`tool-status ${status(t).toLowerCase()}`}>{statusLabel(tr, status(t))}</span></button>)}</div>}
          {workspace.tools.length === 0 && !welcomeHidden.includes(workspace.server.id) && <div className="canvas-welcome"><button className="icon-button welcome-close" aria-label={tr('close_welcome')} title={tr('close_welcome')} onClick={() => hideWelcome(workspace.server.id)}><X size={16} /></button><div className="welcome-symbol"><Network size={35} strokeWidth={1.4} /></div><p className="eyebrow">{tr('a_blank_canvas_endless_capability')}</p><h2>{tr('what_will_your_server_do')}</h2><p>{tr('bring_an_api_into_your_workspace')}<br />{tr('then_turn_its_operations_into_useful')}</p><button className="button primary" disabled={!!busy || (!workspace.connections.length ? role !== 'administrator' : !canAuthor)} onClick={() => workspace.connections.length ? void addTool(workspace.connections[0].id, 'inventory') : setConnectionModal({ name: 'Demo APIs', base_url: workspace.allowed_api_origins[0] })}><Plus size={16} />{workspace.connections.length ? tr('add_your_first_tool') : tr('connect_your_first_api')}</button><span className="welcome-hint">{tr('start_with_the_included_inventory_and')}</span></div>}
        </div>
        {testOpen && editor && <section className="test-drawer"><div className="drawer-heading"><FlaskConical size={17} /><strong>{tr('tool_playground')}</strong><span className="tiny-tag">{tr('isolated_draft_test')}</span><span className="toolbar-spacer" /><button className="icon-button" aria-label={tr('close_playground')} onClick={() => setTestOpen(false)}><X size={17} /></button></div><div className="test-columns"><div><label htmlFor="arguments">{tr('arguments')} <span>{tr('path_query_body')}</span></label><textarea id="arguments" spellCheck={false} value={argumentsText} onChange={e => setArgumentsText(e.target.value)} />{editor.effect === 'write' && <label className="checkbox-row"><input type="checkbox" checked={confirmWrite} onChange={e => setConfirmWrite(e.target.checked)} />{tr('i_authorize_this_live_write_to')}</label>}<button className="button primary small-button" disabled={!canAuthor || !!busy || dirty || (editor.effect === 'write' && !confirmWrite)} onClick={() => void runTest()}>{busy === 'Testing' ? <LoaderCircle size={14} className="spin" /> : <Play size={14} />}{tr('run_test')}</button></div><div className="output-column"><div className="output-tabs" role="tablist"><button role="tab" aria-selected={drawerTab === 'logs'} className={drawerTab === 'logs' ? 'active' : ''} onClick={() => setDrawerTab('logs')}>{tr('logs')}</button>{testResult && <button role="tab" aria-selected={drawerTab === 'result'} className={drawerTab === 'result' ? 'active' : ''} onClick={() => setDrawerTab('result')}>{tr('result')}</button>}<span className="toolbar-spacer" />{testResult && <span className={testResult.success ? 'success-text' : 'error'}>{testResult.success ? tr('passed') : tr('failed')} · {String(testResult.duration_ms)} ms</span>}</div>{drawerTab === 'result' && testResult ? <pre className="result-output" role="tabpanel">{JSON.stringify(testResult.result || testResult.error, null, 2)}</pre> : <div className="log-output" role="tabpanel" aria-live="polite" ref={logRef}>{testLog.length ? testLog.map((entry, i) => <div key={i} className={`log-line ${entry.level}`}><time>{new Date(entry.at).toLocaleTimeString(locale, { hour12: false })}</time><span>{logText(entry)}</span></div>) : <div className="result-placeholder"><Braces size={24} /><p>{tr('log_empty')}</p><small>{tr('tests_use_agentgateway_without_publishing_the')}</small></div>}{busy === 'Testing' || busy === 'Validating' ? <div className="log-line info"><time /><span><LoaderCircle size={11} className="spin" /> {tr('log_working')}</span></div> : null}</div>}</div></div></section>}
        <div className="canvas-footer"><span><GitBranch size={13} /> {tr('working_draft')}</span><span>{tr('layout_changes_never_affect_the_live')}</span><span className="toolbar-spacer" /><span>{tr('n_published_tools', { count: activeCount })}</span></div>
      </main>
      <aside className="inspector"><div className="inspector-heading"><Settings2 size={16} /><span>{tr('inspector')}</span>{editor && <span className={`tool-status ${dirty ? 'draft' : status(editor).toLowerCase()}`}>{dirty ? tr('unsaved') : statusLabel(tr, status(editor))}</span>}<button className="icon-button panel-heading-toggle" aria-label={tr('collapse_inspector')} onClick={() => setRightOpen(false)}><PanelRightClose size={16} /></button></div>
        {editor ? <><div className="inspector-body"><div className="inspector-intro"><span className="icon-tile small"><Braces size={20} /></span><div><h2>{tr('configure_tool')}</h2><p>{tr('shape_what_your_agent_can_do')}</p></div></div><fieldset disabled={!canAuthor || !!busy}><label>{tr('tool_name')}<input value={editor.name} onChange={e => edit({ name: e.target.value })} placeholder="get_inventory_item" /></label><label>{tr('description')}<textarea rows={3} value={editor.description} onChange={e => edit({ description: e.target.value })} placeholder={tr('explain_when_and_how_to_use')} /></label>{editor.kind === 'mcp' ? <><div className="form-divider" /><p className="section-label">{tr('mcp_tool')}</p><label>{tr('upstream_server')}<select value={editor.connection_id ?? ''} onChange={e => edit({ connection_id: e.target.value })}>{workspace.connections.filter(c => compatible(editor, c)).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><div className="detail-row"><span>{tr('upstream_tool')}</span><code>{editor.upstream_tool}</code></div><button className="text-button" type="button" onClick={() => setSourceView({ title: tr('input_schema_title', { name: editor.upstream_tool ?? '' }), subtitle: tr('input_schema_subtitle'), source: JSON.stringify(editor.input_schema ?? {}, null, 2) })}><Braces size={13} /> {tr('view_input_schema')}</button><label>{tr('side_effects')}<select value={editor.effect} onChange={e => edit({ effect: e.target.value as 'read' | 'write' })}><option value="read">{tr('read_data')}</option><option value="write">{tr('write_or_change_data')}</option></select></label><p className="field-help">{tr('mcp_effect_help')}</p><div className="form-divider" /><p className="section-label">{tr('input_parameters')} <span>{Object.keys(editor.input_schema?.properties ?? {}).length}</span></p>{Object.entries(editor.input_schema?.properties ?? {}).map(([name, property]) => <div className="detail-row" key={name}><span>{name}{editor.input_schema?.required?.includes(name) ? '' : tr('optional_suffix')}</span><code>{String(property.type ?? 'any')}</code></div>)}{!Object.keys(editor.input_schema?.properties ?? {}).length && <p className="field-help">{tr('no_inputs_agents_call_this_tool')}</p>}<p className="field-help">{tr('mcp_inputs_help')}</p></> : editor.kind === 'python' ? <><div className="form-divider" /><p className="section-label">{tr('python_tool')}</p><div className="detail-row"><span>{tr('pack_function')}</span><code>{editor.pack}.{editor.function}</code></div><button className="text-button" type="button" disabled={!!busy} onClick={() => void viewSource(editor.pack!, editor.function)}><Braces size={13} /> {tr('view_source')}</button><div className="detail-row"><span>{tr('side_effects')}</span><strong>{editor.effect === 'write' ? tr('write_or_change_data') : tr('read_data')}</strong></div>{packToolOf(editor)?.requires_connection ? <label>{tr('connection')}<select value={editor.connection_id ?? ''} onChange={e => edit({ connection_id: e.target.value })}><option value="" disabled>{tr('choose_a_connection')}</option>{workspace.connections.filter(c => compatible(editor, c)).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label> : <p className="field-help">{tr('this_tool_runs_in_the_python')}</p>}<div className="form-divider" /><p className="section-label">{tr('input_parameters')} <span>{packToolOf(editor)?.parameters.length ?? 0}</span></p>{packToolOf(editor)?.parameters.length ? packToolOf(editor)!.parameters.map(p => <div className="detail-row" key={p.name}><span>{p.name}{p.required ? '' : tr('optional_suffix')}</span><code>{p.type}</code></div>) : <p className="field-help">{tr('no_inputs_agents_call_this_tool')}</p>}<p className="field-help">{tr('inputs_are_defined_by_the_pack')} <code>body</code>.</p><label>{tr('configuration_json')}<textarea className="code-input" rows={4} spellCheck={false} value={configText} onChange={e => { setConfigText(e.target.value); setDirty(true); }} placeholder="{}" /></label></> : <><div className="form-divider" /><p className="section-label">{tr('api_operation')}</p><label>{tr('connection')}<select value={editor.connection_id ?? ''} onChange={e => edit({ connection_id: e.target.value })}>{workspace.connections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><div className="endpoint-input"><label>{tr('method')}<select value={editor.method} onChange={e => edit({ method: e.target.value as 'GET' | 'POST', effect: e.target.value === 'POST' ? 'write' : editor.effect })}><option>GET</option><option>POST</option></select></label><label>{tr('path')}<input value={editor.path} onChange={e => edit({ path: e.target.value })} placeholder="/items/{item_id}" /></label></div><label>{tr('side_effects')}<select value={editor.effect} onChange={e => edit({ effect: e.target.value as 'read' | 'write' })}><option value="read">{tr('read_data')}</option><option value="write">{tr('write_or_change_data')}</option></select></label><p className="field-help">{tr('classify_the_actual_api_behavior_write')}</p><div className="form-divider" /><div className="parameters-heading"><p className="section-label">{tr('input_parameters')} <span>{editor.parameters.length}</span></p><button className="icon-button" aria-label={tr('add_parameter')} onClick={() => edit({ parameters: [...editor.parameters, { name: `parameter_${editor.parameters.length + 1}`, location: 'query', type: 'string', required: false, description: '' }] })}><Plus size={16} /></button></div>{editor.parameters.map((p, i) => <div className="parameter-card" key={i}><div className="parameter-top"><input aria-label={tr('parameter_n_name', { n: i + 1 })} value={p.name} onChange={e => editParameter(i, { name: e.target.value })} /><button className="icon-button" aria-label={tr('remove_parameter_n', { n: i + 1 })} onClick={() => edit({ parameters: editor.parameters.filter((_, j) => i !== j) })}><Trash2 size={14} /></button></div><div className="parameter-options"><select aria-label={tr('parameter_n_location', { n: i + 1 })} value={p.location} onChange={e => editParameter(i, { location: e.target.value as 'path' | 'query', required: e.target.value === 'path' ? true : p.required })}><option value="path">{tr('path')}</option><option value="query">{tr('query')}</option></select><select aria-label={tr('parameter_n_type', { n: i + 1 })} value={p.type} onChange={e => editParameter(i, { type: e.target.value as Parameter['type'] })}>{['string', 'integer', 'number', 'boolean'].map(t => <option key={t}>{t}</option>)}</select><label className="checkbox-row"><input type="checkbox" checked={p.required} onChange={e => editParameter(i, { required: e.target.checked })} />{tr('required')}</label></div></div>)}{editor.parameters.length === 0 && <p className="field-help">{tr('no_parameters_yet_add_path_or')}</p>}{editor.method === 'POST' && <label>{tr('json_body_schema')}<textarea className="code-input" rows={7} value={bodyText} onChange={e => { setBodyText(e.target.value); setDirty(true); }} placeholder={'{"type":"object","properties":{}}'} /></label>}</>}<div className="form-divider" /><label className="checkbox-row include-tool"><input type="checkbox" checked={editor.enabled} onChange={e => edit({ enabled: e.target.checked })} /><span>{tr('include_in_next_release')}<small>{tr('excluding_a_tool_takes_effect_when')}</small></span></label></fieldset></div><div className="inspector-actions"><div><button className="button" disabled={!!busy || dirty || !canAuthor} onClick={() => void validateTool()}><Check size={15} />{tr('validate')}</button><button className="button" disabled={!!busy || dirty || !canAuthor} onClick={openTest}><FlaskConical size={15} />{tr('test_tool')}</button></div><button className="button primary full-width" disabled={!dirty || !!busy || !canAuthor} onClick={() => void saveEditor()}>{busy === 'Saving' ? <LoaderCircle className="spin" size={16} /> : <Save size={16} />}{tr('save_draft')}</button>{dirty && <button className="text-button discard" onClick={() => { setDirty(false); const tool = workspace.tools.find(t => t.id === editor.id)!; setEditor(tool); setBodyText(tool.body_schema ? JSON.stringify(tool.body_schema, null, 2) : ''); setConfigText(JSON.stringify(tool.config ?? {}, null, 2)); }}>{tr('discard_changes')}</button>}</div></> : selectedConnection ? <div className="inspector-body"><span className="icon-tile"><Database size={26} /></span><h2>{selectedConnection.name}</h2><p className="muted">{tr('a_reusable_connection_for_your_rest')}</p><label>{tr('approved_base_url')}<code className="endpoint-display">{selectedConnection.base_url}</code></label><div className="detail-row"><span>{tr('protocol')}</span><strong>{tr(`protocol_${selectedConnection.protocol ?? 'rest'}`)}</strong></div><div className="detail-row"><span>{tr('authentication')}</span><strong>{tr(`auth_${(selectedConnection.auth_mode || 'none').replace('-token', '').replace('-doas', '').replace('s3-sigv4', 's3')}`)}{selectedConnection.secret_ref ? ` · ${selectedConnection.secret_ref}` : ''}{selectedConnection.proxy_principal ? ` · ${selectedConnection.proxy_principal}` : ''}</strong></div><div className="detail-row"><span>{tr('revision')}</span><strong>{selectedConnection.revision}</strong></div><div className="detail-row"><span>{tr('last_check')}</span><strong className={selectedConnection.probe_summary ? (selectedConnection.probe_summary.success ? 'success-text' : 'error') : ''}>{selectedConnection.probe_summary ? translateError(selectedConnection.probe_summary.message) : tr('not_checked')}</strong></div>{selectedConnection.probe_summary && <p className="field-help">{new Date(selectedConnection.probe_summary.checked_at).toLocaleString(locale)} · {selectedConnection.probe_summary.duration_ms} ms{selectedConnection.probe_summary.pack ? ` · ${selectedConnection.probe_summary.pack}.probe` : ''}</p>}<button className="button full-width" disabled={!!busy || !canAuthor} onClick={() => void checkConnection(selectedConnection)}>{busy === 'Checking connection' ? <LoaderCircle className="spin" size={16} /> : <FlaskConical size={16} />}{tr('check_connection')}</button>{selectedConnection.protocol === 'mcp' && <><p className="section-label">{tr('discovered_tools')} <span>{selectedConnection.discovered?.length ?? 0}</span></p>{selectedConnection.discovered?.length ? selectedConnection.discovered.map(t => <div className="detail-row" key={t.name}><code>{t.name}</code><small>{t.description.slice(0, 80)}</small></div>) : <p className="field-help">{tr('not_checked')}</p>}<p className="field-help">{selectedConnection.federate ? tr('federate_on') : tr('federate_off')}</p></>}<button className="button full-width" disabled={role !== 'administrator'} onClick={() => setConnectionModal(selectedConnection)}><Settings2 size={16} />{tr('edit_connection')}</button><p className="field-help">{tr('changing_a_connection_requires_affected_tools')}</p></div> : <div className="inspector-overview"><span className="icon-tile"><Server size={25} /></span><h2>{tr('your_server_at_a_glance')}</h2><p>{tr('choose_a_tool_or_connection_on')}</p>{(() => { const summary = servers.find(s => s.id === workspace.server.id); const { state, warning } = liveState(summary); const url = workspace.deployment.endpoint || workspace.server.mcp_url; const live = runtime.effective_release_id; const latest = workspace.server.active_release_id; return <section className={`live-card ${state}`} aria-label={tr('live_card_label')}><div className="live-head"><span className={`live-pill ${state}`}><span className="status-dot" />{tr(`live_${state}`)}</span>{workspace.deployment.application_name && <small>{workspace.deployment.application_name}</small>}</div><p className="section-label">{tr('mcp_endpoint')}</p><div className="live-url"><code>{url}</code><button className="icon-button" aria-label={tr('copy_url')} title={tr('copy_url')} onClick={() => { void navigator.clipboard?.writeText(url).then(() => setNotice(tr('url_copied')), () => setError(tr('copy_failed'))); }}><Copy size={14} /></button></div>{state === 'running' && <p className={`live-line ${live && latest && live !== latest ? 'warn' : ''}`}>{!latest ? tr('live_no_release') : live === latest ? tr('live_latest', { release: latest.slice(0, 8) }) : tr('live_behind', { live: live?.slice(0, 8) ?? tr('none'), latest: latest.slice(0, 8) })}</p>}{summary?.runtime?.online && <p className="live-line">{tr('live_heartbeat', { age: summary.runtime.heartbeat_age ?? 0, host: summary.runtime.host ?? '?' })}</p>}{state === 'not_deployed' && <p className="live-line">{tr('live_not_deployed_hint')}</p>}{['stopped', 'failed', 'offline'].includes(state) && <p className="live-line">{tr('live_down_hint')}</p>}{warning && <p className="error">{warning}</p>}<small>{tr('use_your_separate_mcp_token_to')}</small><button className="text-button" onClick={openDeployment}><Radio size={13} />{tr('live_open_deploy')}</button></section>; })()}<div className="overview-stat"><span>{tr('draft_tools')}</span><strong>{workspace.tools.length}</strong></div><div className="overview-stat"><span>{tr('published_tools')}</span><strong>{activeCount}</strong></div><div className="overview-stat"><span>{tr('connections_2')}</span><strong>{workspace.connections.length}</strong></div><div className="workflow-steps"><p className="section-label">{tr('steps_to_create')}</p>{progress(workspace).map((step, i) => <div key={step.key} className={step.done ? 'done' : ''} role="checkbox" aria-checked={step.done} aria-readonly="true" title={tr(`step_${step.key}_hint`)}><span className="step-box">{step.done ? <Check size={12} strokeWidth={3} /> : i + 1}</span>{tr(`step_${step.key}`)}</div>)}</div></div>}
      </aside>
    </div>
    {policiesOpen && <Modal title={tr('api_access_policies')} subtitle={tr('policies_subtitle')} close={() => setPoliciesOpen(false)}><div className="policy-list">{origins.map(origin => <div className="policy-row" key={origin.id}><div><strong>{origin.origin}</strong><small>{origin.description || tr('no_description')}{origin.bootstrap ? ' · bootstrap' : ''}</small></div>{origin.bootstrap ? <span className="tiny-tag">{tr('environment')}</span> : <button className="icon-button" aria-label={tr('remove_x', { name: origin.origin })} onClick={() => void removeOrigin(origin)}><Trash2 size={15} /></button>}</div>)}</div><form onSubmit={addOrigin} className="policy-form"><label>{tr('api_origin')}<input required type="url" value={originDraft.origin} onChange={e => setOriginDraft({ ...originDraft, origin: e.target.value })} placeholder="https://api.example.com" /></label><label>{tr('description')}<input value={originDraft.description} onChange={e => setOriginDraft({ ...originDraft, description: e.target.value })} placeholder={tr('customer_support_api')} /></label>{error && <p className="error" role="alert">{error}</p>}{originNote && <p className="success-text" role="status">{originNote}</p>}<button className="button primary full-width" disabled={!!busy}><Plus size={15} />{tr('approve_origin')}</button></form><p className="field-help policy-help">{tr('origins_must_be_scheme_and_host')}</p></Modal>}{openapiOpen && <Modal title={tr('import_an_openapi_document')} subtitle={tr('openapi_subtitle')} close={() => setOpenapiOpen(false)}><form onSubmit={e => { e.preventDefault(); void discoverOpenAPI(); }}><label>{tr('swagger_or_openapi_url')}<input autoFocus required type="url" value={openapiUrl} onChange={e => setOpenapiUrl(e.target.value)} placeholder="https://api.example.com/openapi.json" /></label><p className="field-help">{tr('the_builder_fetches_the_document_server')}</p><button className="button primary full-width" disabled={openapiBusy || !openapiUrl.trim()} type="submit">{openapiBusy ? <LoaderCircle className="spin" size={16} /> : <Search size={16} />}{tr('find_api_operations')}</button></form>{openapi && <><div className="detail-row"><span>{openapi.title} {openapi.version && `· v${openapi.version}`}</span><code>{openapi.base_url}</code></div>{openapi.truncated && <p className="field-help">{tr('showing_the_first_200_operations')}</p>}<div className="openapi-results">{openapi.operations.length ? openapi.operations.map((operation, index) => <button className="openapi-operation" disabled={operation.supported === false} key={`${operation.method}-${operation.path}-${index}`} onClick={() => void selectOperation(operation)}><b className={`method ${operation.method.toLowerCase()}`}>{operation.method}</b><code>{operation.path}</code><small>{operation.supported === false ? tr('not_supported_profile') : operation.name}</small>{operation.supported === false ? <span className="tiny-tag">{tr('preview')}</span> : <Plus size={14} />}</button>) : <p className="openapi-empty">{tr('no_operations_were_found')}</p>}</div></>}</Modal>}
    {connectionModal && <Modal title={connectionModal.protocol === 'mcp' ? (connectionModal.id ? tr('edit_mcp_server') : tr('connect_mcp_server')) : connectionModal.id ? tr('edit_api_connection') : tr('connect_an_api')} subtitle={tr('connection_subtitle')} close={closeConnection}><form onSubmit={(e: FormEvent) => { e.preventDefault(); let saved: Connection | undefined; void run('Saving connection', async () => { const data = { name: connectionModal.name, base_url: connectionModal.base_url, protocol: connectionModal.protocol || 'rest', federate: connectionModal.protocol === 'mcp' ? Boolean(connectionModal.federate) : false, auth_mode: connectionModal.auth_mode || 'none', secret_ref: connectionModal.secret_ref || '', proxy_principal: connectionModal.proxy_principal || '', keytab_ref: connectionModal.keytab_ref || '', doas_parameter: connectionModal.doas_parameter || 'doAs' }; saved = await api<Connection>(connectionModal.id ? `/connections/${connectionModal.id}` : '/connections', { method: connectionModal.id ? 'PATCH' : 'POST', headers: connectionModal.id ? { 'If-Match': String(connectionModal.revision) } : {}, body: JSON.stringify(data) }); setConnectionModal(null); setSelected(saved.id); setEditor(null); await refresh(); if (pendingOperation) await addImportedTool(saved.id, pendingOperation); else if (pendingPackTool) { const pending = pendingPackTool; setPendingPackTool(null); await addPackTool(pending.pack, pending.tool, undefined, saved.id); } else setNotice(tr('api_connection_saved_add_an_operation')); }).then(() => { if (saved) void checkConnection(saved); }); }}><label>{tr('connection_name')}<input autoFocus required maxLength={80} value={connectionModal.name || ''} onChange={e => setConnectionModal({ ...connectionModal, name: e.target.value })} placeholder={tr('inventory_api')} /></label><label>{tr('base_url')}<input required value={connectionModal.base_url || ''} onChange={e => setConnectionModal({ ...connectionModal, base_url: e.target.value })} placeholder={connectionModal.protocol === 'mcp' ? 'https://helios.example.cloudera.site/mcp' : 'http://mock-api:8080'} /></label><label>{tr('protocol')}<select value={connectionModal.protocol || 'rest'} onChange={e => { const protocol = e.target.value as Protocol; setConnectionModal({ ...connectionModal, protocol, auth_mode: protocol === 's3' ? 's3-sigv4' : connectionModal.auth_mode === 's3-sigv4' ? 'none' : connectionModal.auth_mode }); }}><option value="rest">{tr('protocol_rest')}</option><option value="webhdfs">{tr('protocol_webhdfs')}</option><option value="s3">{tr('protocol_s3')}</option><option value="mcp">{tr('protocol_mcp')}</option></select></label><p className="field-help">{tr('protocol_help')}</p>{connectionModal.protocol === 'mcp' && <><label className="checkbox-row"><input type="checkbox" checked={Boolean(connectionModal.federate)} onChange={e => setConnectionModal({ ...connectionModal, federate: e.target.checked })} />{tr('federate_label')}</label><p className="field-help">{tr('federate_help')}</p></>}<label>{tr('authentication')}<select value={connectionModal.auth_mode || 'none'} onChange={e => setConnectionModal({ ...connectionModal, auth_mode: e.target.value as Connection['auth_mode'] })}><option value="none">{tr('auth_none')}</option><option value="static">{tr('auth_static')}</option><option value="forward-token">{tr('auth_forward')}</option><option value="proxy-doas">{tr('auth_proxy')}</option><option value="s3-sigv4">{tr('auth_s3')}</option></select></label>{connectionModal.auth_mode === 's3-sigv4' && <><label>{tr('secret_ref')}<input required pattern="FACTORY_SECRET_[A-Z0-9_]+" value={connectionModal.secret_ref || ''} onChange={e => setConnectionModal({ ...connectionModal, secret_ref: e.target.value })} placeholder="FACTORY_SECRET_OZONE" /></label><p className="field-help">{tr('auth_help_s3')}</p></>}{connectionModal.auth_mode === 'static' && <><label>{tr('secret_ref')}<input required pattern="FACTORY_SECRET_[A-Z0-9_]+" value={connectionModal.secret_ref || ''} onChange={e => setConnectionModal({ ...connectionModal, secret_ref: e.target.value })} placeholder="FACTORY_SECRET_INVENTORY" /></label><p className="field-help">{tr('secret_ref_help')}</p></>}{connectionModal.auth_mode === 'forward-token' && <p className="field-help">{tr('auth_help_forward')}</p>}{connectionModal.auth_mode === 'proxy-doas' && <><label>{tr('proxy_principal')}<input required value={connectionModal.proxy_principal || ''} onChange={e => setConnectionModal({ ...connectionModal, proxy_principal: e.target.value })} placeholder="svc_mcp@EXAMPLE.COM" /></label><label>{tr('keytab_ref')}<input required pattern="FACTORY_SECRET_[A-Z0-9_]+" value={connectionModal.keytab_ref || ''} onChange={e => setConnectionModal({ ...connectionModal, keytab_ref: e.target.value })} placeholder="FACTORY_SECRET_KEYTAB" /></label><label>{tr('doas_parameter')}<input value={connectionModal.doas_parameter || 'doAs'} onChange={e => setConnectionModal({ ...connectionModal, doas_parameter: e.target.value })} /></label><p className="field-help">{tr('auth_help_proxy')}</p></>}<p className="field-help">{tr('approved_origins', { origins: workspace.allowed_api_origins.join(', ') })}</p><div className="inline-info"><ShieldCheck size={19} /><p>{tr('this_first_profile_connects_to_apis')}</p></div>{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy} type="submit">{busy ? <LoaderCircle className="spin" size={16} /> : <Plus size={16} />}{tr('save_connection')}</button></form></Modal>}
    {sourceView && <Modal title={sourceView.title} subtitle={sourceView.subtitle} close={() => setSourceView(null)}><pre className="result-output source-view">{sourceView.source}</pre></Modal>}
    {packEditor && <Modal title={packEditor.existing ? tr('edit_pack_title', { name: packEditor.name }) : tr('new_tool_pack')} subtitle={tr('pack_editor_subtitle')} close={() => setPackEditor(null)}><form onSubmit={e => { e.preventDefault(); void savePack(); }}>{!packEditor.existing && <label>{tr('pack_name')}<input autoFocus required pattern="[a-z][a-z0-9_]{0,29}" title={tr('lowercase_letters_digits_and_underscores_starts')} value={packEditor.name} onChange={e => setPackEditor({ ...packEditor, name: e.target.value })} placeholder="hdfs_files" /></label>}<label>{tr('python_source')}<textarea className="code-input source-editor" rows={18} spellCheck={false} value={packEditor.source} onChange={e => setPackEditor({ ...packEditor, source: e.target.value })} /></label><p className="field-help">{tr('each_tool_is_a_function_decorated')} <code>@pack_tool(effect=…, requires_connection=…)</code> {tr('whose_first_parameter_is')} <code>ctx: ToolContext</code>. Typed parameters (str, int, float, bool) become the tool's inputs; the docstring becomes its description. <a href={helpUrl} target="_blank" rel="noreferrer">{tr('read_the_how_to_guide')}</a>.</p>{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy || !packEditor.name.trim() || !packEditor.source.trim()} type="submit">{busy === 'Saving pack' ? <LoaderCircle className="spin" size={16} /> : <Save size={16} />}{tr('save_pack')}</button></form></Modal>}
    {importDraft && <Modal title={tr('import_dialog_title')} subtitle={tr('import_dialog_subtitle')} close={() => { setImportDraft(null); setError(''); }}>{importDraft.result ? <div className="import-result"><p className="success-text" role="status">{tr('import_done', { name: importDraft.result.server.name, tools: importDraft.result.tools, connections: importDraft.result.connections })}</p><p className="section-label">{tr('import_secrets')}</p>{importDraft.result.required_secrets.length ? <pre className="result-output manifest-env">{importDraft.result.required_secrets.join('\n')}</pre> : <p className="field-help">{tr('import_secrets_none')}</p>}{importDraft.result.packs_written.length > 0 && <p className="field-help">{tr('import_packs_written', { packs: importDraft.result.packs_written.join(', ') })}</p>}<p className="field-help">{tr('import_next')}</p><button className="button primary full-width" onClick={() => { setServerId(importDraft.result!.server.id); setImportDraft(null); }}>{tr('import_open')}</button></div> : (() => { const doc = importDraft.document as { format?: string; tools?: unknown[]; connections?: unknown[]; packs?: Record<string, string>; required_secrets?: string[] }; const packNames = Object.keys(doc.packs ?? {}); return <form onSubmit={e => { e.preventDefault(); void submitImport(); }}><div className="detail-row"><span>{tr('import_file')}</span><code>{importDraft.fileName}</code></div><div className="detail-row"><span>{tr('import_contents')}</span><strong>{tr('import_summary', { tools: doc.tools?.length ?? 0, connections: doc.connections?.length ?? 0, packs: packNames.length })}</strong></div>{doc.required_secrets?.length ? <div className="detail-row"><span>{tr('import_secrets')}</span><code>{doc.required_secrets.join(', ')}</code></div> : null}<label>{tr('import_name')}<input required maxLength={80} value={importDraft.name} onChange={e => setImportDraft({ ...importDraft, name: e.target.value })} /></label>{packNames.length > 0 && <label className="checkbox-row"><input type="checkbox" checked={importDraft.replacePacks} onChange={e => setImportDraft({ ...importDraft, replacePacks: e.target.checked })} />{tr('import_replace_packs', { packs: packNames.join(', ') })}</label>}{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy || !importDraft.name.trim() || doc.format !== 'daedalus-server/v1'} type="submit">{busy === 'Importing' ? <LoaderCircle className="spin" size={16} /> : <Upload size={16} />}{tr('import_button')}</button></form>; })()}</Modal>}
    {serversOpen && <Modal title={tr('servers_title')} subtitle={tr('servers_subtitle')} close={() => setServersOpen(false)}><div className="server-list">{servers.map(s => { const pod = (s.owner?.process ?? '').match(/ on (\S+)$/)?.[1]; const current = s.id === (serverId || workspace.server.id); return <article key={s.id} className={`server-card ${current ? 'current' : ''}`}><div className="server-card-head"><div><strong>{s.name}</strong><small>{tr('server_id_short', { id: s.id.slice(0, 8) })}{current ? ` · ${tr('server_current')}` : ''}</small></div>{!current && <button className="button small-button" onClick={() => { if (dirty && !window.confirm(tr('confirm_switch_server'))) return; setServerId(s.id); setServersOpen(false); }}>{tr('server_open')}</button>}</div><div className="detail-row"><span>{tr('server_contents')}</span><strong>{tr('server_contents_value', { tools: s.tools ?? 0, connections: s.connections ?? 0, release: s.active_release_id?.slice(0, 8) ?? tr('none') })}</strong></div><div className="detail-row"><span>{tr('deploy')}</span><strong>{s.deployment.application_name ? `${s.deployment.application_name} · ${tr(`deploy_status_${s.deployment.status}`)}` : tr(`deploy_status_${s.deployment.status}`)}</strong></div><div className="detail-row"><span>{tr('server_serving')}</span><strong className={s.runtime?.online && s.runtime.ready ? 'success-text' : ''}>{s.runtime?.online ? tr('server_serving_online', { host: s.runtime.host ?? '?', revision: (s.runtime.revision ?? '?').slice(0, 8), age: s.runtime.heartbeat_age ?? 0, release: s.runtime.effective_release_id?.slice(0, 8) ?? tr('none') }) : s.runtime?.host ? tr('server_serving_offline_last', { host: s.runtime.host }) : tr('server_serving_never')}</strong></div><div className="detail-row"><span>{tr('server_owner')}</span><strong>{s.owner ? tr('server_owner_value', { process: s.owner.process ?? tr('server_owner_unnamed'), since: s.owner.since ? clock(s.owner.since) : '?' }) : tr('server_owner_none')}</strong></div>{s.owner && !s.runtime?.online && <p className="error">{tr('server_owner_silent', { pod: pod ?? '?' })}</p>}{s.contender && <p className="error">{tr('server_contended', { host: s.contender.host ?? '?', revision: (s.contender.revision ?? '?').slice(0, 8), time: clock(s.contender.at), owner: s.contender.owner ?? '?' })}</p>}</article>; })}</div></Modal>}
    {deleteDraft && <Modal title={tr('delete_server_dialog', { name: workspace.server.name })} subtitle={tr('delete_server_subtitle')} close={() => { setDeleteDraft(null); setError(''); }}><form onSubmit={e => { e.preventDefault(); void deleteServer(); }}><div className="detail-row"><span>{tr('delete_server_contents')}</span><strong>{tr('delete_server_counts', { tools: workspace.tools.length, connections: workspace.connections.length, releases: workspace.releases.length })}</strong></div>{workspace.deployment.application_id && workspace.deployment.provider === 'cloudera-ai' ? <label className="checkbox-row"><input type="checkbox" checked={deleteDraft.deleteApplication} onChange={e => setDeleteDraft({ ...deleteDraft, deleteApplication: e.target.checked })} />{tr('delete_server_application', { name: workspace.deployment.application_name ?? '' })}</label> : runtime.online ? <p className="error">{tr('delete_server_still_served')}</p> : null}<p className="field-help">{tr('delete_server_keep_copy')} <button type="button" className="text-button" onClick={() => void exportServer()}><Download size={13} />{tr('export_server')}</button></p><label>{tr('delete_server_confirm', { name: workspace.server.name })}<input autoFocus value={deleteDraft.confirm} onChange={e => setDeleteDraft({ ...deleteDraft, confirm: e.target.value })} /></label>{error && <p className="error" role="alert">{error}</p>}<button className="button full-width danger-button" type="submit" disabled={!!busy || deleteDraft.confirm !== workspace.server.name}>{busy === 'Deleting server' ? <LoaderCircle className="spin" size={16} /> : <Trash2 size={16} />}{tr('delete_server_button')}</button></form></Modal>}
    {serverModal && <Modal title={tr('create_mcp_server')} subtitle={tr('server_subtitle')} close={() => setServerModal(false)}><form onSubmit={e => { e.preventDefault(); void createServer(); }}><label>{tr('server_name')}<input autoFocus required value={newServerName} onChange={e => setNewServerName(e.target.value)} placeholder={tr('customer_support_mcp')} /></label><button className="button primary full-width" disabled={!!busy || !newServerName.trim()} type="submit"><Plus size={16} />{tr('create_server')}</button></form></Modal>}
    {deploymentOpen && <Modal title={tr('deployment_monitoring')} subtitle={tr('deployment_subtitle')} close={() => setDeploymentOpen(false)}><div className="deployment-card"><div><span className={`tool-status ${workspace.deployment.status}`}>{tr(`deploy_status_${workspace.deployment.status}`)}</span><strong>{workspace.deployment.application_name || tr('application_not_provisioned')}</strong></div>{workspace.deployment.application_id ? <p className="field-help">{tr('deploy_name_fixed')}</p> : <label>{tr('deploy_application_name')}<input value={deployName || suggestedName(workspace.server.name)} maxLength={63} pattern="[a-z][a-z0-9-]{1,61}[a-z0-9]" title={tr('deploy_name_rule')} onChange={e => setDeployName(e.target.value)} /><span className="field-help">{tr('deploy_name_help', { url: `https://${deployName || suggestedName(workspace.server.name)}.<workbench-domain>/mcp` })}</span></label>}<p className="muted">{tr('provider_line', { provider: workspace.deployment.provider })} {workspace.deployment.message ? translateError(workspace.deployment.message) : tr('publish_then_deploy')}{workspace.deployment.status !== 'not_deployed' && <span className="result-time"> {tr('deploy_last_result', { time: clock(workspace.deployment.updated_at) })}</span>}</p><div className="detail-row"><span>{tr('active_release')}</span><code>{workspace.server.active_release_id?.slice(0, 8) || tr('none')}</code></div><div className="detail-row"><span>{tr('deployed_release')}</span><code>{workspace.deployment.deployed_release_id?.slice(0, 8) || tr('none')}</code></div>{workspace.deployment.endpoint && <div className="detail-row"><span>{tr('endpoint_2')}</span><code>{workspace.deployment.endpoint}</code></div>}<div className="detail-row"><span>{tr('server_health')}</span><strong className={runtime.online && runtime.ready ? 'success-text' : ''}>{runtime.online && runtime.ready ? tr('health_online', { release: runtime.effective_release_id?.slice(0, 8) ?? tr('none') }) : tr('health_offline')}</strong></div>{runtime.revision && <div className="detail-row"><span>{tr('server_code')}</span><code>{tr('code_on_host', { revision: runtime.revision.slice(0, 8), host: runtime.host ?? '?' })}</code></div>}{liveStarted && <p className="field-help live-check"><LoaderCircle className="spin" size={12} /> {tr('deploy_checking', { time: liveCheck ? new Date(liveCheck.at).toLocaleTimeString(locale, { hour12: false }) : '-' })}</p>}{liveStarted && liveCheck && liveCheck.at - liveStarted > 600000 && <p className="error">{tr('deploy_still_provisioning')}</p>}{liveCheck?.error && <p className="error">{translateError(liveCheck.error)}</p>}{workspace.deployment.provider === 'manual' && (workspace.deployment.metrics as { manifest?: { name: string; subdomain: string; entrypoint: string; runtime_image: string; environment: Record<string, string> } }).manifest && (() => { const m = (workspace.deployment.metrics as { manifest: { name: string; subdomain: string; entrypoint: string; runtime_image: string; environment: Record<string, string> } }).manifest; return <div className="manual-manifest"><p className="section-label">{tr('manual_title')}</p><div className="detail-row"><span>{tr('manual_name')}</span><code>{m.name}</code></div><div className="detail-row"><span>{tr('manual_subdomain')}</span><code>{m.subdomain}</code></div><div className="detail-row"><span>{tr('manual_script')}</span><code>{m.entrypoint}</code></div><p className="field-help">{tr('manual_script_note')}</p><div className="detail-row"><span>{tr('manual_runtime')}</span><code>{m.runtime_image || tr('manual_runtime_same')}</code></div><p className="section-label">{tr('manual_env')}</p><pre className="result-output manifest-env">{Object.entries(m.environment).map(([k, v]) => `${k}=${v}`).join('\n')}</pre><p className="field-help">{tr('manual_pin_note')}</p><p className="field-help">{tr('manual_auto')}</p></div>; })()}{error && <p className="error" role="alert">{errorAt ? `${clock(errorAt)} · ` : ''}{error}</p>}{!workspace.server.active_release_id && <p className="field-help">{tr('deploy_needs_release')}</p>}<div className="deployment-actions"><button className="button primary" disabled={!canPublish || !!busy || !workspace.server.active_release_id || (!workspace.deployment.application_id && !/^[a-z][a-z0-9-]{1,61}[a-z0-9]$/.test(deployName || suggestedName(workspace.server.name)))} onClick={() => void deploy()}><Rocket size={15} />{tr('deploy_release')}</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('refresh')}>{tr('refresh')}</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('stop')}>{tr('stop')}</button><button className="button" disabled={!canPublish || !!busy} onClick={() => void deploy('delete')}>{tr('delete')}</button></div><p className="field-help">{tr('gateway_health_appears_in_the_workspace')}</p>{builderCode && <p className="field-help code-footer">{tr('builder_code', { revision: builderCode.revision.slice(0, 8), time: clock(builderCode.started_at) })}</p>}</div></Modal>}
    {preview && <Modal title={tr('review_your_release')} subtitle={tr('preview_subtitle')} close={closePreview}><div className="release-diff">{(['added', 'changed', 'removed'] as const).map(kind => <div key={kind}><p className="section-label">{tr(`diff_${kind}`)} <span>{preview[kind].length}</span></p>{preview[kind].length ? preview[kind].map(name => <div className={`diff-item ${kind}`} key={name}>{kind === 'added' ? <Plus size={15} /> : kind === 'removed' ? <X size={15} /> : <Settings2 size={15} />}<code>{name}</code></div>) : <p className="field-help">{tr('no_kind_tools', { kind: tr(`diff_${kind}`) })}</p>}</div>)}</div>{preview.problems.length > 0 && <div className="publish-problems"><strong>{tr('before_you_publish')}</strong><ul>{preview.problems.map(p => <li key={p}>{translateError(p)}</li>)}</ul></div>}{error && <p className="error" role="alert">{error}</p>}<button className="button primary full-width" disabled={!!busy || !!preview.problems.length || !canPublish} onClick={() => void run('Publishing', async () => { const release = await api<{ id: string; status: string }>('/releases', { method: 'POST', body: JSON.stringify({ revision: preview.revision }) }); setPreview(null); await refresh(); setNotice(release.status === 'active' ? tr('release_active_deploy_it', { release: release.id.slice(0, 8) }) : tr('release_submitted_waiting_for_the_server')); })}>{busy === 'Publishing' ? <LoaderCircle className="spin" size={16} /> : <Rocket size={16} />}{tr('publish_release')}</button></Modal>}
    {history && <Modal title={tr('release_history')} subtitle={tr('history_subtitle')} close={closeHistory}><div className="runtime-detail"><Radio size={16} /><span>{runtime.online && runtime.ready ? tr('gateway_ready') : tr('gateway_unavailable')}</span>{runtime.gateway_pid && <code>PID {runtime.gateway_pid}</code>}</div>{workspace.releases.length === 0 ? <div className="history-empty"><History size={30} /><p>{tr('your_first_release_starts_here')}</p><small>{tr('validate_and_test_a_tool_then')}</small></div> : <div className="release-list">{workspace.releases.map(r => <article key={r.id}><div><span className={`tool-status ${r.status}`}>{r.status}</span><code>{r.id.slice(0, 8)}</code><time>{new Date(r.created_at).toLocaleString(locale)}</time></div><p>{r.tool_names.length ? r.tool_names.join(', ') : tr('empty_catalog')}</p>{r.error && <p className="error">{r.error}</p>}{r.status === 'superseded' && <button className="text-button" disabled={!canPublish || !!busy || !!pendingRelease} onClick={() => void run('Restoring', async () => { await api('/releases/rollback', { method: 'POST', body: JSON.stringify({ revision: workspace.server.revision, release_id: r.id }) }); await refresh(); setNotice(tr('restore_submitted_for_server_verification')); })}><Undo2 size={14} />{tr('restore_this_release')}</button>}</article>)}</div>}{error && <p className="error" role="alert">{error}</p>}</Modal>}
  </div>;
}
