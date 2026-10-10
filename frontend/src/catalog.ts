import type { Pathway, WasteCategory } from './api'
export type LocationId = 'paddy' | 'food' | 'paper' | 'plastic' | 'wood'
export interface Location { id: LocationId; title: string; category: string; preferredSubtype: string; weight: number; color: string; position: [number, number, number]; caption: string }
// These are display preferences, never dataset identifiers. Exact names are
// resolved against /api/wastes before enabling a location.
export const locations: Location[] = [
  { id: 'paddy', title: 'Paddy fields', category: 'Agricultural residues', preferredSubtype: 'Rice straw after harvest', weight: 250, color: '#e9bd59', position: [-4.5, 0, -3.8], caption: 'Harvest residues' },
  { id: 'food', title: 'Food market', category: 'Food and organic waste', preferredSubtype: 'EBMUD food waste pulp; mesophilic; 15-day MCRT', weight: 80, color: '#ff937b', position: [3.8, 0, -4.1], caption: 'Published food reference' },
  { id: 'paper', title: 'Paper warehouse', category: 'Paper and cardboard', preferredSubtype: 'Newsprint', weight: 120, color: '#b1bafb', position: [-4.5, 0, 3.5], caption: 'Paper collection' },
  { id: 'plastic', title: 'Materials facility', category: 'Plastics', preferredSubtype: 'Commercial reference polymer PP-1', weight: 150, color: '#61d3ec', position: [4.2, 0, 3.8], caption: 'Reference polymers' },
  { id: 'wood', title: 'Timber yard', category: 'Wood and forestry waste', preferredSubtype: 'Dry wood reference', weight: 100, color: '#65d6a5', position: [0, 0, -5.8], caption: 'Published wood scenarios' },
]
export function resolveLocation(location: Location, categories: WasteCategory[]) {
  const category = categories.find(c => c.waste_category === location.category)
  const subtype = category?.subtypes.find(s => s === location.preferredSubtype)
  return subtype ? { category: category!.waste_category, subtype, weight: location.weight } : null
}
export const isVerifiedPathway = (pathway: Pathway) => pathway.default_eligible && pathway.mapping_status === 'VERIFIED'
export function defaultPathway(pathways: Pathway[]) {
  // The backend orders evidence-gated candidates; do not invent an efficiency score.
  return pathways.find(p => isVerifiedPathway(p) && p.recommended_output !== null) || pathways.find(isVerifiedPathway)
}
export function defaultOutput(pathway: Pathway) {
  if (isVerifiedPathway(pathway)) return pathway.recommended_output || ''
  // Diagnostic choices remain explicit and cannot become an automatic recommendation.
  return pathway.requested_outputs.find(o => !pathway.blocked_forecasts.includes(o)) || pathway.requested_outputs[0] || ''
}
export function pathwayLabel(pathway: Pathway) {
  if (pathway.mapping_status === 'RESTRICTED') return 'Restricted / no calculation'
  if (pathway.mapping_status === 'UNKNOWN') return 'UNKNOWN mapping / unsupported'
  return `Verified mapping / ${pathway.feasibility_status}`
}
export function validateInputs(weight: string, moisture: string): string | null {
  if (!weight.trim() || !Number.isFinite(Number(weight)) || Number(weight) <= 0) return 'Enter a finite quantity greater than zero kilograms.'
  if (moisture.trim() && (!Number.isFinite(Number(moisture)) || Number(moisture) < 0 || Number(moisture) > 100)) return 'Moisture must be between 0 and 100% wet basis, or left unknown.'
  return null
}
