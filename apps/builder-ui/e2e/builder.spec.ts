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
  if (await page.getByRole('heading', { name: /MCP server/ }).isVisible().catch(() => false)) return;
  await page.getByLabel('Management token').fill(token);
  await page.getByRole('button', { name: 'Enter workspace' }).click();
  await expect(page.getByRole('heading', { name: 'My MCP server' })).toBeVisible();
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
