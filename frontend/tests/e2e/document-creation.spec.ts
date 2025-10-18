import { test, expect } from '@playwright/test';

test('document creation flow', async ({ page }) => {
  // This is a placeholder test. It will fail because the functionality is not implemented yet.
  await page.goto('http://localhost:3000');
  await page.click('text=New Document');
  await page.fill('input[name=title]', 'My new document');
  await page.click('text=Create');
  await expect(page.locator('h1')).toHaveText('My new document');
});
