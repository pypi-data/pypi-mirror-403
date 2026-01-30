import { expect, test } from '@jupyterlab/galata';

/**
 * Don't load JupyterLab webpage before running the tests.
 * This is required to ensure we capture all log messages.
 */
test.use({ autoGoto: false });

test('should emit an activation console message', async ({ page }) => {
  const logs: string[] = [];

  page.on('console', message => {
    logs.push(message.text());
  });

  await page.goto();

  expect(
    logs.filter(
      s =>
        s ===
        'JupyterLab extension jupyterlab_proxy_launcher_command_extension is activated!'
    )
  ).toHaveLength(1);
});

test('should show command in command palette', async ({ page }) => {
  await page.goto();

  // Open command palette
  await page.keyboard.press('Control+Shift+C');

  // Wait for command palette to appear
  await page.waitForSelector('.lm-CommandPalette-input');

  // Search for proxy launcher command
  await page.fill('.lm-CommandPalette-input', 'Open Proxy Launcher');

  // Verify command appears in results
  const commandItem = page.locator(
    '.lm-CommandPalette-item:has-text("Open Proxy Launcher")'
  );
  await expect(commandItem).toBeVisible();
});

test('should open proxy launcher dialog', async ({ page }) => {
  await page.goto();

  // Open command palette and execute command
  await page.keyboard.press('Control+Shift+C');
  await page.waitForSelector('.lm-CommandPalette-input');
  await page.fill('.lm-CommandPalette-input', 'Open Proxy Launcher');
  await page.click('.lm-CommandPalette-item:has-text("Open Proxy Launcher")');

  // Wait for dialog to appear
  const dialog = page.locator('.jp-Dialog');
  await expect(dialog).toBeVisible();

  // Verify dialog title
  await expect(dialog.locator('.jp-Dialog-header')).toContainText(
    'Proxy Launcher'
  );

  // Verify port input exists
  const portInput = dialog.locator('input[type="number"]');
  await expect(portInput).toBeVisible();

  // Verify path input exists
  const pathInput = dialog.locator('input[type="text"]');
  await expect(pathInput).toBeVisible();

  // Verify checkbox exists
  const checkbox = dialog.locator('input[type="checkbox"]');
  await expect(checkbox).toBeVisible();

  // Verify helper text exists
  await expect(dialog.locator('text=e.g., 8501')).toBeVisible();
  await expect(dialog.locator('text=e.g., /api/docs')).toBeVisible();
  await expect(
    dialog.locator('text=Connect to a service running on the specified port')
  ).toBeVisible();

  // Close dialog
  await dialog.locator('button:has-text("Cancel")').click();
  await expect(dialog).not.toBeVisible();
});

test('should validate port input', async ({ page }) => {
  await page.goto();

  // Open dialog via keyboard shortcut
  await page.keyboard.press('Control+Shift+P');

  // Wait for dialog
  const dialog = page.locator('.jp-Dialog');
  await expect(dialog).toBeVisible();

  // Try to submit without port
  await dialog.locator('button:has-text("Open")').click();

  // Verify validation error dialog appears
  const errorDialog = page.locator('.jp-Dialog:has-text("Invalid Port")');
  await expect(errorDialog).toBeVisible();

  // Close error dialog
  await errorDialog.locator('button:has-text("OK")').click();
});
