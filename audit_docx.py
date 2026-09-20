from docx import Document
from docx.oxml.ns import qn

PATH = r'C:\Users\Sunil\Documents\EB1A\Academic\IEEE\IEEE_conf_PQSF_MCP_ICSCSA_sha1\Manuscript-3-Final.docx'
doc = Document(PATH)

print('=== PAGE LAYOUT ===')
for i, sec in enumerate(doc.sections):
    sp = sec._sectPr
    cols_el = sp.find(qn('w:cols'))
    type_el = sp.find(qn('w:type'))
    col_num = cols_el.get(qn('w:num'), '1') if cols_el is not None else '1'
    col_spc = cols_el.get(qn('w:space'), '?') if cols_el is not None else '?'
    sec_type = type_el.get(qn('w:val'), 'nextPage') if type_el is not None else 'body'
    try:
        t = sec.top_margin.inches
        l = sec.left_margin.inches
        b = sec.bottom_margin.inches
        r2 = sec.right_margin.inches
        pw = sec.page_width.inches
        ph = sec.page_height.inches
        print(f'  Section {i}: {sec_type}, cols={col_num}(gap={col_spc}), '
              f'page={pw:.2f}x{ph:.2f}in, T={t:.3f} B={b:.3f} L={l:.3f} R={r2:.3f}')
    except Exception as e:
        print(f'  Section {i}: {sec_type}, cols={col_num}(gap={col_spc}) -- margin read error: {e}')

print()
print('=== INLINE SECTION BREAKS ===')
found = 0
for p in doc.paragraphs:
    pPr = p._p.find(qn('w:pPr'))
    if pPr is not None:
        isp = pPr.find(qn('w:sectPr'))
        if isp is not None:
            t = isp.find(qn('w:type'))
            c = isp.find(qn('w:cols'))
            typ = t.get(qn('w:val')) if t is not None else 'nextPage'
            col = c.get(qn('w:num'), '1') if c is not None else '1'
            found += 1
            print(f'  -> style={p.style.name!r}, type={typ}, cols={col}')
            print(f'     text={p.text[:60]!r}')
print(f'  Total inline breaks: {found}')

print()
print('=== PARAGRAPH STYLE SUMMARY ===')
from collections import Counter
style_counts = Counter(p.style.name for p in doc.paragraphs)
for style, count in style_counts.most_common():
    print(f'  {count:3d} x {style!r}')

print()
print('=== FONT SAMPLE (first run, paras 0-14) ===')
for i, p in enumerate(doc.paragraphs[:15]):
    if not p.runs:
        continue
    r = p.runs[0]
    fname = r.font.name or '(inherited)'
    fsize = r.font.size.pt if r.font.size else None
    print(f'  [{i:02d}] {p.style.name!r:22s} font={fname!r} {fsize}pt | {p.text[:50]!r}')

print()
print('=== TABLES ===')
for i, t in enumerate(doc.tables):
    nrows = len(t.rows)
    ncols = len(t.columns)
    h = [c.text.strip()[:18] for c in t.rows[0].cells] if t.rows else []
    print(f'  Table {i+1}: {nrows}r x {ncols}c  headers={h}')

print()
print('=== LAST 6 PARAGRAPHS (references check) ===')
for p in doc.paragraphs[-6:]:
    print(f'  {p.style.name!r:15s} | {p.text[:80]!r}')
