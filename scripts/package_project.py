"""Package source and final artifacts; exclude runtime secrets and database state."""
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'output'/'NEC_Fee_Assist_Complete_Project.zip'
files=[]
for directory in ['app','scripts','tests','output']:
    for path in (ROOT/directory).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc','.zip'):
            files.append(path)
files.extend(ROOT/name for name in ['README.md','requirements.txt','run.ps1','.gitignore'])
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):archive.write(path,str(path.relative_to(ROOT)))
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    names=archive.namelist()
    assert not any(name.startswith(('data/','.venv/','tmp/')) or 'demo_credentials' in name for name in names)
print('Packaged',len(files),'files;',target.stat().st_size,'bytes:',target)
