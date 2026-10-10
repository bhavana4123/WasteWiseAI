"""CLI demonstration; reads scientific datasets and never writes to data/."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import CalculationInput, DataRepository, recommend

def example_requests():
    return [
        CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, 'kg', 10, 'bio-oil', parameter_id='P0022', reference_mode=True),
        CalculationInput('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', 1, 'tonnes', 16.52, 'syngas', parameter_id='P0056', reference_mode=True),
        CalculationInput('Municipal solid waste', 'Dry shredded garbage sample A', 100, 'kg', 0, 'solid fuel energy', reference_mode=True),
        CalculationInput('Food and organic waste', 'EBMUD source-separated delivered food waste', 1, 'tonnes', None, 'biomethane', parameter_id='P0004', reference_mode=True),
        CalculationInput('Food and organic waste', 'EBMUD food waste pulp', 100, 'kg', 90, 'biogas', parameter_id='P0001', reference_mode=True),
        CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, 'kg', None, 'bio-oil', parameter_id='P0022', reference_mode=True),
        CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, 'kg', 10, 'biochar', parameter_id='P0023', reference_mode=True),
        CalculationInput('Food and organic waste', 'Source-separated food waste', 100, 'kg', None, 'electricity', 'Combined heat and power'),
        CalculationInput('Municipal solid waste', 'Non-recyclable non-hazardous MSW', 100, 'kg', None, 'electricity'),
        CalculationInput('Agricultural residues', 'Corn stover', 100, 'kg', None, 'ethanol'),
        CalculationInput('Used cooking oil and fats', 'Yellow grease', 100, 'kg', None, 'biodiesel'),
        CalculationInput('Sewage sludge', 'Detroit 50/50 primary/secondary sludge; WW06 SS-2', 100, 'kg', 80, 'bio-oil'),
        CalculationInput('Municipal solid waste', 'Combustible RDF fraction', 100, 'kg', None, 'solid fuel energy'),
        CalculationInput('Landfill waste', 'Biodegradable waste already in MSW landfill', 100, 'kg', None, 'biogas'),
        CalculationInput('Industrial waste heat', 'Industrial hot gases and liquids', 100, 'kg', None, 'useful heat'),
        CalculationInput('Hazardous and medical waste', 'Regulated medical waste', 100, 'kg', None, 'electricity', 'Combustion'),
        CalculationInput('Inert waste', 'Glass', 100, 'kg', None, 'electricity'),
    ]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--examples', action='store_true')
    parser.add_argument('--category')
    parser.add_argument('--subtype')
    parser.add_argument('--quantity', type=float)
    parser.add_argument('--unit', choices=['g', 'kg', 'tonnes'], default='kg')
    parser.add_argument('--moisture', type=float, help='Wet-basis mass percent; absent stays unknown')
    parser.add_argument('--output', default='electricity')
    parser.add_argument('--technology')
    parser.add_argument('--parameter-id', help='Select one original study/operating-condition yield')
    parser.add_argument('--property-id')
    parser.add_argument('--reference-mode', action='store_true', help='Explicitly opt into published reference mass accounting, not a plant forecast')
    args = parser.parse_args()
    try:
        repo = DataRepository()
        if args.examples:
            result = [recommend(r, repo) for r in example_requests()]
        else:
            if not args.category or not args.subtype or args.quantity is None:
                parser.error('--category, --subtype and --quantity are required unless --examples')
            request = CalculationInput(args.category, args.subtype, args.quantity, args.unit, args.moisture, args.output, args.technology, args.parameter_id, args.property_id, args.reference_mode)
            result = recommend(request, repo)
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
        if not repo.unchanged():
            raise RuntimeError('Scientific dataset changed during calculation')
    except (ValueError, OSError) as error:
        print(json.dumps({'status': 'INVALID_INPUT_OR_DATA', 'error': str(error)}))
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
