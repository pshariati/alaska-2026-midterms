import fs from 'node:fs/promises';
import path from 'node:path';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const base=path.dirname(new URL(import.meta.url).pathname);
const url=(await fs.readFile(path.join(base,'math_link.txt'),'utf8')).trim();
const p=Presentation.create({slideSize:{width:1280,height:720}});
const s=p.slides.add();s.background.fill='#FFFFFF';
function t(str,x,y,w,h,size=28,bold=false,color='#24384F'){
const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=str;q.text.style={typeface:'Arial',fontFamily:'Arial',fontSize:size,bold,color,insets:0};return q;}
t('OPTIONAL METHODS',64,32,700,28,16,true,'#526A80');
t('Want the math?',64,87,1100,70,46,true);
t('Scan for the full method, equations and sources',64,166,1100,55,29,false,'#526A80');
t('Six steps from ballot rankings\nto a candidate axis',64,286,600,94,33,true);
t('Includes symbol definitions, MDS fitting,\nrepeated fits and normalization, plus\nthe separate consistency calculation.',64,414,600,128,27);
const link=t('Open the mathematical methods PDF',64,578,670,42,24,true,'#347CB1');link.text.get('Open the mathematical methods PDF').link={uri:url,isExternal:true};
const bytes=await fs.readFile(path.join(base,'Alaska_MDS_QR.png'));
s.images.add({blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),contentType:'image/png',alt:'QR code linking to the full MDS mathematical methods PDF',fit:'contain',position:{left:770,top:248,width:410,height:410}});
t('View-only PDF · No sign-in required',64,669,1100,28,17,false,'#526A80');
s.speakerNotes.text='The mathematical details are optional. Scan the QR code or use the clickable link to open a four-page PDF containing the six steps, equations, definitions and sources. The PDF has view-only access for anyone with the link and does not require sign-in. The QR code was independently decoded to verify its exact destination.\n'+url;
await fs.mkdir(path.join(base,'output'),{recursive:true});
const draft=path.join(base,'qr_slide_draft.pptx');await(await PresentationFile.exportPptx(p)).save(draft);
const preview=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(base,'QR_Slide_Preview.png'),new Uint8Array(await preview.arrayBuffer()));
process.env.RUNTIME_NODE_MODULES='/Users/pejmonshariati/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const skill='/Users/pejmonshariati/.codex/plugins/cache/openai-primary-runtime/presentations/26.1112.11011/skills/presentations';
const {finalizePresentation}=await import(path.join(skill,'container_tools/artifact_tool_utils.mjs'));
await finalizePresentation({workspaceDir:base,candidatePath:draft,finalPath:path.join(base,'output/Alaska_MDS_QR_Slide.pptx'),pythonExecutable:'/Users/pejmonshariati/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],explicitTotalSlideCount:1,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(base,'qr_slide_validation.json')});
console.log('QR slide ready');
