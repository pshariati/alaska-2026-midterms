import sharp from 'sharp';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const here=path.dirname(fileURLToPath(import.meta.url));
const svg=path.join(here,'House_Sankey_Nov11.svg');
await sharp(svg,{density:192}).resize(3840,2160).png().toFile(path.join(here,'House_Sankey_Nov11.png'));
await sharp(svg).resize(1440,810).png().toFile(path.join(here,'House_Sankey_Preview.png'));
console.log('Rendered high-resolution PNG and preview.');
