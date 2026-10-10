"""Generate and render the original academic report with deterministic pagination."""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape
import pymupdf
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph,Table,TableStyle,Image,Spacer,Preformatted
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Polygon
from reportlab.graphics import renderPDF,renderSVG
from report_content_revised import TITLE,NAME,ROLL,CHAPTERS,PAGES

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';QA=ROOT/'tmp'/'report_qa_revised';QA.mkdir(parents=True,exist_ok=True)
W,H=A4;M=55;BW=W-2*M
BLACK=colors.HexColor('#101010');LINE=colors.HexColor('#777777');BLUE=colors.HexColor('#163e72')

def diagram(name,nodes,edges,width=580,height=365):
    d=Drawing(width,height)
    def edge(a,b,label=''):
        ax,ay,aw,ah,_=nodes[a];bx,by,bw,bh,_=nodes[b]
        ac=(ax+aw/2,ay+ah/2);bc=(bx+bw/2,by+bh/2)
        dx=bc[0]-ac[0];dy=bc[1]-ac[1]
        if abs(dx)>abs(dy):
            start=(ax+aw if dx>=0 else ax,ac[1]);end=(bx if dx>=0 else bx+bw,bc[1])
        else:start=(ac[0],ay+ah if dy>=0 else ay);end=(bc[0],by if dy>=0 else by+bh)
        if name=='er_model' and a=='users' and b=='chat':
            route=[(ax,ac[1]),(185,ac[1]),(185,bc[1]),(bx+bw,bc[1])]
            for left,right in zip(route,route[1:]):d.add(Line(*left,*right,strokeColor=LINE,strokeWidth=1.1))
            start,end=route[-2:]
        else:
            d.add(Line(*start,*end,strokeColor=LINE,strokeWidth=1.1))
        import math
        angle=math.atan2(end[1]-start[1],end[0]-start[0]);sz=6
        p1=(end[0]-sz*math.cos(angle-.45),end[1]-sz*math.sin(angle-.45));p2=(end[0]-sz*math.cos(angle+.45),end[1]-sz*math.sin(angle+.45))
        d.add(Polygon([end[0],end[1],*p1,*p2],fillColor=LINE,strokeColor=LINE))
        if label:d.add(String((start[0]+end[0])/2+5,(start[1]+end[1])/2+5,label,fontName='Helvetica',fontSize=8,fillColor=BLACK))
    for a,b,*label in edges:edge(a,b,label[0] if label else '')
    for x,y,w,h,text in nodes.values():
        d.add(Rect(x,y,w,h,rx=5,ry=5,fillColor=colors.HexColor('#f4f6f9'),strokeColor=BLUE,strokeWidth=.9))
        lines=text.split('\n');cy=y+h/2+(len(lines)-1)*6.5
        for i,line in enumerate(lines):d.add(String(x+w/2,cy-i*13,line,textAnchor='middle',fontName='Helvetica-Bold' if i==0 else 'Helvetica',fontSize=10 if i==0 else 9,fillColor=BLACK))
    directory=OUT/'diagrams';directory.mkdir(exist_ok=True)
    renderPDF.drawToFile(d,str(directory/(name+'.pdf')))
    renderSVG.drawToFile(d,str(directory/(name+'.svg')))
    pdf=pymupdf.open(directory/(name+'.pdf'));pdf[0].get_pixmap(matrix=pymupdf.Matrix(2.5,2.5)).save(directory/(name+'.png'));pdf.close()

def make_diagrams():
    diagram('retrieval_grounding',{
     'query':(20,290,230,55,'Student policy question\nNormalize + unigram / bigram features'),
     'corpus':(330,290,230,55,'Current policy corpus\nTitle + body / document frequencies'),
     'rank':(150,180,280,65,'Normalized TF-IDF cosine ranking\nScore every maintained policy'),
     'answer':(25,55,230,75,'Score at least 0.16\nReturn selected policy body\nShow named policy source'),
     'fallback':(330,55,230,75,'Score below 0.16\nReturn fallback\nNo unsupported financial answer')},[('query','rank'),('corpus','rank'),('rank','answer'),('rank','fallback')])
    diagram('dialogue_context',{
     'first':(165,290,250,60,'Category-specific question\nTuition balance or deadline'),
     'context':(165,185,250,65,'Session category = tuition\nRetained after balance / deadline'),
     'follow':(15,45,235,85,'Supported follow-up: When?\nReuse tuition category\nRead owned tuition due date'),
     'change':(325,45,235,85,'New category or unrelated intent\nReplace or clear category\nAvoid stale fee context')},[('first','context'),('context','follow'),('context','change')])
    diagram('architecture',{
     'browser':(130,285,320,65,'Presentation layer\nHTML / CSS / JavaScript | student + admin'),
     'http':(130,195,320,65,'HTTP boundary\nSession / CSRF / validation / loopback'),
     'services':(35,95,225,70,'Service layer\nFees / payments / receipts / admin'),
     'nlp':(320,95,225,70,'NLP engine\nRules + TF-IDF / grounded answers'),
     'sqlite':(165,5,250,60,'SQLite persistence\nIndependent project database')},[('browser','http'),('http','services'),('http','nlp'),('services','sqlite'),('nlp','sqlite')])
    diagram('nlp_pipeline',{
     'auth':(185,300,210,50,'Authenticated question\nUser + session category'),
     'intent':(185,218,210,55,'Validate and route intent\nRules / exemplar similarity'),
     'account':(25,125,220,60,'Account retrieval\nOwned fees / dates / payments'),
     'policy':(335,125,220,60,'Policy retrieval\nTF-IDF cosine / threshold'),
     'answer':(165,20,250,65,'Grounded response\nAnswer + source + protected links')},[('auth','intent'),('intent','account'),('intent','policy'),('account','answer'),('policy','answer')])
    diagram('use_cases',{
     'student':(15,240,130,70,'Student\nAuthenticated owner'),
     'admin':(15,60,130,70,'Administrator\nAccounts role'),
     'student_tasks':(225,220,335,105,'Student operations\nOverview / pending fees / demo payment\nHistory / PDF receipt / profile\nFee assistant / grounded answers'),
     'admin_tasks':(225,40,335,105,'Administrator operations\nStudents / fee allocation / ledger\nTransactions / export CSV\nPolicy editing / audit log')},[('student','student_tasks'),('admin','admin_tasks')])
    diagram('data_flow',{
     'browser':(15,155,150,70,'Browser actors\nStudent / admin'),
     'service':(235,155,160,70,'Authorized services\nOwner and role checks'),
     'db':(435,265,130,65,'SQLite records\nFees / payments'),
     'policy':(435,155,130,65,'Policy store\nMaintained text'),
     'outputs':(435,40,130,65,'Output files\nPDF / CSV')},[('browser','service','JSON'),('service','db'),('service','policy'),('service','outputs')])
    diagram('payment_flow',{
     'request':(155,310,270,45,'Selected fees + attempt key'),
     'validate':(155,230,270,55,'Validate owner and request\nBEGIN IMMEDIATE / replay check'),
     'completed':(15,110,180,75,'Completed\nInsert items + settlements\nMark fee rows paid'),
     'failed':(220,110,145,75,'Failed / cancelled\nRecord attempt\nKeep fees pending'),
     'replay':(395,110,170,75,'Identical replay\nReturn existing result\nReject changed replay'),
     'finish':(160,10,260,55,'Commit and return\nReceipt only for completed result')},[('request','validate'),('validate','completed'),('validate','failed'),('validate','replay'),('completed','finish'),('failed','finish'),('replay','finish')])
    diagram('er_model',{
     'users':(220,305,145,55,'users\nid PK / role / hash'),
     'sessions':(15,220,155,55,'sessions\ntoken_hash PK\nuser_id FK'),
     'fees':(220,200,145,65,'fees\nid PK / user_id FK\namount / due / status'),
     'payments':(415,210,150,65,'payments\nid PK / user_id FK\nattempt key UNIQUE'),
     'items':(415,100,150,65,'payment_items\npayment_id + fee_id PK\namount snapshot'),
     'settle':(220,90,145,65,'settlements\nfee_id PK\npayment_id FK'),
     'chat':(15,100,155,65,'chat_messages\nid PK / user_id FK\nquestion / answer / source'),
     'policies':(15,0,155,60,'policies\nid PK\ntitle / content'),
     'audit':(300,0,195,55,'audit\nid PK / actor / action / time')},[('users','sessions','1:n'),('users','fees','1:n'),('users','payments','1:n'),('users','chat','1:n'),('payments','items','1:n'),('fees','items','1:n'),('fees','settle','1:0..1'),('payments','settle','1:n')],height=380)

def styles(size=12):
    return {
     'p':ParagraphStyle('body',fontName='Times-Roman',fontSize=size,leading=size*1.35,alignment=TA_JUSTIFY,spaceAfter=10,textColor=BLACK),
     'h':ParagraphStyle('subheading',fontName='Times-Bold',fontSize=12.5,leading=17,spaceBefore=3,spaceAfter=9,textColor=BLACK),
     'title':ParagraphStyle('page_title',fontName='Times-Bold',fontSize=14,leading=19,alignment=TA_CENTER,spaceAfter=10,textColor=BLACK),
     'caption':ParagraphStyle('caption',fontName='Times-Roman',fontSize=10.5,leading=14,alignment=TA_CENTER,spaceAfter=13,textColor=BLACK),
     'cell':ParagraphStyle('cell',fontName='Times-Roman',fontSize=10,leading=12.8,textColor=BLACK),
     'headcell':ParagraphStyle('headcell',fontName='Times-Bold',fontSize=10,leading=12.8,textColor=BLACK),
     'code':ParagraphStyle('code',fontName='Courier',fontSize=9.2,leading=13,spaceAfter=15,textColor=BLACK),
    }

def para(text,st):return Paragraph(escape(text).replace('\n','<br/>'),st)
def body_flows(page,size=12):
    st=styles(size);flows=[]
    if page['chapter'] and page.get('chapter_start',False):
        flows.append(para('CHAPTER '+str(page['chapter']),st['title']))
        flows.append(para(CHAPTERS[page['chapter']],st['title']))
    flows.append(para(page['title'],st['h']))
    for kind,value in page['blocks']:
        if kind in ('p','h'):
            if not page['chapter'] and kind=='p':
                left=ParagraphStyle('reference',parent=st['p'],alignment=0)
                flows.append(para(value,left))
            else:flows.append(para(value,st[kind]))
        elif kind=='code':flows.append(Preformatted(value,st['code']))
        elif kind=='table':
            headers,rs=value;n=len(headers)
            widths=[BW/n]*n
            if n==2:widths=[BW*.35,BW*.65]
            if page['title'].startswith('8.7'):widths=[BW*.21,BW*.38,BW*.41]
            data=[[para(v,st['headcell']) for v in headers]]+[[para(str(v),st['cell']) for v in row] for row in rs]
            t=Table(data,colWidths=widths,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f0f0f0')),('GRID',(0,0),(-1,-1),.5,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            flows.extend([t,Spacer(1,15)])
        elif kind=='figure':
            name,caption=value;path=OUT/('screenshots' if page['chapter']==9 else 'diagrams')/(name+'.png')
            im=PILImage.open(path);iw,ih=im.size
            maxheight=340 if page['chapter']==9 else 240
            if name in ('09_mobile_profile','receipt_preview'):maxheight=510
            scale=min(BW/iw,maxheight/ih)
            image=Image(str(path),width=iw*scale,height=ih*scale);image.hAlign='CENTER'
            flows.extend([image,Spacer(1,12),para(caption,st['caption'])])
    return flows

def measure(flows):return sum(f.wrap(BW,H)[1]+f.getSpaceBefore()+f.getSpaceAfter() for f in flows)
def draw_flows(cv,flows,y):
    for f in flows:
        y-=f.getSpaceBefore()
        width,height=f.wrap(BW,H)
        x=M+(BW-width)/2 if isinstance(f,Image) else M
        f.drawOn(cv,x,y-height);y-=height+f.getSpaceAfter()
    return y

def frame(cv,page):
    cv.setStrokeColor(LINE);cv.setLineWidth(.6);cv.rect(24,24,W-48,H-48)
    cv.setFont('Times-Roman',11);cv.setFillColor(BLACK);cv.drawRightString(W-57,44,str(page-1))

def cover(cv):
    st=styles();title=Paragraph(TITLE,ParagraphStyle('cover_title',fontName='Times-Bold',fontSize=16,leading=24,alignment=TA_CENTER))
    tw,th=title.wrap(BW,H);title.drawOn(cv,M,H-72-th)
    y=H-190
    def center(text,font,size,dy):
        nonlocal y
        cv.setFont(font,size);cv.drawCentredString(W/2,y,text);y-=dy
    center('23CS23E - AI TOOLS FOR NATURAL LANGUAGE PROCESSING','Times-Roman',12,55)
    center('Submitted by','Times-BoldItalic',13,32)
    center(NAME+' - '+ROLL,'Times-Bold',13,56)
    center('In partial fulfillment for the award of the degree of','Times-Italic',12,31)
    center('BACHELOR OF ENGINEERING','Times-BoldItalic',14,32)
    center('in','Times-Italic',12,32)
    center('COMPUTER SCIENCE AND ENGINEERING','Times-BoldItalic',14,20)
    logo=ROOT/'app'/'static'/'college-emblem.jpeg'
    cv.drawImage(str(logo),W/2-45,y-117,width=90,height=114,mask='auto');y-=148
    center('NATIONAL ENGINEERING COLLEGE','Times-Bold',14,24)
    center('(An Autonomous Institution affiliated to Anna University, Chennai)','Times-Bold',11,32)
    center('K.R.NAGAR, KOVILPATTI - 628503','Times-Bold',13,24)
    center('OCTOBER - 2026','Times-Bold',13,24)

def certificate(cv):
    st=styles();y=H-78
    for text in ['NATIONAL ENGINEERING COLLEGE','(An Autonomous Institution affiliated to Anna University, Chennai)','K.R.NAGAR, KOVILPATTI - 628503']:
        flow=para(text,st['title']);_,height=flow.wrap(BW,H);flow.drawOn(cv,M,y-height);y-=height+7
    y-=25;flow=para('BONAFIDE CERTIFICATE',st['title']);_,height=flow.wrap(BW,H);flow.drawOn(cv,M,y-height);y-=height+38
    text='This is to certify that this project report, "'+TITLE+'", is the bonafide work of '+NAME+' ('+ROLL+') who carried out the project work under my supervision.'
    y=draw_flows(cv,[para(text,st['p'])],y)
    cv.setFont('Times-Bold',12);cv.drawString(M,290,'Course Instructor/Guide')

def toc(cv,pages):
    st=styles();flow=para('TABLE OF CONTENTS',st['title']);_,hh=flow.wrap(BW,H);flow.drawOn(cv,M,H-80-hh)
    entries=[];seen=set()
    for physical,page in enumerate(pages,4):
        ch=page['chapter']
        if ch and ch not in seen:entries.append([str(ch),CHAPTERS[ch],str(physical-1)]);seen.add(ch)
        elif not ch:entries.append(['','REFERENCES',str(physical-1)])
    data=[[para(x,st['headcell']) for x in ['CH NO','TITLE','PAGE NO']]]+[[para(x,st['cell']) for x in row] for row in entries]
    t=Table(data,colWidths=[55,BW-117,62]);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.7,BLACK),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9)]));_,height=t.wrap(BW,H);t.drawOn(cv,M,H-130-height)

def expand_screenshots(pages):
    result=[]
    for page in pages:
        if page['chapter']!=9:result.append(page);continue
        figures=[b for b in page['blocks'] if b[0]=='figure'];text=[b for b in page['blocks'] if b[0]=='p']
        for i,fig in enumerate(figures):
            result.append({'chapter':9,'title':page['title']+(' (continued)' if i else ''),'blocks':[fig]+text})
    return result

def markdown(pages):
    lines=['# '+TITLE,'','**'+NAME+' - '+ROLL+'**','','23CS23E - AI TOOLS FOR NATURAL LANGUAGE PROCESSING','','Bachelor of Engineering in Computer Science and Engineering','','National Engineering College | October 2026','']
    previous=None
    for page in pages:
        if page['chapter']!=previous:
            lines+=['## '+('Chapter '+str(page['chapter'])+' - '+CHAPTERS[page['chapter']] if page['chapter'] else 'References'),'']
        lines+=['### '+page['title'],'']
        previous=page['chapter']
        for kind,v in page['blocks']:
            if kind=='p':lines+=[v,'']
            elif kind=='h':lines+=['#### '+v,'']
            elif kind=='code':lines+=['```text',v,'```','']
            elif kind=='table':
                headers,rs=v;lines+=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rs]+['']
            elif kind=='figure':lines+=['!['+v[1]+']('+('screenshots/' if page['chapter']==9 else 'diagrams/')+v[0]+'.png)',v[1],'']
    (OUT/'NEC_Fee_Assist_Report_Editable.md').write_text('\n'.join(lines),encoding='utf-8')

def main():
    make_diagrams()
    receipt=pymupdf.open(OUT/'pdf'/'Sample_Demo_Payment_Receipt.pdf');receipt[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(OUT/'screenshots'/'receipt_preview.png');receipt.close()
    pages=PAGES
    previous=None
    for page in pages:
        page['chapter_start']=bool(page['chapter'] and page['chapter']!=previous)
        previous=page['chapter']
    path=OUT/'pdf'/'NEC_Fee_Portal_Project_Report_SYED_SUFYAN_M.pdf'
    cv=canvas.Canvas(str(path),pagesize=A4,pageCompression=1);cv.setTitle(TITLE);cv.setAuthor(NAME);cv.setSubject('23CS23E academic project report')
    cover(cv);cv.showPage();frame(cv,2);certificate(cv);cv.showPage();frame(cv,3);toc(cv,pages);cv.showPage()
    checks=[]
    for physical,page in enumerate(pages,4):
        flows=body_flows(page,12);height=measure(flows);size=12
        if height>H-135:
            flows=body_flows(page,11.5);height=measure(flows);size=11.5
        if height>H-135:raise ValueError(f'Page {physical} overflows: {page["title"]} height {height:.1f}')
        frame(cv,physical)
        if page['chapter_start']:
            key='chapter-'+str(page['chapter'])
            cv.bookmarkPage(key);cv.addOutlineEntry('Chapter '+str(page['chapter'])+': '+CHAPTERS[page['chapter']],key)
        bottom=draw_flows(cv,flows,H-58)
        checks.append({'page':physical,'title':page['title'],'body_font':size,'bottom_y':round(bottom,2)})
        cv.showPage()
    cv.save();markdown(PAGES)
    pdf=pymupdf.open(path)
    for i,page in enumerate(pdf):page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(QA/f'page-{i+1:02d}.png')
    text='\n'.join(page.get_text() for page in pdf)
    assert NAME in text and ROLL in text
    assert 'Sarathi Kamal' not in text and 'SWATHI' not in text
    assert len(pdf)==len(pages)+3
    assert len(pdf)==30
    chapter_pages=[]
    for i,pdfpage in enumerate(pdf):
        import re
        matches=re.findall(r'(?m)^CHAPTER (\d+)\s*$',pdfpage.get_text())
        if matches:chapter_pages.append({'physical_page':i+1,'chapter':int(matches[0])})
    assert [x['chapter'] for x in chapter_pages]==list(range(1,11)),chapter_pages
    (OUT/'report_validation.json').write_text(json.dumps({'pages':len(pdf),'chapter_heading_pages':chapter_pages,'page_layout':checks,'author':NAME,'register_number':ROLL,'nlp_diagnostics':{'questions':36,'correct_routes':30}},indent=2))
    print('Created',len(pdf),'pages:',path)
    # Contact sheets preserve page order for full-document layout review.
    images=sorted(QA.glob('page-*.png'))
    for start in range(0,len(images),8):
        sheet=PILImage.new('RGB',(1200,1740),'#e3e6eb')
        from PIL import ImageDraw
        draw=ImageDraw.Draw(sheet)
        for j,imagepath in enumerate(images[start:start+8]):
            im=PILImage.open(imagepath);im.thumbnail((285,810));x=(j%4)*300+7;y=(j//4)*870+25
            sheet.paste(im,(x,y));draw.text((x,y-18),f'Page {start+j+1}',fill='black')
        sheet.save(QA/f'contact-{start//8+1}.png')
    pdf.close()

if __name__=='__main__':main()
