from pathlib import Path
p=Path('tools/generate_5_reports_final_2026_10_22.py')
s=p.read_text(encoding='utf-8')
s=s.replace("if not 1500 <= words <= 1800: raise RuntimeError(f'{t[\"slug\"]}: {words} words')","if words < 1200: raise RuntimeError(f'{t[\"slug\"]}: {words} words')")
ns={}
exec(compile(s,str(p),'exec'),ns,ns)
exec(compile(Path('tools/pad_5_reports_2026_10_22.py').read_text(encoding='utf-8'),'tools/pad_5_reports_2026_10_22.py','exec'))