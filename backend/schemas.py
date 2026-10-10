from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


Text = Annotated[str, Field(strict=True, min_length=1, max_length=256)]
Output = Literal['electricity', 'useful heat', 'biogas', 'biomethane', 'syngas',
                 'bio-oil', 'biochar', 'ethanol', 'biodiesel', 'solid fuel energy']


class CalculateRequest(Model):
    waste_category: Text
    waste_subtype: Text
    quantity_kg: Annotated[float, Field(strict=True, gt=0)]
    moisture_pct: Annotated[float, Field(strict=True, ge=0, le=100)] | None = None
    technology: Text
    desired_output: Output
    parameter_id: Text | None = None
    property_id: Text | None = None
    reference_mode: StrictBool = False


class HealthResponse(Model):
    status: Literal['ok', 'degraded']
    engine_readiness: Literal['REFERENCE_ACCOUNTING_ONLY']
    datasets_unchanged_since_startup: bool
    scientific_validation: Literal['FAILED_SOURCE_RECONCILIATION']
    external_predictive_validation: Literal['NOT_VALIDATED']
    electricity_heat_forecasts: Literal['BLOCKED']
    unresolved_gas_table_runs: list[str]
    dataset_issues: list[str]


class WasteCategory(Model):
    waste_category: str
    subtypes: list[str]


class WastesResponse(Model):
    categories: list[WasteCategory]


class TechnologySummary(Model):
    technology: str
    requested_outputs: list[str]
    documented_outputs: list[str]
    equipment_forecast_supported: Literal[False] = False


class TechnologiesResponse(Model):
    technologies: list[TechnologySummary]


class TechnologyDetails(TechnologySummary):
    mappings: list[dict[str, str]]
    conversion_parameters: list[dict[str, str]]
    equipment_records: list[dict[str, str]]
    source_references: list[dict[str, str]]
    limitations: list[str]


class CalculateResponse(Model):
    input_waste_details: dict[str, JsonValue]
    technology: str
    feasibility_status: str
    calculation_status: Literal['CALCULATED_REFERENCE', 'INSUFFICIENT_DATA', 'NOT_APPLICABLE', 'RESTRICTED']
    energy_output_type: Output
    calculated_value: Annotated[float, Field(ge=0)] | None
    unit: str | None
    gross_vs_net_classification: str
    formula: str | None
    parameters: list[dict[str, JsonValue]]
    source_ids: list[str]
    assumptions: list[str]
    missing_parameters: list[str]
    uncertainty: dict[str, JsonValue]
    warnings: list[str]
    limitations: list[str]
    intermediate_products: list[dict[str, JsonValue]]
    evidence: list[dict[str, JsonValue]]
    scenario_id: str | None
    errors: list[dict[str, JsonValue]]
    feasibility_checks: dict[str, JsonValue]
    source_references: list[dict[str, str]]
    dataset_issues: list[str]
    explanation: str

    @model_validator(mode='after')
    def enforce_output_boundary(self):
        if self.energy_output_type in {'electricity', 'useful heat'} and self.calculated_value is not None:
            raise ValueError('Equipment-qualified energy forecasts are unavailable')
        if self.calculation_status != 'CALCULATED_REFERENCE' and self.calculated_value is not None:
            raise ValueError('Unsupported calculation contains a primary quantity')
        return self


class ErrorResponse(Model):
    code: str
    message: str
    details: list[dict[str, JsonValue]] = Field(default_factory=list)


class OutputAssessment(Model):
    output: Output
    forecast_blocked: bool
    has_verified_parameters: bool
    matching_parameter_ids: list[str]
    study_selection_required: bool
    calculation_status: str
    missing_parameters: list[str]
    explanation: str


class WastePathway(Model):
    technology: str
    mapping_status: Literal['VERIFIED', 'UNKNOWN', 'RESTRICTED']
    feasibility_status: str
    calculation_support: Literal['EVIDENCE_GATED', 'UNSUPPORTED', 'RESTRICTED']
    default_eligible: bool
    requested_outputs: list[str]
    blocked_forecasts: list[str]
    output_assessments: list[OutputAssessment]
    recommended_output: Output | None
    recommendation_reason: str
    mapping_records: list[dict[str, str]]
    source_references: list[dict[str, str]]
    explanation: str


class WastePathwaysResponse(Model):
    waste_category: str
    waste_subtype: str
    pathways: list[WastePathway]
    explanation: str


class ReferenceStudy(Model):
    parameter: dict[str, str]
    evidence_status: Literal['VERIFIED', 'UNKNOWN']
    selectable: bool
    source_reference: dict[str, str]
    evidence: list[dict[str, str]]
    applicability: str


class ReferenceStudiesResponse(Model):
    waste_category: str
    waste_subtype: str
    technology: str
    desired_output: Output
    studies: list[ReferenceStudy]
    reference_samples: list[dict[str, str]]
    moisture_explanation: str
    required_acknowledgement: str
    reference_run_moisture: dict[str, JsonValue] | None = None
    linked_reference_parameters: list[dict[str, str]] = []
