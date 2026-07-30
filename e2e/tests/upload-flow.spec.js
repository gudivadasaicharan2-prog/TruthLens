/**
 * End-to-end test for image upload flow.
 */

const { test, expect } = require('@playwright/test');

test.describe('Image Upload Flow', () => {
  test('user can upload an image and receive results', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to detect page
    await page.click('text=Detect');
    await expect(page).toHaveURL(/.*detect/);
    
    // Upload a test image
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./e2e/fixtures/sample.jpg');
    
    // Wait for analysis to complete
    await expect(page.locator('text=Analyzing')).toBeHidden();
    await expect(page.locator('text=Results')).toBeVisible();
    
    // Verify results are displayed
    await expect(page.locator('text=Verdict')).toBeVisible();
    await expect(page.locator('text=Confidence')).toBeVisible();
  });

  test('user sees error for invalid file type', async ({ page }) => {
    await page.goto('/detect');
    
    // Try to upload a text file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./e2e/fixtures/sample.txt');
    
    // Verify error message
    await expect(page.locator('text=Invalid file type')).toBeVisible();
  });

  test('user can download report after analysis', async ({ page }) => {
    await page.goto('/detect');
    
    // Upload image
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./e2e/fixtures/sample.jpg');
    
    // Wait for analysis
    await expect(page.locator('text=Results')).toBeVisible();
    
    // Click download report button
    const downloadPromise = page.waitForEvent('download');
    await page.click('text=Download Report');
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });
});
