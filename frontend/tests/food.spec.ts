import { test, expect, type Page } from '@playwright/test'
const subtype = 'EBMUD food waste pulp; mesophilic; 15-day MCRT'
async function food(page: Page) {
  await page.goto('/simulation')
  await expect(page.getByText('Engine connected', { exact: true })).toBeVisible({ timeout: 45000 })
  await page.getByRole('button', { name: 'Choose Food market', exact: true }).click()
  await expect(page.locator('#subtype')).toHaveValue(subtype)
  await expect(page.locator('#technology')).toHaveValue('Anaerobic digestion')
  await expect(page.locator('#output')).toHaveValue('biogas')
  await expect(page.locator('#study')).toBeVisible()
  await page.locator('#study').selectOption('P0006')
}
async function ready(page: Page) {
  await food(page)
  await page.locator('#quantity').fill('100')
  await page.locator('#moisture').fill('93.6')
  await page.locator('#reference-mode').check()
}

test('Food Market submits a real biogas reference and preserves distinct methane and the truck journey', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await ready(page)
  await page.getByTestId('food-linked-parameters').locator('summary').click()
  await expect(page.getByTestId('food-linked-parameters')).toContainText('W0059 / volatile solids pct ts: 86.3 % of TS')
  const pending = page.waitForResponse(response => response.url().endsWith('/api/calculate'))
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  const response = await pending
  expect(response.status()).toBe(200)
  expect(response.request().postDataJSON()).toEqual({ waste_category: 'Food and organic waste', waste_subtype: subtype, quantity_kg: 100, moisture_pct: 93.6, technology: 'Anaerobic digestion', desired_output: 'biogas', parameter_id: 'P0006', reference_mode: true })
  const body = await response.json()
  expect(body.calculated_value).toBeCloseTo(5.015303445151446, 11)
  await expect(page.getByTestId('calculation-status')).toHaveText('CALCULATED REFERENCE')
  await expect(page.getByTestId('primary-quantity')).toHaveText('5.01530344515145')
  await expect(page.getByText('m3 biogas (source T/P unspecified)', { exact: true })).toBeVisible()
  await expect(page.getByTestId('food-methane-volume')).toContainText('3.20979420489693')
  await expect(page.getByTestId('food-methane-volume')).toContainText('64% vol CH4')
  await expect(page.getByTestId('food-result-context')).toContainText('ratio-of-published-means')
  await expect(page.getByTestId('food-energy-gap')).toContainText('Chemical energy in MJ unavailable')
  await page.locator('#results summary').filter({ hasText: 'Calculation formula' }).click()
  await expect(page.locator('#results .formula')).toHaveText(body.formula)
  await expect(page.locator('#results').getByRole('link', { name: /S03/ })).toBeVisible()
  const canvas = page.locator('canvas')
  const position = await canvas.getAttribute('data-truck-position')
  await expect.poll(() => canvas.getAttribute('data-truck-position')).not.toBe(position)
  await expect(page.getByRole('progressbar', { name: 'Conceptual animation progress' })).toHaveAttribute('aria-valuenow', '100', { timeout: 30000 })
  await expect(page.getByText('Visual journey complete', { exact: true })).toBeVisible()
  await page.screenshot({ path: '../reports/food_waste_reference_desktop.png', fullPage: true })
  expect(errors).toEqual([])
})

test('food study, basis and acknowledgement are explicit and wrong moisture never sends a calculation', async ({ page }) => {
  let calls = 0
  page.on('request', request => { if (request.url().endsWith('/api/calculate')) calls++ })
  await food(page)
  await expect(page.locator('#moisture')).toHaveValue('')
  await expect(page.locator('#reference-mode')).not.toBeChecked()
  const calculate = page.getByRole('button', { name: 'Calculate reference output', exact: true })
  await expect(calculate).toBeDisabled()
  await page.locator('#moisture').fill('93.5'); await page.locator('#reference-mode').check()
  await expect(page.getByTestId('reference-gaps')).toContainText('93.6% wet basis')
  await expect(calculate).toBeDisabled()
  await page.locator('#moisture').fill('93.6')
  await expect(calculate).toBeEnabled()
  await page.locator('#study').selectOption('')
  await expect(page.locator('#reference-mode')).not.toBeChecked()
  await expect(calculate).toBeDisabled()
  expect(calls).toBe(0)
})

test('explicit published food sample uses W0059 and acknowledgement resets on basis changes', async ({ page }) => {
  await ready(page)
  await page.locator('#reference-sample').selectOption('W0059')
  await expect(page.locator('#moisture')).toHaveValue('')
  await expect(page.locator('#reference-mode')).not.toBeChecked()
  await page.locator('#reference-mode').check()
  const pending = page.waitForResponse(response => response.url().endsWith('/api/calculate'))
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  const response = await pending
  expect(response.request().postDataJSON()).toMatchObject({ property_id: 'W0059', moisture_pct: null })
  expect((await response.json()).calculated_value).toBeCloseTo(5.015303445151446, 11)
  await expect(page.getByTestId('primary-quantity')).toBeVisible()
  await page.locator('#study').selectOption('')
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
  await expect(page.locator('#reference-mode')).not.toBeChecked()
})

test('missing food dependency evidence disables the guided study rather than inventing a value', async ({ page }) => {
  await page.route('**/api/reference-studies?**', async route => {
    const response = await route.fetch()
    const data = await response.json()
    if (data.waste_subtype === subtype) {
      data.studies.forEach((study: { selectable: boolean; evidence_status: string }) => { study.selectable = false; study.evidence_status = 'UNKNOWN' })
      data.linked_reference_parameters = []
      data.reference_run_moisture = null
    }
    await route.fulfill({ response, json: data })
  })
  await page.goto('/simulation')
  await expect(page.getByText('Engine connected', { exact: true })).toBeVisible({ timeout: 45000 })
  await page.getByRole('button', { name: 'Choose Food market', exact: true }).click()
  await expect(page.locator('#study option[value="P0006"]')).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Calculate reference output', exact: true })).toBeDisabled()
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
})

test('food guided flow and results remain readable on mobile without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await ready(page)
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  await expect(page.getByTestId('calculation-status')).toHaveText('CALCULATED REFERENCE')
  await expect(page.getByTestId('food-methane-volume')).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: '../reports/food_waste_reference_mobile.png', fullPage: true })
})

test('leaving food clears its study and results and preserves the timber reference flow', async ({ page }) => {
  await ready(page)
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  await expect(page.getByTestId('primary-quantity')).toBeVisible()
  await page.getByRole('button', { name: 'Choose Timber yard', exact: true }).click()
  await expect(page.locator('#subtype')).toHaveValue('Dry wood reference')
  await expect(page.locator('#study')).toHaveValue('')
  await expect(page.locator('#moisture')).toHaveValue('')
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
  await page.locator('#study').selectOption('P0022'); await page.locator('#moisture').fill('10'); await page.locator('#reference-mode').check()
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  await expect(page.getByTestId('primary-quantity')).toHaveText('67.5')
})


test('food study selector is reachable in the initial desktop panel without opening advanced controls', async ({ page }) => {
  await page.setViewportSize({ width: 1536, height: 1100 })
  await page.goto('/simulation')
  await expect(page.getByText('Engine connected', { exact: true })).toBeVisible({ timeout: 45000 })
  await page.getByRole('button', { name: 'Choose Food market', exact: true }).click()
  await expect(page.locator('#study')).toBeVisible()
  const study = await page.locator('#study').boundingBox()
  const footer = await page.locator('.run-footer').boundingBox()
  expect(study!.y + study!.height).toBeLessThanOrEqual(footer!.y + 1)
  await expect(page.getByTestId('advanced-controls')).not.toHaveAttribute('open', '')
})
