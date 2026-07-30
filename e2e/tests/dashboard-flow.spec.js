/**
 * End-to-end test for dashboard and history flow.
 */

const { test, expect } = require('@playwright/test');

test.describe('Dashboard and History Flow', () => {
  test('user can view analysis history', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'SecurePass123');
    await page.click('button[type="submit"]');
    
    // Navigate to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Verify history section is visible
    await expect(page.locator('text=History')).toBeVisible();
  });

  test('user can view analysis details from history', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Click on a history item
    await page.click('.history-item:first-child');
    
    // Verify details modal or page opens
    await expect(page.locator('text=Analysis Details')).toBeVisible();
  });

  test('user can navigate to settings', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Click settings link
    await page.click('text=Settings');
    
    // Verify settings page loads
    await expect(page).toHaveURL(/.*settings/);
    await expect(page.locator('text=Settings')).toBeVisible();
  });
});
