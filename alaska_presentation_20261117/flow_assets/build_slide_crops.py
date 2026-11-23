"""Crop presentation-only SVGs for slide placement; original assets stay untouched."""
from pathlib import Path
import re
OUT=Path(__file__).resolve().parent
s=(OUT/'dan_j_first_flow.svg').read_text()
s=s.replace('width="1600" height="800" viewBox="0 0 1600 800"',
            'width="1600" height="590" viewBox="0 110 1600 590"')
# Cropping excludes the internal title, subtitle and footer. Flow labels are preserved.
s=re.sub(r'<text class="(?:t|sub)"[^>]*>.*?</text>', '', s)
(OUT/'dan_j_first_flow_slide.svg').write_text(s)

s=(OUT/'senate_full_sankey.svg').read_text()
s=s.replace('width="2000" height="1060" viewBox="0 0 2000 1060"',
            'width="2000" height="770" viewBox="0 150 2000 770"')
s=re.sub(r'<text class="(?:title|sub|foot)"[^>]*>.*?</text>', '', s)
s=s.replace('.stage{font-size:21px;', '.stage{font-size:30px;')
s=s.replace('.label{font-size:16px;', '.label{font-size:29px;')
# The first two labels have a wider ribbon to their right than the margin at left.
# Identify stage-1 major candidate text robustly, retaining each original vertical coordinate.
s=re.sub(r'<text class="label" text-anchor="end" x="251" y="([^"]+)">(Peltola  117,505|Daniel S\.  115,917)</text>',
         r'<text class="label" text-anchor="start" x="300" y="\1">\2</text>',s)
(OUT/'senate_full_sankey_slide.svg').write_text(s)
print('Created cropped SVGs; ribbon paths and all numeric counts unchanged.')
