"""Build the readable PDF from the editable Markdown engineering report.
Run from any directory: python tools/build_report.py
"""
from pathlib import Path
import re, html
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
FONT=Path('/usr/share/fonts/truetype/dejavu')
if not FONT.exists():
    from matplotlib import get_data_path
    FONT=Path(get_data_path())/'fonts/ttf'
pdfmetrics.registerFont(TTFont('Nodi',str(FONT/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('NodiBold',str(FONT/'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('Nodi',normal='Nodi',bold='NodiBold',italic='Nodi',boldItalic='NodiBold')
style=getSampleStyleSheet()
for s in style.byName.values():s.fontName='Nodi'
style['Normal'].fontSize=9;style['Normal'].leading=13;style['Normal'].spaceAfter=7
style['Title'].fontName='NodiBold';style['Title'].fontSize=29;style['Title'].leading=35;style['Title'].textColor=colors.HexColor('#143b42');style['Title'].spaceAfter=18
for n,sz in [('Heading1',19),('Heading2',13),('Heading3',10)]:
    style[n].fontName='NodiBold';style[n].fontSize=sz;style[n].leading=sz+5;style[n].textColor=colors.HexColor('#143b42');style[n].spaceBefore=12;style[n].spaceAfter=9
style.add(ParagraphStyle('Cell',parent=style['Normal'],fontSize=7.4,leading=10,spaceAfter=0))
style.add(ParagraphStyle('Caption',parent=style['Normal'],fontSize=7.5,leading=10,textColor=colors.HexColor('#536369')))
def inline(t):
    t=html.escape(t)
    t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<link href="{m[2] if "://" in m[2] else "https://github.com/DavidBorsky/NODI-Robotic-Alarm-Clock/blob/main/"+m[2]}" color="#147b83">{m[1]}</link>',t)
    t=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',t)
    t=re.sub(r'`([^`]+)`',r'<font name="Nodi">\1</font>',t)
    return t
lines=(ROOT/'Documentation/engineering_report.md').read_text().splitlines();story=[];i=0
while i<len(lines):
    line=lines[i].strip()
    if not line:i+=1;continue
    if line=='<!-- pagebreak -->':story.append(PageBreak());i+=1;continue
    if line.startswith('!['):
        m=re.match(r'!\[([^]]*)\]\(([^)]+)\)',line);p=(ROOT/'Documentation'/m[2]).resolve()
        from PIL import Image as PI
        w,h=PI.open(p).size;mw=495;mh=285;r=min(mw/w,mh/h)
        story.extend([Image(str(p),width=w*r,height=h*r),Paragraph(inline(m[1]),style['Caption'])]);i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            row=[v.strip() for v in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r'[:\- ]+',v) for v in row):rows.append(row)
            i+=1
        n=len(rows[0]);widths=[495/n]*n
        if n==2:widths=[160,335]
        if n==3:widths=[130,155,210]
        if n==4:widths=[90,120,140,145]
        tbl=Table([[Paragraph(inline(v),style['Cell']) for v in r] for r in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebed')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#c7d1d0')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([tbl,Spacer(1,10)]);continue
    if line.startswith('#'):
        level=len(line)-len(line.lstrip('#'));s='Title' if level==1 else 'Heading'+str(min(level-1,3));story.append(Paragraph(inline(line[level:].strip()),style[s]));i+=1;continue
    if line.startswith('- '):story.append(Paragraph('• '+inline(line[2:]),style['Normal']));i+=1;continue
    text=[]
    while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','![','<!--','- ')):
        text.append(lines[i].strip());i+=1
    if text:story.append(Paragraph(inline(' '.join(text)),style['Normal']))
    else:i+=1

def footer(c,doc):
    c.saveState();c.setStrokeColor(colors.HexColor('#93adae'));c.line(48,42,547,42);c.setFont('Nodi',7)
    c.setFillColor(colors.HexColor('#536369'));c.drawString(48,30,'NODI / Engineering design challenge / Rev A / Computational prototype')
    c.drawRightString(547,30,str(doc.page));c.restoreState()
pdf=ROOT/'Documentation/NODI_Engineering_Design_Report.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),rightMargin=50,leftMargin=50,topMargin=45,bottomMargin=58,title='NODI — Engineering Design Report',author='David Borsky — AI-assisted design study')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(pdf.relative_to(ROOT))
