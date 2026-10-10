"""Package the upgraded project and final report; omit runtime secrets and legacy reports."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'output/NEC_Fee_Assist_AI_Agent_Project_SYED_SUFYAN.zip'
files=[]
for folder in ['app','tests','output/ai_lab_assets']:
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.log'})
files.extend(ROOT/'scripts'/name for name in ['ai_lab_content.py','build_ai_lab_report.py','capture_ai_lab.py','evaluate_ai_agent.py','package_ai_lab.py'])
files.extend(ROOT/name for name in ['README.md','requirements.txt','run.ps1','.gitignore','output/pdf/NEC_Fee_Assist_AI_Lab_Report_SYED_SUFYAN.pdf'])
with zipfile.ZipFile(TARGET,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(files):z.write(path,path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(TARGET) as z:
    assert z.testzip() is None
    assert not any(name.startswith(('data/','.venv/','tmp/')) or 'demo_credentials' in name or name.endswith(('.sqlite3','.db','.env')) for name in z.namelist())
print('Packaged',len(files),'files:',TARGET)
