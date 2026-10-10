"""Read-only FastAPI facade for the existing evidence-gated engine."""
from contextlib import asynccontextmanager
import logging
import time

from fastapi import Depends, FastAPI, HTTPException, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from engine import CalculationInput, DataRepository
from engine.numerics import validate_numeric_tree
from engine.food_reference import FOOD_SUBTYPE, food_bundle, linked_food_parameters
from engine.recommender import calculate, OUTPUT_ROUTES
from .schemas import (CalculateRequest, CalculateResponse, ErrorResponse, HealthResponse,
                      TechnologiesResponse, TechnologyDetails, WastesResponse, WastePathwaysResponse, ReferenceStudiesResponse)

from .recommendation import assess_outputs, recommendation_key
from .settings import cors_origins

logger = logging.getLogger('wastewise.api')
LIMITATIONS = [
    'Published-reference accounting only; no equipment-qualified operating forecast.',
    'External predictive validation has not been achieved.',
    'Three historical gas-table energy discrepancies remain unresolved: runs 920, 924, 1110.',
    'Electricity and useful heat forecasts remain blocked.',
    'Equipment moisture feasibility is UNKNOWN where documented limits are missing.',
]


@asynccontextmanager
async def lifespan(app):
    # Fail startup if the scientific repository cannot be read/validated.
    app.state.repository = DataRepository()
    logger.info('Scientific repository loaded; reference accounting only')
    yield


app = FastAPI(title='WasteWise AI API', version='1.0.0', lifespan=lifespan,
              description='Evidence-gated reference calculations. No externally validated plant forecasts.',
              responses={422: {'model': ErrorResponse}, 503: {'model': ErrorResponse},
                         500: {'model': ErrorResponse}})
app.add_middleware(CORSMiddleware, allow_origins=cors_origins(),
                   allow_methods=['GET', 'POST'], allow_headers=['Content-Type'], allow_credentials=False)


@app.middleware('http')
async def log_requests(request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    logger.info('%s %s status=%s duration_ms=%.1f', request.method, request.url.path,
                response.status_code, (time.monotonic() - start) * 1000)
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    # Never echo invalid NaN/Infinity inputs or exception objects into JSON.
    details = [{'location': list(e['loc']), 'message': e['msg'], 'type': e['type']} for e in exc.errors()]
    return JSONResponse(status_code=422, content=ErrorResponse(
        code='INVALID_REQUEST', message='Request validation failed', details=details).model_dump())


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    return JSONResponse(status_code=exc.status_code, content=ErrorResponse(
        code={404: 'NOT_FOUND', 422: 'INVALID_REQUEST', 503: 'DATA_UNAVAILABLE'}.get(exc.status_code, 'HTTP_ERROR'),
        message=str(exc.detail)).model_dump())


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logger.exception('API request failed', exc_info=exc)
    return JSONResponse(status_code=500, content=ErrorResponse(
        code='INTERNAL_ERROR', message='Calculation service failed; no result is available').model_dump())


def repository(request: Request):
    repo = request.app.state.repository
    try:
        if not repo.unchanged():
            raise HTTPException(503, 'Scientific datasets changed since startup; restart after integrity review')
    except OSError:
        raise HTTPException(503, 'Scientific datasets unavailable') from None
    return repo


def waste_catalog(repo):
    # Cache names only on the startup repository. CSV fingerprint checks guard
    # every data request; mapping/parameter verification is never cached here.
    cached = getattr(repo, '_api_waste_catalog', None)
    if cached is not None:
        return cached
    categories = {}
    for table in ('waste_properties', 'technology_mapping'):
        for row in repo.tables[table]:
            categories.setdefault(row['waste_category'], set()).add(row['waste_subtype'])
    # Conversion records have no category column. Resolve only through the
    # engine's documented exact scopes/aliases, never through fuzzy names.
    for subtype in {r['waste_subtype'] for r in repo.tables['conversion_parameters']}:
        for category in categories:
            if repo.applicable_technologies(category, subtype):
                categories[category].add(subtype)
    repo._api_waste_catalog = categories
    return categories


def technology_summary(repo, technology):
    rows = [r for r in repo.tables['technology_mapping'] if r['technology'] == technology]
    return {'technology': technology, 'requested_outputs': sorted(OUTPUT_ROUTES[technology]),
            'documented_outputs': sorted({r['possible_energy_outputs'] for r in rows if r['possible_energy_outputs']}),
            'equipment_forecast_supported': False}


@app.get('/api/health', response_model=HealthResponse)
def health(request: Request):
    repo = request.app.state.repository
    try:
        unchanged = repo.unchanged()
    except OSError:
        unchanged = False
    return dict(status='ok' if unchanged else 'degraded', engine_readiness='REFERENCE_ACCOUNTING_ONLY',
                datasets_unchanged_since_startup=unchanged, scientific_validation='FAILED_SOURCE_RECONCILIATION',
                external_predictive_validation='NOT_VALIDATED', electricity_heat_forecasts='BLOCKED',
                unresolved_gas_table_runs=['920', '924', '1110'], dataset_issues=repo.issues)


@app.get('/api/wastes', response_model=WastesResponse)
def wastes(repo=Depends(repository)):
    return {'categories': [{'waste_category': c, 'subtypes': sorted(s)}
                           for c, s in sorted(waste_catalog(repo).items())]}


def fresh_repository(repo):
    try:
        current = DataRepository(repo.root)
    except (OSError, ValueError):
        raise HTTPException(503, 'Scientific repository could not be loaded') from None
    if current.hashes != repo.hashes:
        raise HTTPException(503, 'Scientific datasets changed during request')
    return current


@app.get('/api/pathways', response_model=WastePathwaysResponse)
def waste_pathways(waste_category: str = Query(min_length=1, max_length=256),
                   waste_subtype: str = Query(min_length=1, max_length=256), repo=Depends(repository)):
    current = fresh_repository(repo)
    catalog = waste_catalog(repo)
    if waste_category not in catalog or waste_subtype not in catalog[waste_category]:
        raise HTTPException(422, 'Unknown waste category/subtype pair; select an exact name from /api/wastes')
    mappings = current.applicable_technologies(waste_category, waste_subtype)
    pathways = []
    for technology, outputs in sorted(OUTPUT_ROUTES.items()):
        rows = [m for m in mappings if m['technology'] == technology]
        restricted = any(m.get('hazard_flag') == 'true' or m['feasibility_status'] == 'restricted' for m in rows)
        verified = bool(rows) and not restricted
        sources = sorted({m['source_id'] for m in rows})
        pathways.append(dict(
            technology=technology,
            mapping_status='RESTRICTED' if restricted else 'VERIFIED' if verified else 'UNKNOWN',
            feasibility_status='restricted' if restricted else rows[0]['feasibility_status'] if rows else 'not_established',
            calculation_support='RESTRICTED' if restricted else 'EVIDENCE_GATED' if verified else 'UNSUPPORTED',
            default_eligible=verified and all(m['feasibility_status'] in {'conditional', 'demonstrated', 'feasible'} for m in rows),
            requested_outputs=sorted(outputs), blocked_forecasts=sorted(outputs & {'electricity', 'useful heat'}),
            mapping_records=rows, source_references=[current.source(s) for s in sources],
            explanation=('Restricted material: no ordinary conversion calculation or installation recommendation.' if restricted else
                         'Verified feed-to-technology mapping under the listed conditions. Numerical outputs still require matching parameters and evidence; equipment forecasts are not established.' if verified else
                         'No verified mapping for this exact published feed. Scientific applicability is UNKNOWN; the current engine cannot support this combination (NOT_APPLICABLE). No category-wide yield transfer is allowed.'),
        ))
    for pathway in pathways:
        assessments, recommended = assess_outputs(current, waste_category, waste_subtype, pathway)
        pathway['output_assessments'] = assessments
        pathway['recommended_output'] = recommended
        pathway['recommendation_reason'] = ('Ranked by nonblocked output, verified matching parameter availability, documented compatibility and missing requirements; ties are alphabetical. Not an efficiency, economic or plant-performance optimum.' if pathway['default_eligible'] else 'No automatic recommendation: mapping is unknown or restricted.')
    pathways.sort(key=recommendation_key)
    return dict(waste_category=waste_category, waste_subtype=waste_subtype, pathways=pathways,
                explanation='Verified mappings are conditional evidence, not plant feasibility or numerical forecast approval.' if any(p['default_eligible'] for p in pathways) else
                'No verified unrestricted pathway exists for this exact feed. Select another published subtype or explicitly inspect an unsupported route; no technology is selected automatically.')


@app.get('/api/technologies', response_model=TechnologiesResponse)
def technologies(repo=Depends(repository)):
    return {'technologies': [technology_summary(repo, t) for t in
                            sorted({r['technology'] for r in repo.tables['technology_mapping']})]}


@app.get('/api/technologies/{technology:path}', response_model=TechnologyDetails,
         responses={404: {'model': ErrorResponse}})
def technology_details(technology: str, repo=Depends(repository)):
    mappings = [dict(r) for r in repo.tables['technology_mapping'] if r['technology'] == technology]
    if not mappings:
        raise HTTPException(404, 'Unknown documented technology')
    parameters = repo.conversion_parameters(technology)
    equipment = repo.equipment_performance(technology)
    source_ids = sorted({r['source_id'] for r in mappings + parameters + equipment})
    return {**technology_summary(repo, technology), 'mappings': mappings,
            'conversion_parameters': parameters, 'equipment_records': equipment,
            'source_references': [repo.source(s) for s in source_ids], 'limitations': LIMITATIONS}


@app.post('/api/calculate', response_model=CalculateResponse)
def calculate_request(body: CalculateRequest, repo=Depends(repository)):
    catalog = waste_catalog(repo)
    if body.waste_category not in catalog or body.waste_subtype not in catalog[body.waste_category]:
        raise HTTPException(422, 'Unknown waste category/subtype pair; select an exact name from /api/wastes')
    if body.technology not in OUTPUT_ROUTES:
        raise HTTPException(422, 'Unknown technology; select an exact name from /api/technologies')
    # A fresh read avoids retaining cached evidence hashes across calculations.
    current = fresh_repository(repo)
    try:
        request = CalculationInput(body.waste_category, body.waste_subtype, body.quantity_kg,
                                   'kg', body.moisture_pct, body.desired_output,
                                   body.technology, body.parameter_id, body.property_id, body.reference_mode)
        result = calculate(request, body.technology, current).to_dict()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    result['source_references'] = [current.source(s) for s in result['source_ids']]
    result['dataset_issues'] = current.issues
    result['limitations'] = list(dict.fromkeys(result['limitations'] + LIMITATIONS))
    result['explanation'] = ('Published reference accounting under stated conditions; not a plant forecast.'
                             if result['calculation_status'] == 'CALCULATED_REFERENCE' else
                             '; '.join(result['missing_parameters'] + result['warnings']) or
                             'No supported numerical result for this feedstock and requested route.')
    validate_numeric_tree(result)
    return CalculateResponse.model_validate(result)


@app.get('/api/reference-studies', response_model=ReferenceStudiesResponse)
def reference_studies(waste_category: str = Query(min_length=1, max_length=256),
                      waste_subtype: str = Query(min_length=1, max_length=256),
                      technology: str = Query(min_length=1, max_length=256),
                      desired_output: str = Query(min_length=1, max_length=256), repo=Depends(repository)):
    catalog = waste_catalog(repo)
    if waste_subtype not in catalog.get(waste_category, set()):
        raise HTTPException(422, 'Unknown waste category/subtype pair')
    if technology not in OUTPUT_ROUTES or desired_output not in OUTPUT_ROUTES[technology]:
        raise HTTPException(422, 'Unknown technology or incompatible output')
    current = fresh_repository(repo)
    # The engine determines applicable output-specific parameter IDs. No frontend
    # parameter-name guessing or transfer between feed types is involved.
    preview = calculate(CalculationInput(waste_category, waste_subtype, 1.0, 'kg', None,
                                        desired_output, technology), technology, current)
    ids = set(preview.uncertainty.get('available_parameter_ids', []))
    if preview.scenario_id:
        ids.add(preview.scenario_id)
    studies = []
    for row in current.conversion_parameters(technology, waste_subtype):
        if row['parameter_id'] not in ids:
            continue
        verified = current.verified_field('conversion_parameters', row, 'value_typical')
        if technology == 'Anaerobic digestion' and waste_subtype == FOOD_SUBTYPE:
            verified = verified and not food_bundle(current)[1]
        studies.append(dict(parameter=row, evidence_status='VERIFIED' if verified else 'UNKNOWN',
                            selectable=verified, source_reference=current.source(row['source_id']),
                            evidence=current.evidence_for('conversion_parameters', row, 'value_typical'),
                            applicability='Matched published rates and exact TS/VS basis support a ratio-of-means reference reconstruction, not a directly measured mass-specific yield.' if technology == 'Anaerobic digestion' and waste_subtype == FOOD_SUBTYPE else 'Verified published yield and basis only. Equivalence of the user waste, preprocessing, reactor conditions and equipment scale is not established.'))
    sources = {s['parameter']['source_id'] for s in studies if s['selectable']}
    samples = []
    for row in current.waste_properties(waste_category, waste_subtype):
        if row.get('model_ready') == 'false' or row['source_id'] not in sources:
            continue
        field = 'moisture_pct' if row.get('moisture_pct') else 'total_solids_pct'
        if field == 'total_solids_pct' and 'wet' not in row.get('solids_basis', '').lower():
            continue
        if current.verified_field('waste_properties', row, field):
            samples.append({**row, 'property_id': row['waste_id'], 'verified_basis_field': field})
    run_moisture = preview.feasibility_checks.get('reference_run_moisture')
    if run_moisture and not any(s['selectable'] and s['parameter']['parameter_id'] == run_moisture.get('parameter_id', run_moisture.get('record_id')) for s in studies):
        run_moisture = None
    if technology == 'Anaerobic digestion' and waste_subtype == FOOD_SUBTYPE:
        return dict(waste_category=waste_category, waste_subtype=waste_subtype, technology=technology,
            desired_output=desired_output, studies=studies, reference_samples=samples,
            reference_run_moisture=run_moisture, linked_reference_parameters=linked_food_parameters(current),
            moisture_explanation='W0059 is diluted, preprocessed mesophilic 15-day reference pulp: 6.4% TS by wet mass and 86.3% VS/TS. Matching moisture is 93.6% wet basis (100 - TS). Enter that measured value, or explicitly select the exact published sample. This is not raw delivered market waste or an equipment moisture limit; no moisture response or VS composition is inferred for other feeds.',
            required_acknowledgement='I use only the selected EBMUD mesophilic 15-day reference pulp with its published TS and VS/TS basis. This is a ratio-of-published-means reconstruction, not a measured mass-specific biogas yield, BMP test or plant forecast. Raw methane is not total biogas or upgraded biomethane. Gas T/P is unspecified; no MJ, electricity or useful heat estimate is supported.')
    return dict(waste_category=waste_category, waste_subtype=waste_subtype, technology=technology,
                desired_output=desired_output, studies=studies, reference_samples=samples, reference_run_moisture=run_moisture,
                moisture_explanation=(f"This published run observed {run_moisture['value']}% wet-basis chip moisture. Reference calculation requires that same value; no moisture-response model or equipment moisture limit is established. No value is filled automatically." if run_moisture else
                'Use only the exact published sample at its verified basis; never assume this represents the user waste.' if samples else
                'No verified same-sample wet-basis moisture or total-solids record exists for this reference. Enter user-measured wet-basis moisture. A dry-feed yield does not imply zero moisture.'),
                required_acknowledgement='I use this selected gasification run for reference accounting only. Feed equivalence and equipment-qualified plant performance are not established. Gas T/P is unspecified: volume is not Nm3. Gas chemical energy is before utilization, not electricity, useful heat or net plant energy.' if technology == 'Gasification' else
                'I use the selected published operating conditions for reference mass accounting only. Feed equivalence and equipment-qualified plant performance are not established; liquid includes water, and this is not an energy forecast.')
