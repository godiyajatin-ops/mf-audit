#!/usr/bin/env python
"""Auditable Stage A3 TER/BER extraction for the frozen 16-pair universe."""
from __future__ import annotations
import csv, hashlib, json, re, sys, tempfile
from collections import defaultdict
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from openpyxl import load_workbook

ROOT=Path(__file__).resolve().parents[1]
SOURCE_DIR=ROOT/'data'/'raw_docs'/'probe'/'ter'
CSV_PATH=ROOT/'data'/'manual'/'scheme_facts.csv'
AS_OF=date(2026,9,30)
SOURCE_FILES=('HDFCMF_SCHEMES_TER_30-09-2026.xls','TER-2026-2027.xlsx','ter-of-mf-schemes.xlsx','TotalExpenseRatio2026-2027.xlsx','TotalExpenseRatioSep2026.xlsx')
PRIORITY={n:i for i,n in enumerate(('ter-of-mf-schemes.xlsx','HDFCMF_SCHEMES_TER_30-09-2026.xls','TER-2026-2027.xlsx','TotalExpenseRatio2026-2027.xlsx','TotalExpenseRatioSep2026.xlsx'))}

def norm(v): return re.sub(r'[^a-z0-9]','',str(v or '').casefold())
def parse_date(v,epoch):
    if isinstance(v,datetime): return v.date()
    if isinstance(v,date): return v
    if isinstance(v,(int,float)):
        try: return epoch.from_excel(v).date()
        except Exception: return None
    for fmt in ('%d/%m/%Y','%d-%b-%Y','%d-%B-%Y','%Y-%m-%d','%d-%m-%Y'):
        try: return datetime.strptime(str(v or '').strip(),fmt).date()
        except ValueError: pass
    return None
def number(v):
    if v is None or (isinstance(v,str) and not v.strip()): return None
    if isinstance(v,str): v=v.strip().replace(',','').removesuffix('%')
    try: return float(v)
    except (ValueError,TypeError): return None
def open_book(path):
    # HDFC's .xls file has XLSX/ZIP bytes despite its extension; read in memory unchanged.
    if path.suffix.lower()=='.xls': return load_workbook(BytesIO(path.read_bytes()),read_only=True,data_only=True)
    return load_workbook(path,read_only=True,data_only=True)
def header_info(ws):
    for rn,row in enumerate(ws.iter_rows(values_only=True),1):
        vals=list(row); labels=[str(x or '').strip().casefold() for x in vals]
        name=next((i for i,x in enumerate(labels) if 'scheme name' in x),None)
        day=next((i for i,x in enumerate(labels) if 'date' in x and ('ter' in x or 'dd/mm' in x)),None)
        ber=[i for i,x in enumerate(labels) if 'base expense ratio' in x or re.search(r'\bber\b',x)]
        ter=[i for i,x in enumerate(labels) if 'total ter' in x or x in ('ter (%)','total ter (%)')]
        if name is not None and day is not None and ber and ter: return rn,vals,name,day,ber,ter
    return None
def plan_columns(header,bers,ters,groups):
    labels=[str(x or '').casefold() for x in header]; g=[str(x or '').casefold() for x in groups]; cur=''
    for i,x in enumerate(g):
        if 'regular plan' in x: cur='regular'
        elif 'direct plan' in x: cur='direct'
        g[i]=cur
    g += [''] * max(0,len(labels)-len(g))
    result={}
    for p in ('regular','direct'):
        b=[i for i in bers if p in labels[i] or g[i]==p]
        t=[i for i in ters if p in labels[i] or g[i]==p]
        if len(b)==len(t)==1: result[p]=(b[0],t[0])
    return result
def read_sources(targets,issues,scanned,records):
    for filename in SOURCE_FILES:
        path=SOURCE_DIR/filename
        if not path.is_file(): issues.append(f'missing source file: {filename}'); continue
        try: wb=open_book(path)
        except Exception as e: issues.append(f'{filename}: unable to open ({type(e).__name__}: {e})'); continue
        try:
            for ws in wb.worksheets:
                info=header_info(ws)
                if not info:
                    scanned.append({'file':filename,'sheet':ws.title,'status':'read; no TER/BER table header'})
                    continue
                rn,header,name_col,date_col,bers,ters=info
                groups=list(next(ws.iter_rows(min_row=max(1,rn-1),max_row=max(1,rn-1),values_only=True))) if rn>1 else []
                cols=plan_columns(header,bers,ters,groups)
                if set(cols)!={'direct','regular'}:
                    issues.append(f'{filename}/{ws.title}: Direct and Regular BER/TER columns are ambiguous'); continue
                scanned.append({'file':filename,'sheet':ws.title,'status':'TER/BER table read','header_row':rn})
                maxcol=max(name_col,date_col,*[i for pair in cols.values() for i in pair])
                for rownum,row in enumerate(ws.iter_rows(min_row=rn+1,values_only=True),rn+1):
                    row=list(row)
                    if len(row)<=maxcol or not row[name_col]: continue
                    ids=targets.get(norm(row[name_col]),[])
                    if not ids: continue
                    if len(ids)!=1:
                        issues.append(f'{filename}/{ws.title} row {rownum}: {row[name_col]!r} maps ambiguously to {ids}'); continue
                    if parse_date(row[date_col],wb.epoch)!=AS_OF: continue
                    pid=ids[0]
                    for plan,(bi,ti) in cols.items():
                        ber,ter=number(row[bi]),number(row[ti])
                        if ber is None or ter is None:
                            issues.append(f'{filename}/{ws.title} row {rownum}: pair {pid} {plan} has missing/non-numeric BER or TER'); continue
                        records[(pid,plan)].append({'ber':ber,'ter':ter,'provenance':{'file':filename,'sheet':ws.title,'row':rownum,'scheme_name':str(row[name_col])}})
        except Exception as e: issues.append(f'{filename}: scan failed ({type(e).__name__}: {e})')
        finally: wb.close()
def main():
    with CSV_PATH.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f); fields=list(reader.fieldnames or []); rows=list(reader)
    required={'pair_id','scheme_base_name','ter_direct_pct','ter_regular_pct'}
    if not required.issubset(fields): raise RuntimeError(f'Missing CSV columns: {sorted(required-set(fields))}')
    ids=[str(r['pair_id']).strip() for r in rows]
    if len(rows)!=16 or len(set(ids))!=16: raise RuntimeError(f'Expected 16 unique frozen pairs; got {len(rows)} rows/{len(set(ids))} IDs')
    targets=defaultdict(list)
    for r in rows: targets[norm(r['scheme_base_name'])].append(str(r['pair_id']).strip())
    dup={k:v for k,v in targets.items() if len(v)!=1}
    if dup: raise RuntimeError(f'Ambiguous frozen target names: {dup}')
    issues=[]; scanned=[]; records=defaultdict(list)
    read_sources(targets,issues,scanned,records)
    selected={}; unresolved=[]
    for r in rows:
        pid=str(r['pair_id']).strip()
        for plan in ('direct','regular'):
            candidates=records.get((pid,plan),[])
            if not candidates: unresolved.append(f'pair {pid} {plan}: no exact-name 30-Sep-2026 record'); continue
            values={(round(x['ber'],12),round(x['ter'],12)) for x in candidates}
            if len(values)!=1:
                desc='; '.join(f"{x['provenance']['file']} / {x['provenance']['sheet']} / row {x['provenance']['row']}: BER={x['ber']}, TER={x['ter']}" for x in candidates)
                unresolved.append(f'pair {pid} {plan}: conflicting records: {desc}'); continue
            selected[(pid,plan)]=sorted(candidates,key=lambda x:PRIORITY.get(x['provenance']['file'],999))[0]
    unresolved.extend(issues)
    report={'as_of':AS_OF.isoformat(),'source_files':[{'file':n,'sha256':hashlib.sha256((SOURCE_DIR/n).read_bytes()).hexdigest() if (SOURCE_DIR/n).is_file() else None} for n in SOURCE_FILES], 'scanned_sheets':scanned,'coverage_plan_records':len(selected),'expected_plan_records':32,'unresolved':unresolved}
    if unresolved or len(selected)!=32:
        print(json.dumps(report,indent=2,ensure_ascii=True)); print('STOPPED: scheme_facts.csv was not changed.',file=sys.stderr); return 2
    additions=['ber_direct_pct','ber_regular_pct','ter_direct_source_doc','ter_direct_source_sheet','ter_direct_source_row','ter_regular_source_doc','ter_regular_source_sheet','ter_regular_source_row']
    outfields=fields+[x for x in additions if x not in fields]
    for r in rows:
        pid=str(r['pair_id']).strip(); d=selected[(pid,'direct')]; q=selected[(pid,'regular')]
        r['ter_direct_pct']=f"{d['ter']:g}"; r['ter_regular_pct']=f"{q['ter']:g}"
        r['ber_direct_pct']=f"{d['ber']:g}"; r['ber_regular_pct']=f"{q['ber']:g}"; r['ter_as_of']=AS_OF.isoformat()
        for plan,x in (('direct',d),('regular',q)):
            p=x['provenance']; r[f'ter_{plan}_source_doc']=p['file']; r[f'ter_{plan}_source_sheet']=p['sheet']; r[f'ter_{plan}_source_row']=str(p['row'])
    with tempfile.NamedTemporaryFile('w',newline='',encoding='utf-8',dir=CSV_PATH.parent,delete=False) as f:
        temp=Path(f.name); w=csv.DictWriter(f,fieldnames=outfields,extrasaction='ignore'); w.writeheader(); w.writerows(rows); f.flush()
    temp.replace(CSV_PATH)
    report.update(updated=str(CSV_PATH.relative_to(ROOT)),coverage_pairs=16)
    print(json.dumps(report,indent=2,ensure_ascii=True)); return 0
if __name__=='__main__': raise SystemExit(main())
