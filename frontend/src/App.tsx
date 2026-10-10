import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { ArrowRight, BookOpen, CircleHelp, Factory, FlaskConical, Home, Leaf, LoaderCircle, MapPin, Milk, Play, RefreshCw, ShieldCheck, Sprout, Utensils, FileText, X } from 'lucide-react'
import { API_BASE, calculate, loadCatalog, loadPathways, loadReferenceStudies, type ReferenceStudies, type Health, type PathwaysResponse, type Result, type Technology, type WasteCategory } from './api'
import { defaultOutput, defaultPathway, isVerifiedPathway, locations, pathwayLabel, resolveLocation, validateInputs, type LocationId } from './catalog'
import Results from './components/Results'
import Timeline from './components/Timeline'
import ReferenceGuide from './components/ReferenceGuide'
const CityScene = lazy(() => import('./components/CityScene'))
const icons = { paddy: Sprout, food: Utensils, paper: FileText, plastic: Milk, wood: Leaf }
const shortNames = { paddy: 'Paddy', food: 'Food', paper: 'Paper', plastic: 'Plastic', wood: 'Wood' }
const outputName = (output: string) => output === 'bio-oil' ? 'Bio-oil / liquid product' : output.replace(/^./, s => s.toUpperCase())
function useReducedMotion() {
  const [reduced, setReduced] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches)
  useEffect(() => { const query = matchMedia('(prefers-reduced-motion: reduce)'); const change = () => setReduced(query.matches); query.addEventListener('change', change); return () => query.removeEventListener('change', change) }, [])
  return reduced
}
export default function App() {
  const [categories, setCategories] = useState<WasteCategory[]>([])
  const [technologies, setTechnologies] = useState<Technology[]>([])
  const [health, setHealth] = useState<Health | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [retry, setRetry] = useState(0)
  const [selected, setSelected] = useState<LocationId | null>('paddy')
  const [category, setCategory] = useState('')
  const [subtype, setSubtype] = useState('')
  const [weight, setWeight] = useState('250')
  const [moisture, setMoisture] = useState('')
  const [technology, setTechnology] = useState('')
  const [output, setOutput] = useState('')
  const [parameterId, setParameterId] = useState('')
  const [referenceMode, setReferenceMode] = useState(false)
  const [propertyId, setPropertyId] = useState('')
  const [referenceStudies, setReferenceStudies] = useState<ReferenceStudies | null>(null)
  const [studiesLoading, setStudiesLoading] = useState(false)
  const [studiesError, setStudiesError] = useState<string | null>(null)
  const [studiesRetry, setStudiesRetry] = useState(0)
  const [pathways, setPathways] = useState<PathwaysResponse | null>(null)
  const [pathwaysLoading, setPathwaysLoading] = useState(false)
  const [pathwaysError, setPathwaysError] = useState<string | null>(null)
  const [diagnostics, setDiagnostics] = useState(false)
  const [pathRetry, setPathRetry] = useState(0)
  const [result, setResult] = useState<Result | null>(null)
  const [runError, setRunError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [animation, setAnimation] = useState(0)
  const [progress, setProgress] = useState(0)
  const [focusKey, setFocusKey] = useState(0)
  const [nav, setNav] = useState('Home')
  const about = useRef<HTMLDialogElement>(null)
  const controller = useRef<AbortController | null>(null)
  const reducedMotion = useReducedMotion()

  useEffect(() => {
    const abort = new AbortController(); setLoading(true); setLoadError(null)
    loadCatalog(abort.signal).then(data => {
      if (abort.signal.aborted) return
      setCategories(data.categories); setTechnologies(data.technologies); setHealth(data.health)
      const feed = resolveLocation(locations[0], data.categories)
      if (feed) { setCategory(feed.category); setSubtype(feed.subtype); setWeight(String(feed.weight)) }
      else { setSelected(null); setCategory(data.categories[0]?.waste_category || ''); setSubtype(data.categories[0]?.subtypes[0] || '') }
      setLoading(false)
    }).catch(error => { if (!abort.signal.aborted) { setLoadError(error instanceof Error ? error.message : 'Catalog unavailable.'); setLoading(false) } })
    return () => abort.abort()
  }, [retry])
  useEffect(() => {
    setTechnology(''); setOutput(''); setParameterId(''); setDiagnostics(false); setPathways(null); setPathwaysError(null)
    if (!category || !subtype) { setPathwaysLoading(false); return }
    const abort = new AbortController(); setPathwaysLoading(true)
    loadPathways(category, subtype, abort.signal).then(response => {
      if (abort.signal.aborted) return
      if (response.waste_category !== category || response.waste_subtype !== subtype) throw new Error('Pathway response belongs to a different feed; selection is disabled.')
      setPathways(response); const first = defaultPathway(response.pathways)
      if (first) { setTechnology(first.technology); setOutput(defaultOutput(first)) }
      setPathwaysLoading(false)
    }).catch(error => { if (!abort.signal.aborted) { setPathwaysError(error instanceof Error ? error.message : 'Pathways unavailable.'); setPathwaysLoading(false) } })
    return () => abort.abort()
  }, [category, subtype, pathRetry])
  useEffect(() => () => controller.current?.abort(), [])
  useEffect(() => { controller.current?.abort(); setBusy(false); setResult(null); setRunError(null); setAnimation(0); setProgress(0) }, [category, subtype, weight, moisture, technology, output, parameterId, propertyId, referenceMode])

  const chooseFeed = (newCategory: string, newSubtype: string, location: LocationId | null) => {
    if (busy) return
    // Clear dependent controls immediately; never allow the previous feed's route
    // during asynchronous pathway loading, even for a rapid selection change.
    setTechnology(''); setOutput(''); setParameterId(''); setPathways(null); setDiagnostics(false)
    setCategory(newCategory); setSubtype(newSubtype); setMoisture(''); setPropertyId(''); setReferenceMode(false); setSelected(location); setFocusKey(k => k + 1)
  }
  const chooseLocation = (id: LocationId) => {
    const feed = resolveLocation(locations.find(l => l.id === id)!, categories)
    if (!feed || busy) return
    if (feed.category === category && feed.subtype === subtype) { setSelected(id); setFocusKey(k => k + 1); setWeight(String(feed.weight)); return }
    chooseFeed(feed.category, feed.subtype, id); setWeight(String(feed.weight))
  }
  const currentPathway = pathways?.pathways.find(p => p.technology === technology)
  const currentTech = technologies.find(t => t.technology === technology)
  const verified = pathways?.pathways.filter(isVerifiedPathway) || []
  const other = pathways?.pathways.filter(p => !isVerifiedPathway(p)) || []
  const studies = currentTech?.conversion_parameters.filter(p => p.waste_subtype === subtype) || []
  const assessment = currentPathway?.output_assessments.find(a => a.output === output)
  const guidedFood = category === 'Food and organic waste' && subtype === 'EBMUD food waste pulp; mesophilic; 15-day MCRT' && technology === 'Anaerobic digestion' && output === 'biogas'
  const guidedReference = (guidedFood || category === 'Wood and forestry waste' && ((subtype === 'Dry wood reference' && technology === 'Pyrolysis' && output === 'bio-oil') || (subtype === 'Wood chips, Walawender 1985 run 98' && technology === 'Gasification' && output === 'syngas'))) && !!currentPathway && isVerifiedPathway(currentPathway)
  useEffect(() => {
    setReferenceStudies(null); setStudiesError(null); setPropertyId('')
    if (!guidedReference) { setStudiesLoading(false); return }
    const abort = new AbortController(); setStudiesLoading(true)
    loadReferenceStudies(category, subtype, technology, output, abort.signal).then(data => {
      if (abort.signal.aborted) return
      if (data.waste_category !== category || data.waste_subtype !== subtype || data.technology !== technology || data.desired_output !== output) throw new Error('Reference studies belong to a different scenario.')
      setReferenceStudies(data); setStudiesLoading(false)
    }).catch(error => { if (!abort.signal.aborted) { setStudiesError(error instanceof Error ? error.message : 'Reference evidence unavailable.'); setStudiesLoading(false) } })
    return () => abort.abort()
  }, [guidedReference, category, subtype, technology, output, studiesRetry])
  const selectedStudy = referenceStudies?.studies.find(s => s.parameter.parameter_id === parameterId && s.selectable)
  const selectedSample = referenceStudies?.reference_samples.find(s => s.property_id === propertyId && s.source_id === selectedStudy?.parameter.source_id)
  const referenceGaps = !guidedReference ? [] : [
    ...(studiesLoading ? ['Wait for published study evidence to finish loading.'] : []),
    ...(studiesError ? ['Published study evidence could not be loaded; retry before calculating.'] : []),
    ...(!selectedStudy ? ['Select an applicable verified published operating mode.'] : []),
    ...(!moisture.trim() && !selectedSample ? ['Enter measured wet-basis moisture or explicitly select an available exact reference sample. No default is applied.'] : []),
    ...(referenceStudies?.reference_run_moisture && moisture.trim() && Number(moisture) !== referenceStudies.reference_run_moisture.value ? [`Match the selected run moisture: ${referenceStudies.reference_run_moisture.value}% wet basis. Other moisture requires a verified response model.`] : []),
    ...(!referenceMode ? ['Acknowledge the selected reference conditions and that this is not plant output.'] : []),
  ]
  const invalid = validateInputs(weight, moisture)
  const available = locations.filter(l => resolveLocation(l, categories)).map(l => l.id)
  const chooseTechnology = (name: string) => {
    const pathway = pathways?.pathways.find(p => p.technology === name)
    if (!pathway || (!isVerifiedPathway(pathway) && !diagnostics)) return
    setTechnology(name); setOutput(defaultOutput(pathway)); setParameterId(''); setPropertyId(''); setReferenceMode(false)
  }
  const run = async () => {
    if (busy || invalid || referenceGaps.length > 0 || !currentPathway || !currentTech || pathwaysLoading || !output || (!isVerifiedPathway(currentPathway) && !diagnostics) || health?.status !== 'ok') return
    controller.current?.abort(); const abort = new AbortController(); controller.current = abort
    setBusy(true); setResult(null); setRunError(null); setProgress(0); setAnimation(a => isVerifiedPathway(currentPathway) && selected ? a + 1 : 0)
    try {
      const response = await calculate({ waste_category: category, waste_subtype: subtype, quantity_kg: Number(weight), moisture_pct: moisture.trim() ? Number(moisture) : null, technology, desired_output: output, parameter_id: parameterId || null, ...(guidedReference && selectedSample ? { property_id: selectedSample.property_id } : {}), reference_mode: referenceMode }, abort.signal)
      if (!abort.signal.aborted) setResult(response)
    } catch (error) { if (!abort.signal.aborted) { setRunError(error instanceof Error ? error.message : 'Calculation failed.'); setAnimation(0); setProgress(0) } }
    finally { if (!abort.signal.aborted) setBusy(false) }
  }
  return <div id="home" className="app-shell"><a className="skip-link" href="#controls">Skip to simulation controls</a>
    <header className="topbar"><a className="brand" href="/" onClick={() => setNav('Home')}><span className="brand-mark"><Leaf size={24}/></span><span><strong>WasteWise<span> AI</span></strong><small>THE CIRCULAR CITY LAB</small></span></a><nav aria-label="Main navigation">{[{ name: 'Home', target: '/', icon: Home }, { name: 'Simulation', target: '#simulation', icon: Factory }, { name: 'Insights', target: '#results', icon: FlaskConical }].map(n => <a href={n.target} key={n.name} className={nav === n.name ? 'active' : ''} onClick={() => setNav(n.name)}><n.icon size={15}/>{n.name}</a>)}<button onClick={() => about.current?.showModal()}><CircleHelp size={15}/>About</button></nav><span className={`connection ${health?.status === 'ok' ? 'online' : ''}`}><span/>{loading ? 'Connecting' : health?.status === 'ok' ? 'Engine connected' : 'Engine unavailable'}</span></header>
    <main><div className="page-intro"><div><span className="eyebrow">EXPLORE. TRACE. UNDERSTAND.</span><h1>Every resource has a <em>next chapter.</em></h1></div><div className="intro-note"><ShieldCheck size={18}/><span>Reference accounting only<small>Electricity & heat forecasts blocked</small></span></div></div>
      <div className="workspace" id="simulation">
        <section className="panel city-panel" aria-labelledby="city-heading"><div className="city-section-heading"><div><MapPin size={16}/><h2 id="city-heading">Your circular city</h2></div><span>INTERACTIVE 3D / CONCEPTUAL</span></div><Suspense fallback={<div className="scene-loading"><LoaderCircle className="spin"/> Preparing the city...</div>}><CityScene selected={selected} onSelect={chooseLocation} available={busy ? [] : available} animation={animation} technology={technology} reducedMotion={reducedMotion} progress={progress} onProgress={setProgress} focusKey={focusKey} feedSubtype={subtype}/></Suspense><div className="city-footer"><strong>{selected ? locations.find(l => l.id === selected)?.title : 'Custom published feed'}</strong><span>{subtype || 'Loading catalog...'}</span><small>Illustrative mass / conceptual transport</small></div></section>
        <section className={`panel controls-panel ${guidedReference ? 'guided-timber' : ''}`} id="controls" aria-labelledby="controls-title"><div className="panel-heading"><div><span className="eyebrow">01 / BUILD A SCENARIO</span><h2 id="controls-title">Source & conversion</h2></div><Leaf size={19} className="accent"/></div>
          {loading && <p className="loading-message"><LoaderCircle size={15} className="spin"/>Loading the published catalog...</p>}{loadError && <div className="error-box" role="alert">{loadError}<button onClick={() => setRetry(r => r + 1)}><RefreshCw size={13}/>Retry connection</button></div>}{health?.status === 'degraded' && <div className="error-box" role="alert">Dataset integrity is degraded. Calculations are disabled.</div>}
          <fieldset disabled={busy || loading || !!loadError}><legend className="sr-only">Waste source and inputs</legend><div className="source-grid">{locations.map(l => { const Icon = icons[l.id]; return <button key={l.id} type="button" className={`source-card ${selected === l.id ? 'selected' : ''}`} style={{ '--source-color': l.color } as React.CSSProperties} disabled={!available.includes(l.id)} onClick={() => chooseLocation(l.id)} aria-label={`Choose ${l.title}`} aria-pressed={selected === l.id}><Icon size={20}/><strong>{shortNames[l.id]}</strong><small>{l.weight} kg*</small></button> })}</div>
            <div className="control-section"><label htmlFor="category">Published category</label><select id="category" value={category} onChange={e => chooseFeed(e.target.value, categories.find(c => c.waste_category === e.target.value)?.subtypes[0] || '', locations.find(l => l.category === e.target.value)?.id || null)}><option value="" disabled>Select waste category</option>{categories.map(c => <option key={c.waste_category}>{c.waste_category}</option>)}</select><label htmlFor="subtype">Exact waste subtype</label><select id="subtype" value={subtype} onChange={e => chooseFeed(category, e.target.value, locations.find(l => l.category === category)?.id || null)}><option value="" disabled>Select published subtype</option>{categories.find(c => c.waste_category === category)?.subtypes.map(s => <option key={s}>{s}</option>)}</select>
              <div className="input-pair"><div><label htmlFor="quantity">Quantity <span>kg</span></label><input id="quantity" type="number" step="any" min="0" value={weight} onChange={e => setWeight(e.target.value)} aria-invalid={!!invalid && invalid.includes('quantity')}/></div><div><label htmlFor="moisture">Moisture <span>% wet basis</span></label><input id="moisture" type="number" step="any" min="0" max="100" value={moisture} placeholder="Unknown" onChange={e => { setMoisture(e.target.value); setPropertyId('') }} aria-invalid={!!invalid && invalid.includes('Moisture')}/></div></div><p className="hint">*Illustrative mass. Blank moisture means unknown.</p>{category === 'Plastics' && <p className="hint">Published polymers are references, not measured post-consumer waste.</p>}
            </div>
            <div className="control-section route-section"><div className="section-label">Exact-feed pathways<span className="section-number">ENGINE VERIFIED</span></div>{pathwaysLoading && <p className="loading-message" role="status"><LoaderCircle size={14} className="spin"/>Checking feed-specific mappings...</p>}{pathwaysError && <div className="error-box" role="alert">{pathwaysError}<button onClick={() => setPathRetry(n => n + 1)}>Retry pathways</button></div>}
              {!pathwaysLoading && pathways && <div className={`pathway-summary ${verified.length ? 'verified' : 'unknown'}`} data-testid="pathway-summary"><strong>{verified.length ? `${verified.length} verified ${verified.length === 1 ? 'mapping' : 'mappings'} / conditional evidence` : 'NO VERIFIED PATHWAY'}</strong><p>{verified.length ? 'A documented mapping does not establish an output yield or plant feasibility.' : 'No verified mapping exists for this exact feed. No technology is automatically selected.'}</p></div>}
              {currentPathway && isVerifiedPathway(currentPathway) && <div className="automatic-recommendation" data-testid="automatic-recommendation"><span className="eyebrow">AUTOMATIC / BEST DOCUMENTED MATCH</span><strong>{technology}</strong><span>{output ? outputName(output) : 'No unblocked output available'}</span><p>{assessment?.explanation}</p>{assessment?.study_selection_required && <p>{guidedReference ? 'Choose a documented operating mode in the guided panel below.' : 'Choose matching conditions in advanced options; no study is silently assumed.'}</p>}<small>Evidence completeness, not an efficiency or plant-performance optimum.</small></div>}
              {guidedReference && <ReferenceGuide technology={technology} data={referenceStudies} loading={studiesLoading} error={studiesError} retry={() => setStudiesRetry(n => n + 1)} parameterId={parameterId} onStudy={id => { setParameterId(id); setPropertyId(''); setReferenceMode(false) }} propertyId={propertyId} onSample={id => { setPropertyId(id); setMoisture(''); setReferenceMode(false) }} moisture={moisture} acknowledged={referenceMode} onAcknowledge={setReferenceMode} gaps={referenceGaps}/>}
              <details className="advanced-controls" data-testid="advanced-controls"><summary>Advanced technology, product & study options</summary>
              <label htmlFor="technology">Technology</label><select id="technology" value={technology} disabled={pathwaysLoading || !pathways} onChange={e => chooseTechnology(e.target.value)}><option value="">{verified.length ? 'Select a verified mapping' : 'No verified route / choose explicitly'}</option><optgroup label="Verified exact-feed mappings">{verified.map(p => <option value={p.technology} key={p.technology}>{p.technology} / {p.feasibility_status}</option>)}</optgroup>{diagnostics && <optgroup label="Diagnostic only / no verified unrestricted mapping">{other.map(p => <option value={p.technology} key={p.technology}>{p.technology} / {p.mapping_status}</option>)}</optgroup>}</select>
              {currentPathway && <p className="route-evidence" data-testid="route-evidence">{pathwayLabel(currentPathway)}{currentPathway.source_references.length ? ` / ${currentPathway.source_references.map(s => s.source_id).join(', ')}` : ''}</p>}
              <label className="checkbox-label diagnostic-toggle"><input id="diagnostics" type="checkbox" checked={diagnostics} onChange={e => { setDiagnostics(e.target.checked); if (!e.target.checked && currentPathway && !isVerifiedPathway(currentPathway)) { setTechnology(''); setOutput(''); setParameterId('') } }}/><span>Explicitly inspect unsupported / unknown routes</span></label>
              <label htmlFor="output">Requested output</label><select id="output" disabled={!currentPathway || pathwaysLoading} value={output} onChange={e => { setOutput(e.target.value); setParameterId(''); setPropertyId(''); setReferenceMode(false) }}><option value="" disabled>Select product</option>{currentPathway?.requested_outputs.map(o => <option key={o} value={o}>{outputName(o)}{currentPathway.blocked_forecasts.includes(o) ? ' / forecast blocked' : ''}</option>)}</select>
              {['electricity', 'useful heat'].includes(output) && <p className="energy-notice">Unsupported equipment forecast. Run only to inspect the backend's missing requirements.</p>}
              {!guidedReference && studies.length > 0 && <><label htmlFor="study">Published study / parameter</label><select id="study" value={parameterId} onChange={e => setParameterId(e.target.value)}><option value="">No explicit study selected</option>{studies.map(p => <option key={p.parameter_id} value={p.parameter_id}>{p.parameter_id} / {p.parameter_name} / {p.operating_conditions}</option>)}</select></>}
              </details>
              {!guidedReference && <label className="checkbox-label"><input id="reference-mode" type="checkbox" checked={referenceMode} onChange={e => setReferenceMode(e.target.checked)}/><span>Use published reference accounting<small>Explicit acknowledgement / not a plant forecast</small></span></label>}
            </div>
          </fieldset>{invalid && !loading && <p className="validation-error" role="alert">{invalid}</p>}
          <div className="run-footer"><button className="run-button" disabled={busy || loading || pathwaysLoading || !!loadError || !!pathwaysError || referenceGaps.length > 0 || !currentPathway || !output || !!invalid || health?.status !== 'ok'} onClick={() => void run()}>{busy ? <LoaderCircle size={17} className="spin"/> : <Play size={15} fill="currentColor"/>}{busy ? 'Checking evidence...' : guidedReference ? 'Calculate reference output' : 'Run simulation'}<ArrowRight size={17}/></button></div>
        </section>
        <Timeline progress={progress} started={animation > 0} pending={busy} status={result?.calculation_status || null}/><Results result={result} pending={busy} error={runError}/>
      </div><footer className="footer"><span><Leaf size={13}/>WasteWise AI / Conceptual city, preserved science</span><a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer"><BookOpen size={13}/>API documentation</a></footer>
    </main>
    <dialog className="about-dialog" ref={about}><button className="dialog-close" aria-label="Close About" onClick={() => about.current?.close()}><X size={20}/></button><span className="eyebrow">SCIENTIFIC BOUNDARIES</span><h2>Verified mappings.<br/>Honest uncertainty.</h2><p>The city is a conceptual interface to the existing scientific engine. A verified conditional feed mapping is not a supported numerical forecast or equipment qualification.</p><p>UNKNOWN means applicability or equipment limits are not established. NOT_APPLICABLE means the engine does not support the selected route/output. INSUFFICIENT_DATA means required scientific parameters or qualifications are missing.</p><p>External predictive validation is incomplete. Gas-table runs 920, 924 and 1110 remain unreconciled. Electricity and useful heat forecasts are blocked. The datasets and scientific equations remain unchanged.</p><button className="run-button" onClick={() => about.current?.close()}>Return to the city<ArrowRight size={17}/></button></dialog>
  </div>
}

