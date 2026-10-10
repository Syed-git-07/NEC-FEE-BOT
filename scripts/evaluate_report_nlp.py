"""Small authored diagnostic evaluation for the revised report, using temporary data."""
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import service as s,nlp

CASES=[
 ('balance','What are my pending fees?'),('balance','Show my outstanding balance'),('balance','How much do I owe?'),('balance','remaining amount'),('balance','amount payable'),('balance','charges left to settle'),
 ('deadline','When should I pay tuition?'),('deadline','What is the due date for examination?'),('deadline','tuition deadline'),('deadline','last date for library fee'),('deadline','payment cutoff'),
 ('history','Show payment history'),('history','List transactions'),('history','Which fees have I already paid?'),('history','latest payment'),('history','completed payments'),
 ('receipt','Download my receipt'),('receipt','payment acknowledgement'),('receipt','proof of payment'),('receipt','invoice'),
 ('profile','What is my register number?'),('profile','my department'),('profile','student details'),('profile','name'),
 ('help','hi'),('help','hello'),('help','help'),
 ('policy','How do refunds work?'),('policy','Is there a late fine?'),('policy','What if a payment failed?'),('policy','Can I receive a scholarship?'),('policy','Are partial payments allowed?'),('policy','Can I pay by UPI?'),
 ('fallback','quantum banana nebula'),('fallback','weather forecast tomorrow'),('fallback','write a poem about mountains'),
]

def main():
    original=s.DB;records=[]
    with tempfile.TemporaryDirectory(prefix='fee_nlp_report_') as directory:
        s.DB=Path(directory)/'diagnostic.sqlite3';s.init()
        credentials=json.loads((s.DB.parent/'demo_credentials.json').read_text())['student']
        _,token=s.login(credentials['id'],credentials['password'])
        for expected,question in CASES:
            # Reset category context so each question is evaluated independently.
            with s.db() as c:c.execute("UPDATE sessions SET context='' WHERE token_hash=?",(s.digest(token),))
            result=s.chat(s.session(token),token,question)
            records.append({'question':question,'expected':expected,'predicted':result['intent'],'correct':result['intent']==expected,'score':result['score'],'source':result['source'],'answer':result['answer']})
        s.DB=original
    labels=sorted({expected for expected,_ in CASES});metrics=[]
    for label in labels:
        tp=sum(r['expected']==label and r['predicted']==label for r in records)
        fp=sum(r['expected']!=label and r['predicted']==label for r in records)
        fn=sum(r['expected']==label and r['predicted']!=label for r in records)
        precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0
        metrics.append({'intent':label,'support':sum(r['expected']==label for r in records),'correct':tp,'precision':precision,'recall':recall,'f1':f1})
    correct=sum(r['correct'] for r in records)
    report={'description':'Authored diagnostic set, not an independent production benchmark','questions':len(records),'correct':correct,'accuracy':correct/len(records),'macro_f1':sum(m['f1'] for m in metrics)/len(metrics),'per_intent':metrics,'records':records}
    path=Path(__file__).resolve().parents[1]/'output'/'nlp_diagnostic_evaluation.json';path.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
    print('Errors:',[(r['question'],r['expected'],r['predicted']) for r in records if not r['correct']])

if __name__=='__main__':main()
