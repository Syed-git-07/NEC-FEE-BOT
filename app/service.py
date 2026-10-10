import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from . import nlp, agent
from .contact import SUPPORT_EMAIL, SUPPORT_PHONE, SUPPORT_LINE

ROOT=Path(__file__).resolve().parents[1]
DB=Path(os.environ.get('FEE_ASSIST_DB',str(ROOT/'data'/'fee_assist.sqlite3')))
IST=timezone(timedelta(hours=5,minutes=30))

class Error(Exception):
    def __init__(self,status,message): self.status=status; self.message=message

def now(): return datetime.now(IST).isoformat(timespec='seconds')
def money(paise): return 'INR '+format(paise/100,',.2f')
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def password_hash(password,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()
def password_ok(password,stored): return hmac.compare_digest(password_hash(password,stored.split(':')[0]),stored)

@contextmanager
def db():
    c=sqlite3.connect(DB,timeout=10,isolation_level=None)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    try: yield c
    finally: c.close()

def rows(c,sql,args=()): return [dict(r) for r in c.execute(sql,args)]
def public_user(row): return {k:row[k] for k in ('id','name','role','department','semester')}
def audit(c,actor,action,target): c.execute('INSERT INTO audit(actor,action,target,created_at) VALUES(?,?,?,?)',(actor,action,str(target),now()))

POLICIES=[
 ('Payment methods','This academic demonstration uses simulated payments. No money is transferred and no UPI, card or bank details are collected. A real payment gateway is not connected.'),
 ('Late payment and fines','The demonstration does not add automatic late fines. The due date indicates the last date recorded for each assigned fee. Any real college fine must be confirmed by the accounts office.'),
 ('Refund requests','Refunds are not processed through this demonstration. Contact the college accounts office with your register number and payment receipt for an authorized decision. No refund eligibility is assumed.'),
 ('Scholarship assistance','Scholarship eligibility and concessions must be verified by the college accounts office. The demonstration has no scholarship decision engine and does not automatically reduce assigned fees.'),
 ('Receipt download','After a completed simulated payment, open Transaction history and choose Download receipt. Receipts are available only to the account owner and administrators.'),
 ('Failed or cancelled payments','Failed and cancelled simulated payments remain in Transaction history. They do not settle fees or generate payment receipts. You may retry an unpaid fee with a new attempt.'),
 ('Partial payments and installments','This demonstration accepts the full assigned amount of each selected fee. You can select individual fees, but cannot partially pay one fee. Installment permission must be confirmed with the accounts office.'),
 ('Accounts support',f'For fee payment support, payment disputes, fee corrections and official policies, contact the college accounts office. Email: {SUPPORT_EMAIL}. Phone: {SUPPORT_PHONE}.'),
 ('Privacy and account security','Account balances and payment receipts require sign-in. Students can access their own records. The fee assistant retrieves account data and policies without changing fees or initiating payments.'),
]

def init():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with db() as c:
        c.executescript((ROOT/'app'/'schema.sql').read_text())
        # Additive migration: preserve existing accounts, payments and conversation rows.
        for table,column,definition in [('sessions','agent_state',"TEXT NOT NULL DEFAULT '{}'"),
                                        ('chat_messages','actions',"TEXT NOT NULL DEFAULT '[]'"),
                                        ('chat_messages','links',"TEXT NOT NULL DEFAULT '[]'"),
                                        ('chat_messages','guide',"TEXT NOT NULL DEFAULT 'null'")]:
            if column not in {r['name'] for r in c.execute('PRAGMA table_info('+table+')')}:
                c.execute('ALTER TABLE '+table+' ADD COLUMN '+column+' '+definition)
        if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]:
            c.execute('UPDATE users SET name=? WHERE id=? AND name=?',('SYED SUFYAN','2403957610421048','SYED SUFYAN M'))
            legacy='Contact the college accounts office for payment disputes, fee corrections and official policies. No telephone number or email address is invented in this demonstration.'
            c.execute('UPDATE policies SET content=?,updated_at=? WHERE title=? AND content=?',(dict(POLICIES)['Accounts support'],now(),'Accounts support',legacy))
            return
        credentials={'student':{'id':'2403957610421048','password':secrets.token_urlsafe(12)},'admin':{'id':'admin','password':secrets.token_urlsafe(14)}}
        c.execute('BEGIN IMMEDIATE')
        for uid,name,role,pwd in [ ('2403957610421048','SYED SUFYAN','student',credentials['student']['password']),('admin','Accounts Administrator','admin',credentials['admin']['password']) ]:
            c.execute('INSERT INTO users(id,name,role,password_hash) VALUES(?,?,?,?)',(uid,name,role,password_hash(pwd)))
        # Illustrative academic data; not an official college fee schedule.
        for head,ledger,amount,due in [('Tuition','Academic',4500000,'2026-10-20'),('Examination','Academic',250000,'2026-10-15'),('Library','Academic',150000,'2026-10-25'),('Transport','Services',1200000,'2026-11-05')]:
            c.execute('INSERT INTO fees(user_id,head,ledger,academic_year,amount,due_date) VALUES(?,?,?,?,?,?)',('2403957610421048',head,ledger,'2026-2027',amount,due))
        for title,content in POLICIES: c.execute('INSERT INTO policies(title,content,updated_at) VALUES(?,?,?)',(title,content,now()))
        c.commit()
        path=DB.parent/'demo_credentials.json'
        path.write_text(json.dumps(credentials,indent=2))
        try: os.chmod(path,0o600)
        except OSError: pass

def login(uid,password):
    if not isinstance(uid,str) or not isinstance(password,str) or len(uid)>80 or len(password)>256: raise Error(400,'Invalid sign-in details.')
    with db() as c:
        user=c.execute('SELECT * FROM users WHERE id=?',(uid.strip(),)).fetchone()
        # Run a password derivation even when the identifier is absent.
        good=password_ok(password,user['password_hash']) if user else password_ok(password,'0'*32+':'+'0'*64)
        if not user or not good: raise Error(401,'Incorrect ID or password.')
        token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32)
        c.execute('DELETE FROM sessions WHERE expires<?',(int(time.time()),))
        c.execute('INSERT INTO sessions(token_hash,user_id,csrf,expires) VALUES(?,?,?,?)',(digest(token),uid.strip(),csrf,int(time.time())+7200))
        audit(c,uid,'sign_in','session')
        return {'user':public_user(user),'csrf':csrf},token

def session(token):
    with db() as c:
        r=c.execute('SELECT u.*,s.csrf,s.context,s.agent_state FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?',(digest(token or ''),int(time.time()))).fetchone()
        if not r: raise Error(401,'Please sign in.')
        return dict(r)

def require_admin(user):
    if user['role']!='admin': raise Error(403,'Administrator access required.')

def dashboard(user):
    with db() as c:
        clause='' if user['role']=='admin' else 'WHERE user_id=?'
        args=() if user['role']=='admin' else (user['id'],)
        fees=rows(c,'SELECT * FROM fees '+clause+' ORDER BY due_date,id',args)
        payments=rows(c,'SELECT p.*,u.name FROM payments p JOIN users u ON u.id=p.user_id '+('' if user['role']=='admin' else 'WHERE p.user_id=?')+' ORDER BY p.created_at DESC,p.rowid DESC LIMIT 200',args)
        stats={'assigned':sum(f['amount'] for f in fees),'paid':sum(f['amount'] for f in fees if f['status']=='paid'),'pending':sum(f['amount'] for f in fees if f['status']=='pending'),'students':c.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0] if user['role']=='admin' else 1}
        return {'user':public_user(user),'csrf':user['csrf'],'fees':fees,'payments':payments,'stats':stats,'policies':rows(c,'SELECT * FROM policies ORDER BY id'),'students':rows(c,"SELECT id,name,department,semester FROM users WHERE role='student' ORDER BY name") if user['role']=='admin' else [],'audit':rows(c,'SELECT * FROM audit ORDER BY id DESC LIMIT 100') if user['role']=='admin' else []}

def pay(user,data):
    if user['role']!='student': raise Error(403,'Student account required.')
    if set(data)!=set(['fee_ids','outcome','idempotency_key']): raise Error(400,'Invalid payment fields.')
    ids=data.get('fee_ids'); key=data.get('idempotency_key'); outcome=data.get('outcome')
    if not isinstance(ids,list) or not 1<=len(ids)<=30 or any(type(i) is not int for i in ids) or len(ids)!=len(set(ids)): raise Error(400,'Select valid fees.')
    if not isinstance(key,str) or not re_key(key) or outcome not in ('completed','failed','cancelled'): raise Error(400,'Invalid payment attempt.')
    req=digest(json.dumps([sorted(ids),outcome]))
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        try:
            old=c.execute('SELECT * FROM payments WHERE user_id=? AND idempotency_key=?',(user['id'],key)).fetchone()
            if old:
                if old['request_hash']!=req: raise Error(409,'Payment attempt differs from the original.')
                c.rollback(); return dict(old)
            fs=rows(c,'SELECT * FROM fees WHERE id IN ('+','.join('?' for _ in ids)+') AND user_id=?',(*ids,user['id']))
            if len(fs)!=len(ids): raise Error(404,'Fee not found.')
            if any(f['status']!='pending' for f in fs): raise Error(409,'A selected fee has already been paid.')
            amount=sum(f['amount'] for f in fs); pid='DEMO-'+secrets.token_hex(6).upper()
            c.execute('INSERT INTO payments(id,user_id,amount,status,created_at,idempotency_key,request_hash) VALUES(?,?,?,?,?,?,?)',(pid,user['id'],amount,outcome,now(),key,req))
            for f in fs:
                c.execute('INSERT INTO payment_items VALUES(?,?,?)',(pid,f['id'],f['amount']))
                if outcome=='completed':
                    c.execute('INSERT INTO settlements VALUES(?,?)',(f['id'],pid))
                    c.execute("UPDATE fees SET status='paid' WHERE id=?",(f['id'],))
            audit(c,user['id'],'payment_'+outcome,pid)
            result=dict(c.execute('SELECT * FROM payments WHERE id=?',(pid,)).fetchone())
            c.commit(); return result
        except Exception: c.rollback(); raise

def re_key(key):
    import re
    return bool(re.fullmatch(r'[a-zA-Z0-9_-]{16,80}',key))

def add_fee(user,data):
    require_admin(user)
    if set(data)!=set(['user_id','head','ledger','amount','due_date','academic_year']): raise Error(400,'Invalid fee fields.')
    for k in ['user_id','head','ledger','due_date','academic_year']:
        if not isinstance(data[k],str) or not data[k].strip() or len(data[k])>100: raise Error(400,'Complete all fee fields.')
    if type(data['amount']) is not int or not 1<=data['amount']<=100000000: raise Error(400,'Enter a valid amount.')
    try: date.fromisoformat(data['due_date'])
    except ValueError: raise Error(400,'Enter a valid due date.')
    with db() as c:
        u=c.execute("SELECT id FROM users WHERE id=? AND role='student'",(data['user_id'],)).fetchone()
        if not u: raise Error(404,'Student not found.')
        c.execute('BEGIN IMMEDIATE')
        cursor=c.execute('INSERT INTO fees(user_id,head,ledger,amount,due_date,academic_year) VALUES(?,?,?,?,?,?)',tuple(data[k].strip() if isinstance(data[k],str) else data[k] for k in ['user_id','head','ledger','amount','due_date','academic_year']))
        audit(c,user['id'],'fee_assigned',cursor.lastrowid); c.commit()
        return {'id':cursor.lastrowid}

def add_student(user,data):
    require_admin(user)
    if set(data)!=set(['id','name','department','semester','password']): raise Error(400,'Invalid student fields.')
    if not all(isinstance(data[k],str) and data[k].strip() and len(data[k])<=100 for k in ['id','name','department']): raise Error(400,'Complete student details.')
    if not isinstance(data['password'],str) or not 12<=len(data['password'])<=128: raise Error(400,'Password must contain 12 to 128 characters.')
    if type(data['semester']) is not int or not 1<=data['semester']<=8: raise Error(400,'Semester must be 1 to 8.')
    with db() as c:
        try:
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT INTO users(id,name,department,semester,password_hash,role) VALUES(?,?,?,?,?,?)',(data['id'].strip(),data['name'].strip(),data['department'].strip(),data['semester'],password_hash(data['password']),'student'))
            audit(c,user['id'],'student_created',data['id']); c.commit()
        except sqlite3.IntegrityError: c.rollback(); raise Error(409,'Student ID already exists.')
    return {'created':True}

def update_policy(user,data):
    require_admin(user)
    if set(data)!=set(['id','title','content']) or type(data['id']) is not int or not all(isinstance(data[k],str) and data[k].strip() and len(data[k])<=limit for k,limit in [('title',100),('content',5000)]): raise Error(400,'Invalid policy details.')
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        cursor=c.execute('UPDATE policies SET title=?,content=?,updated_at=? WHERE id=?',(data['title'].strip(),data['content'].strip(),now(),data['id']))
        if not cursor.rowcount: c.rollback(); raise Error(404,'Policy not found.')
        audit(c,user['id'],'policy_updated',data['id']); c.commit()
    return {'updated':True}

def chat(user,token,question):
    if not isinstance(question,str) or not question.strip() or len(question)>1000: raise Error(400,'Enter a question of up to 1000 characters.')
    # Session identity and state come from the server, never from language input.
    user=session(token)
    data=dashboard(user)
    plan,agent_state=agent.handle(user,question,json.loads(user['agent_state']),data['fees'],data['payments'])
    if plan is not None:
        with db() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('UPDATE sessions SET agent_state=?,context=? WHERE token_hash=?',
                      (json.dumps(agent_state),'',digest(token)))
            c.execute('INSERT INTO chat_messages(user_id,question,answer,intent,source,score,created_at,actions,guide,links) VALUES(?,?,?,?,?,?,?,?,?,?)',
                      (user['id'],question.strip(),plan['answer'],plan['intent'],plan['source'],plan['score'],now(),json.dumps(plan['actions']),json.dumps(plan['guide']),json.dumps(plan['links'])))
            audit(c,user['id'],'agent_task',json.dumps({'actions':plan['actions'],'task':agent_state.get('task','navigation')}))
            c.commit()
        return plan
    question=question.strip(); intent,score=nlp.classify(question,user['context'])
    cat=nlp.category(question,user['context']); source='Account records'; links=[]
    with db() as c:
        fs=rows(c,'SELECT * FROM fees WHERE user_id=? ORDER BY due_date',(user['id'],))
        selected=[f for f in fs if not cat or cat in f['head'].lower()]
        pending=[f for f in selected if f['status']=='pending']
        if intent=='balance':
            answer=('Your '+(cat+' ' if cat else '')+'outstanding balance is '+money(sum(f['amount'] for f in pending))+'.')
            if pending: answer+='\n'+'\n'.join(f['head']+': '+money(f['amount']) for f in pending)
            if cat and not selected: answer='No '+cat+' fee is assigned to your account.'
        elif intent=='deadline':
            answer='\n'.join(f['head']+': due '+f['due_date'] for f in pending) if pending else 'There are no unpaid '+(cat+' ' if cat else '')+'fees in your account.'
        elif intent in ('history','receipt'):
            ps=rows(c,'SELECT * FROM payments WHERE user_id=? ORDER BY created_at DESC,rowid DESC LIMIT 5',(user['id'],))
            if intent=='receipt': ps=[p for p in ps if p['status']=='completed']
            answer='\n'.join(p['id']+' - '+money(p['amount'])+' - '+p['status'] for p in ps) or ('No completed payment receipt is available.' if intent=='receipt' else 'No payment attempts are recorded yet.')
            links=[{'label':'Receipt '+p['id'],'url':'/api/receipt/'+p['id']} for p in ps if p['status']=='completed']
        elif intent=='profile': answer=user['name']+'\nRegister number: '+user['id']+'\nDepartment: '+user['department']+'\nSemester: '+str(user['semester'])
        elif intent=='help':
            answer='I can check your pending fees, due dates, payment history and receipts, or answer fee policy questions.'; source='Assistant help'
        else:
            policies=rows(c,'SELECT * FROM policies ORDER BY id')
            # Expand a payment-mode term to its maintained policy topic, not a new answer.
            import re
            retrieval_question=question+' payment methods' if re.search(r'\b(upi|card|payment modes?)\b',question.lower()) else question
            matches=nlp.rank(retrieval_question,[p['title']+' '+p['content'] for p in policies])
            score,index=matches[0] if matches else (0,0)
            if score>=0.16:
                p=policies[index]; answer=p['content']; source='Policy: '+p['title']; intent='policy'
            else:
                answer='I could not find a reliable answer. Ask about pending fees, due dates, payments or receipts, or contact the accounts office.\n'+SUPPORT_LINE; source='No matching record'; intent='fallback'
        c.execute('BEGIN IMMEDIATE')
        c.execute('UPDATE sessions SET context=? WHERE token_hash=?',(cat if intent in ('balance','deadline') else '',digest(token)))
        c.execute('INSERT INTO chat_messages(user_id,question,answer,intent,source,score,created_at) VALUES(?,?,?,?,?,?,?)',(user['id'],question,answer,intent,source,score,now()))
        c.commit()
        return {'answer':answer,'intent':intent,'source':source,'score':round(score,4),'links':links}

def chat_history(user):
    with db() as c:
        history=rows(c,'SELECT question,answer,intent,source,score,created_at,actions,guide,links FROM chat_messages WHERE user_id=? ORDER BY id DESC LIMIT 30',(user['id'],))[::-1]
    for item in history:
        item['actions']=json.loads(item['actions']); item['guide']=json.loads(item['guide']); item['links']=json.loads(item['links'])
    return history

def receipt(user,pid):
    with db() as c:
        p=c.execute('SELECT p.*,u.name,u.department,u.semester FROM payments p JOIN users u ON u.id=p.user_id WHERE p.id=?',(pid,)).fetchone()
        if not p or (user['role']!='admin' and p['user_id']!=user['id']): raise Error(404,'Receipt not found.')
        if p['status']!='completed': raise Error(409,'Receipt is available only for completed payments.')
        items=rows(c,'SELECT f.head,f.academic_year,pi.amount FROM payment_items pi JOIN fees f ON f.id=pi.fee_id WHERE pi.payment_id=?',(pid,))
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from xml.sax.saxutils import escape
    b=io.BytesIO()
    doc=SimpleDocTemplate(b,pagesize=A4,rightMargin=40,leftMargin=40,topMargin=135,bottomMargin=115,title='Demonstration payment receipt '+pid)
    normal=ParagraphStyle('receipt_body',fontName='Helvetica',fontSize=10,leading=15)
    heading=ParagraphStyle('receipt_heading',fontName='Helvetica-Bold',fontSize=17,leading=22)
    story=[Paragraph('PAYMENT RECEIPT',heading),Spacer(1,20)]
    meta=[]
    for label,value in [('Receipt number',pid),('Student',p['name']),('Register number',p['user_id']),('Department',p['department']),('Payment date',p['created_at']),('Status','Completed (simulated)')]:
        meta.append([Paragraph(escape(label),normal),Paragraph(escape(str(value)),normal)])
    info=Table(meta,colWidths=[135,380]);info.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),10),('LEFTPADDING',(0,0),(-1,-1),0)]))
    story.extend([info,Spacer(1,22)])
    table=Table([['Fee head','Academic year','Amount (INR)']]+[[Paragraph(escape(i['head']),normal),Paragraph(escape(i['academic_year']),normal),format(i['amount']/100,',.2f')] for i in items]+[['Total','',format(p['amount']/100,',.2f')]],colWidths=[265,120,130],repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9efff')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#ced7e6')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('ALIGN',(-1,1),(-1,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story.append(table)
    def furniture(cv,document):
        cv.saveState();cv.setFillColorRGB(.12,.37,1);cv.rect(35,725,525,80,fill=1,stroke=0)
        cv.setFillColorRGB(1,1,1);cv.setFont('Helvetica-Bold',18);cv.drawString(55,774,'National Engineering College')
        cv.setFont('Helvetica',11);cv.drawString(55,749,'NEC Fee Assist | Demonstration receipt')
        cv.setFillColorRGB(.08,.12,.2);cv.setFont('Helvetica',9)
        cv.drawString(40,94,SUPPORT_LINE)
        cv.linkURL('mailto:'+SUPPORT_EMAIL,(95,92,230,105),relative=0)
        cv.linkURL('tel:'+SUPPORT_PHONE,(267,92,345,105),relative=0)
        cv.drawString(40,75,'Academic demonstration. No money transferred. Not an official college receipt.')
        cv.drawRightString(550,54,'Page '+str(document.page));cv.restoreState()
    doc.build(story,onFirstPage=furniture,onLaterPages=furniture)
    return b.getvalue()
