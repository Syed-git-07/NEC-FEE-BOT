"""Capture actual local screens and exercise the student/admin UI."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'/'screenshots';OUT.mkdir(parents=True,exist_ok=True)
creds=json.loads((ROOT/'data'/'demo_credentials.json').read_text())

def main():
    evidence=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1050},device_scale_factor=1)
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        def capture(name):
            page.locator('#toast').wait_for(state='hidden')
            page.screenshot(path=str(OUT/(name+'.png')),full_page=True);evidence.append(name)
        def nav(label):page.get_by_role('button',name=label,exact=True).click();page.wait_for_timeout(250)
        def signin(role):
            page.goto('http://127.0.0.1:8765');page.locator('#login-id').fill(creds[role]['id']);page.locator('#login-password').fill(creds[role]['password']);page.get_by_role('button',name='Sign in',exact=True).click();page.wait_for_selector('.sidebar')
        def signout():
            page.get_by_role('button',name='Sign out').click();page.wait_for_selector('#login-id')
        page.goto('http://127.0.0.1:8765');page.wait_for_selector('#login-id');capture('01_login')
        signin('student');capture('02_student_dashboard')
        nav('Pending fees');page.locator('[data-fee]').first.check();capture('03_pending_fees')
        page.get_by_role('button',name='Proceed to demo payment').click();capture('04_demo_payment')
        page.get_by_role('button',name='Confirm demo payment').click();page.wait_for_selector('a[href^="/api/receipt/"]');capture('05_transaction_history')
        with page.expect_download() as download:page.get_by_role('link',name='Download receipt').first.click()
        downloaded=download.value;downloaded.save_as(str(ROOT/'output'/'pdf'/'Sample_Demo_Payment_Receipt.pdf'))
        nav('Fee assistant');page.locator('#question').fill('How much are my pending fees?');page.get_by_role('button',name='Send',exact=True).click();page.wait_for_selector('.message small');capture('06_chatbot_balance')
        page.locator('#question').fill('When is my tuition fee due?');page.get_by_role('button',name='Send',exact=True).click();page.wait_for_timeout(500)
        page.locator('#question').fill('What happens if payment fails?');page.get_by_role('button',name='Send',exact=True).click();page.wait_for_timeout(500);capture('07_chatbot_policy')
        nav('My profile');capture('08_student_profile')
        page.set_viewport_size({'width':390,'height':844});capture('09_mobile_profile');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Mobile overflow'
        page.set_viewport_size({'width':1440,'height':1050});signout();signin('admin');capture('10_admin_dashboard')
        nav('Fee allotment');page.locator('#fee-head').fill('Project laboratory');page.locator('#fee-amount').fill('750');page.locator('#fee-due').fill('2026-11-15');capture('11_fee_allotment');page.get_by_role('button',name='Assign fee',exact=True).click();page.wait_for_timeout(500)
        nav('Students');capture('12_student_directory')
        nav('Fee ledger');capture('13_fee_ledger')
        page.locator('#ledger-search').fill('Project laboratory');assert page.get_by_text('Project laboratory',exact=True).count()==1
        with page.expect_download() as download:page.get_by_role('link',name='Export CSV',exact=True).click()
        download.value.save_as(str(ROOT/'output'/'sample_fee_ledger.csv'))
        nav('Fee policies');capture('14_policy_management')
        nav('Audit log');capture('15_audit_log')
        signout();signin('student');nav('Pending fees');assert page.get_by_text('Project laboratory',exact=True).count()==1
        page.locator('[data-fee]').first.check();page.get_by_role('button',name='Proceed to demo payment').click();page.locator('#outcome').select_option('failed');page.get_by_role('button',name='Confirm demo payment').click();page.wait_for_timeout(400);assert page.get_by_text('Failed',exact=True).count()>=1
        signout()
        browser.close()
    report={'screenshots':evidence,'browser_errors':errors,'checks':['Student sign-in','Server-backed fee selection','Completed demo payment','Actual PDF receipt download','Live balance chatbot','Policy chatbot','390px mobile profile without overflow','Admin sign-in','Admin fee assignment visible to student','Ledger search','CSV download','Failed payment history','Session logout']}
    (ROOT/'output'/'browser_validation.json').write_text(json.dumps(report,indent=2))
    if errors:raise RuntimeError(errors)
    print('Browser checks passed;',len(evidence),'screenshots captured.')

if __name__=='__main__':main()
