import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const W=path.join(ROOT,'presentations');
const BUILD=path.join(W,'.build');
const SKILL='/Users/pejmonshariati/.codex/plugins/cache/openai-primary-runtime/presentations/26.1112.11011/skills/presentations';
process.env.RUNTIME_NODE_MODULES='/Users/pejmonshariati/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(path.join(SKILL,'container_tools/artifact_tool_utils.mjs'));
const FONT='Arial';
const C={navy:'#24384F',text:'#26384D',muted:'#526A80',line:'#CBD6DF',blue:'#347CB1',red:'#BA5054',yellow:'#DBA429',green:'#609C8C',purple:'#8B65B1',pale:'#F3F6F9'};

const draft=path.join(BUILD,'candidate.pptx');
const out=path.join(W,'output','Alaska_2026_Research_Presentation_Final.pptx');
const result=await finalizePresentation({workspaceDir:W,candidatePath:draft,finalPath:out,pythonExecutable:'/Users/pejmonshariati/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[2,7,13,21,22,23,25,26,27].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:29,requiredNativeTableOwnerSlides:[2,7,13,21,22,23,25,26,27],fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation_final.json')});
console.log(JSON.stringify(result));
