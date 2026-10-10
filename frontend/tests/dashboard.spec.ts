import { test, expect, type Page } from '@playwright/test'
// Keep browser regressions deterministic when Google Fonts is unreachable.
test.beforeEach(async ({ page }) => {
  await page.route('https://fonts.googleapis.com/**', route => route.abort())
  await page.route('https://fonts.gstatic.com/**', route => route.abort())
})
async function ready(page: Page) {
  await page.goto('/simulation')
  // Catalog initialization has two bounded 20-second API phases; allow both
  // before interaction assertions. This does not retry or accept missing data.
  await expect(page.getByText('Engine connected', { exact: true })).toBeVisible({ timeout: 45000 })
  await expect(page.getByRole('button', { name: 'Choose Paddy fields', exact: true })).toBeEnabled()
  await expect(page.getByTestId('pathway-summary')).toBeVisible()
  await page.getByTestId('advanced-controls').evaluate((node: HTMLDetailsElement) => { node.open = true })
}
async function wood(page: Page) {
  await page.getByRole('button', { name: 'Choose Timber yard', exact: true }).click()
  await expect(page.locator('#subtype')).toHaveValue('Dry wood reference')
  await expect(page.locator('#technology')).toHaveValue('Pyrolysis')
  await page.locator('#moisture').fill('10')
  await page.locator('#study').selectOption('P0022')
  await page.locator('#reference-mode').check()
}

test('renders a genuine 3D city without JavaScript errors and captures desktop', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', e => errors.push(e.message))
  await ready(page)
  await expect(page.locator('canvas')).toBeVisible()
  for (const name of ['Paddy fields', 'Food market', 'Paper warehouse', 'Materials facility', 'Timber yard']) await expect(page.getByRole('button', { name: `Select ${name} on map`, exact: true })).toBeVisible()
  await page.waitForTimeout(1500)
  await page.screenshot({ path: '../reports/frontend-fixed-dashboard.png', fullPage: true })
  expect(errors).toEqual([])
})
test('all source cards update exact waste names and illustrative weights', async ({ page, request }) => {
  const catalog = await (await request.get('http://127.0.0.1:28100/api/wastes')).json()
  await ready(page)
  const feeds = [
    ['Paddy fields', 'Agricultural residues', 'Rice straw after harvest', '250'],
    ['Food market', 'Food and organic waste', 'EBMUD food waste pulp; mesophilic; 15-day MCRT', '80'],
    ['Paper warehouse', 'Paper and cardboard', 'Newsprint', '120'],
    ['Materials facility', 'Plastics', 'Commercial reference polymer PP-1', '150'],
    ['Timber yard', 'Wood and forestry waste', 'Dry wood reference', '100'],
  ]
  for (const [name, category, subtype, weight] of feeds) {
    expect(catalog.categories.find((c: { waste_category: string }) => c.waste_category === category).subtypes).toContain(subtype)
    await page.getByRole('button', { name: `Choose ${name}`, exact: true }).click()
    await expect(page.locator('#category')).toHaveValue(category)
    await expect(page.locator('#subtype')).toHaveValue(subtype)
    await expect(page.locator('#quantity')).toHaveValue(weight)
    await expect(page.locator('#moisture')).toHaveValue('')
  }
})
test('clickable 3D map pins select their source', async ({ page }) => {
  await ready(page)
  await page.getByRole('button', { name: 'Select Food market on map', exact: true }).click()
  await expect(page.locator('#quantity')).toHaveValue('80')
  await expect(page.locator('#subtype')).toHaveValue('EBMUD food waste pulp; mesophilic; 15-day MCRT')
  await expect(page.getByRole('button', { name: 'Choose Food market', exact: true })).toHaveAttribute('aria-pressed', 'true')
})
test('real reference request displays only its backend quantity, basis and sources', async ({ page }) => {
  await ready(page); await wood(page)
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/api/calculate') && r.request().method() === 'POST')
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  const response = await responsePromise
  expect(response.status()).toBe(200)
  expect(response.request().postDataJSON()).toEqual({ waste_category: 'Wood and forestry waste', waste_subtype: 'Dry wood reference', quantity_kg: 100, moisture_pct: 10, technology: 'Pyrolysis', desired_output: 'bio-oil', parameter_id: 'P0022', reference_mode: true })
  const body = await response.json()
  await expect(page.getByTestId('calculation-status')).toHaveText('CALCULATED REFERENCE')
  await expect(page.getByTestId('primary-quantity')).toHaveText(String(body.calculated_value))
  await expect(page.getByText(body.unit, { exact: true })).toBeVisible()
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: '../reports/frontend-fixed-reference-result.png', fullPage: true })
  await page.locator('#results summary').filter({ hasText: 'Source references' }).click()
  await expect(page.locator('#results').getByRole('link', { name: 'IEA Bioenergy Annual Report 2006' })).toBeVisible()
  await page.locator('#quantity').fill('200')
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
})
test('guided timber explains missing acknowledgement before requesting a forecast', async ({ page }) => {
  await ready(page)
  await page.getByRole('button', { name: 'Choose Timber yard', exact: true }).click()
  await expect(page.locator('#technology')).toHaveValue('Pyrolysis')
  await page.locator('#moisture').fill('10'); await page.locator('#study').selectOption('P0022')
  await expect(page.getByRole('button', { name: 'Calculate reference output', exact: true })).toBeDisabled()
  await expect(page.getByTestId('reference-gaps')).toContainText('Acknowledge the selected reference conditions')
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
})

for (const output of ['electricity', 'useful heat']) test(`${output} forecast stays blocked`, async ({ page }) => {
  await ready(page); await wood(page)
  await page.locator('#output').selectOption(output)
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  await expect(page.getByTestId('calculation-status')).toHaveText('INSUFFICIENT DATA')
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
  await expect(page.getByTestId('blocked-output')).toBeVisible()
})
test('gas scenario preserves source volume units and UNKNOWN equipment moisture feasibility', async ({ page }) => {
  await ready(page)
  await page.getByRole('button', { name: 'Choose Timber yard', exact: true }).click()
  await page.locator('#subtype').selectOption('Wood chips, Walawender 1985 run 98')
  await expect(page.locator('#technology')).toHaveValue('Gasification')
  await page.locator('#moisture').fill('16.52'); await page.locator('#study').selectOption('P0056')
  await page.locator('#reference-mode').check()
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  await expect(page.getByTestId('calculation-status')).toHaveText('CALCULATED REFERENCE')
  await page.getByText('Equipment & reference checks', { exact: true }).click()
  await expect(page.locator('#results pre').first()).toContainText('UNKNOWN')
  await expect(page.getByTestId('primary-quantity').locator('..')).not.toContainText('Nm3')
})
test('invalid input values are rejected before API requests', async ({ page }) => {
  await ready(page); await wood(page)
  for (const value of ['-1', '0', '']) {
    await page.locator('#quantity').fill(value)
    await expect(page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true })).toBeDisabled()
  }
  await page.locator('#quantity').fill('100'); await page.locator('#moisture').fill('101')
  await expect(page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true })).toBeDisabled()
  await expect(page.getByRole('alert')).toContainText('Moisture must be between')
})
test('navigation and About dialog work with keyboard controls', async ({ page }) => {
  await ready(page)
  await page.getByRole('link', { name: 'Simulation', exact: true }).click()
  await expect(page).toHaveURL(/#simulation$/)
  await page.getByRole('link', { name: 'Insights', exact: true }).click()
  await expect(page).toHaveURL(/#results$/)
  await page.getByRole('button', { name: 'About', exact: true }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape'); await expect(page.getByRole('dialog')).not.toBeVisible()
  await page.getByRole('link', { name: 'Home', exact: true }).click()
  await expect(page).toHaveURL(/\/$/); await expect(page.getByRole('heading', { level: 1 })).toContainText('Waste is not the end.')
})
test('API connection failure shows a recoverable error', async ({ page }) => {
  await page.route('**/api/**', route => route.abort())
  await page.goto('/simulation')
  await expect(page.getByRole('alert')).toContainText('Cannot connect to FastAPI')
  await expect(page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true })).toBeDisabled()
  await page.unroute('**/api/**')
  await page.getByRole('button', { name: 'Retry connection' }).click()
  await expect(page.getByText('Engine connected', { exact: true })).toBeVisible()
})
test('malformed calculation response is rejected rather than displaying invented values', async ({ page }) => {
  await ready(page); await wood(page)
  await page.route('**/api/calculate', route => route.fulfill({ json: { calculated_value: 9999 } }))
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('did not match the documented contract')
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
})
test('WebGL unavailable fallback still permits real API calculation', async ({ page }) => {
  await page.addInitScript(() => { const original = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, ...args: Parameters<typeof original>) { if (String(args[0]).includes('webgl')) return null; return original.apply(this, args) } as typeof original })
  await ready(page)
  await expect(page.getByTestId('webgl-fallback')).toBeVisible()
  await wood(page)
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  await expect(page.getByTestId('calculation-status')).toHaveText('CALCULATED REFERENCE')
})
test('mobile layout has no horizontal overflow and controls remain usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await ready(page)
  await expect(page.locator('canvas')).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.getByRole('button', { name: 'Choose Food market', exact: true }).click()
  await expect(page.locator('#quantity')).toHaveValue('80')
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: '../reports/frontend-fixed-mobile.png', fullPage: true })
})


test('unmapped rice paper and polymer feeds never silently select a general technology', async ({ page }) => {
  await ready(page)
  for (const name of ['Paddy fields', 'Paper warehouse', 'Materials facility']) {
    await page.getByRole('button', { name: `Choose ${name}`, exact: true }).click()
    await expect(page.getByTestId('pathway-summary')).toContainText('NO VERIFIED PATHWAY')
    await expect(page.locator('#technology')).toHaveValue('')
    await expect(page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true })).toBeDisabled()
    await expect(page.locator('#technology option[value="Gasification"]')).toHaveCount(0)
  }
})
test('exact-feed mappings change with waste selection and documented aliases work', async ({ page, request }) => {
  await ready(page)
  await page.getByRole('button', { name: 'Choose Food market', exact: true }).click()
  await expect(page.locator('#technology')).toHaveValue('Anaerobic digestion')
  await expect(page.locator('#technology optgroup').first().locator('option')).toHaveCount(2)
  await expect(page.getByTestId('route-evidence')).toContainText('Verified mapping / conditional')
  const response = await request.get('http://127.0.0.1:28100/api/pathways', { params: { waste_category: 'Food and organic waste', waste_subtype: 'EBMUD food waste pulp; mesophilic; 15-day MCRT' } })
  const verified = (await response.json()).pathways.filter((p: { default_eligible: boolean }) => p.default_eligible)
  expect(verified.map((p: { technology: string }) => p.technology)).toEqual(['Anaerobic digestion', 'Combined heat and power'])
  await page.getByRole('button', { name: 'Choose Timber yard', exact: true }).click()
  await expect(page.locator('#technology')).toHaveValue('Pyrolysis')
  await expect(page.locator('#technology optgroup').first().locator('option')).toHaveCount(1)
  await page.locator('#category').selectOption('Agricultural residues')
  await page.locator('#subtype').selectOption('Corn stover')
  await expect(page.locator('#technology')).toHaveValue('Fermentation')
  await expect(page.getByTestId('route-evidence')).toContainText('demonstrated')
})
test('explicit unsupported diagnostic returns actual NOT_APPLICABLE with no fabricated output', async ({ page }) => {
  await ready(page)
  await page.locator('#diagnostics').check()
  await page.locator('#technology').selectOption('Gasification')
  await expect(page.getByTestId('route-evidence')).toContainText('UNKNOWN mapping / unsupported')
  await page.locator('#moisture').fill('20')
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/api/calculate'))
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  const response = await responsePromise
  expect(response.request().postDataJSON()).toMatchObject({ waste_subtype: 'Rice straw after harvest', technology: 'Gasification', quantity_kg: 250, moisture_pct: 20, desired_output: 'syngas' })
  expect((await response.json()).calculation_status).toBe('NOT_APPLICABLE')
  await expect(page.getByTestId('calculation-status')).toHaveText('NOT APPLICABLE')
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
  await expect(page.getByTestId('blocked-output')).toContainText('Verified feedstock-to-technology mapping')
  await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')
  await expect(page.getByText('No verified visual route', { exact: true })).toBeVisible()
  await page.locator('#diagnostics').uncheck()
  await expect(page.locator('#technology')).toHaveValue('')
})
test('restricted feed remains restricted and never auto-selected', async ({ page }) => {
  await ready(page)
  await page.locator('#category').selectOption('Hazardous and medical waste')
  await expect(page.getByTestId('pathway-summary')).toContainText('NO VERIFIED PATHWAY')
  await expect(page.locator('#technology')).toHaveValue('')
  await page.locator('#diagnostics').check(); await page.locator('#technology').selectOption('Combustion')
  await expect(page.getByTestId('route-evidence')).toContainText('Restricted')
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  await expect(page.getByTestId('calculation-status')).toHaveText('RESTRICTED')
  await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
})
test('compact pins reveal details on hover and camera smoothly focuses on selection', async ({ page }) => {
  await ready(page)
  // Wait for the lazy 3D module and its first projection frame, not just API readiness.
  await expect(page.locator('.compact-pin')).toHaveCount(5, { timeout: 45000 })
  await expect(page.getByRole('tooltip')).toHaveCount(0)
  const before = await page.locator('canvas').getAttribute('data-camera-transform')
  const pin = page.getByRole('button', { name: 'Select Food market on map', exact: true })
  await pin.hover(); await expect(page.getByRole('tooltip')).toContainText('EBMUD food waste pulp; mesophilic; 15-day MCRT')
  await pin.click()
  await expect.poll(() => page.locator('canvas').getAttribute('data-camera-transform')).not.toBe(before)
  await expect(page.locator('#technology')).toHaveValue('Anaerobic digestion')
  await page.mouse.move(5, 5); await pin.blur()
  await expect(page.getByRole('tooltip')).toHaveCount(0)
})
test('3D truck and conversion journey advance with animation and complete independently of API status', async ({ page }) => {
  await ready(page); await wood(page)
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  const progress = page.getByRole('progressbar', { name: 'Conceptual animation progress' })
  await expect.poll(async () => Number(await progress.getAttribute('aria-valuenow'))).toBeGreaterThan(0)
  const position = await page.locator('canvas').getAttribute('data-truck-position')
  await expect.poll(() => page.locator('canvas').getAttribute('data-truck-position')).not.toBe(position)
  await expect(page.getByTestId('calculation-status')).toHaveText('CALCULATED REFERENCE')
  await expect(progress).toHaveAttribute('aria-valuenow', '100', { timeout: 30000 })
  await expect(page.locator('.hub-pin')).toHaveClass(/active/)
  await expect(page.getByText('Visual journey complete', { exact: true })).toBeVisible()
})
test('desktop city controls and result panel fit without excessive page scrolling', async ({ page }) => {
  await page.setViewportSize({ width: 1536, height: 960 }); await ready(page)
  const dimensions = await page.evaluate(() => ({ height: document.documentElement.scrollHeight, viewport: innerHeight, city: document.querySelector('.city-viewport')!.getBoundingClientRect().width, resultBottom: document.querySelector('#results')!.getBoundingClientRect().bottom }))
  expect(dimensions.height).toBeLessThanOrEqual(dimensions.viewport + 90)
  expect(dimensions.resultBottom).toBeLessThanOrEqual(dimensions.viewport + 50)
  expect(dimensions.city).toBeGreaterThan(900)
})
test('changing feed discards delayed previous pathway responses', async ({ page }) => {
  await ready(page)
  await page.route('**/api/pathways?*', async route => {
    if (new URL(route.request().url()).searchParams.get('waste_category') === 'Food and organic waste') {
      const response = await route.fetch()
      await new Promise(resolve => setTimeout(resolve, 1300))
      await route.fulfill({ response }).catch(() => {})
    } else await route.continue()
  })
  await page.getByRole('button', { name: 'Choose Food market', exact: true }).click()
  await page.getByRole('button', { name: 'Choose Paper warehouse', exact: true }).click()
  await expect(page.getByTestId('pathway-summary')).toContainText('NO VERIFIED PATHWAY')
  await page.waitForTimeout(1500)
  await expect(page.locator('#technology')).toHaveValue('')
  await expect(page.locator('#subtype')).toHaveValue('Newsprint')
})


test('small supported quantities retain the actual backend value instead of rounding to a fictional zero', async ({ page }) => {
  await ready(page); await wood(page)
  await page.locator('#quantity').fill('0.00000001')
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/api/calculate'))
  await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
  const body = await (await responsePromise).json()
  expect(body.calculated_value).toBeGreaterThan(0)
  await expect(page.getByTestId('primary-quantity')).toHaveText(String(body.calculated_value))
  await expect(page.getByText(body.unit, { exact: true })).toBeVisible()
})


test('source selection automatically recommends technology and output with advanced options collapsed', async ({ page }) => {
  await page.goto('/simulation')
  await expect(page.getByText('Engine connected', { exact: true })).toBeVisible({ timeout: 45000 })
  await page.getByRole('button', { name: 'Choose Timber yard', exact: true }).click()
  await expect(page.getByTestId('automatic-recommendation')).toContainText('Pyrolysis')
  await expect(page.getByTestId('automatic-recommendation')).toContainText('Bio-oil')
  await expect(page.locator('#technology')).toHaveValue('Pyrolysis')
  await expect(page.locator('#output')).toHaveValue('bio-oil')
  await expect(page.locator('#output')).toBeHidden()
  expect(await page.getByTestId('advanced-controls').evaluate((node: HTMLDetailsElement) => node.open)).toBe(false)
  await expect(page.locator('#reference-mode')).not.toBeChecked()
  await expect(page.locator('#moisture')).toHaveValue('')
  await page.screenshot({ path: '../reports/automatic-selection-dashboard.png', fullPage: true })
})

test('verified alternatives remain switchable without automatically choosing blocked electricity', async ({ page }) => {
  await ready(page)
  await page.getByRole('button', { name: 'Choose Food market', exact: true }).click()
  await expect(page.locator('#technology')).toHaveValue('Anaerobic digestion')
  await expect(page.locator('#output')).toHaveValue('biogas')
  await page.locator('#technology').selectOption('Combined heat and power')
  await expect(page.locator('#output')).toHaveValue('')
  await expect(page.getByTestId('automatic-recommendation')).toContainText('No unblocked output available')
  await expect(page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true })).toBeDisabled()
  await page.locator('#technology').selectOption('Anaerobic digestion')
  await expect(page.locator('#output')).toHaveValue('biogas')
})

test('quantity edits scale the actual supported backend reference result', async ({ page }) => {
  await ready(page); await wood(page)
  let first = 0
  for (const mass of [100, 200]) {
    await page.locator('#quantity').fill(String(mass))
    const pending = page.waitForResponse(r => r.url().endsWith('/api/calculate'))
    await page.getByRole('button', { name: /^(Run simulation|Calculate reference output)$/, exact: true }).click()
    const response = await pending
    expect(response.request().postDataJSON().quantity_kg).toBe(mass)
    const body = await response.json()
    expect(body.calculation_status).toBe('CALCULATED_REFERENCE')
    await expect(page.getByTestId('primary-quantity')).toHaveText(String(body.calculated_value))
    if (mass === 100) first = body.calculated_value
    else expect(body.calculated_value).toBeCloseTo(first * 2, 12)
  }
})


async function guidedTimber(page: Page) {
  await page.goto('/simulation')
  await expect(page.getByText('Engine connected', { exact: true })).toBeVisible({ timeout: 45000 })
  await page.getByRole('button', { name: 'Choose Timber yard', exact: true }).click()
  await expect(page.getByTestId('reference-guide')).toBeVisible()
  await expect(page.locator('#study option[value="P0022"]')).toHaveCount(1)
}

test('guided primary timber flow submits the exact verified mode and returns real reference output', async ({ page }) => {
  await guidedTimber(page)
  expect(await page.getByTestId('advanced-controls').evaluate((node: HTMLDetailsElement) => node.open)).toBe(false)
  await expect(page.locator('#study')).toBeVisible()
  await expect(page.locator('#study')).toHaveValue('')
  await expect(page.getByRole('button', { name: 'Calculate reference output', exact: true })).toBeDisabled()
  await page.locator('#quantity').fill('100'); await page.locator('#moisture').fill('10')
  await page.locator('#study').selectOption('P0022')
  await expect(page.locator('.study-options')).toContainText('75 % dry feed mass')
  await expect(page.locator('.study-options')).toContainText('around 500 degC')
  await expect(page.locator('.study-options')).toContainText('S07')
  await page.locator('#reference-mode').check()
  await expect(page.getByTestId('reference-ready')).toBeVisible()
  const pending = page.waitForResponse(r => r.url().endsWith('/api/calculate'))
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  const response = await pending
  expect(response.request().postDataJSON()).toEqual({ waste_category: 'Wood and forestry waste', waste_subtype: 'Dry wood reference', quantity_kg: 100, moisture_pct: 10, technology: 'Pyrolysis', desired_output: 'bio-oil', parameter_id: 'P0022', reference_mode: true })
  const result = await response.json()
  expect(result.calculated_value).toBe(67.5)
  expect(result.gross_vs_net_classification).toBe('intermediate_product_quantity')
  expect(result.source_ids).toContain('S07')
  expect(result.parameters.some((p: { measurement_basis?: string }) => p.measurement_basis === 'dry wood mass')).toBe(true)
  await expect(page.getByTestId('primary-quantity')).toHaveText(String(result.calculated_value))
  await expect(page.getByText(result.unit, { exact: true })).toBeVisible()
  await page.locator('#results summary').filter({ hasText: 'Calculation formula' }).click()
  await expect(page.locator('#results .formula')).toHaveText(result.formula)
  await page.screenshot({ path: '../reports/timber-guided-reference-result.png', fullPage: true })
})

test('guided timber cannot invent same-sample moisture or submit an unknown basis', async ({ page }) => {
  await guidedTimber(page)
  await page.locator('#study').selectOption('P0025'); await page.locator('#reference-mode').check()
  await expect(page.locator('#moisture')).toHaveValue('')
  await expect(page.locator('#reference-sample')).toHaveCount(0)
  await expect(page.getByTestId('reference-moisture-note')).toContainText('No verified same-sample')
  await expect(page.getByTestId('reference-gaps')).toContainText('Enter measured wet-basis moisture')
  await expect(page.getByRole('button', { name: 'Calculate reference output', exact: true })).toBeDisabled()
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
})

test('changing documented mode resets acknowledgement and uses its real yield', async ({ page }) => {
  await guidedTimber(page)
  await page.locator('#moisture').fill('10'); await page.locator('#study').selectOption('P0022'); await page.locator('#reference-mode').check()
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  await expect(page.getByTestId('primary-quantity')).toHaveText('67.5')
  await page.locator('#study').selectOption('P0025')
  await expect(page.locator('#reference-mode')).not.toBeChecked()
  await expect(page.getByTestId('primary-quantity')).toHaveCount(0)
  await page.locator('#quantity').fill('200'); await page.locator('#reference-mode').check()
  const pending = page.waitForResponse(r => r.url().endsWith('/api/calculate'))
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  const response = await pending
  expect(response.request().postDataJSON().parameter_id).toBe('P0025')
  const result = await response.json()
  expect(result.calculated_value).toBe(90)
  await expect(page.getByTestId('primary-quantity')).toHaveText('90')
})


test('guided study selector is visible in the initial timber panel without advanced settings', async ({ page }) => {
  await guidedTimber(page)
  const placement = await page.evaluate(() => {
    const study = document.querySelector('#study')!.getBoundingClientRect()
    const panel = document.querySelector('#controls')!.getBoundingClientRect()
    return { studyBottom: study.bottom, panelBottom: panel.bottom, scroll: document.querySelector('#controls fieldset')!.scrollTop }
  })
  expect(placement.studyBottom).toBeLessThan(placement.panelBottom - 50)
  expect(placement.scroll).toBe(0)
  await page.screenshot({ path: '../reports/timber-guided-primary-panel.png', fullPage: true })
})


test('one guided gasification reference exposes actual gas volume and pre-utilization MJ', async ({ page }) => {
  await ready(page)
  await page.getByRole('button', { name: 'Choose Timber yard', exact: true }).click()
  await page.locator('#subtype').selectOption('Wood chips, Walawender 1985 run 98')
  await expect(page.locator('#technology')).toHaveValue('Gasification')
  await expect(page.locator('#output')).toHaveValue('syngas')
  await page.getByTestId('advanced-controls').evaluate((node: HTMLDetailsElement) => { node.open = false })
  await expect(page.locator('#study')).toBeVisible()
  await page.locator('#study').selectOption('P0056')
  await expect(page.locator('#moisture')).toHaveValue('')
  await expect(page.getByTestId('reference-moisture-note')).toContainText('16.52%')
  await page.locator('#quantity').fill('100'); await page.locator('#moisture').fill('17'); await page.locator('#reference-mode').check()
  await expect(page.getByRole('button', { name: 'Calculate reference output', exact: true })).toBeDisabled()
  await expect(page.getByTestId('reference-gaps')).toContainText('Match the selected run moisture: 16.52%')
  await page.locator('#moisture').fill('16.52')
  const pending=page.waitForResponse(r => r.url().endsWith('/api/calculate'))
  await page.getByRole('button', { name: 'Calculate reference output', exact: true }).click()
  const response=await pending
  expect(response.request().postDataJSON()).toEqual({waste_category:'Wood and forestry waste',waste_subtype:'Wood chips, Walawender 1985 run 98',quantity_kg:100,moisture_pct:16.52,technology:'Gasification',desired_output:'syngas',parameter_id:'P0056',reference_mode:true})
  const result=await response.json()
  expect(result.calculated_value).toBeCloseTo(185.3256,9)
  await expect(page.getByTestId('calculation-status')).toHaveText('CALCULATED REFERENCE')
  await expect(page.getByTestId('primary-quantity')).toContainText('185.3256')
  await expect(page.getByTestId('gas-chemical-energy')).toContainText('987.785448')
  await expect(page.getByTestId('gas-chemical-energy')).toContainText('MJ HHV')
  await expect(page.getByTestId('gas-chemical-energy')).toContainText('before utilization')
  expect(result.feasibility_checks.moisture_feasibility.status).toBe('UNKNOWN')
  expect(result.source_ids).toEqual(['S02'])
  await page.screenshot({path:'../reports/gasification-guided-reference.png',fullPage:true})
})



