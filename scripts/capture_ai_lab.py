"""Capture the real upgraded app against an isolated temporary demonstration DB."""
import html, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'output'/'ai_lab_assets';ASSETS.mkdir(parents=True,exist_ok=True)
QA=ROOT/'tmp'/'pdfs';QA.mkdir(parents=True,exist_ok=True)
PORT=8874;BASE=f'http://127.0.0.1:{PORT}'

def source_html(file,start=1,end=None,tree=False):
    path=ROOT/file;lines=path.read_text().splitlines();end=end or len(lines)
    listing=['app/server.py','app/service.py','app/agent.py','app/nlp.py','app/schema.sql',
             'app/static/app.js','app/static/style.css','tests/test_project.py',
             'scripts/evaluate_ai_agent.py','requirements.txt','run.ps1']
    sidebar=''.join('<div class="file">'+html.escape(p)+'</div>' for p in listing if (ROOT/p).exists())
    code=''.join(f'<div class="line"><span class="num">{n}</span><span>{html.escape(line) or " "}</span></div>' for n,line in enumerate(lines,1) if start<=n<=end)
    return f'''<!doctype html><meta charset="utf-8"><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#1e1e1e;color:#dedede;font-family:Consolas,monospace}}
    header{{background:#303030;padding:12px 20px;font:14px Segoe UI;color:#ddd}}
    aside{{width:275px;background:#252526;position:absolute;top:43px;bottom:0;padding:20px 14px;font-size:13px;line-height:2}}
    .file{{white-space:nowrap}}main{{margin-left:275px}}.tab{{background:#292929;padding:12px 20px;font-size:15px;border-bottom:2px solid #1f5eff}}
    .code{{padding:16px 12px 24px;font-size:17px;line-height:1.55;overflow:hidden}}
    .line{{display:flex;white-space:pre-wrap;overflow-wrap:anywhere}}.line>span:last-child{{min-width:0;flex:1}}.num{{color:#858585;min-width:52px;text-align:right;padding-right:20px;user-select:none}}
    </style><header>NEC FEE BOT / Source Code Viewer</header><aside>PROJECT FILES<br>{sidebar}</aside>
    <main><div class="tab">{html.escape(file)}</div><div class="code">{code}</div></main>'''

def main():
    runtime=QA/'capture_data';runtime.mkdir(exist_ok=True)
    # Unique per run: never reset or reuse the real project's runtime DB.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='fee_agent_capture_') as temp:
        env={**os.environ,'FEE_ASSIST_DB':str(Path(temp)/'demo.sqlite3')}
        log=open(QA/'capture_server.log','w')
        proc=subprocess.Popen([sys.executable,'-m','app.server','--port',str(PORT)],cwd=ROOT,env=env,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            for _ in range(80):
                try:urllib.request.urlopen(BASE,timeout=1).close();break
                except Exception:time.sleep(.15)
            else:raise RuntimeError('Isolated capture server did not start')
            credentials=json.loads((Path(temp)/'demo_credentials.json').read_text())
            errors=[];checks=[]
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                ctx=browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1)
                page=ctx.new_page();page.on('pageerror',lambda err:errors.append(str(err)))
                def capture(name):page.screenshot(path=str(ASSETS/(name+'.png')),full_page=True)
                def login(role):
                    page.goto(BASE);page.locator('#login-id').fill(credentials[role]['id']);page.locator('#login-password').fill(credentials[role]['password'])
                    page.get_by_role('button',name='Sign in',exact=True).click();page.wait_for_selector('.sidebar')
                def ask(question):
                    count=page.locator('.message.question').count()
                    page.locator('#question').fill(question);page.get_by_role('button',name='Send',exact=True).click()
                    page.wait_for_function('(n)=>document.querySelectorAll(".message.question").length>n',arg=count)
                    page.get_by_role('button',name='Send',exact=True).wait_for(state='visible')
                page.goto(BASE);page.wait_for_selector('#login-id');capture('01_login')
                login('student');capture('02_dashboard')
                page.locator('#open-assistant').click();ask('Could you navigate to my profile?')
                page.get_by_role('heading',name='My profile',exact=True).wait_for();capture('03_auto_profile')
                checks.append('Paraphrased task opens profile and retains assistant')
                ask('Help me pay tuition')
                page.get_by_role('heading',name='Pending fees',exact=True).wait_for()
                assert page.locator('[data-fee]:checked').count()==1
                assert 'Tuition' in page.locator('tr').filter(has=page.locator('input:checked')).inner_text()
                capture('04_payment_agent');checks.append('Tuition selected without payment execution')
                page.get_by_role('button',name='Close fee assistant',exact=True).click()
                page.get_by_role('button',name='Proceed to demo payment',exact=True).click()
                capture('05_confirmation')
                page.get_by_role('button',name='Confirm demo payment',exact=True).click()
                page.get_by_role('link',name='Download receipt',exact=True).wait_for()
                checks.append('Payment completed only through existing confirmation form')
                page.locator('#open-assistant').click();ask('Download my receipt')
                page.get_by_role('link',name='Download latest receipt',exact=True).wait_for();capture('06_receipt_agent')
                with page.expect_download() as info:page.get_by_role('link',name='Download latest receipt',exact=True).click()
                info.value.save_as(str(QA/'agent_receipt.pdf'))
                checks.append('Agent finds owner-protected receipt; actual PDF download succeeds')
                ask('Open fee allotment')
                assert 'administrator account' in page.locator('.message .bubble').last.inner_text()
                assert page.locator('h1').inner_text()=='Transaction history'
                checks.append('Student admin-page request is denied')
                # Client defense also rejects invented action types and page identifiers.
                page.evaluate("applyAgentActions([{type:'navigate',page:'https://attacker.example'},{type:'select_fees',fee_ids:[-1,999999999]},{type:'execute_sql',sql:'DELETE FROM fees'}])")
                assert page.locator('h1').inner_text()=='Transaction history'
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert page.locator('.agent-dock').bounding_box()['width']<=390
                capture('07_mobile_agent');checks.append('Mobile assistant fits a 390px viewport')
                page.set_viewport_size({'width':1440,'height':1000})
                page.get_by_role('button',name='Sign out',exact=True).click();page.wait_for_selector('#login-id')
                login('admin');page.locator('#open-assistant').click();ask('Help me assign fees')
                page.get_by_role('heading',name='Fee allotment',exact=True).wait_for();capture('08_admin_guide')
                checks.append('Administrator gets fee-allotment navigation and workflow guidance')
                page.get_by_role('button',name='Close fee assistant',exact=True).click()
                page.get_by_role('button',name='Fee policies',exact=True).click();capture('09_policies')
                codepage=ctx.new_page();codepage.set_viewport_size({'width':1600,'height':940})
                for name,file,needle,length in [
                    ('code_server','app/server.py','token=self.token()',18),
                    ('code_model','app/agent.py','def predict(',25),
                    ('code_tools','app/static/app.js','function applyAgentActions(',11),
                    ('code_folder','app/schema.sql','PRAGMA',22)]:
                    lines=(ROOT/file).read_text().splitlines();start=next(i for i,l in enumerate(lines,1) if needle in l)
                    codepage.set_content(source_html(file,start,start+length-1));codepage.screenshot(path=str(ASSETS/(name+'.png')),full_page=True)
                browser.close()
            assert not errors,errors
            (ASSETS/'browser_checks.json').write_text(json.dumps({'checks':checks,'browser_errors':errors},indent=2))
            print('Browser checks passed:',len(checks),'workflow checks; screenshots saved.')
        finally:
            proc.terminate();proc.wait(timeout=10);log.close()

if __name__=='__main__':main()
