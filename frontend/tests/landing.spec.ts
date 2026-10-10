import { test, expect } from '@playwright/test'
// Keep browser regressions deterministic when Google Fonts is unreachable.
test.beforeEach(async ({ page }) => {
  await page.route('https://fonts.googleapis.com/**', route => route.abort())
  await page.route('https://fonts.gstatic.com/**', route => route.abort())
})

test('complete landing page uses the required typography, real city preview and accessible colors', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toContainText("Waste is not the end.It's the beginning.")
  for (const title of ['Explore Materials', 'Understand Pathways', 'See the Evidence', 'Discover', 'Select Waste', 'Choose a Study', 'Calculate', 'Understand Results']) {
    const heading = page.getByRole('heading', { name: title, exact: true })
    await expect(heading).toBeVisible()
    const style = await heading.evaluate(node => { const css = getComputedStyle(node); return { color: css.color, font: css.fontFamily, style: css.fontStyle, weight: css.fontWeight } })
    expect(style).toEqual({ color: 'rgb(223, 255, 69)', font: '"Times New Roman", Times, serif', style: 'italic', weight: '400' })
  }
  for (const id of ['city', 'pathways', 'how-it-works']) await expect(page.locator(`#${id}`)).toBeVisible()
  for (const primary of await page.locator('.ww-primary').all()) {
    await expect(primary).toHaveCSS('color', 'rgb(245, 247, 237)')
    await expect(primary).toHaveCSS('font-weight', '700')
  }
  for (const highlight of await page.locator('.ww-highlight').all()) {
    await expect(highlight).toHaveCSS('color', 'rgb(223, 255, 69)')
    await expect(highlight).toHaveCSS('font-style', 'italic')
  }
  const img = page.locator('.ww-city-preview img')
  await img.scrollIntoViewIfNeeded()
  await expect.poll(() => img.evaluate((node: HTMLImageElement) => node.complete && node.naturalWidth > 0)).toBe(true)
  await expect(page.locator('canvas')).toHaveCount(0)
  expect(await page.evaluate(() => performance.getEntriesByType('resource').some(entry => /\/assets\/three-/.test(entry.name)))).toBe(false)
  await expect(page.getByText('Reference calculations are not validated plant-performance predictions.', { exact: true })).toBeVisible()
  await expect(page.locator('.ww-footer .ww-brand')).toHaveCSS('color', 'rgb(245, 247, 237)')
  await page.screenshot({ path: '../reports/landing-desktop.png', fullPage: true })
  expect(errors).toEqual([])
})

for (const [name, index] of [['Explore', 0], ['Explore WasteWise', 0], ['Explore WasteWise', 1], ['Explore the 3D City', 0]] as const) {
  test(`${name} CTA ${index + 1} opens the existing dashboard and refreshes directly`, async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name, exact: true }).nth(index).click()
    await expect(page).toHaveURL(/\/simulation$/)
    await expect(page.getByText('Engine connected', { exact: true })).toBeVisible({ timeout: 45000 })
    await expect(page.locator('canvas')).toBeVisible()
    await page.reload()
    await expect(page.getByRole('button', { name: 'Choose Timber yard', exact: true })).toBeEnabled({ timeout: 45000 })
    await page.getByRole('link', { name: 'Home', exact: true }).click()
    await expect(page).toHaveURL(/\/$/)
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Waste is not the end.')
  })
}

test('section navigation and process link scroll to their targets', async ({ page }) => {
  await page.goto('/')
  for (const [name, id] of [['3D City', 'city'], ['Pathways', 'pathways'], ['How It Works', 'how-it-works'], ['Home', 'home']]) {
    await page.getByRole('navigation').getByRole('link', { name, exact: true }).click()
    await expect(page).toHaveURL(new RegExp(`#${id}$`))
    await expect.poll(() => page.locator(`#${id}`).evaluate(node => Math.abs(node.getBoundingClientRect().top) < 150)).toBe(true)
  }
  await page.getByRole('link', { name: 'How It Works', exact: true }).last().click()
  await expect(page).toHaveURL(/#how-it-works$/)
})

for (const width of [360, 390, 768, 1024]) test(`responsive landing at ${width}px has usable navigation and no overflow`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  if (width < 761) {
    await page.getByRole('button', { name: 'Open navigation' }).click()
    await expect(page.getByRole('button', { name: 'Close navigation' })).toHaveAttribute('aria-expanded', 'true')
    await page.getByRole('navigation').getByRole('link', { name: 'Pathways' }).click()
    await expect(page.getByRole('button', { name: 'Open navigation' })).toHaveAttribute('aria-expanded', 'false')
  }
  for (const card of await page.locator('.ww-card').all()) {
    const bounds = await card.boundingBox()
    expect(bounds!.x).toBeGreaterThanOrEqual(0)
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(width)
  }
  await page.screenshot({ path: `../reports/landing-${width}.png`, fullPage: true })
})

test('reduced motion removes entrance and hover animation', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await expect(page.locator('.ww-hero .ww-heading')).toHaveCSS('animation-name', 'none')
  await expect(page.locator('.ww-feature').first()).toHaveCSS('transition-duration', '0s')
})


