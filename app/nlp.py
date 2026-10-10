"""Offline, explainable unigram/bigram TF-IDF retrieval and account intent routing.

Similarity is a ranking score, never a calibrated probability. The chatbot has no
mutation tools, executes no generated SQL and calls no external model service.
"""
import math
import re
from collections import Counter

STOP = set('a an the is are i my me of to for in on do does can please tell what how much when this that and it'.split())
EXAMPLES = {
 'balance': ['pending fees outstanding balance unpaid amount dues payable total remaining', 'what fees do i owe how much should i pay'],
 'deadline': ['deadline due date last date when pay tuition examination hostel transport'],
 'history': ['payment history transaction payments paid completed payment status latest payment'],
 'receipt': ['download receipt invoice acknowledgement proof payment receipt'],
 'profile': ['profile name roll register number department semester student details'],
 'help': ['hello hi help capabilities questions assist'],
}

def tokens(text):
    return [t for t in re.findall(r'[a-z0-9]+', text.lower()) if t not in STOP]

def features(text):
    ts = tokens(text)
    return Counter(ts + [' '.join(ts[i:i+2]) for i in range(len(ts)-1)])

def rank(query, documents):
    if not documents:
        return []
    docs = [features(d) for d in documents]
    df = Counter(term for doc in docs for term in doc)
    idf = {t: math.log((len(docs)+1)/(freq+1))+1 for t,freq in df.items()}
    def vector(bag):
        v = {t:(1+math.log(n))*idf[t] for t,n in bag.items() if t in idf}
        norm = math.sqrt(sum(w*w for w in v.values())) or 1
        return {t:w/norm for t,w in v.items()}
    q = vector(features(query))
    return sorted([(sum(w*q.get(t,0) for t,w in vector(d).items()),i) for i,d in enumerate(docs)], reverse=True)

def classify(question, context=''):
    q = question.lower().strip()
    # Explicit policy and fee-type questions should go to the maintained knowledge base.
    if re.search(r'\b(late|fine|refund\w*|scholarship\w*|installment\w*|instalment\w*|partial|payment methods?|payment modes?|card|upi|failed|cancel\w*|support|contact|secure|privacy)\b',q):
        return 'policy', 1.0
    if q in ('when','when?','due date?','last date?') and context:
        return 'deadline', 1.0
    if re.search(r'receipt|invoice|acknowledg|proof of payment',q): return 'receipt',1.0
    if re.search(r'deadline|due date|last date|when.*pay|payment cutoff',q): return 'deadline',1.0
    if re.search(r'pending|outstanding|balance|owe|unpaid|dues|how much|charges left',q): return 'balance',1.0
    if re.search(r'history|transaction|already paid|payment status|paid fees|latest payment',q): return 'history',1.0
    if re.search(r'profile|roll|register number|department|semester|my name',q) or q=='name': return 'profile',1.0
    if q in ('hi','hello','help'): return 'help',1.0
    docs, labels = [],[]
    for intent,examples in EXAMPLES.items():
        for example in examples: docs.append(example); labels.append(intent)
    score,index = rank(q,docs)[0]
    return (labels[index],score) if score>=0.28 else ('policy',score)

def category(question,previous=''):
    q=question.lower()
    for head in ['tuition','examination','hostel','transport','library']:
        if head in q or (head=='examination' and 'exam' in q): return head
    if q.strip() in ('when','when?','due date?','last date?'): return previous
    return ''
