import type { ReferenceStudies } from '../api'
interface Props {
  technology: string;
  data: ReferenceStudies | null; loading: boolean; error: string | null; retry: () => void;
  parameterId: string; onStudy: (id: string) => void; propertyId: string; onSample: (id: string) => void;
  moisture: string; acknowledged: boolean; onAcknowledge: (value: boolean) => void; gaps: string[];
}
export default function ReferenceGuide({ technology, data, loading, error, retry, parameterId, onStudy, propertyId, onSample, moisture, acknowledged, onAcknowledge, gaps }: Props) {
  const selected = data?.studies.find(s => s.parameter.parameter_id === parameterId)
  const food = technology === 'Anaerobic digestion'
  return <section className="reference-guide" aria-labelledby="reference-guide-title" data-testid="reference-guide">
    <span className="eyebrow">GUIDED PUBLISHED REFERENCE</span><h3 id="reference-guide-title">{food ? 'Complete your food-waste reference' : technology === 'Gasification' ? 'Complete your gasification reference' : 'Complete your timber reference'}</h3>
    <p className="hint">{food ? 'Choose the published reference, then confirm its solids basis and assumptions.' : 'Confirm weight above, choose a documented mode, enter measured moisture, then acknowledge the reference conditions.'}</p>
    {loading && <p role="status">Checking published studies and their evidence...</p>}
    {error && <div className="error-box" role="alert">{error}<button type="button" onClick={retry}>Retry studies</button></div>}
    {data && <>
      <label htmlFor="study">1. Select documented study / operating mode</label>
      <select id="study" value={parameterId} onChange={e => onStudy(e.target.value)}><option value="">Choose a published mode; none assumed</option>{data.studies.map(s => <option key={s.parameter.parameter_id} value={s.parameter.parameter_id} disabled={!s.selectable}>{s.parameter.parameter_id} / {s.parameter.operating_conditions} / {s.parameter.value_typical} {s.parameter.unit} / {s.parameter.source_id} / {s.evidence_status}</option>)}</select>
      {food && <p className="hint" data-testid="food-reference-method">Reconstruct biogas from matched published averages for the exact preprocessed pulp. This is not a directly measured mass-specific yield, raw-market-waste estimate or batch digestion time. Methane volume is shown separately; chemical energy in MJ is unavailable.</p>}
      {!data.studies.length && <p className="hint">No applicable output-specific parameter record is available.</p>}
      <div className="study-options">{data.studies.filter(s => s.parameter.parameter_id === parameterId).map(s => <article key={s.parameter.parameter_id} className={parameterId === s.parameter.parameter_id ? 'selected' : ''}>
        <strong>{s.parameter.parameter_id} / {s.parameter.operating_conditions.split(';')[0]}</strong><span>{s.evidence_status} {food ? 'matched rate and basis' : 'yield'} evidence / user-waste applicability UNKNOWN</span>
        <p>{s.parameter.value_typical} {s.parameter.unit} / {s.parameter.measurement_basis}</p><small>{s.parameter.operating_conditions}</small>
        <a href={s.source_reference.source_url} target="_blank" rel="noreferrer">{s.parameter.source_id} / {s.source_reference.publication_title}</a><small>{s.parameter.evidence_location}</small>
      </article>)}</div>
      {food && selected && data.linked_reference_parameters.length > 0 && <details data-testid="food-linked-parameters"><summary>Matched reference parameters and sources</summary><ul>{data.linked_reference_parameters.map(p => <li key={`${p.record_id}:${p.field}`}>{p.record_id} / {p.field.replaceAll('_', ' ')}: {p.value} {p.unit} / {p.source_id}<small>{p.evidence_location}</small></li>)}</ul></details>}
      <h4>2. Confirm moisture basis</h4><p className="hint" data-testid="reference-moisture-note">{data.moisture_explanation}</p>
      {data.reference_samples.length > 0 && <><label htmlFor="reference-sample">Optional exact reference-sample basis</label><select id="reference-sample" value={propertyId} onChange={e => onSample(e.target.value)}><option value="">Use my measured moisture above</option>{data.reference_samples.filter(s => s.source_id === selected?.parameter.source_id).map(s => <option key={s.property_id} value={s.property_id}>{s.property_id} / {s.verified_basis_field}: {s[s.verified_basis_field]}% / published sample only</option>)}</select></>}
      <p className="hint">{propertyId ? 'Exact reference sample selected; its verified basis will be used by the engine.' : moisture.trim() ? `User-entered ${moisture}% wet-basis moisture. This measurement is not source-verified by WasteWise.` : 'Moisture is unknown. No value has been substituted.'}</p>
      <h4>3. Acknowledge selected reference conditions</h4>{selected && <p className="hint">{selected.parameter.operating_conditions}. {selected.parameter.limitations}</p>}
      <label className="checkbox-label"><input id="reference-mode" type="checkbox" checked={acknowledged} disabled={!selected?.selectable} onChange={e => onAcknowledge(e.target.checked)}/><span>{data.required_acknowledgement}</span></label>
    </>}
    {gaps.length > 0 ? <div className="reference-gaps" data-testid="reference-gaps"><strong>Still required before calculation</strong><ul>{gaps.map(gap => <li key={gap}>{gap}</li>)}</ul></div> : <p className="reference-ready" data-testid="reference-ready">Ready for reference {food ? 'biogas-volume reconstruction and separate methane-volume' : technology === 'Gasification' ? 'gas volume and fuel chemical-energy' : 'liquid-product'} accounting. Plant performance remains unvalidated.</p>}
  </section>
}
