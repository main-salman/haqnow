import { test, expect } from '@playwright/test';

const BASE = 'https://www.haqnow.com';

// Helper: wait for backend health with retries to avoid flaky CI failures
async function waitForBackendHealth(request: any, retries = 6, delayMs = 5000): Promise<boolean> {
  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      const res = await request.get(`${BASE}/api/health`, { timeout: 5000 });
      if (res.ok()) return true;
    } catch {
      // ignore and retry
    }
    await new Promise((r) => setTimeout(r, delayMs));
  }
  return false;
}

let backendHealthy = false;
test.beforeAll(async ({ request }) => {
  backendHealthy = await waitForBackendHealth(request);
});

test.beforeEach(async () => {
  if (!backendHealthy) test.skip('Backend health endpoint unavailable; skipping e2e');
});

// Basic homepage UI checks
test('homepage renders and country dropdown overlays map', async ({ page }) => {
  await page.goto(BASE);
  await expect(page.getByText('Global Corruption Document Distribution')).toBeVisible();
  // Open country select by clicking its placeholder text to avoid role differences
  await page.getByText('Choose a country to view documents...').first().click();
  const list = page.locator('[role="listbox"]');
  await expect(list).toBeVisible();
});

// Admin login + approve flow (requires valid creds set as env in CI)
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || '';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || '';

// Smoke test admin login page is reachable
test('admin login page loads', async ({ page }) => {
  await page.goto(`${BASE}/admin-login-page`);
  await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
});

// Search results smoke
// Prefer a stable search by country derived from API to avoid flakiness
test('search page loads and returns documents', async ({ page, request }) => {
  const res = await request.get(`${BASE}/api/search/search?q=&per_page=1`);
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  const doc = body?.documents?.[0];
  expect(typeof doc?.country).toBe('string');
  const country = doc.country as string;

  await page.goto(`${BASE}/search-page?country=${encodeURIComponent(country)}`);
  // Expect at least one result card element containing the Ask AI link text
  await expect(page.getByText(/Ask Questions About this Document/i)).toBeVisible({ timeout: 15000 });
});

// Helper to fetch a valid document id from API
async function fetchFirstDocumentId(request: any): Promise<number> {
  const res = await request.get(`${BASE}/api/search/search?q=&per_page=1`);
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(Array.isArray(body.documents)).toBeTruthy();
  expect(body.documents.length).toBeGreaterThan(0);
  return body.documents[0].id as number;
}

// Document detail smoke + AI button
test('document detail shows download buttons and AI button', async ({ page, request }) => {
  const docId = await fetchFirstDocumentId(request);
  await page.goto(`${BASE}/document-detail-page?id=${docId}`);
  await expect(page.getByRole('button', { name: /Ask AI about this document/i })).toBeVisible();
});

// Backend doc-scoped AI endpoint responds
test('AI document-question endpoint responds for a real document', async ({ request }) => {
  const docId = await fetchFirstDocumentId(request);
  const res = await request.post(`${BASE}/api/rag/document-question`, {
    data: { question: 'Give one-line summary', document_id: docId },
    headers: { 'Content-Type': 'application/json' },
    timeout: 60000,
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(typeof body.answer).toBe('string');
  expect(body.sources?.[0]?.document_id).toBe(docId);
});
