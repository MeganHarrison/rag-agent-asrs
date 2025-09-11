import { test, expect } from '@playwright/test';

test.describe('FM Global Expert Page Tests', () => {
  test('should show Railway connection status and test chat functionality', async ({ page }) => {
    // Navigate to the FM Global Expert page
    await page.goto('http://localhost:3010/fm-global-expert');
    
    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');
    
    // Wait for the connection status check to complete
    await page.waitForTimeout(3000);
    
    // Take first screenshot showing the Railway connection status indicator
    await page.screenshot({ 
      path: '../screenshots/fm-global-working-1.png',
      fullPage: true 
    });
    
    // Find the chat input field with the correct placeholder
    const chatInput = page.locator('input[placeholder="Type message"]');
    await expect(chatInput).toBeVisible({ timeout: 10000 });
    
    // Type the test question
    await chatInput.fill("What are the clearance requirements for ASRS rack sprinklers?");
    
    // Find and click the submit button (Send button)
    const submitButton = page.locator('button[type="submit"]').last();
    await expect(submitButton).toBeVisible();
    await submitButton.click();
    
    // Wait for the response to appear (longer timeout for AI response)
    await page.waitForTimeout(12000);
    
    // Look for AI response - it should appear with the orange AI avatar
    const aiResponse = page.locator('div:has(div.bg-orange-500):has-text("AI")').first();
    await expect(aiResponse).toBeVisible({ timeout: 15000 });
    
    // Take second screenshot showing the response
    await page.screenshot({ 
      path: '../screenshots/fm-global-working-2.png',
      fullPage: true 
    });
    
    // Verify the page loaded correctly and response exists
    const responseText = await page.locator('div.prose').first().textContent();
    expect(responseText).toBeTruthy();
    console.log('Response preview:', responseText?.substring(0, 200));
  });
});