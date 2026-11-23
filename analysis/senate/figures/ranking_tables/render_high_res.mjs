import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import sharp from 'sharp';
const base=path.dirname(fileURLToPath(import.meta.url));
for(const name of ['Daniel_S_next_to_Dan_J','Peltola_before_Daniel_S']){
 const svg=await fs.readFile(path.join(base,name+'.svg'));
 await sharp(svg,{density:216}).png().toFile(path.join(base,name+'_HighRes.png'));
 console.log(name,await sharp(path.join(base,name+'_HighRes.png')).metadata().then(v=>({width:v.width,height:v.height})));
}
// This is a terminology-only rendering of the existing editable notebook table.
// Original source records and notebook are not modified.
const rows=[['Both valid: Peltola above Dan S.','568','14.42%'],['Both valid: Dan S. above Peltola','423','10.74%'],['Only Peltola valid among the finalists','765','19.42%'],['Only Dan S. valid among the finalists','481','12.21%'],['Neither finalist valid','1,703','43.22%']];
let parts=['<svg xmlns="http://www.w3.org/2000/svg" width="572" height="292" viewBox="0 0 572 292"><rect width="572" height="292" fill="white"/>',
'<style>text{font-family:Arial,sans-serif;font-size:13px;fill:#071D2F}.head{font-weight:700;fill:white}.title{font-size:16px;font-weight:700;fill:#29475D}</style>',
'<text class="title" x="11" y="18">Daniel J. Sullivan Jr.: 3,940 first-choice ballots</text>',
'<rect x="11" y="39" width="539" height="40" fill="#1D3C58"/>',
'<text class="head" x="23" y="63">Valid rankings</text><text class="head" x="340" y="63" text-anchor="end">Ballots</text><text class="head" x="538" y="63" text-anchor="end">Share of Daniel-first cohort</text>'];
rows.forEach((r,i)=>{
 const y=79+i*40;
 parts.push(`<rect x="11" y="${y}" width="539" height="40" fill="${i===0?'#D8EDFF':i%2?'#F4F6F8':'#F2F2F2'}"/>`);
 parts.push(`<line x1="11" y1="${y+40}" x2="550" y2="${y+40}" stroke="#DCE6EC" stroke-width="0.6"/>`);
 parts.push(`<text x="23" y="${y+24}">${r[0]}</text><text x="340" y="${y+24}" text-anchor="end">${r[1]}</text><text x="538" y="${y+24}" text-anchor="end">${r[2]}</text>`);
});
parts.push('</svg>');
const svg=parts.join('\n');
await fs.writeFile(path.join(base,'Valid_Finalist_Rankings.svg'),svg);
await sharp(Buffer.from(svg),{density:576}).png().toFile(path.join(base,'Valid_Finalist_Rankings_HighRes.png'));
console.log('Valid_Finalist_Rankings',await sharp(path.join(base,'Valid_Finalist_Rankings_HighRes.png')).metadata().then(v=>({width:v.width,height:v.height})));
await fs.writeFile(path.join(base,'HIGH_RES_FILES.json'),JSON.stringify({rendering:'Direct vector text rendering, not enlargement of raster previews',terminology:'All occurrences of countable replaced with valid in the five-row table',counts_unchanged:true},null,2));
