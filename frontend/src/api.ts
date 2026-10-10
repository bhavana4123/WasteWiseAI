import { z } from 'zod'

const number = z.number().finite()
const record = z.record(z.string())
const dynamic = z.record(z.unknown())
export const healthSchema = z.object({ status: z.enum(['ok', 'degraded']), engine_readiness: z.string(), datasets_unchanged_since_startup: z.boolean(), scientific_validation: z.string(), external_predictive_validation: z.string(), electricity_heat_forecasts: z.string(), unresolved_gas_table_runs: z.array(z.string()), dataset_issues: z.array(z.string()) })
export const wastesSchema = z.object({ categories: z.array(z.object({ waste_category: z.string(), subtypes: z.array(z.string()) })) })
export const technologySchema = z.object({ technology: z.string(), requested_outputs: z.array(z.string()), documented_outputs: z.array(z.string()), equipment_forecast_supported: z.boolean() })
export const detailsSchema = technologySchema.extend({ mappings: z.array(record), conversion_parameters: z.array(record), equipment_records: z.array(record), source_references: z.array(record), limitations: z.array(z.string()) })
export const technologiesSchema = z.object({ technologies: z.array(technologySchema) })
export const resultSchema = z.object({ input_waste_details: dynamic, technology: z.string(), feasibility_status: z.string(), calculation_status: z.enum(['CALCULATED_REFERENCE', 'INSUFFICIENT_DATA', 'NOT_APPLICABLE', 'RESTRICTED']), energy_output_type: z.string(), calculated_value: number.nonnegative().nullable(), unit: z.string().nullable(), gross_vs_net_classification: z.string(), formula: z.string().nullable(), parameters: z.array(dynamic), source_ids: z.array(z.string()), assumptions: z.array(z.string()), missing_parameters: z.array(z.string()), uncertainty: dynamic, warnings: z.array(z.string()), limitations: z.array(z.string()), intermediate_products: z.array(dynamic), evidence: z.array(dynamic), scenario_id: z.string().nullable(), errors: z.array(dynamic), feasibility_checks: dynamic, source_references: z.array(record), dataset_issues: z.array(z.string()), explanation: z.string() })
export type Result = z.infer<typeof resultSchema>
export type Health = z.infer<typeof healthSchema>
export type WasteCategory = z.infer<typeof wastesSchema>['categories'][number]
export type Technology = z.infer<typeof detailsSchema>
export interface CalculationRequest { waste_category: string; waste_subtype: string; quantity_kg: number; moisture_pct: number | null; technology: string; desired_output: string; parameter_id: string | null; property_id?: string; reference_mode: boolean }
export const API_BASE = (import.meta.env.VITE_API_BASE_URL?.trim() ||
  (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')).replace(/\/+$/, '')

export async function fetchApi<T>(path: string, schema: z.ZodType<T, z.ZodTypeDef, unknown>, options: RequestInit = {}): Promise<T> {
  const timeout = new AbortController()
  const timer = window.setTimeout(() => timeout.abort(), 20000)
  const abort = () => timeout.abort()
  options.signal?.addEventListener('abort', abort, { once: true })
  if (options.signal?.aborted) timeout.abort()
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, signal: timeout.signal, headers: { 'Content-Type': 'application/json', ...options.headers } })
    const body: unknown = await response.json()
    if (!response.ok) {
      const error = z.object({ message: z.string() }).safeParse(body)
      throw new Error(error.success ? error.data.message : `API request failed (${response.status})`)
    }
    const result = schema.safeParse(body)
    if (!result.success) throw new Error('The API response did not match the documented contract. No result is displayed.')
    return result.data
  } catch (error) {
    if (timeout.signal.aborted) throw new Error('Request cancelled or timed out. Check that FastAPI is running.')
    if (error instanceof TypeError) throw new Error(`Cannot connect to FastAPI at ${API_BASE}. Start the backend and check CORS.`)
    throw error
  } finally { window.clearTimeout(timer); options.signal?.removeEventListener('abort', abort) }
}

export async function loadCatalog(signal: AbortSignal) {
  const [health, wastes, summaries] = await Promise.all([
    fetchApi('/api/health', healthSchema, { signal }), fetchApi('/api/wastes', wastesSchema, { signal }), fetchApi('/api/technologies', technologiesSchema, { signal }),
  ])
  const technologies = await Promise.all(summaries.technologies.map(t => fetchApi(`/api/technologies/${encodeURIComponent(t.technology)}`, detailsSchema, { signal })))
  return { health, categories: wastes.categories, technologies }
}
export const calculate = (body: CalculationRequest, signal: AbortSignal) => fetchApi('/api/calculate', resultSchema, { method: 'POST', body: JSON.stringify(body), signal })
export const canDisplayQuantity = (result: Result) => result.calculation_status === 'CALCULATED_REFERENCE' && result.calculated_value !== null && !['electricity', 'useful heat'].includes(result.energy_output_type)

export const pathwaySchema = z.object({
  technology: z.string(), mapping_status: z.enum(['VERIFIED', 'UNKNOWN', 'RESTRICTED']),
  feasibility_status: z.string(), calculation_support: z.enum(['EVIDENCE_GATED', 'UNSUPPORTED', 'RESTRICTED']),
  default_eligible: z.boolean(), requested_outputs: z.array(z.string()), blocked_forecasts: z.array(z.string()),
  recommended_output: z.string().nullable(), recommendation_reason: z.string(),
  output_assessments: z.array(z.object({ output: z.string(), forecast_blocked: z.boolean(), has_verified_parameters: z.boolean(), matching_parameter_ids: z.array(z.string()), study_selection_required: z.boolean(), calculation_status: z.string(), missing_parameters: z.array(z.string()), explanation: z.string() })),
  mapping_records: z.array(record), source_references: z.array(record), explanation: z.string(),
})
export const pathwaysSchema = z.object({ waste_category: z.string(), waste_subtype: z.string(), pathways: z.array(pathwaySchema), explanation: z.string() })
export type Pathway = z.infer<typeof pathwaySchema>
export type PathwaysResponse = z.infer<typeof pathwaysSchema>
export const loadPathways = (category: string, subtype: string, signal: AbortSignal) => fetchApi(
  `/api/pathways?${new URLSearchParams({ waste_category: category, waste_subtype: subtype })}`, pathwaysSchema, { signal })

export function formatQuantity(value: number) {
  if (value !== 0 && (Math.abs(value) < .00001 || Math.abs(value) >= 1e10)) return value.toString()
  return new Intl.NumberFormat('en', { maximumSignificantDigits: 15 }).format(value)
}


export const referenceStudiesSchema = z.object({
  waste_category: z.string(), waste_subtype: z.string(), technology: z.string(), desired_output: z.string(),
  linked_reference_parameters: z.array(record).default([]),
  studies: z.array(z.object({ parameter: record, evidence_status: z.enum(['VERIFIED', 'UNKNOWN']), selectable: z.boolean(), source_reference: record, evidence: z.array(record), applicability: z.string() })),
  reference_samples: z.array(record), reference_run_moisture: z.object({ value: number, unit: z.string(), kind: z.string(), source_id: z.string(), record_id: z.string(), evidence_location: z.string() }).nullable(), moisture_explanation: z.string(), required_acknowledgement: z.string(),
})
export type ReferenceStudies = z.infer<typeof referenceStudiesSchema>
export const loadReferenceStudies = (category: string, subtype: string, technology: string, output: string, signal: AbortSignal) => fetchApi(
  `/api/reference-studies?${new URLSearchParams({ waste_category: category, waste_subtype: subtype, technology, desired_output: output })}`, referenceStudiesSchema, { signal })
