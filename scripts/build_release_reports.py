#!/usr/bin/env python3
"""Generate standalone version history PDF/PPTX summaries from data/releases.json."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

ROOT = Path(__file__).resolve().parents[1]
releases = json.loads((ROOT / 'data' / 'releases.json').read_text(encoding='utf-8'))
out = ROOT / 'public' / 'reports'
out.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(UnicodeCIDFont('HYGothic-Medium'))
body = ParagraphStyle('ko', fontName='HYGothic-Medium', fontSize=10.5, leading=17, textColor=colors.HexColor('#243347'), spaceAfter=8)
heading = ParagraphStyle('heading', parent=body, fontSize=19, leading=27, textColor=colors.HexColor('#12243b'), spaceAfter=13)
sub = ParagraphStyle('sub', parent=body, fontSize=13, leading=20, textColor=colors.HexColor('#b07a25'), spaceBefore=10, spaceAfter=6)
def box(slide, left, top, width, height, text, font_size=17, color=(239,244,250), bold=False):
    shape = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = shape.text_frame
    frame.word_wrap = True
    frame.clear()
    p = frame.paragraphs[0]
    p.text = text
    p.font.name = 'Malgun Gothic'
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = RGBColor(*color)
    return shape

for entry in releases['entries']:
    version = entry['version']
    pdf_path = out / f'WoW_KR_Radar_v{version}_History.pdf'
    story = [
        Paragraph('WoW KR Radar | 개발 버전 히스토리', heading),
        Paragraph(f"V{escape(version)} · {escape(entry['date'])} · {escape(entry['type'])}", sub),
        Paragraph(escape(entry['title']), sub),
        Paragraph(escape(entry['summary']), body),
        HRFlowable(width='100%', thickness=1, color=colors.HexColor('#d5dce5')),
        Spacer(1, 12),
        Paragraph('주요 변경사항', sub),
    ]
    story.extend(Paragraph('• ' + escape(x), body) for x in entry['changes'])
    story.append(Paragraph('운영 참고사항', sub))
    story.extend(Paragraph('• '+escape(x), body) for x in entry['notes'])
    story.append(Spacer(1, 12))
    story.append(Paragraph('원본 코드 변경 이력은 GitHub 커밋 기록에서 확인할 수 있습니다. 이 문서는 변경사항을 재구성한 요약 자료이며 기존 배포 상태를 복원하는 백업은 아닙니다.', body))
    SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=45, rightMargin=45, topMargin=50, bottomMargin=50, title=f'WoW KR Radar v{version} History').build(story)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    bg = (13,23,39)
    gold = (225,177,99)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(*bg)
    box(slide,0.8,0.65,11.5,0.5,'WOW KR RADAR  |  DEVELOPMENT HISTORY',16,gold,True)
    box(slide,0.8,1.5,11.5,0.8,'V'+version+' · '+entry['title'],31,bold=True)
    box(slide,0.8,2.6,11.5,1.6,entry['summary'],22)
    box(slide,0.8,5.95,11.5,0.7,entry['date']+'  ·  '+entry['type'],14,gold)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(*bg)
    box(slide,0.8,0.5,11.8,0.7,'주요 개발 변경사항',27,gold,True)
    for idx, item in enumerate(entry['changes'][:6]):
        box(slide,0.95,1.45+idx*0.83,11.5,0.75, f'{idx+1:02d}   {item}',17)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(*bg)
    box(slide,0.8,0.5,11.7,0.7,'운영 상태 및 참고사항',26,gold,True)
    for idx, item in enumerate(entry['notes']):
        box(slide,0.95,1.6+idx*1.05,11.4,0.95,'• '+item,18)
    box(slide,0.95,5.95,11.4,0.65,'과거 버전의 변경사항 요약. 코드 복원용 백업은 아닙니다.',14,(146,166,187))
    prs.save(out / f'WoW_KR_Radar_v{version}_History.pptx')
print('Generated',len(releases['entries']),'PDF/PPTX release summary pairs')
