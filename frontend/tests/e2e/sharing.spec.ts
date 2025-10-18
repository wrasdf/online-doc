
import { test, expect } from '@playwright/test';

const UI_URL = 'http://localhost:3000';

// Define user credentials
const ownerUser = {
  email: 'owner@example.com',
  password: 'password123',
  username: 'owneruser',
};

const sharedUser = {
  email: 'shared@example.com',
  password: 'password123',
  username: 'shareduser',
};

// Helper function to register and login a user
async function registerAndLogin(page: any, user: any) {
  await page.goto(`${UI_URL}/register`);
  await page.fill('input[name="username"]', user.username);
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(`${UI_URL}/login`);

  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(new RegExp('.*/documents'));
}

async function logout(page: any) {
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(`${UI_URL}/login`);
}

test.describe('Document Sharing Flow', () => {
  let page: any;
  let ownerContext: any;
  let sharedUserContext: any;

  test.beforeAll(async ({ browser }) => {
    ownerContext = await browser.newContext();
    sharedUserContext = await browser.newContext();

    // Register users
    const ownerPage = await ownerContext.newPage();
    await registerAndLogin(ownerPage, ownerUser);
    await ownerPage.close();

    const sharedUserPage = await sharedUserContext.newPage();
    await registerAndLogin(sharedUserPage, sharedUser);
    await sharedUserPage.close();
  });

  test.beforeEach(async () => {
    page = await ownerContext.newPage();
    await page.goto(UI_URL);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should allow a user to share a document with another user', async () => {
    // 1. Log in as the first user and create a document
    await registerAndLogin(page, ownerUser);
    const documentTitle = `My Shared Document - ${Date.now()}`;
    await page.fill('input[placeholder="Enter document title..."]', documentTitle);
    await page.click('button:has-text("Create Document")');
    await expect(page).toHaveURL(new RegExp('.*/documents/.*'));

    // 2. Share the document with the second user
    await page.click('button:has-text("Share")');
    await page.fill('input[placeholder="Enter email to share with..."]', sharedUser.email);
    await page.click('button:has-text("Add Collaborator")');
    await expect(page.locator('.collaborator-list')).toContainText(sharedUser.email);
    await page.click('button.btn-close'); // Close share dialog

    // 3. Log out
    await logout(page);

    // 4. Log in as the second user
    const sharedPage = await sharedUserContext.newPage();
    await sharedPage.goto(UI_URL);
    await registerAndLogin(sharedPage, sharedUser);

    // 5. Verify that the shared document is visible in the document list
    await expect(sharedPage.locator('.card-title')).toContainText(documentTitle);

    // 6. Open the shared document and verify that it can be edited
    await sharedPage.click(`text=${documentTitle}`);
    await expect(sharedPage).toHaveURL(new RegExp('.*/documents/.*'));

    const editor = sharedPage.locator('.cm-content');
    await editor.fill('This is an edit from the shared user.');
    await expect(editor).toHaveText('This is an edit from the shared user.');
  });
});
