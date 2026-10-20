import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const environment = Object.fromEntries(readFileSync(resolve(process.cwd(), '../../.env'), 'utf8').split('\n').filter(l => l && !l.startsWith('#')).map(l => { const i = l.indexOf('='); return [l.slice(0, i), l.slice(i + 1)]; }));
const admin = environment.FACTORY_ADMINISTRATOR_TOKEN;
const suffix = Date.now().toString(36);
const inventoryName = `browser_inventory_${suffix}`;

test.beforeAll(async ({ request }) => {
  // This URL is exclusively the isolated daedalus-checks project.
  const headers = { Authorization: `Bearer ${admin}` };
  const response = await request.get('http://127.0.0.1:18000/api/workspace', { headers });
  for (const tool of (await response.json()).tools) {
    const { id, revision, validated, tested, published, test_summary, ...spec } = tool;
    const updated = await request.patch(`http://127.0.0.1:18000/api/tools/${id}`, { headers: { ...headers, 'If-Match': String(revision) }, data: { ...spec, enabled: false } });
    expect(updated.ok()).toBeTruthy();
  }
});

async function login(page: Page, token = admin, url = '/') {
  await page.goto(url);
  // Open-admin builds show the login form only until the workspace loads, so give the heading a moment before logging in.
  const heading = page.getByRole('heading', { name: /MCP server/ });
  if (await heading.waitFor({ timeout: 5_000 }).then(() => true, () => false)) return;
  await page.getByLabel('Management token').fill(token);
  await page.getByRole('button', { name: 'Enter workspace' }).click();
  await expect(page.getByRole('heading', { name: 'My MCP server' })).toBeVisible();
}

/** Packs are collapsed by default; open one (idempotently) and return its group. */
async function openPack(page: Page, name: string) {
  const group = page.locator('.pack-group').filter({ has: page.getByRole('button', { name: `Show or hide the ${name} pack` }) });
  const toggle = group.getByRole('button', { name: `Show or hide the ${name} pack` });
  if (await toggle.getAttribute('aria-expanded') !== 'true') await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  return group;
}

async function workspace(page: Page) {
  const response = await page.request.get('http://127.0.0.1:18000/api/workspace', { headers: { Authorization: `Bearer ${admin}` } });
  expect(response.ok()).toBeTruthy();
  return response.json();
}

async function save(page: Page) {
  await page.getByRole('button', { name: 'Save draft', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Save draft', exact: true })).toBeDisabled();
}

async function runTest(page: Page) {
  await page.getByRole('button', { name: 'Validate', exact: true }).click();
  await expect(page.locator('.message-bar')).toContainText('Tool definition validated');
  await page.getByRole('button', { name: 'Test tool', exact: true }).click();
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.test-columns')).toContainText('Passed');
}

async function publish(page: Page) {
  await page.getByRole('button', { name: 'Review & publish', exact: true }).click();
  const modal = page.getByRole('dialog', { name: 'Review your release' });
  await expect(modal).toBeVisible();
  await expect(modal.locator('.publish-problems')).toHaveCount(0);
  const previous = (await workspace(page)).server.active_release_id;
  await modal.getByRole('button', { name: 'Publish release', exact: true }).click();
  await expect(modal).not.toBeVisible();
  await expect.poll(async () => (await workspace(page)).server.active_release_id, { timeout: 25_000 }).not.toBe(previous);
  await expect(page.getByRole('button', { name: 'Review & publish', exact: true })).toBeEnabled();
}

test('author, persist, move, test, publish and restore through the browser', async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page);
  const initial = await workspace(page);
  await page.getByRole('button', { name: 'Add connection', exact: true }).click();
  const connection = page.getByRole('dialog', { name: 'Connect an API' });
  await connection.getByLabel('Connection name').fill(`Browser APIs ${suffix}`);
  await connection.getByLabel('Base URL').fill('http://mock-api:8080');
  await connection.getByRole('button', { name: 'Save connection' }).click();
  await expect(connection).not.toBeVisible();
  const group = page.locator('.connection-group').filter({ hasText: `Browser APIs ${suffix}` });
  await group.getByRole('button', { name: /Find inventory item/ }).click();
  await expect(page.getByLabel('Tool name', { exact: true })).toBeVisible();
  await page.getByLabel('Tool name', { exact: true }).fill(inventoryName);
  await page.getByRole('textbox', { name: 'Description', exact: true }).fill('Browser-verified inventory lookup.');
  await save(page);
  await page.getByLabel('Search tools').fill(inventoryName);
  await page.getByRole('button', { name: 'Fit View', exact: true }).click();
  const before = await workspace(page);
  const tool = before.tools.find((t: { name: string }) => t.name === inventoryName);
  const node = page.locator(`.react-flow__node[data-id="${tool.id}"]`);
  await expect(node).toBeVisible();
  await page.waitForTimeout(500); // Wait for the intentional fit-view animation.
  const box = await node.boundingBox();
  expect(box).not.toBeNull();
  const start = { x: box!.x + box!.width / 2, y: box!.y + box!.height / 3 };
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  await page.mouse.move(start.x + 55, start.y + 40, { steps: 15 });
  await page.mouse.up();
  await expect.poll(async () => (await workspace(page)).layout.positions[tool.id]).toBeTruthy();
  const positioned = await workspace(page);
  expect(positioned.server.revision).toBe(before.server.revision);
  expect(positioned.tools.find((t: { id: string }) => t.id === tool.id).revision).toBe(tool.revision);
  await page.reload();
  await expect(node).toBeVisible();
  await node.click();
  await expect(page.getByRole('textbox', { name: 'Description', exact: true })).toHaveValue('Browser-verified inventory lookup.');
  expect((await workspace(page)).layout.positions[tool.id]).toEqual(positioned.layout.positions[tool.id]);
  await runTest(page);
  await expect(page.locator('.result-output')).toContainText('Precision bearing');
  await page.screenshot({ path: testInfo.outputPath('builder-desktop.png'), fullPage: true });
  await page.getByRole('button', { name: 'Close playground' }).click();
  await publish(page);
  const firstRelease = (await workspace(page)).server.active_release_id;
  expect((await workspace(page)).server.runtime.gateway_pid).toBe(initial.server.runtime.gateway_pid);
  await page.getByRole('textbox', { name: 'Description', exact: true }).fill('Updated through the browser.');
  await save(page);
  await runTest(page);
  await page.getByRole('button', { name: 'Close playground' }).click();
  await publish(page);
  expect((await workspace(page)).server.runtime.gateway_pid).toBe(initial.server.runtime.gateway_pid);
  await page.getByRole('button', { name: 'Releases', exact: true }).click();
  const history = page.getByRole('dialog', { name: 'Release history' });
  const oldRelease = history.locator('article').filter({ hasText: firstRelease.slice(0, 8) });
  await oldRelease.getByRole('button', { name: 'Restore this release' }).click();
  await expect.poll(async () => (await workspace(page)).active_tools.find((t: { id: string }) => t.id === tool.id)?.spec.description).toBe('Browser-verified inventory lookup.');
  await history.getByRole('button', { name: 'Close dialog' }).click();
  expect((await workspace(page)).tools.find((t: { id: string }) => t.id === tool.id).description).toBe('Updated through the browser.');
  await page.getByRole('button', { name: 'List', exact: true }).click();
  await expect(page.locator('.table-row').filter({ hasText: inventoryName })).toBeVisible();
  expect(errors).toEqual([]);
});

test('drag an operation, search tools, and enforce read-only browser controls', async ({ page }, testInfo) => {
  await login(page);
  await page.getByRole('button', { name: 'Add connection', exact: true }).click();
  const connection = page.getByRole('dialog', { name: 'Connect an API' });
  await connection.getByLabel('Connection name').fill(`Drag APIs ${suffix}`);
  await connection.getByLabel('Base URL').fill('http://mock-api:8080');
  await connection.getByRole('button', { name: 'Save connection' }).click();
  await expect(connection).not.toBeVisible();
  const group = page.locator('.connection-group').filter({ hasText: `Drag APIs ${suffix}` });
  await group.getByRole('button', { name: /Get support ticket/ }).dragTo(page.locator('.react-flow__pane'), { targetPosition: { x: 290, y: 240 } });
  await expect(page.getByLabel('Tool name', { exact: true })).toHaveValue(/get_ticket/);
  const ticketName = `browser_ticket_${suffix}`;
  await page.getByLabel('Tool name', { exact: true }).fill(ticketName);
  await save(page);
  await runTest(page);
  await expect(page.locator('.result-output')).toContainText('Replace workstation');
  await page.getByRole('button', { name: 'Close playground' }).click();
  await page.getByLabel('Search tools').fill(ticketName);
  await expect(page.locator('.react-flow__node').filter({ hasText: inventoryName })).toHaveCount(0);
  await expect(page.locator('.react-flow__node').filter({ hasText: ticketName })).toBeVisible();
  await page.getByRole('button', { name: 'Sign out' }).click();
  await login(page, environment.FACTORY_VIEWER_TOKEN);
  await expect(page.getByRole('button', { name: 'Review & publish' })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Add connection', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'List', exact: true }).click();
  await page.locator('.table-row').filter({ hasText: ticketName }).click();
  await expect(page.getByLabel('Tool name', { exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Save draft' })).toBeDisabled();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('heading', { name: 'My MCP server' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('builder-mobile.png'), fullPage: true });
});

test('production assets and management API work on one application port', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page, admin, 'http://127.0.0.1:18000/');
  await expect(page.getByRole('button', { name: 'Review & publish' })).toBeEnabled();
  expect(await page.locator('script[src^="/assets/"]').count()).toBeGreaterThan(0);
  await expect(page.locator('.react-flow__node').first()).toBeVisible();
  expect(errors).toEqual([]);
});

test('creates an isolated server workspace and shows its deployment state', async ({ page }) => {
  await login(page);
  const name = `Deployable server ${Date.now().toString(36)}`;
  await page.getByRole('button', { name: 'New server', exact: true }).click();
  const modal = page.getByRole('dialog', { name: 'Create MCP server' });
  await modal.getByLabel('Server name').fill(name);
  await modal.getByRole('button', { name: 'Create server', exact: true }).click();
  await expect(page.getByRole('heading', { name: new RegExp(name) })).toBeVisible();
  await expect(page.locator('.canvas-count')).toContainText('0 tools');
  await page.getByRole('button', { name: 'Deploy', exact: true }).click();
  const deployment = page.getByRole('dialog', { name: 'Deployment & monitoring' });
  await expect(deployment).toContainText('Application not provisioned');
  await expect(deployment).toContainText('not deployed');
});

test('create, inspect and test Python pack tools from the palette', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page);
  // fetch_json needs an API connection; make sure one exists so "Add all" creates every demo tool.
  const connection = await page.request.post('http://127.0.0.1:18000/api/connections', { headers: { Authorization: `Bearer ${admin}` }, data: { name: `Pack APIs ${suffix}`, base_url: 'http://mock-api:8080' } });
  expect(connection.ok()).toBeTruthy();
  const demo = await openPack(page, 'demo');
  await expect(demo.getByRole('button', { name: /^READ whoami/ })).toBeVisible();
  // Collapsing hides the tools but keeps the header and Add all.
  await demo.getByRole('button', { name: 'Show or hide the demo pack' }).click();
  await expect(demo.getByRole('button', { name: /^READ whoami/ })).toHaveCount(0);
  await expect(demo.getByRole('button', { name: 'Add all', exact: true })).toBeVisible();
  await openPack(page, 'demo');
  await demo.getByRole('button', { name: /^READ echo/ }).click();
  await expect(page.getByLabel('Tool name', { exact: true })).toHaveValue(/^echo/);
  await expect(page.locator('.inspector')).toContainText('PYTHON TOOL');
  await expect(page.locator('.inspector')).toContainText('demo.echo');
  await expect(page.locator('.inspector')).toContainText('text');
  await runTest(page);
  await expect(page.locator('.result-output')).toContainText('example');
  await page.getByRole('button', { name: 'Close playground' }).click();
  const created = (await workspace(page)).tools.find((t: { pack?: string; function?: string }) => t.pack === 'demo' && t.function === 'echo');
  expect(created.kind).toBe('python');
  expect(created.connection_id).toBeNull();
  await demo.getByRole('button', { name: 'Add all', exact: true }).click();
  await expect(page.locator('.message-bar')).toContainText(/tools added|already on the canvas/);
  // Earlier runs leave their own demo tools behind, so compare the set of functions rather than the list.
  await expect.poll(async () => [...new Set((await workspace(page)).tools.filter((t: { pack?: string }) => t.pack === 'demo').map((t: { function?: string }) => t.function))].sort()).toEqual(['echo', 'fetch_json', 'whoami']);
  await page.getByRole('button', { name: 'List', exact: true }).click();
  await expect(page.locator('.table-row').filter({ hasText: 'demo.whoami' })).toBeVisible();
  expect(errors).toEqual([]);
  // Remove the pack tools so repeated runs do not crowd the canvas for the other tests.
  for (const tool of (await workspace(page)).tools.filter((t: { pack?: string }) => t.pack === 'demo')) {
    const removed = await page.request.delete(`http://127.0.0.1:18000/api/tools/${tool.id}`, { headers: { Authorization: `Bearer ${admin}`, 'If-Match': String(tool.revision) } });
    expect(removed.ok()).toBeTruthy();
  }
});

test('administrators write a project pack in the browser and use its tools', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page);
  const packName = `browser_pack_${suffix.replace(/[^a-z0-9_]/g, '')}`;
  await page.getByRole('button', { name: 'New pack', exact: true }).click();
  const editor = page.getByRole('dialog', { name: 'New tool pack' });
  await editor.getByLabel('Pack name').fill(packName);
  await editor.getByLabel('Python source').fill('from factory.packs import ToolContext, pack_tool\n\n@pack_tool()\ndef broken(ctx: ToolContext, n: list) -> dict:\n    """Bad parameter type."""\n    return {}\n');
  await editor.getByRole('button', { name: 'Save pack', exact: true }).click();
  await expect(editor.locator('.error')).toContainText('must be a str, int, float or bool');
  await editor.getByLabel('Python source').fill('"""Browser-authored pack."""\nfrom factory.packs import ToolContext, pack_tool\n\n\n@pack_tool()\ndef greet(ctx: ToolContext, name: str) -> dict:\n    """Greet someone by name."""\n    return {"greeting": f"Hello, {name}"}\n');
  await editor.getByRole('button', { name: 'Save pack', exact: true }).click();
  await expect(editor).not.toBeVisible();
  await expect(page.locator('.message-bar')).toContainText(`Pack ${packName} saved with greet`);
  const group = await openPack(page, packName);
  await expect(group).toContainText('project');
  await group.getByRole('button', { name: 'View code' }).click();
  await expect(page.getByRole('dialog', { name: `${packName} pack` })).toContainText('def greet');
  await page.getByRole('dialog', { name: `${packName} pack` }).getByRole('button', { name: 'Close dialog' }).click();
  await group.getByRole('button', { name: /^READ greet/ }).click();
  await expect(page.locator('.inspector')).toContainText(`${packName}.greet`);
  await page.locator('.inspector').getByRole('button', { name: 'View source' }).click();
  await expect(page.getByRole('dialog', { name: `${packName}.greet` })).toContainText('Greet someone by name.');
  await page.getByRole('dialog', { name: `${packName}.greet` }).getByRole('button', { name: 'Close dialog' }).click();
  await runTest(page);
  await expect(page.locator('.result-output')).toContainText('Hello, example');
  await page.getByRole('button', { name: 'Close playground' }).click();
  await expect(page.locator('.inspector')).toContainText('Tested');
  // Editing the pack invalidates the test evidence without any restart.
  await group.getByRole('button', { name: 'Edit', exact: true }).click();
  const edit = page.getByRole('dialog', { name: `Edit pack ${packName}` });
  await edit.getByLabel('Python source').fill('"""Browser-authored pack."""\nfrom factory.packs import ToolContext, pack_tool\n\n\n@pack_tool()\ndef greet(ctx: ToolContext, name: str) -> dict:\n    """Greet someone by name."""\n    return {"greeting": f"Hi, {name}"}\n');
  await edit.getByRole('button', { name: 'Save pack', exact: true }).click();
  await expect(edit).not.toBeVisible();
  await expect(page.locator('.inspector')).not.toContainText('Tested');
  expect(errors).toEqual([]);
  const headers = { Authorization: `Bearer ${admin}` };
  for (const tool of (await workspace(page)).tools.filter((t: { pack?: string }) => t.pack === packName)) {
    expect((await page.request.delete(`http://127.0.0.1:18000/api/tools/${tool.id}`, { headers: { ...headers, 'If-Match': String(tool.revision) } })).ok()).toBeTruthy();
  }
  expect((await page.request.delete(`http://127.0.0.1:18000/api/packs/${packName}`, { headers })).ok()).toBeTruthy();
});

test('the help link opens the tool pack guide from both the dev server and the application port', async ({ page }) => {
  await login(page);
  const link = page.getByRole('link', { name: 'Help', exact: true });
  await expect(link).toHaveAttribute('href', '/help/tool-packs.html');
  for (const origin of ['http://127.0.0.1:15173', 'http://127.0.0.1:18000']) {
    const response = await page.request.get(`${origin}/help/tool-packs.html`);
    expect(response.ok()).toBeTruthy();
    expect(await response.text()).toContain('Writing a tool pack');
  }
});

test('the language selector switches the Builder to Korean and back', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page);
  await page.getByRole('combobox', { name: 'Language' }).selectOption('ko');
  await expect(page.getByRole('button', { name: '검토 및 게시' })).toBeVisible();
  await expect(page.getByRole('link', { name: '도움말' })).toHaveAttribute('href', '/help/ko/tool-packs.html');
  await expect(page.locator('.palette')).toContainText('도구 팩');
  await page.reload();
  await expect(page.getByRole('button', { name: '검토 및 게시' })).toBeVisible(); // remembered per browser
  const korean = await page.request.get('http://127.0.0.1:18000/help/ko/tool-packs.html');
  expect(korean.ok()).toBeTruthy();
  expect(await korean.text()).toContain('도구 팩 작성하기');
  await page.getByRole('combobox', { name: '언어' }).selectOption('en');
  await expect(page.getByRole('button', { name: 'Review & publish' })).toBeVisible();
  expect(errors).toEqual([]);
});

test('connections carry an authentication mode and only a secret reference', async ({ page }) => {
  await login(page);
  await page.getByRole('button', { name: 'Add connection', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Connect an API' });
  await dialog.getByLabel('Connection name').fill(`Secured APIs ${suffix}`);
  await dialog.getByLabel('Base URL').fill('http://mock-api:8080');
  await dialog.getByLabel('Authentication').selectOption('static');
  await dialog.getByLabel('Secret reference').fill(`FACTORY_SECRET_BROWSER_${suffix.toUpperCase()}`);
  await dialog.getByRole('button', { name: 'Save connection' }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.locator('.inspector')).toContainText('Service secret');
  await expect(page.locator('.inspector')).toContainText(`FACTORY_SECRET_BROWSER_${suffix.toUpperCase()}`);
  const saved = (await workspace(page)).connections.find((c: { name: string }) => c.name === `Secured APIs ${suffix}`);
  expect(saved.auth_mode).toBe('static');
  expect(JSON.stringify(saved)).not.toContain('s3cret');
  await page.getByRole('button', { name: 'Edit connection' }).click();
  const edit = page.getByRole('dialog', { name: 'Edit API connection' });
  await expect(edit.getByLabel('Authentication')).toHaveValue('static');
  await edit.getByLabel('Authentication').selectOption('forward-token');
  await expect(edit).toContainText("caller's own token");
  await edit.getByRole('button', { name: 'Close dialog' }).click();
});

test('connections are typed by protocol and the canvas only links compatible tools', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page);
  const headers = { Authorization: `Bearer ${admin}` };
  // Start from a workspace with only REST connections: the HDFS pack cannot attach to them.
  for (const c of (await workspace(page)).connections.filter((c: { protocol?: string }) => c.protocol && c.protocol !== 'rest')) {
    for (const t of (await workspace(page)).tools.filter((t: { connection_id: string | null }) => t.connection_id === c.id)) await page.request.delete(`http://127.0.0.1:18000/api/tools/${t.id}`, { headers: { ...headers, 'If-Match': String(t.revision) } });
    await page.request.delete(`http://127.0.0.1:18000/api/connections/${c.id}`, { headers: { ...headers, 'If-Match': String(c.revision) } });
  }
  const hdfs = await openPack(page, 'hdfs');
  await expect(hdfs).toContainText('Needs a WebHDFS');
  await hdfs.getByRole('button', { name: 'Add all', exact: true }).click();
  await expect(page.locator('.message-bar')).toContainText('need a WebHDFS');
  expect((await workspace(page)).tools.filter((t: { pack?: string }) => t.pack === 'hdfs')).toHaveLength(0);
  // A WebHDFS connection to the fixture makes the pack usable; Add all links every tool to it.
  await page.getByRole('button', { name: 'Add connection', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Connect an API' });
  await dialog.getByLabel('Connection name').fill(`HDFS fixture ${suffix}`);
  await dialog.getByLabel('Base URL').fill('http://mock-api:8080');
  await dialog.getByLabel('Protocol').selectOption('webhdfs');
  await dialog.getByRole('button', { name: 'Save connection' }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.locator('.inspector')).toContainText('WebHDFS');
  await expect(hdfs).not.toContainText('Needs a WebHDFS');
  await hdfs.getByRole('button', { name: 'Add all', exact: true }).click();
  await expect(page.locator('.message-bar')).toContainText('8 tools added');
  const fixture = (await workspace(page)).connections.find((c: { name: string }) => c.name === `HDFS fixture ${suffix}`);
  const tools = (await workspace(page)).tools.filter((t: { pack?: string }) => t.pack === 'hdfs');
  expect(tools.every((t: { connection_id: string | null }) => t.connection_id === fixture.id)).toBeTruthy();
  // The inspector offers only compatible connections, and a passing test shows on the tool.
  const listing = tools.find((t: { function?: string }) => t.function === 'list_directory');
  await page.getByRole('button', { name: 'List', exact: true }).click();
  await page.locator('.table-row').filter({ hasText: 'hdfs.list_directory' }).first().click();
  const options = await page.locator('.inspector select').first().locator('option').allTextContents();
  expect(options).toContain(`HDFS fixture ${suffix}`);
  expect(options.some(o => o.startsWith('Browser APIs') || o.startsWith('Drag APIs'))).toBeFalsy();
  await runTest(page);
  await expect(page.locator('.result-output')).toContainText('"data"'); // the prefilled sample lists /
  await page.getByRole('button', { name: 'Close playground' }).click();
  expect(errors).toEqual([]);
  for (const t of tools) await page.request.delete(`http://127.0.0.1:18000/api/tools/${t.id}`, { headers: { ...headers, 'If-Match': String(t.revision + (t.id === listing.id ? 0 : 0)) } }).catch(() => undefined);
});

test('a failed test marks the tool and its connection edge', async ({ page }) => {
  await login(page);
  const headers = { Authorization: `Bearer ${admin}` };
  const connection = await (await page.request.post('http://127.0.0.1:18000/api/connections', { headers, data: { name: `Unset secret ${suffix}`, base_url: 'http://mock-api:8080', auth_mode: 'static', secret_ref: `FACTORY_SECRET_UNSET_${suffix.toUpperCase()}` } })).json();
  const tool = await (await page.request.post('http://127.0.0.1:18000/api/tools', { headers, data: { name: `failing_${suffix}`, description: 'Will fail: the secret is not set.', connection_id: connection.id, method: 'GET', path: '/fixture/echo' } })).json();
  await page.reload();
  await page.getByRole('button', { name: 'List', exact: true }).click();
  await page.locator('.table-row').filter({ hasText: `failing_${suffix}` }).click();
  await page.getByRole('button', { name: 'Test tool', exact: true }).click();
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.test-columns')).toContainText('Failed');
  await expect(page.locator('.inspector')).toContainText('Failed');
  await page.getByRole('button', { name: 'Close playground' }).click();
  await page.getByRole('button', { name: 'Canvas', exact: true }).click();
  await expect(page.locator(`.react-flow__edge[data-id="api-${tool.id}"] .react-flow__edge-path`)).toHaveAttribute('style', /stroke-dasharray/);
  await page.request.delete(`http://127.0.0.1:18000/api/tools/${tool.id}`, { headers: { ...headers, 'If-Match': String((await workspace(page)).tools.find((t: { id: string }) => t.id === tool.id).revision) } });
  await page.request.delete(`http://127.0.0.1:18000/api/connections/${connection.id}`, { headers: { ...headers, 'If-Match': String(connection.revision) } });
});

test('saving a connection checks it and the verdict shows in the inspector and on the canvas', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page);
  await page.getByRole('button', { name: 'Add connection', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Connect an API' });
  await dialog.getByLabel('Connection name').fill(`Checked HDFS ${suffix}`);
  await dialog.getByLabel('Base URL').fill('http://mock-api:8080');
  await dialog.getByLabel('Protocol').selectOption('webhdfs');
  await dialog.getByRole('button', { name: 'Save connection' }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.locator('.message-bar')).toContainText('WebHDFS answered', { timeout: 30_000 });
  await expect(page.locator('.inspector')).toContainText('WebHDFS answered');
  await expect(page.locator('.inspector')).toContainText('hdfs.probe');
  const connection = (await workspace(page)).connections.find((c: { name: string }) => c.name === `Checked HDFS ${suffix}`);
  expect(connection.probe_summary.success).toBeTruthy();
  await expect(page.locator(`.react-flow__node[data-id="${connection.id}"] .status-dot`)).toHaveClass(/green/);
  await page.getByRole('button', { name: 'Check connection', exact: true }).click();
  await expect(page.locator('.message-bar')).toContainText('WebHDFS answered', { timeout: 30_000 });
  expect(errors).toEqual([]);
  await page.request.delete(`http://127.0.0.1:18000/api/connections/${connection.id}`, { headers: { Authorization: `Bearer ${admin}`, 'If-Match': String(connection.revision) } });
});

test('the selected tool is removed from the canvas toolbar', async ({ page }) => {
  await login(page);
  const demo = await openPack(page, 'demo');
  await demo.getByRole('button', { name: /^READ whoami/ }).click();
  const toolbar = page.locator('.canvas-toolbar');
  const remove = toolbar.getByRole('button', { name: 'Remove tool' });
  await expect(remove).toBeEnabled();
  await expect(page.locator('.inspector').getByRole('button', { name: 'Remove tool' })).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Description', exact: true }).fill('Unsaved edit.');
  await expect(remove).toBeDisabled(); // unsaved inspector changes come first
  await page.getByRole('button', { name: 'Discard changes' }).click();
  const before = (await workspace(page)).tools.filter((t: { pack?: string }) => t.pack === 'demo').length;
  page.once('dialog', dialog => void dialog.accept());
  await remove.click();
  await expect.poll(async () => (await workspace(page)).tools.filter((t: { pack?: string }) => t.pack === 'demo').length).toBe(before - 1);
  await expect(toolbar.getByRole('button', { name: 'Remove tool' })).toHaveCount(0); // nothing selected any more
});

test('setup steps check off as the canvas progresses and uncheck when tools or connections are removed', async ({ page }) => {
  const headers = { Authorization: `Bearer ${admin}` };
  const api = 'http://127.0.0.1:18000/api';
  const step = (label: string) => page.locator('.workflow-steps [role="checkbox"]').filter({ hasText: label });
  // Steps 2-4 in the default workspace: start from a canvas with no included tools.
  for (const t of (await workspace(page)).tools.filter((t: { enabled: boolean }) => t.enabled)) {
    const { id, revision, validated, tested, published, test_summary, ...spec } = t;
    expect((await page.request.patch(`${api}/tools/${id}`, { headers: { ...headers, 'If-Match': String(revision) }, data: { ...spec, enabled: false } })).ok()).toBeTruthy();
  }
  await login(page);
  await expect(page.locator('.workflow-steps .section-label')).toHaveText('STEPS TO CREATE YOUR MCP SERVER');
  for (const label of ['Configure a tool', 'Validate and test', 'Review and publish']) await expect(step(label)).toHaveAttribute('aria-checked', 'false');
  const tool = await (await page.request.post(`${api}/tools`, { headers, data: { name: `steps_${suffix}`, description: 'Steps check tool.', kind: 'python', pack: 'demo', function: 'whoami' } })).json();
  await expect(step('Configure a tool')).toHaveAttribute('aria-checked', 'true');
  await expect(step('Validate and test')).toHaveAttribute('aria-checked', 'false');
  expect((await (await page.request.post(`${api}/tools/${tool.id}/test`, { headers: { ...headers, 'If-Match': '1' }, data: { arguments: {} } })).json()).success).toBeTruthy();
  await expect(step('Validate and test')).toHaveAttribute('aria-checked', 'true');
  const preview = await (await page.request.get(`${api}/releases/preview`, { headers })).json();
  expect(preview.problems).toEqual([]);
  expect((await page.request.post(`${api}/releases`, { headers, data: { revision: preview.revision } })).status()).toBe(202);
  await expect(step('Review and publish')).toHaveAttribute('aria-checked', 'true', { timeout: 30_000 });
  // Removing the only included tool unchecks every step that depended on it.
  await page.getByRole('button', { name: 'List', exact: true }).click();
  await page.locator('.table-row').filter({ hasText: `steps_${suffix}` }).click();
  page.once('dialog', dialog => void dialog.accept());
  await page.locator('.canvas-toolbar').getByRole('button', { name: 'Remove tool' }).click();
  for (const label of ['Configure a tool', 'Validate and test', 'Review and publish']) await expect(step(label)).toHaveAttribute('aria-checked', 'false');
  // Step 1 in a fresh server workspace: adding and removing its only connection.
  const server = await (await page.request.post(`${api}/servers`, { headers, data: { name: `Steps ${suffix}` } })).json();
  await page.getByRole('combobox', { name: 'MCP server workspace' }).selectOption(server.id);
  await expect(step('Connect an API')).toHaveAttribute('aria-checked', 'false');
  const connection = await (await page.request.post(`${api}/connections?server_id=${server.id}`, { headers, data: { name: 'Steps API', base_url: 'http://mock-api:8080' } })).json();
  await expect(step('Connect an API')).toHaveAttribute('aria-checked', 'true');
  await page.getByRole('button', { name: 'Canvas', exact: true }).click();
  await page.locator(`.react-flow__node[data-id="${connection.id}"]`).click();
  await expect(page.locator('.inspector').getByRole('button', { name: 'Remove connection' })).toHaveCount(0);
  page.once('dialog', dialog => void dialog.accept());
  await page.locator('.canvas-toolbar').getByRole('button', { name: 'Remove connection' }).click();
  await expect(step('Connect an API')).toHaveAttribute('aria-checked', 'false');
  await expect(step('Connect an API')).toHaveAttribute('title', /at least one connection/);
});

test('tools from another MCP server are added individually and tested through the executor', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page);
  // MCP servers have their own palette section and connect button, next to Connections and Tool Packs.
  await page.getByRole('button', { name: 'Connect an MCP server' }).first().click();
  const dialog = page.getByRole('dialog', { name: 'Connect an MCP server' });
  await expect(dialog.getByLabel('Protocol')).toHaveValue('mcp');
  await dialog.getByLabel('Connection name').fill(`Upstream MCP ${suffix}`);
  await dialog.getByLabel('Base URL').fill('http://mock-api:8080/upstream/mcp');
  await dialog.getByRole('button', { name: 'Save connection' }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.locator('.message-bar')).toContainText('3 tools discovered (protocol 2025-11-25)', { timeout: 30_000 });
  const group = page.locator('.connection-group').filter({ hasText: `Upstream MCP ${suffix}` });
  await expect(group.getByRole('button', { name: /READ add/ })).toBeVisible();
  // Listed under MCP SERVERS, after every REST/WebHDFS/S3 connection and before TOOL PACKS.
  const order = await page.locator('.palette').evaluate(el => [...el.querySelectorAll('.section-label, .connection-group strong')].map(n => n.textContent?.trim()));
  const mcpHeading = order.findIndex(s => s?.startsWith('MCP SERVERS'));
  expect(mcpHeading).toBeGreaterThan(order.findIndex(s => s?.startsWith('CONNECTIONS')));
  expect(order.indexOf(`Upstream MCP ${suffix}`)).toBeGreaterThan(mcpHeading);
  expect(order.indexOf(`Upstream MCP ${suffix}`)).toBeLessThan(order.findIndex(s => s?.startsWith('TOOL PACKS')));
  await expect(group.getByRole('button', { name: /WRITE file_ticket/ })).toBeVisible();
  await expect(group).not.toContainText('Custom operation');
  await group.getByRole('button', { name: /READ add/ }).click();
  await expect(page.locator('.inspector')).toContainText('MCP TOOL');
  await expect(page.locator('.inspector')).toContainText('Add two integers.');
  await expect(page.getByLabel('Tool name', { exact: true })).toHaveValue(/^add/);
  await runTest(page);
  await expect(page.locator('.result-output')).toContainText('"result": 2');
  await page.getByRole('button', { name: 'Close playground' }).click();
  await page.locator('.inspector').getByRole('button', { name: 'View input schema' }).click();
  await expect(page.getByRole('dialog', { name: 'add input schema' })).toContainText('"required"');
  await page.getByRole('dialog', { name: 'add input schema' }).getByRole('button', { name: 'Close dialog' }).click();
  await group.getByRole('button', { name: 'Add all', exact: true }).click();
  await expect(page.locator('.message-bar')).toContainText('2 tools added');
  const added = (await workspace(page)).tools.filter((t: { kind?: string; connection_id: string | null }) => t.kind === 'mcp');
  expect(added.map((t: { upstream_tool: string }) => t.upstream_tool).sort()).toEqual(['add', 'file_ticket', 'lookup_ticket']);
  expect(added.find((t: { upstream_tool: string }) => t.upstream_tool === 'file_ticket').effect).toBe('write');
  expect(errors).toEqual([]);
  const headers = { Authorization: `Bearer ${admin}` };
  for (const t of added) await page.request.delete(`http://127.0.0.1:18000/api/tools/${t.id}`, { headers: { ...headers, 'If-Match': String(t.revision) } });
});

test('switching MCP servers clears the inspector and the selection', async ({ page }) => {
  const headers = { Authorization: `Bearer ${admin}` };
  const api = 'http://127.0.0.1:18000/api';
  const tool = await (await page.request.post(`${api}/tools`, { headers, data: { name: `switch_${suffix}`, description: 'Selected before switching.', kind: 'python', pack: 'demo', function: 'echo' } })).json();
  const other = await (await page.request.post(`${api}/servers`, { headers, data: { name: `Switch target ${suffix}` } })).json();
  await login(page);
  const picker = page.getByRole('combobox', { name: 'MCP server workspace' });
  const home = await picker.inputValue();
  await page.getByRole('button', { name: 'List', exact: true }).click();
  await page.locator('.table-row').filter({ hasText: `switch_${suffix}` }).click();
  await expect(page.getByLabel('Tool name', { exact: true })).toHaveValue(`switch_${suffix}`);
  await page.getByRole('button', { name: 'Test tool', exact: true }).click();
  await expect(page.locator('.test-drawer')).toBeVisible();
  await picker.selectOption(other.id);
  await expect(page.getByRole('heading', { name: 'Your server, at a glance.' })).toBeVisible();
  await expect(page.getByLabel('Tool name', { exact: true })).toHaveCount(0);
  await expect(page.locator('.test-drawer')).toHaveCount(0);
  await expect(page.locator('.canvas-toolbar').getByRole('button', { name: 'Remove tool' })).toHaveCount(0);
  // Unsaved edits are not dropped silently: cancelling the switch keeps them.
  await picker.selectOption(home);
  await page.locator('.table-row').filter({ hasText: `switch_${suffix}` }).click();
  await page.getByRole('textbox', { name: 'Description', exact: true }).fill('Unsaved.');
  page.once('dialog', dialog => void dialog.dismiss());
  await picker.selectOption(other.id);
  await expect(picker).toHaveValue(home);
  await expect(page.getByRole('textbox', { name: 'Description', exact: true })).toHaveValue('Unsaved.');
  page.once('dialog', dialog => void dialog.accept());
  await picker.selectOption(other.id);
  await expect(page.getByRole('heading', { name: 'Your server, at a glance.' })).toBeVisible();
  await page.request.delete(`${api}/tools/${tool.id}`, { headers: { ...headers, 'If-Match': String(tool.revision) } });
});

test('origin policies accept a pasted URL, report errors in the dialog and keep the layout readable', async ({ page }) => {
  await login(page);
  await page.getByRole('button', { name: 'Policies', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'API access policies' });
  const host = `https://api-${suffix}.example.org`;
  await dialog.getByLabel('API origin').fill(`${host}/mcp`);
  await dialog.getByRole('button', { name: 'Approve origin' }).click();
  await expect(dialog.getByRole('status')).toContainText(`Approved ${host}`);
  await expect(dialog.locator('.policy-row').filter({ hasText: host })).toBeVisible();
  await dialog.getByLabel('API origin').fill(`${host}/again`);
  await dialog.getByRole('button', { name: 'Approve origin' }).click();
  await expect(dialog.getByRole('alert')).toContainText('already registered');
  await expect(dialog).toBeVisible();
  const button = await dialog.getByRole('button', { name: 'Approve origin' }).boundingBox();
  const help = await dialog.locator('.policy-help').boundingBox();
  expect(button!.y + button!.height).toBeLessThanOrEqual(help!.y);
  const created = (await (await page.request.get('http://127.0.0.1:18000/api/policies/origins', { headers: { Authorization: `Bearer ${admin}` } })).json()).find((o: { origin: string }) => o.origin === host);
  await page.request.delete(`http://127.0.0.1:18000/api/policies/origins/${created.id}`, { headers: { Authorization: `Bearer ${admin}`, 'If-Match': String(created.revision) } });
});

test('the empty-canvas welcome can be closed and stays closed for that server', async ({ page }) => {
  const headers = { Authorization: `Bearer ${admin}` };
  const empty = await (await page.request.post('http://127.0.0.1:18000/api/servers', { headers, data: { name: `Empty ${suffix}` } })).json();
  await login(page);
  await page.getByRole('combobox', { name: 'MCP server workspace' }).selectOption(empty.id);
  const welcome = page.locator('.canvas-welcome');
  await expect(welcome).toContainText('What will your server do?');
  await welcome.getByRole('button', { name: 'Close' }).click();
  await expect(welcome).toHaveCount(0);
  await page.reload();
  await page.getByRole('combobox', { name: 'MCP server workspace' }).selectOption(empty.id);
  await expect(page.getByRole('heading', { name: 'Your server, at a glance.' })).toBeVisible();
  await expect(welcome).toHaveCount(0);
});

test('tests show a running log, then the result, with tabs to switch between them', async ({ page }) => {
  await login(page);
  const demo = await openPack(page, 'demo');
  await demo.getByRole('button', { name: /^READ echo/ }).click();
  await page.getByRole('button', { name: 'Validate', exact: true }).click();
  const tabs = page.locator('.output-tabs');
  await expect(tabs.getByRole('tab', { name: 'Logs' })).toHaveAttribute('aria-selected', 'true');
  await expect(tabs.getByRole('tab', { name: 'Result' })).toHaveCount(0);
  const log = page.locator('.log-output');
  await expect(log).toContainText('Definition is valid');
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(tabs.getByRole('tab', { name: 'Result' })).toHaveAttribute('aria-selected', 'true', { timeout: 30_000 });
  await expect(page.locator('.result-output')).toContainText('"text": "example"');
  await tabs.getByRole('tab', { name: 'Logs' }).click();
  for (const step of ['Testing echo', 'Started the executor', 'Started agentgateway', 'Catalog ready on protocol 2026-07-28', 'Tool returned in', 'Test passed in']) await expect(log).toContainText(step);
  await expect(log.locator('.log-line.success').last()).toContainText('Test passed in');
  // Invalid JSON is caught before anything is sent, and errors are red.
  await page.locator('#arguments').fill('{ not json');
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(log.locator('.log-line.error').last()).toContainText('not valid JSON');
  await expect(log.locator('.log-line.error').last()).toHaveCSS('color', 'rgb(192, 57, 43)');
  await page.getByRole('button', { name: 'Close playground' }).click();
  const tool = (await workspace(page)).tools.find((t: { pack?: string; function?: string }) => t.pack === 'demo' && t.function === 'echo');
  await page.request.delete(`http://127.0.0.1:18000/api/tools/${tool.id}`, { headers: { Authorization: `Bearer ${admin}`, 'If-Match': String(tool.revision) } });
});

test('manual deployment explains itself and shows what to create in Workbench', async ({ page }) => {
  const headers = { Authorization: `Bearer ${admin}` };
  const empty = await (await page.request.post('http://127.0.0.1:18000/api/servers', { headers, data: { name: `Deploy ${suffix}` } })).json();
  await login(page);
  await page.getByRole('combobox', { name: 'MCP server workspace' }).selectOption(empty.id);
  await page.getByRole('button', { name: 'Deploy', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Deployment & monitoring' });
  await expect(dialog.getByRole('button', { name: 'Deploy release' })).toBeDisabled();
  await expect(dialog).toContainText('Publish a release first');
  // Before the first deploy the name is a choice, suggested from the server name without an ID suffix.
  await expect(dialog.getByLabel('Application name')).toHaveValue(`deploy-${suffix.toLowerCase()}`);
  await expect(dialog).toContainText('Builder code');
  await dialog.getByRole('button', { name: 'Close dialog' }).click();
  // The default workspace has an active release from earlier tests.
  await page.getByRole('combobox', { name: 'MCP server workspace' }).selectOption('85d30f87-b285-4d17-a89e-84bac6ac37bc');
  await page.getByRole('button', { name: 'Deploy', exact: true }).click();
  await dialog.getByLabel('Application name').fill(`checks-${suffix.toLowerCase()}`);
  await dialog.getByRole('button', { name: 'Deploy release' }).click();
  await expect(dialog).toContainText('Manual mode: no application was created');
  await expect(dialog).toContainText(`checks-${suffix.toLowerCase()}`);
  await expect(dialog.locator('.result-time')).toContainText('last result');
  await expect(dialog).toContainText('ready to deploy');
  await expect(dialog).toContainText('CREATE THE SERVER APPLICATION BY HAND');
  await expect(dialog.locator('.manifest-env')).toContainText('FACTORY_SERVER_ID=');
  await expect(dialog).toContainText('mcp_server_app.py');
});

test('the deploy dialog follows a provisioning application until it runs', async ({ page }) => {
  let state = 'provisioning';
  let checks = 0;
  const endpoint = 'https://my-mcp-server-85d30f87.ml-abc.example.cloudera.site/mcp';
  await page.route('**/api/workspace*', async route => {
    const response = await route.fetch();
    const body = await response.json();
    body.deployment = { ...body.deployment, provider: 'cloudera-ai', status: state, application_name: 'my-mcp-server-85d30f87', application_id: 'app-1', endpoint, message: `Workbench application APPLICATION_${state.toUpperCase()}` };
    await route.fulfill({ response, json: body });
  });
  await page.route('**/api/deployments/live*', async route => {
    checks += 1;
    if (checks >= 2) state = 'running';
    await route.fulfill({ json: { status: state } });
  });
  await login(page);
  await page.getByRole('button', { name: 'Deploy', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Deployment & monitoring' });
  await expect(dialog).toContainText('provisioning');
  await expect(dialog).toContainText('Checking Workbench every 5 seconds');
  await expect(dialog.locator('.tool-status')).toHaveText('running', { timeout: 20_000 });
  await expect(dialog).not.toContainText('Checking Workbench every 5 seconds');
  // The endpoint label and URL are separated.
  const row = dialog.locator('.detail-row').filter({ hasText: endpoint });
  const label = await row.locator('span').first().boundingBox();
  const url = await row.locator('code').boundingBox();
  expect(url!.x - (label!.x + label!.width)).toBeGreaterThanOrEqual(12);
  await expect(dialog).toContainText('Server health');
});

test('a server exports to a file and imports as a new server', async ({ page }) => {
  const headers = { Authorization: `Bearer ${admin}` };
  const api = 'http://127.0.0.1:18000/api';
  const source = await (await page.request.post(`${api}/servers`, { headers, data: { name: `Portable ${suffix}` } })).json();
  await page.request.post(`${api}/tools?server_id=${source.id}`, { headers, data: { name: 'portable_echo', description: 'Echo for the export test.', kind: 'python', pack: 'demo', function: 'echo' } });
  await login(page);
  await page.getByRole('combobox', { name: 'MCP server workspace' }).selectOption(source.id);
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Export', exact: true }).click()]);
  expect(download.suggestedFilename()).toBe(`portable-${suffix.toLowerCase()}.daedalus.json`);
  const file = await download.path();
  await page.locator('input[type="file"]').setInputFiles(file!);
  const dialog = page.getByRole('dialog', { name: 'Import an MCP server' });
  await expect(dialog).toContainText('1 tools, 0 connections, 0 project packs');
  await dialog.getByLabel('Name for the new server').fill(`Portable copy ${suffix}`);
  await dialog.getByRole('button', { name: 'Import server' }).click();
  await expect(dialog.getByRole('status')).toContainText(`Imported Portable copy ${suffix} with 1 tools`);
  await expect(dialog).toContainText('None: this server uses no stored secrets.');
  await dialog.getByRole('button', { name: 'Open the imported server' }).click();
  await expect(dialog).not.toBeVisible();
  const picker = page.getByRole('combobox', { name: 'MCP server workspace' });
  await expect(picker.locator('option:checked')).toHaveText(`Portable copy ${suffix}`);
  await page.getByRole('button', { name: 'List', exact: true }).click();
  await expect(page.locator('.table-row').filter({ hasText: 'portable_echo' })).toBeVisible();
  // A file that is not an export is refused with a reason, in the dialog.
  await page.locator('input[type="file"]').setInputFiles({ name: 'other.json', mimeType: 'application/json', buffer: Buffer.from('{"format":"something-else"}') });
  await expect(dialog.getByRole('alert')).toContainText('not a Daedalus server export');
  await expect(dialog.getByRole('button', { name: 'Import server' })).toBeDisabled();
});

test('an API older than the page is explained instead of showing a raw error', async ({ page }) => {
  await page.route('**/api/workspace*', async route => {
    const response = await route.fetch();
    const body = await response.json();
    body.deployment = { ...body.deployment, provider: 'cloudera-ai', status: 'provisioning', application_id: 'app-1', application_name: 'my-mcp-server-85d30f87' };
    await route.fulfill({ response, json: body });
  });
  let calls = 0;
  await page.route('**/api/deployments/live*', async route => { calls += 1; await route.fulfill({ status: 405, json: { detail: 'Method Not Allowed' } }); });
  await login(page);
  await page.getByRole('button', { name: 'Deploy', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Deployment & monitoring' });
  await expect(dialog).toContainText('Restart the Builder application to finish updating');
  await expect(dialog).not.toContainText('Method Not Allowed');
  await page.waitForTimeout(6000);
  expect(calls).toBe(1); // it stops asking
});

test('the servers area lists every server by name with its state', async ({ page }) => {
  const headers = { Authorization: `Bearer ${admin}` };
  const other = await (await page.request.post('http://127.0.0.1:18000/api/servers', { headers, data: { name: `Listed server ${suffix}` } })).json();
  await login(page);
  await page.getByRole('button', { name: /^All servers:/ }).click();
  const dialog = page.getByRole('dialog', { name: 'MCP servers in this project' });
  const mine = dialog.locator('.server-card').filter({ hasText: 'My MCP server' });
  await expect(mine).toContainText('open now');
  await expect(mine).toContainText('Online on pod'); // the checks stack runs a Server for the default workspace
  await expect(mine).toContainText('Owned by');
  const card = dialog.locator('.server-card').filter({ hasText: `Listed server ${suffix}` });
  await expect(card).toContainText(`ID ${other.id.slice(0, 8)}`);
  await expect(card).toContainText('No Server has run yet');
  await card.getByRole('button', { name: 'Open' }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.getByRole('combobox', { name: 'MCP server workspace' }).locator('option:checked')).toHaveText(`Listed server ${suffix}`);
});

test('the header summarises running servers and the overview shows this server live', async ({ page }) => {
  await login(page);
  // The checks stack runs a Server for the default workspace, so at least one server is running.
  const summary = page.getByRole('button', { name: /^All servers: \d+ of \d+ servers running$/ });
  await expect(summary).toContainText(/[1-9]\d* of \d+ servers running/);
  const card = page.getByRole('region', { name: 'Live status of this MCP server' });
  await expect(card).toContainText('Running');
  await expect(card).toContainText('/mcp');
  await expect(card).toContainText(/Heartbeat \d+s ago from pod/);
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
  await card.getByRole('button', { name: 'Copy the MCP URL' }).click();
  await expect(page.locator('.message-bar')).toContainText('MCP URL copied.');
  await card.getByRole('button', { name: 'Deployment details' }).click();
  await expect(page.getByRole('dialog', { name: 'Deployment & monitoring' })).toBeVisible();
  await page.getByRole('dialog', { name: 'Deployment & monitoring' }).getByRole('button', { name: 'Close dialog' }).click();
  await summary.click();
  await expect(page.getByRole('dialog', { name: 'MCP servers in this project' })).toBeVisible();
  // A server that never ran says so.
  const headers = { Authorization: `Bearer ${admin}` };
  const idle = await (await page.request.post('http://127.0.0.1:18000/api/servers', { headers, data: { name: `Idle ${suffix}` } })).json();
  await page.getByRole('dialog', { name: 'MCP servers in this project' }).getByRole('button', { name: 'Close dialog' }).click();
  await page.getByRole('combobox', { name: 'MCP server workspace' }).selectOption(idle.id);
  await expect(card).toContainText('Not deployed');
  await expect(card).toContainText('Publish a release, then deploy it');
});

test('an administrator deletes a whole MCP server after typing its name', async ({ page }) => {
  const headers = { Authorization: `Bearer ${admin}` };
  const doomed = await (await page.request.post('http://127.0.0.1:18000/api/servers', { headers, data: { name: `Delete me ${suffix}` } })).json();
  await page.request.post(`http://127.0.0.1:18000/api/tools?server_id=${doomed.id}`, { headers, data: { name: 'gone', description: 'Deleted with its server.', kind: 'python', pack: 'demo', function: 'echo' } });
  await login(page);
  const picker = page.getByRole('combobox', { name: 'MCP server workspace' });
  await picker.selectOption('85d30f87-b285-4d17-a89e-84bac6ac37bc');
  await expect(page.getByRole('button', { name: 'Delete', exact: true })).toBeDisabled(); // the default workspace
  await picker.selectOption(doomed.id);
  await page.getByRole('button', { name: 'Delete', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: `Delete Delete me ${suffix}` });
  await expect(dialog).toContainText('1 tools · 0 connections · 0 releases');
  const confirm = dialog.getByRole('button', { name: 'Delete this MCP server' });
  await expect(confirm).toBeDisabled();
  await dialog.getByLabel(`Type Delete me ${suffix} to confirm`).fill(`Delete me ${suffix}`);
  await confirm.click();
  await expect(dialog).not.toBeVisible();
  await expect(page.locator('.message-bar')).toContainText(`Deleted Delete me ${suffix}.`);
  await expect(picker.locator('option', { hasText: `Delete me ${suffix}` })).toHaveCount(0);
  await expect(picker.locator('option:checked')).toHaveText('My MCP server');
});

test('the header Stop button stops the Workbench application after confirming', async ({ page }) => {
  await login(page);
  const stop = page.getByRole('button', { name: 'Stop', exact: true });
  await expect(stop).toBeDisabled(); // nothing deployed yet
  // Simulate a server Daedalus deployed to Workbench; the check stack runs in manual mode.
  let status = 'running';
  await page.route('**/api/workspace*', async route => {
    const workspace = await (await route.fetch()).json();
    const server = status === 'stopped' ? { ...workspace.server, runtime: { ...workspace.server.runtime, online: false, ready: false } } : workspace.server;
    await route.fulfill({ json: { ...workspace, server, deployment: { ...workspace.deployment, provider: 'cloudera-ai', application_id: 'app-1', application_name: 'my-mcp-server', endpoint: 'https://my-mcp-server.example/mcp', status } } });
  });
  let stopped = 0;
  await page.route('**/api/deployments/stop', async route => { stopped += 1; status = 'stopped'; await route.fulfill({ json: { status: 'stopped' } }); });
  await page.reload();
  await expect(stop).toBeEnabled();
  page.once('dialog', dialog => { expect(dialog.message()).toContain('my-mcp-server'); void dialog.dismiss(); });
  await stop.click();
  expect(stopped).toBe(0); // cancelled
  page.once('dialog', dialog => void dialog.accept());
  await stop.click();
  await expect(page.locator('.message-bar')).toContainText('Stopped my-mcp-server (now stopped). You can now delete the server.');
  expect(stopped).toBe(1);
  await expect(stop).toBeDisabled();
});
