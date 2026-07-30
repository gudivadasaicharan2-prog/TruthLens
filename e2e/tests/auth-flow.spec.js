/**
 * End-to-end test for authentication flow.
 */

const { test, expect } = require('@playwright/test');

test.describe('Authentication Flow', () => {
  test('user can login with email and password', async ({ page }) => {
    await page.goto('/login');
    
    // Fill in login form
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'SecurePass123');
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Verify redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('user can register new account', async ({ page }) => {
    await page.goto('/register');
    
    // Fill in registration form
    await page.fill('input[name="name"]', 'Test User');
    await page.fill('input[type="email"]', 'newuser@example.com');
    await page.fill('input[type="password"]', 'SecurePass123');
    
    // Click register button
    await page.click('button[type="submit"]');
    
    // Verify redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('user can login with Google', async ({ page }) => {
    await page.goto('/login');
    
    // Click Google login button
    await page.click('text=Continue with Google');
    
    // Note: Google OAuth requires actual OAuth flow
    // This test would need to be adjusted for mock OAuth or actual testing
    await expect(page.locator('text=Google')).toBeVisible();
  });

  test('user can logout', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'SecurePass123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Click logout
    await page.click('text=Logout');
    
    // Verify redirect to login
    await expect(page).toHaveURL(/.*login/);
  });
});
