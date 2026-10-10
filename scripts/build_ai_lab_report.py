"""Build the reference-matched AI report, including all-page borders and code images."""
import json, math, textwrap
from pathlib import Path
from xml.sax.saxutils import escape
import pymupdf
from PIL import Image as PILImage, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, Image, Preformatted
from ai_lab_content import PAGES

ROOT=Path(__file__).resolve().parents[1];REF=Path(r'D:\Syed Sufyan\AI_REPORT.pdf')
ASSETS=ROOT/'output/ai_lab_assets';QA=ROOT/'tmp/pdfs';QA.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'output/pdf/NEC_Fee_Assist_AI_Lab_Report_SYED_SUFYAN.pdf';OUT.parent.mkdir(exist_ok=True)
W,H=595.32,841.92;M=72.024;BW=451.272
for name,file in [('T','times.ttf'),('TB','timesbd.ttf'),('TI','timesi.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
S={
 'p':ParagraphStyle('body',fontName='T',fontSize=12,leading=19.56,alignment=TA_JUSTIFY,spaceAfter=9),
 'h':ParagraphStyle('heading',fontName='TB',fontSize=12.96,leading=18,spaceBefore=4,spaceAfter=5),
 'title':ParagraphStyle('title',fontName='TB',fontSize=14.04,leading=19.56,alignment=TA_CENTER,spaceAfter=0),
 'bullet':ParagraphStyle('bullet',fontName='T',fontSize=12,leading=19.56,alignment=TA_JUSTIFY,leftIndent=18,firstLineIndent=0,spaceAfter=7),
 'cell':ParagraphStyle('cell',fontName='T',fontSize=10.5,leading=13.7),
 'headcell':ParagraphStyle('headcell',fontName='TB',fontSize=10.5,leading=13.7),
 'caption':ParagraphStyle('caption',fontName='T',fontSize=10.5,leading=14,alignment=TA_CENTER,spaceAfter=9),
 'code':ParagraphStyle('code',fontName='T',fontSize=11,leading=14,spaceAfter=9),
}
def para(t,style):return Paragraph(escape(str(t)).replace('\n','<br/>'),style)
def table(headers,rows):
    n=len(headers);widths=[BW/n]*n
    if n==2:widths=[BW*.34,BW*.66]
    if n==3:widths=[BW*.28,BW*.23,BW*.49]
    if n==4:widths=[BW*.105,BW*.335,BW*.21,BW*.35]
    if headers==['CH NO','TITLE','PAGE NO']:widths=[60,BW-125,65]
    t=Table([[para(v,S['headcell']) for v in headers]]+[[para(v,S['cell']) for v in row] for row in rows],colWidths=widths)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.HexColor('#777777')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    return t

def diagrams():
    """Vector diagrams with orthogonal, non-crossing connectors and Times labels."""
    for name in ['architecture','pipeline']:
        path=ASSETS/(name+'.pdf');c=canvas.Canvas(str(path),pagesize=(460,310))
        def box(x,y,w,h,lines):
            c.setFillColor(colors.HexColor('#f3f3f3'));c.setStrokeColor(colors.HexColor('#333333'));c.setLineWidth(.8);c.roundRect(x,y,w,h,4,fill=1,stroke=1)
            c.setFillColor(colors.black)
            for i,line in enumerate(lines):
                c.setFont('TB' if i==0 else 'T',10.5 if i==0 else 9.5)
                c.drawCentredString(x+w/2,y+h/2+(len(lines)-1)*6-12*i,line)
        def arrow(points):
            c.setStrokeColor(colors.black);c.setLineWidth(.8)
            for a,b in zip(points,points[1:]):c.line(*a,*b)
            x,y=points[-1];px,py=points[-2];a=math.atan2(y-py,x-px)
            for d in [-.45,.45]:c.line(x,y,x-5*math.cos(a+d),y-5*math.sin(a+d))
        if name=='architecture':
            box(90,252,280,43,['Presentation Layer','Portal pages + persistent assistant panel'])
            box(90,183,280,43,['Authenticated HTTP / Service Layer','Sessions, CSRF, roles and account ownership'])
            box(15,102,200,52,['Learned Agent / NLP Engine','Naive Bayes tasks + TF-IDF retrieval'])
            box(245,102,200,52,['Bounded Tool / Answer Services','Navigation, selection, guides and records'])
            box(90,17,280,52,['Independent SQLite Data Layer','Accounts, fees, payments, policies and task state'])
            arrow([(230,252),(230,226)])
            arrow([(160,183),(160,168),(115,168),(115,154)])
            arrow([(300,183),(300,168),(345,168),(345,154)])
            arrow([(215,128),(245,128)])
            arrow([(115,102),(115,84),(160,84),(160,69)])
            arrow([(345,102),(345,84),(300,84),(300,69)])
        else:
            box(100,257,260,40,['Authenticated question / task','Current account and session state'])
            box(100,193,260,40,['Understand the request','Learned task class or account / policy route'])
            box(15,107,200,56,['Task Plan','Role / owner checks + allowed tools'])
            box(245,107,200,56,['Grounded Answer','Owned account data or maintained policy'])
            box(100,16,260,57,['Portal Response','Navigate / select / guide or show answer','Persist exchange; user confirms changes'])
            arrow([(230,257),(230,233)])
            arrow([(155,193),(155,178),(115,178),(115,163)])
            arrow([(305,193),(305,178),(345,178),(345,163)])
            arrow([(115,107),(115,89),(160,89),(160,73)])
            arrow([(345,107),(345,89),(300,89),(300,73)])
        c.save()
        d=pymupdf.open(path);d[0].get_pixmap(matrix=pymupdf.Matrix(2,2)).save(ASSETS/(name+'.png'));d.close()

def frame(cv,number):
    cv.setStrokeColor(colors.black);cv.setLineWidth(.72);cv.rect(24.36,24.24,546.72,793.32)
    cv.setFont('T',11.04);cv.drawCentredString(W/2,39,str(number))

def wrapped_code(value):
    result=[]
    for line in value.splitlines():
        # Wrap at the measured Times width, preserving visible indentation.
        indent=' '*(len(line)-len(line.lstrip())+4)
        rest=line
        while pdfmetrics.stringWidth(rest,'T',11)>BW:
            cut=len(rest)
            while pdfmetrics.stringWidth(rest[:cut],'T',11)>BW:cut-=1
            split=rest.rfind(' ',0,cut)
            if split>len(indent):cut=split
            result.append(rest[:cut]);rest=indent+rest[cut:].lstrip()
        result.append(rest)
    return Preformatted('\n'.join(result),S['code'])

def flows(page):
    fs=[]
    if page['chapter']:
        fs.extend([para('CHAPTER '+str(page['chapter']),S['title']),para(page['title'],S['title']),Spacer(1,9)])
    for kind,value in page['blocks']:
        if kind in ('p','h'):fs.append(para(value,S[kind]))
        elif kind=='bullet':
            fs.append(Paragraph(escape(value),S['bullet'],bulletText='\u2022'))
        elif kind=='code':fs.append(wrapped_code(value))
        elif kind=='table':fs.extend([table(*value),Spacer(1,10)])
        elif kind in ('figure','diagram'):
            name,caption,*limits=value;path=ASSETS/(name+'.png')
            im=PILImage.open(path);iw,ih=im.size;maxh=limits[0] if limits else 235
            scale=min(BW/iw,maxh/ih)
            item=Image(str(path),width=iw*scale,height=ih*scale)
            fs.extend([item,Spacer(1,8),para(caption,S['caption'])])
    return fs

def draw(cv,fs,y=H-66):
    for f in fs:
        y-=f.getSpaceBefore();width,height=f.wrap(BW,H)
        x=M+(BW-width)/2 if isinstance(f,Image) else M
        f.drawOn(cv,x,y-height);y-=height+f.getSpaceAfter()
    if y<62:raise ValueError(f'Page {cv.getPageNumber()} overflows to {y:.1f}')
    return y

def main():
    diagrams()
    raw=QA/'ai_body.pdf';cv=canvas.Canvas(str(raw),pagesize=(W,H),pageCompression=1)
    cv.setAuthor('SYED SUFYAN');cv.setTitle('NEC Fee Assist - Artificial Intelligence Micro Project Report')
    # Cover is replaced with a minimally edited original-reference cover below.
    frame(cv,1);cv.showPage();frame(cv,2)
    draw(cv,[para('TABLE OF CONTENTS',S['title']),Spacer(1,18),table(['CH NO','TITLE','PAGE NO'],[
        ['1','INTRODUCTION','3'],['2','PROBLEM STATEMENT','5'],['3','MODULE DESCRIPTION','6'],
        ['4','ARCHITECTURE DIAGRAM','9'],['5','CODING & IMPLEMENTATION','12'],
        ['6','OUTPUT SCREENSHOTS','20'],['7','CONCLUSION','24']])])
    cv.showPage();layout=[]
    for number,page in enumerate(PAGES,3):
        frame(cv,number);bottom=draw(cv,flows(page));layout.append({'page':number,'bottom_y':round(bottom,2)})
        if number==26:
            cv.setFont('TB',12);cv.drawString(M,H-402,'RUBRICS :')
            cv.drawString(M,H-538,'RESULT:')
            draw(cv,[para('NEC Fee Assist has been implemented and locally tested as an AI-based fee assistance and task navigation system. The learned model, grounded answers, automatic page navigation, fee preparation, receipt discovery and guided workflows are operational. All 43 regression tests and seven browser workflow checks passed. The authored 40-request development diagnostic matched all expected outcomes; this is a local diagnostic rather than a general accuracy guarantee. Payments remain simulated and require the normal confirmation form.',S['p'])],H-548)
        cv.showPage()
    cv.save()
    has_reference=REF.exists()
    reference=pymupdf.open(REF if has_reference else ASSETS/'report_cover_template.pdf');doc=pymupdf.open(raw)
    rubric_source=reference if has_reference else pymupdf.open(ASSETS/'report_rubric_template.pdf')
    cover=pymupdf.open();cover.insert_pdf(reference,from_page=0,to_page=0)
    pg=cover[0]
    for rect in [(70,181,530,233),(72,270,530,290)]:pg.add_redact_annot(rect,fill=(1,1,1))
    pg.apply_redactions()
    for text,rect,font,size in [
        ('NEC Fee Assist: AI Task and Navigation System',(72,186,526,211),'CB',18),
        ('(Learned Task Classification and NLP-Based Fee Assistance)',(72,211,526,234),'CR',12.96),
        ('SYED SUFYAN 2403957610421048',(72,271,526,292),'CB',12.96)]:
        pg.insert_font(fontname=font,fontfile='C:/Windows/Fonts/'+('timesbd.ttf' if font=='CB' else 'times.ttf'))
        remaining=pg.insert_textbox(rect,text,fontname=font,fontsize=size,align=1)
        if remaining<0:raise ValueError('Cover text does not fit: '+text)
    doc.delete_page(0);doc.insert_pdf(cover,from_page=0,to_page=0,start_at=0)
    # Preserve the exact last-page assessment table from the reference.
    doc[25].show_pdf_page(pymupdf.Rect(72,420,524,507),rubric_source,25 if has_reference else 0,clip=pymupdf.Rect(72,420,524,507))
    # Replace diagram preview images with their vector originals for sharp printing.
    for index,name in [(7,'pipeline'),(8,'architecture')]:
        pg=doc[index];xref=pg.get_images()[0][0];rect=pg.get_image_rects(xref)[0]
        pg.delete_image(xref)
        vector=pymupdf.open(ASSETS/(name+'.pdf'));pg.show_pdf_page(rect,vector,0);vector.close()
    doc.set_toc([[1,p['title'],i+3] for i,p in enumerate(PAGES) if p['chapter']])
    doc.set_metadata({'title':'NEC Fee Assist - Artificial Intelligence Micro Project Report','author':'SYED SUFYAN',
                      'subject':'23CS55C - ARTIFICIAL INTELLIGENCE | 2403957610421048','creator':'NEC Fee Assist academic report'})
    doc.subset_fonts();doc.save(OUT,garbage=4,deflate=True)
    doc.close();reference.close();cover.close()
    if not has_reference:rubric_source.close()
    d=pymupdf.open(OUT);text='\n'.join(p.get_text() for p in d)
    assert len(d)==26
    assert 'SYED SUFYAN 2403957610421048' in text.replace('\u00a0',' ')
    assert 'Hari Muthu' not in text and 'PAN Card Fraud' not in text
    violations=[]
    for i,p in enumerate(d):
        pix=p.get_pixmap(colorspace=pymupdf.csGRAY)
        samples=pix.samples
        # Check all four margins visually at points outside the page content.
        for x,y in [(24,400),(571,400),(300,24),(300,817)]:
            assert min(samples[yy*pix.width+xx] for yy in range(y-1,y+2) for xx in range(x-1,x+2))<180, f'Page {i+1} missing border at {x},{y}'
        for b in p.get_text('dict')['blocks']:
            if 'lines' not in b:continue
            for line in b['lines']:
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    if span['text'].strip() and (x0<39 or x1>556 or y0<35 or y1>810):violations.append((i+1,span['text'],span['bbox']))
        p.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(QA/f'page-{i+1:02d}.png')
    assert not violations,violations
    # Review all pages through contact sheets, then full-size representative pages.
    for start in range(0,26,8):
        sheet=PILImage.new('RGB',(1200,900),'#d0d0d0');pen=ImageDraw.Draw(sheet)
        for j,i in enumerate(range(start,min(start+8,26))):
            im=PILImage.open(QA/f'page-{i+1:02d}.png');im.thumbnail((290,410))
            x=(j%4)*300+5;y=(j//4)*450+20;sheet.paste(im,(x,y));pen.text((x,y-16),str(i+1),fill='black')
        sheet.save(QA/f'contact-{start//8+1}.png')
    (ASSETS/'report_validation.json').write_text(json.dumps({'pages':26,'all_page_borders':True,
       'name':'SYED SUFYAN','roll':'2403957610421048','chapter_pages':d.get_toc(),'layout':layout,
       'code_screenshot_pages':[17,18],'output_screenshot_pages':[20,21,22]},indent=2))
    # Self-contained templates contain this student's report, never the friend's identity.
    for index,name in [(0,'report_cover_template.pdf'),(25,'report_rubric_template.pdf')]:
        template=pymupdf.open();template.insert_pdf(d,from_page=index,to_page=index)
        template.save(ASSETS/name,garbage=4,deflate=True);template.close()
    print('Created and validated 26 pages:',OUT);print('Layout:',layout)

if __name__=='__main__':main()
