import sharp from 'sharp';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const here=path.dirname(fileURLToPath(import.meta.url));
for(const name of ['dan_j_first_flow','senate_full_sankey']){
  await sharp(path.join(here,`${name}.svg`),{density:144}).png().toFile(path.join(here,`${name}.png`));
}
