/**
 * E2E tests for real-time collaboration between multiple users.
 *
 * Tests verify that two users can simultaneously edit a document
 * and see each other's changes in real-time.
 */

import { test, expect, Browser, BrowserContext, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:8000';

/**
 * Helper function to register and login a user
 */
async function registerAndLogin(
  page: Page,
  email: string,
  password: string,
  username: string
): Promise<string> {
  // Navigate to registration page
  await page.goto(`${BASE_URL}/auth/register`);

  // Fill registration form
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');

  // Wait for redirect to documents page
  await page.waitForURL(`${BASE_URL}/documents`);

  // Get JWT token from localStorage (for API calls)
  const token = await page.evaluate(() => {
    return localStorage.getItem('access_token');
  });

  return token || '';
}

/**
 * Helper function to create a document
 */
async function createDocument(
  page: Page,
  title: string,
  content: string = ''
): Promise<string> {
  await page.goto(`${BASE_URL}/documents`);
  await page.click('button:has-text("New Document")');

  // Fill document form
  await page.fill('input[name="title"]', title);
  if (content) {
    await page.fill('textarea[name="content"]', content);
  }
  await page.click('button:has-text("Create")');

  // Wait for redirect to document editor
  await page.waitForURL(/\/documents\/[a-f0-9\-]+/);

  // Extract document ID from URL
  const url = page.url();
  const documentId = url.split('/documents/')[1];
  return documentId;
}

/**
 * Helper function to share a document with another user
 */
async function shareDocument(
  page: Page,
  documentId: string,
  email: string
): Promise<void> {
  await page.goto(`${BASE_URL}/documents/${documentId}`);

  // Open share dialog
  await page.click('button[aria-label="Share document"]');

  // Fill share form
  await page.fill('input[name="email"]', email);
  await page.click('button:has-text("Share")');

  // Wait for success message
  await expect(page.locator('text=Document shared successfully')).toBeVisible();
}

test.describe('Real-time collaboration', () => {
  test('two users can edit document simultaneously and see changes in real-time', async ({
    browser,
  }) => {
    // Create two separate browser contexts (simulating two users)
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    try {
      // User 1: Register and create document
      const token1 = await registerAndLogin(
        page1,
        'alice@test.com',
        'password123',
        'Alice'
      );
      const documentId = await createDocument(
        page1,
        'Collaborative Document',
        'Initial content'
      );

      // User 2: Register
      const token2 = await registerAndLogin(
        page2,
        'bob@test.com',
        'password123',
        'Bob'
      );

      // User 1: Share document with User 2
      await shareDocument(page1, documentId, 'bob@test.com');

      // User 2: Navigate to shared document
      await page2.goto(`${BASE_URL}/documents/${documentId}`);

      // Wait for both users to be connected (check for WebSocket connection)
      await page1.waitForSelector('[data-testid="editor-loaded"]');
      await page2.waitForSelector('[data-testid="editor-loaded"]');

      // User 1 should see presence indicator for User 2
      await expect(
        page1.locator('[data-testid="user-presence"]:has-text("Bob")')
      ).toBeVisible({ timeout: 5000 });

      // User 2 should see presence indicator for User 1
      await expect(
        page2.locator('[data-testid="user-presence"]:has-text("Alice")')
      ).toBeVisible({ timeout: 5000 });

      // User 1: Type text in the editor
      const editor1 = page1.locator('[data-testid="codemirror-editor"]');
      await editor1.click();
      await page1.keyboard.type('Hello from Alice! ');

      // User 2: Should see the text appear in real-time
      await expect(editor1).toContainText('Hello from Alice!', {
        timeout: 2000,
      });

      // User 2: Type text in the editor
      const editor2 = page2.locator('[data-testid="codemirror-editor"]');
      await editor2.click();
      await page2.keyboard.press('End'); // Move to end of document
      await page2.keyboard.type('Hello from Bob!');

      // User 1: Should see Bob's text appear in real-time
      await expect(editor1).toContainText('Hello from Bob!', {
        timeout: 2000,
      });

      // Verify final content on both pages
      const finalContent = 'Initial contentHello from Alice! Hello from Bob!';
      await expect(editor1).toContainText(finalContent);
      await expect(editor2).toContainText(finalContent);
    } finally {
      await page1.close();
      await page2.close();
      await context1.close();
      await context2.close();
    }
  });

  test('cursor positions are visible to other users', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    try {
      // Setup: User 1 creates document, User 2 joins
      await registerAndLogin(page1, 'carol@test.com', 'password123', 'Carol');
      const documentId = await createDocument(
        page1,
        'Cursor Test',
        'Line 1\nLine 2\nLine 3'
      );

      await registerAndLogin(page2, 'dave@test.com', 'password123', 'Dave');
      await shareDocument(page1, documentId, 'dave@test.com');
      await page2.goto(`${BASE_URL}/documents/${documentId}`);

      // Wait for both editors to load
      await page1.waitForSelector('[data-testid="editor-loaded"]');
      await page2.waitForSelector('[data-testid="editor-loaded"]');

      // User 1: Move cursor to specific position
      const editor1 = page1.locator('[data-testid="codemirror-editor"]');
      await editor1.click();
      await page1.keyboard.press('ArrowDown');
      await page1.keyboard.press('ArrowDown');

      // User 2: Should see User 1's cursor indicator
      const cursor1 = page2.locator(
        '[data-testid="cursor-indicator"][data-user="carol@test.com"]'
      );
      await expect(cursor1).toBeVisible({ timeout: 2000 });

      // User 2: Move cursor
      const editor2 = page2.locator('[data-testid="codemirror-editor"]');
      await editor2.click();
      await page2.keyboard.press('End');

      // User 1: Should see User 2's cursor indicator
      const cursor2 = page1.locator(
        '[data-testid="cursor-indicator"][data-user="dave@test.com"]'
      );
      await expect(cursor2).toBeVisible({ timeout: 2000 });
    } finally {
      await page1.close();
      await page2.close();
      await context1.close();
      await context2.close();
    }
  });

  test('user can reconnect after network interruption', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
      // Setup
      await registerAndLogin(page, 'eve@test.com', 'password123', 'Eve');
      const documentId = await createDocument(page, 'Reconnect Test', 'Content');

      await page.waitForSelector('[data-testid="editor-loaded"]');

      // Simulate network interruption by going offline
      await context.setOffline(true);

      // Wait for disconnection indicator
      await expect(
        page.locator('[data-testid="connection-status"]:has-text("Disconnected")')
      ).toBeVisible({ timeout: 5000 });

      // Type while offline (changes should be queued)
      const editor = page.locator('[data-testid="codemirror-editor"]');
      await editor.click();
      await page.keyboard.type('Offline changes');

      // Reconnect
      await context.setOffline(false);

      // Wait for reconnection
      await expect(
        page.locator('[data-testid="connection-status"]:has-text("Connected")')
      ).toBeVisible({ timeout: 10000 });

      // Verify offline changes were synced
      await expect(editor).toContainText('Offline changes');
    } finally {
      await page.close();
      await context.close();
    }
  });

  test('changes persist after page reload', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
      // Setup
      await registerAndLogin(page, 'frank@test.com', 'password123', 'Frank');
      const documentId = await createDocument(
        page,
        'Persistence Test',
        'Initial'
      );

      await page.waitForSelector('[data-testid="editor-loaded"]');

      // Make changes
      const editor = page.locator('[data-testid="codemirror-editor"]');
      await editor.click();
      await page.keyboard.press('End');
      await page.keyboard.type(' changes');

      // Wait for auto-save (15 seconds according to spec)
      await page.waitForTimeout(16000);

      // Verify auto-save indicator
      await expect(
        page.locator('[data-testid="save-status"]:has-text("Saved")')
      ).toBeVisible();

      // Reload page
      await page.reload();
      await page.waitForSelector('[data-testid="editor-loaded"]');

      // Verify changes persisted
      const editorAfterReload = page.locator('[data-testid="codemirror-editor"]');
      await expect(editorAfterReload).toContainText('Initial changes');
    } finally {
      await page.close();
      await context.close();
    }
  });

  test('concurrent edits from three users are synchronized', async ({
    browser,
  }) => {
    // Create three separate contexts
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const context3 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    const page3 = await context3.newPage();

    try {
      // User 1: Create document
      await registerAndLogin(page1, 'grace@test.com', 'password123', 'Grace');
      const documentId = await createDocument(page1, 'Three User Test', '');

      // Users 2 and 3: Register
      await registerAndLogin(page2, 'henry@test.com', 'password123', 'Henry');
      await registerAndLogin(page3, 'iris@test.com', 'password123', 'Iris');

      // Share with both users
      await shareDocument(page1, documentId, 'henry@test.com');
      await shareDocument(page1, documentId, 'iris@test.com');

      // All users navigate to document
      await page2.goto(`${BASE_URL}/documents/${documentId}`);
      await page3.goto(`${BASE_URL}/documents/${documentId}`);

      // Wait for all editors to load
      await page1.waitForSelector('[data-testid="editor-loaded"]');
      await page2.waitForSelector('[data-testid="editor-loaded"]');
      await page3.waitForSelector('[data-testid="editor-loaded"]');

      // All users should see each other's presence
      await expect(
        page1.locator('[data-testid="user-presence"]:has-text("Henry")')
      ).toBeVisible({ timeout: 5000 });
      await expect(
        page1.locator('[data-testid="user-presence"]:has-text("Iris")')
      ).toBeVisible({ timeout: 5000 });

      // All users type simultaneously
      const editor1 = page1.locator('[data-testid="codemirror-editor"]');
      const editor2 = page2.locator('[data-testid="codemirror-editor"]');
      const editor3 = page3.locator('[data-testid="codemirror-editor"]');

      await editor1.click();
      await editor2.click();
      await editor3.click();

      // Type at the same time
      await Promise.all([
        page1.keyboard.type('Grace: '),
        page2.keyboard.type('Henry: '),
        page3.keyboard.type('Iris: '),
      ]);

      // All users should eventually see all changes (Yjs will merge them)
      // The exact order depends on Yjs CRDT resolution, but all text should be present
      await expect(editor1).toContainText('Grace:', { timeout: 3000 });
      await expect(editor1).toContainText('Henry:', { timeout: 3000 });
      await expect(editor1).toContainText('Iris:', { timeout: 3000 });

      // Verify consistency across all clients
      const content1 = await editor1.textContent();
      const content2 = await editor2.textContent();
      const content3 = await editor3.textContent();

      expect(content1).toBe(content2);
      expect(content2).toBe(content3);
    } finally {
      await page1.close();
      await page2.close();
      await page3.close();
      await context1.close();
      await context2.close();
      await context3.close();
    }
  });

  test('user leaving document removes their cursor indicator', async ({
    browser,
  }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    try {
      // Setup
      await registerAndLogin(page1, 'jack@test.com', 'password123', 'Jack');
      const documentId = await createDocument(page1, 'Leave Test', '');

      await registerAndLogin(page2, 'kelly@test.com', 'password123', 'Kelly');
      await shareDocument(page1, documentId, 'kelly@test.com');
      await page2.goto(`${BASE_URL}/documents/${documentId}`);

      await page1.waitForSelector('[data-testid="editor-loaded"]');
      await page2.waitForSelector('[data-testid="editor-loaded"]');

      // User 1 should see User 2's presence
      await expect(
        page1.locator('[data-testid="user-presence"]:has-text("Kelly")')
      ).toBeVisible({ timeout: 5000 });

      // User 2 leaves (closes page)
      await page2.close();

      // User 1 should see User 2's presence removed
      await expect(
        page1.locator('[data-testid="user-presence"]:has-text("Kelly")')
      ).toBeHidden({ timeout: 5000 });

      // User 1 should see "User left" notification
      await expect(
        page1.locator('[data-testid="notification"]:has-text("Kelly left")')
      ).toBeVisible({ timeout: 2000 });
    } finally {
      await page1.close();
      await context1.close();
      await context2.close();
    }
  });
});
