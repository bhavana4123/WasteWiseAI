from dataclasses import dataclass, field, asdict
from .units import mass_to_kg, number

OUTPUTS = {'electricity', 'useful heat', 'biogas', 'biomethane', 'syngas', 'bio-oil', 'biochar', 'ethanol', 'biodiesel', 'solid fuel energy'}

@dataclass(frozen=True)
class CalculationInput:
    waste_category: str
    waste_subtype: str
    quantity: float
    unit: str = 'kg'
    moisture_pct: float | None = None
    desired_output: str = 'electricity'
    technology_preference: str | None = None
    parameter_id: str | None = None
    property_id: str | None = None
    reference_mode: bool = False

    def __post_init__(self):
        if not isinstance(self.waste_category, str) or not isinstance(self.waste_subtype, str) or not self.waste_category.strip() or not self.waste_subtype.strip():
            raise ValueError('Waste category and subtype are required')
        mass_to_kg(self.quantity, self.unit)
        object.__setattr__(self, 'quantity', number(self.quantity, 'quantity'))
        if self.desired_output not in OUTPUTS:
            raise ValueError(f'Unsupported desired output: {self.desired_output}')
        if self.moisture_pct is not None:
            if not 0 <= number(self.moisture_pct, 'moisture_pct') <= 100:
                raise ValueError('Moisture must be 0–100% wet basis')
            object.__setattr__(self, 'moisture_pct', number(self.moisture_pct, 'moisture_pct'))
        if not isinstance(self.reference_mode, bool):
            raise ValueError('reference_mode must be boolean')

    @property
    def mass_kg(self):
        return mass_to_kg(self.quantity, self.unit)

@dataclass
class CalculationResult:
    input_waste_details: dict
    technology: str
    feasibility_status: str = 'conditional'
    calculation_status: str = 'INSUFFICIENT_DATA'
    energy_output_type: str = ''
    calculated_value: float | None = None
    unit: str | None = None
    gross_vs_net_classification: str = 'not_calculated'
    formula: str | None = None
    parameters: list = field(default_factory=list)
    source_ids: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)
    missing_parameters: list = field(default_factory=list)
    uncertainty: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    limitations: list = field(default_factory=list)
    intermediate_products: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    scenario_id: str | None = None
    errors: list = field(default_factory=list)
    feasibility_checks: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
