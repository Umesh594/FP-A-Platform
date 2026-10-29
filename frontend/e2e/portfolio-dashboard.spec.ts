import { expect, test } from "@playwright/test";

test("portfolio dashboard remains usable at desktop and mobile widths", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Portfolio Dashboard" })).toBeVisible();
  await expect(page.getByText("Summit Growth Partners")).toBeVisible();
  const dimensions = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.viewportWidth);
});
