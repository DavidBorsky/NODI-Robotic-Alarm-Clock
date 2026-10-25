"""Check the public package: local Markdown links, PDF parsing and accidental secrets.
This supplements CAD and controller verification; it is not a hardware test.
"""
import re,json,hashlib
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
errors=[];links=0;pdfs={}
for p in ROOT.rglob('*.md'):
    for raw in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        target=raw.split('#')[0].split('?')[0]
        if not target or '://' in target or target.startswith('mailto:'):continue
        target=target.strip('<>');links+=1
        if not (p.parent/target).exists():errors.append(f'Broken link: {p.relative_to(ROOT)} -> {target}')
for p in ROOT.rglob('*.pdf'):
    pdfs[str(p.relative_to(ROOT))]=len(PdfReader(p).pages)
    if p.stat().st_size<2000:errors.append('Suspiciously small PDF: '+p.name)
# Credential patterns are assembled to avoid matching this source file itself.
patterns=[r'gh'+'[pousr]_[A-Za-z0-9]{30,}',r'github'+'_pat_[A-Za-z0-9_]{30,}',r'AK'+'IA[A-Z0-9]{16}',r'-----BEGIN '+'(?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
files=[p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts]
for p in files:
    if p.suffix in {'.py','.md','.json','.yaml','.yml','.csv','.txt','.ino','.h','.cpp','.sh'}:
        for pat in patterns:
            if re.search(pat,p.read_text(errors='ignore')):errors.append('Credential-like text in '+str(p.relative_to(ROOT)))
report={'status':'PASS' if not errors else 'FAIL','local_markdown_links_checked':links,'pdf_pages':pdfs,'files_checked':len(files),'secret_pattern_scan':'no matches' if not any('Credential' in x for x in errors) else 'MATCH','limitations':'Pattern scan does not prove absence of every secret. Review tracked files before publishing.','errors':errors}
(ROOT/'Documentation/package_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
