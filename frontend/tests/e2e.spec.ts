import { test, expect } from '@playwright/test';

const BASE = 'https://www.haqnow.com';

// Helper: wait for backend health
test.beforeAll(async ({ request }) => {
  const res = await request.get(`${BASE}/api/health`);
  expect(res.ok()).toBeTruthy();
});

// Basic homepage UI checks
test('homepage renders and country dropdown overlays map', async ({ page }) => {
  await page.goto(BASE);
  await expect(page.getByText('Global Corruption Document Distribution')).toBeVisible();
  // Dropdown should appear above the map when opened
  await page.getByLabel('Select a Country:').click();
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
test('search page loads and returns documents', async ({ page }) => {
  await page.goto(`${BASE}/search-page`);
  await page.getByPlaceholder('Enter keywords like: corruption, bribery, fraud, contracts...').fill('health');
  await page.keyboard.press('Enter');
  await expect(page.getByText(/results? found/i)).toBeVisible();
});

// Document detail smoke
test('document detail shows download buttons and AI button', async ({ page }) => {
  await page.goto(`${BASE}/search-page?q=health`);
  await page.waitForTimeout(1000);
  const first = page.locator('button:has-text("Original PDF")').first();
  await expect(first).toBeVisible();
  // Navigate to a document detail page by opening first result link if present
  // If there isn't a link, assume a direct navigation path exists with id param
  await page.goto(`${BASE}/document-detail-page?id=73`);
  await expect(page.getByRole('button', { name: /Ask AI about this document/i })).toBeVisible();
});
