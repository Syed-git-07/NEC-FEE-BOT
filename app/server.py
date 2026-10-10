"""Loopback-only academic server. Never reads the reference portal's configuration."""
import csv
import hmac
import io
import json
import mimetypes
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from . import service as s

STATIC=s.ROOT/'app'/'static'
LIMITS={}; LOCK=threading.Lock()

class Handler(BaseHTTPRequestHandler):
    server_version='FeeAssist'
    def log_message(self,format,*args): pass
    def send(self,status,body,kind='application/json',cookie=None,download=None):
        if kind=='application/json': body=json.dumps(body).encode()
        self.send_response(status)
        for name,value in {'Content-Type':kind,'Content-Length':str(len(body)),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}.items(): self.send_header(name,value)
        if cookie: self.send_header('Set-Cookie',cookie)
        if download: self.send_header('Content-Disposition','attachment; filename="'+download+'"')
        try:
            self.end_headers(); self.wfile.write(body)
        except ConnectionError:
            pass  # A browser navigation can close the connection after a committed request.
    def token(self):
        jar=SimpleCookie()
        try: jar.load(self.headers.get('Cookie',''))
        except Exception: return ''
        return jar['fee_session'].value if 'fee_session' in jar else ''
    def rate_limit(self,bucket,max_calls):
        key=(self.client_address[0],bucket); stamp=time.monotonic()
        with LOCK:
            calls=[t for t in LIMITS.get(key,[]) if t>stamp-60]
            if len(calls)>=max_calls: raise s.Error(429,'Too many requests. Try again shortly.')
            LIMITS[key]=calls+[stamp]
    def body(self):
        if self.headers.get_content_type()!='application/json': raise s.Error(415,'JSON request required.')
        try: size=int(self.headers.get('Content-Length','0'))
        except ValueError: raise s.Error(400,'Invalid request size.')
        if not 1<=size<=16384: raise s.Error(413,'Request is too large or empty.')
        try: data=json.loads(self.rfile.read(size))
        except (ValueError,UnicodeDecodeError): raise s.Error(400,'Invalid JSON request.')
        if not isinstance(data,dict): raise s.Error(400,'JSON object required.')
        return data
    def check_origin(self):
        port=self.server.server_address[1]
        valid={f'127.0.0.1:{port}',f'localhost:{port}'}
        if self.headers.get('Host','') not in valid: raise s.Error(403,'Invalid host.')
        origin=self.headers.get('Origin')
        if origin and origin not in {f'http://{host}' for host in valid}: raise s.Error(403,'Invalid request origin.')
        if self.headers.get('Sec-Fetch-Site')=='cross-site': raise s.Error(403,'Cross-site request denied.')
    def do_GET(self): self.dispatch('GET')
    def do_POST(self): self.dispatch('POST')
    def dispatch(self,method):
        try:
            self.check_origin(); path=urlparse(self.path).path
            self.rate_limit('requests',300)
            if method=='GET' and not path.startswith('/api/'):
                mapping={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/nec-logo.webp':'nec-logo.webp'}
                if path not in mapping: raise s.Error(404,'Page not found.')
                file=STATIC/mapping[path]
                return self.send(200,file.read_bytes(),mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
            if method=='POST': data=self.body()
            if path=='/api/login' and method=='POST':
                self.rate_limit('login',12)
                if set(data)!=set(['id','password']): raise s.Error(400,'Invalid sign-in fields.')
                result,token=s.login(data['id'],data['password'])
                return self.send(200,result,cookie='fee_session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=7200')
            token=self.token(); user=s.session(token)
            if method=='POST' and not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),user['csrf']): raise s.Error(403,'Invalid security token. Refresh and try again.')
            if method=='GET' and path=='/api/dashboard': return self.send(200,s.dashboard(user))
            if method=='GET' and path=='/api/chat/history': return self.send(200,s.chat_history(user))
            if method=='GET' and path.startswith('/api/receipt/'):
                pid=path.removeprefix('/api/receipt/')
                import re
                if not re.fullmatch(r'DEMO-[A-F0-9]{12}',pid): raise s.Error(404,'Receipt not found.')
                return self.send(200,s.receipt(user,pid),'application/pdf',download=pid+'.pdf')
            if method=='GET' and path=='/api/admin/export':
                s.require_admin(user); dashboard=s.dashboard(user)
                out=io.StringIO(newline=''); writer=csv.writer(out)
                writer.writerow(['Fee ID','Register number','Fee head','Ledger','Academic year','Amount INR','Due date','Status'])
                def safe(value):
                    v=str(value)
                    return "'"+v if v.startswith(('=','+','-','@','\t','\r','\n')) else v
                for fee in dashboard['fees']: writer.writerow([safe(fee[k]) for k in ['id','user_id','head','ledger','academic_year']]+[format(fee['amount']/100,'.2f'),fee['due_date'],fee['status']])
                return self.send(200,out.getvalue().encode('utf-8-sig'),'text/csv; charset=utf-8',download='fee-ledger.csv')
            if method=='POST' and path=='/api/logout':
                with s.db() as c: c.execute('DELETE FROM sessions WHERE token_hash=?',(s.digest(token),))
                return self.send(200,{'signed_out':True},cookie='fee_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
            if method=='POST' and path=='/api/payment': return self.send(200,s.pay(user,data))
            if method=='POST' and path=='/api/chat':
                self.rate_limit('chat',40)
                if set(data)!=set(['question']): raise s.Error(400,'Invalid question fields.')
                return self.send(200,s.chat(user,token,data['question']))
            if method=='POST' and path=='/api/admin/fee': return self.send(201,s.add_fee(user,data))
            if method=='POST' and path=='/api/admin/student': return self.send(201,s.add_student(user,data))
            if method=='POST' and path=='/api/admin/policy': return self.send(200,s.update_policy(user,data))
            raise s.Error(404,'Endpoint not found.')
        except s.Error as e: self.send(e.status,{'error':e.message})
        except Exception as e:
            import logging
            logging.exception('Request failed')
            self.send(500,{'error':'The request could not be completed.'})

def main():
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8765); args=parser.parse_args()
    s.init()
    print(f'NEC Fee Assist: http://127.0.0.1:{args.port}',flush=True)
    print('Local demo credentials: '+str(s.DB.parent/'demo_credentials.json'),flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

if __name__=='__main__': main()
