"""Read original PDF page text or render a page for visual evidence review."""
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.deps'))
import pymupdf
parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('pages', nargs='+', type=int, help='1-based PDF page numbers')
parser.add_argument('--render', action='store_true')
args = parser.parse_args()
with pymupdf.open(ROOT/'data/raw'/args.filename) as doc:
    for number in args.pages:
        page = doc[number-1]
        if args.render:
            path = ROOT/'data/processed'/f'{Path(args.filename).stem}_review_{number}.png'
            page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(path)
            print(path)
        else:
            print(f'PDF PAGE {number}\n{page.get_text(sort=True)}')
