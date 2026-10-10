"""Offline learned task planner with role-scoped, allow-listed UI tools.

Multinomial Naive Bayes learns word/phrase likelihoods from labelled examples.
Cosine evidence and model separation gate execution; unknown tasks abstain.
No tool executes SQL, arbitrary URLs, scripts, payments or administrator writes.
"""
import math
import re
from collections import Counter, defaultdict
from . import nlp

EXAMPLES = {
 'fees': ['open pending fees', 'take me to my fees', 'go to unpaid fees page', 'navigate to fee selection', 'show the pending fees screen', 'view my outstanding fees page'],
 'history': ['open transaction history', 'take me to payment history', 'go to transactions page', 'show my payment history', 'view previous payments', 'navigate to history'],
 'profile': ['open my profile', 'take me to my account details', 'go to profile page', 'show my student profile', 'navigate to my personal details', 'view profile screen'],
 'dashboard': ['open dashboard', 'take me home', 'go to overview', 'navigate to account overview', 'back to dashboard', 'show the home page'],
 'pay': ['help me pay tuition', 'pay my examination fee', 'prepare payment for library', 'select transport fees for payment', 'pay all my fees now', 'open payment page', 'I want to pay tuition', 'take me to payment page'],
 'receipt': ['download my receipt', 'get my latest receipt', 'find my payment invoice', 'open completed payment receipt', 'help me download payment acknowledgement', 'download proof of payment'],
 'allotment': ['open fee allotment', 'take me to assign a fee', 'go to fee allocation form', 'help me assign fees', 'navigate to allotment', 'allocate a new fee'],
 'students': ['open student directory', 'take me to students', 'go to add student page', 'help me add a student', 'show student list', 'navigate to student management'],
 'ledger': ['open fee ledger', 'take me to ledger', 'go to fees register', 'export fee ledger', 'help me export csv', 'navigate to ledger export'],
 'policies': ['open policy editor', 'take me to fee policies', 'go to policy management', 'help me edit a policy', 'navigate to policies', 'update policy text'],
 'audit': ['open audit log', 'take me to activity history', 'go to audit records', 'view administrator actions', 'navigate to audit trail', 'show audit screen'],
 'answer': ['how much are my pending fees', 'when is tuition due', 'what is my register number', 'what happens if payment fails', 'how do refunds work', 'are partial payments allowed', 'what is my balance', 'is there a late fine', 'can I pay by UPI', 'hello', 'payment methods', 'explain privacy policy'],
}
PAGES = {
 'student': {'dashboard', 'fees', 'history', 'profile', 'assistant'},
 'admin': {'dashboard', 'allotment', 'students', 'ledger', 'history', 'policies', 'audit', 'assistant'},
}
LABELS = {'fees':'Pending fees','history':'Transaction history','profile':'My profile',
 'dashboard':'Overview','allotment':'Fee allotment','students':'Students',
 'ledger':'Fee ledger','policies':'Fee policies','audit':'Audit log'}
VOCAB=set(); COUNTS={}; TOTALS={}
for label, examples in EXAMPLES.items():
    counts=Counter()
    for example in examples: counts.update(nlp.features(example))
    COUNTS[label]=counts; TOTALS[label]=sum(counts.values()); VOCAB.update(counts)

def predict(question):
    """Return learned label and cosine evidence, or abstain from UI actions."""
    # An information question must not trigger navigation just because it names a page.
    if not re.search(r'^(?:please\s+)?(?:open|take|go|navigate|show|view|prepare|pay|guide|select|download|get|find|export|edit|add|assign|allocate|help|settle|back|return)\b|^(?:i (?:want|need|would like)|(?:could|can|would|will) you|how (?:do|can) i)\b',question.lower().strip()):
        return None
    bag=nlp.features(question)
    known={t:n for t,n in bag.items() if t in VOCAB}
    if not known:return None
    scores={label:sum(n*math.log((counts[t]+1)/(TOTALS[label]+len(VOCAB)))
                            for t,n in known.items()) for label,counts in COUNTS.items()}
    ordered=sorted(scores,key=scores.get,reverse=True)
    label=ordered[0]
    documents=[];labels=[]
    for target,examples in EXAMPLES.items():
        documents.extend(examples);labels.extend([target]*len(examples))
    ranked=nlp.rank(question,documents)
    evidence=max((score for score,i in ranked if labels[i]==label),default=0)
    margin=(scores[label]-scores[ordered[1]])/max(1,sum(known.values()))
    if label=='answer' or evidence<0.18 or margin<0.035:return None
    return label,round(evidence,4)

def result(answer,actions=None,guide=None,score=1.0,links=None):
    return {'answer':answer,'intent':'agent','source':'Fee Assist agent',
            'score':score,'links':links or [],'actions':actions or [],'guide':guide}

def navigate(page):return {'type':'navigate','page':page,'label':LABELS.get(page,'Fee assistant')}

def handle(user,question,stored,fees,payments):
    q=question.strip().lower(); state={}
    identifiers=re.findall(r'\b\d{16}\b',q)
    if user['role']=='student' and (any(uid!=user['id'] for uid in identifiers) or re.search(r'\b(?:another|other) student\b',q)):
        return result('I can only work with your signed-in account.'),state
    # Reject external navigation and requests for executable or authority-changing tools.
    if re.search(r'https?://|javascript:|file:|\b(?:sql|scripts?|passwords?|tokens?|secrets?|delete|erase|impersonate)\b',q):
        return result('I can open portal pages and guide fee tasks. Choose a task within this portal.'),state
    if q in {'cancel','cancel task','stop','stop task'}:
        return result('Task cancelled.',[{'type':'clear_selection'}]),state
    if q in {'next','continue','next step','what next','what next?'}:
        if stored.get('task')=='guide' and stored.get('page') in PAGES[user['role']]:
            guide=stored['guide']; step=stored.get('step',0)+1
            if step>=len(guide['steps']):return result('Complete the action in the page form when ready.'),state
            return result(guide['steps'][step],[navigate(stored['page'])],guide),{**stored,'step':step}
        if stored.get('task')=='payment':
            pending=[f for f in fees if f['status']=='pending' and f['id'] in stored.get('fee_ids',[])]
            if not pending:return result('Those fees are already settled. Opening transaction history.',[navigate('history')]),state
            guide={'title':'Review payment','steps':['Review the selected fees.','Choose Proceed to demo payment.','Review the outcome and confirm in the payment form.']}
            return result('Review the selected fees, then proceed to demo payment.',
                          [navigate('fees'),{'type':'select_fees','fee_ids':[f['id'] for f in pending]}],guide),stored
        if stored.get('task')=='receipt':
            completed=[p for p in payments if p['status']=='completed']
            if completed:
                item=completed[0]
                return result('Your latest completed-payment receipt is ready.',[navigate('history')],
                              links=[{'label':'Download latest receipt','url':'/api/receipt/'+item['id']}]),state
            return result('A receipt is available after a completed demo payment.',[navigate('history')]),state
        return result('What would you like to do? You can open a page, prepare a fee payment or find a receipt.'),state
    prediction=predict(question)
    if not prediction:return None,stored
    task,score=prediction
    if task=='pay':
        if user['role']!='student':return result('Fee payments are available in a student account.'),state
        categories=[name for name in ['tuition','examination','hostel','transport','library']
                    if name in q or (name=='examination' and re.search(r'\bexam\b',q))]
        category=categories[0] if len(categories)==1 else ''
        pending=[f for f in fees if f['status']=='pending' and (not categories or any(name in f['head'].lower() for name in categories))]
        if not pending:
            return result('There are no pending '+(category+' ' if category else '')+'fees to select.',[navigate('fees')],score=score),state
        ids=[f['id'] for f in pending]
        guide={'title':'Pay '+(category+' fee' if category else 'pending fees'),
               'steps':['Review the selected fees.','Proceed to demo payment.','Confirm the outcome in the payment form.','Find the receipt in Transaction history.']}
        answer='Selected '+', '.join(f['head'] for f in pending)+' for review. Confirm the payment in the payment form.'
        return result(answer,[navigate('fees'),{'type':'select_fees','fee_ids':ids}],guide,score),{'task':'payment','fee_ids':ids}
    if task=='receipt':
        if user['role']!='student':return result('Open Transactions to choose a student payment receipt.',[navigate('history')]),state
        completed=[p for p in payments if p['status']=='completed']
        if not completed:
            guide={'title':'Get a receipt','steps':['Complete a demo payment.','Open Transaction history.','Choose Download receipt.']}
            return result('No completed-payment receipt is available yet.',[navigate('history')],guide,score),{'task':'receipt'}
        item=completed[0]
        return result('Your latest completed-payment receipt is ready.',[navigate('history')],score=score,
                      links=[{'label':'Download latest receipt','url':'/api/receipt/'+item['id']}]),state
    if task not in PAGES[user['role']]:
        return result('That page requires an administrator account.'),state
    guide=None
    if task in {'allotment','students','policies','ledger'}:
        steps={'allotment':['Choose a student.','Enter the fee details.','Review and choose Assign fee.'],
               'students':['Enter the student details.','Set a temporary password.','Review and choose Add student.'],
               'policies':['Choose a policy.','Edit the title and content.','Review and choose Save policy.'],
               'ledger':['Find the required student or fee.','Choose Export CSV to download the ledger.']}
        guide={'title':LABELS[task],'steps':steps[task]}
    if guide:state={'task':'guide','page':task,'guide':guide,'step':0}
    return result('Opening '+LABELS[task]+'.',[navigate(task)],guide,score),state
