from __future__ import annotations
import argparse, json, math, re, shutil
from pathlib import Path
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description='Convert the original Dash app CSV outputs into GitHub Pages JSON data.')
parser.add_argument('--src', required=True, help='Path to the original project folder containing out/.')
parser.add_argument('--out', default=str(Path(__file__).resolve().parents[1]), help='GitHub Pages project root (default: parent of tools/).')
args = parser.parse_args()
SRC = Path(args.src).expanduser().resolve()
OUT = Path(args.out).expanduser().resolve()
DATA = OUT / 'data'
for d in [DATA/'news', DATA/'market', DATA/'factor', DATA/'event']:
    d.mkdir(parents=True, exist_ok=True)

TFI_TOPICS = ['생산','선박','자동차','반도체','설비투자','건설투자','실업','채용','구직','도소매','정부지출','물가','주가','주택가격','세계교역']
TFI_LONG = ['생산','선박','자동차','반도체','설비투자','건설투자','실업','채용','구직','도소매','정부지출','물가전망','주가전망','주택가격전망','세계교역']
TFI_ENG = ['Production','Shipbuilding','Automobile','Semiconductor','Facilities Investment','Construction','Unemployment','Recruitment','Job Search','Wholesale and Retail','Government Expenditure','Inflation','Stock Price','Housing Price','World Trade']
NEWS_IDS = ['production','shipbuilding','automobile','semiconductor','facilities-investment','construction','unemployment','recruitment','job-search','wholesale-retail','government-expenditure','inflation','stock-price','housing-price','world-trade']

KRX_FIELDS = ['코스피','전기전자','화학','금융업','의약품','운수장비','음식료품','전기가스업','건설업','기계']
KRX_ENG = ['KOSPI','Electrical & Electronic Equip.','Chemicals','Finance','Medical Supplies','Transport Equipment','Foods & Beverages','Electricity & Gas','Construction','Machinery']
AR_FIELDS = ['전체','전자/영상/통신장비등','화학물질/제품','금융','의료물질/의약품',['자동차', '조선/기타운수'],'식료품','전기/가스/증기','건설업','기타기계/장비']
AR_ENG = ['All-industry','Electronic components, computer, radio, television and communication equipment and apparatuses','Chemicals and chemical products','Finance','Pharmaceuticals, medicinal chemicals and botanical products','Motor vehicles, trailers and semitrailers & Other transport equipment','Food products','Electricity, gas, steam and air conditioning supply','Construction','Other machinery and equipment']
FIELD_TYPES = [3,1,1,1,1,2,1,1,1,1]
MARKET_IDS = ['kospi','electronics','chemicals','finance','medical-supplies','transport-equipment','foods-beverages','electricity-gas','construction','machinery']

FA_FIELDS = ['전자/영상/통신장비등', '정보통신업', '화학물질/제품', '의료물질/의약품', '금융', '전문/과학/기술',
               '도매/소매', '기타기계/장비', '자동차', '의료/정밀기기', '식료품', '운수/창고업', '1차금속',
               '예술/스포츠/여가', '조선/기타운수']
FA_ENG = ['Electronic, video, and communication equipment', 'Information and communication industry', 'Chemicals', 'Medical substances and medicine', 'Finance', 'Specialized, scientific, and technical services',
               'Wholesale and retail', 'Other machines and equipment', 'Automobile', 'Medical and precision equipment', 'Groceries', 'Transportation and warehouse', 'Primary metal',
               'Art, sports, and leisure services', 'Shipbuilding and other transportation']
FA_IDS = ['electronic-video-communication','information-communication','chemicals','medical-medicine','finance','science-technical','wholesale-retail','other-machinery','automobile','medical-precision','groceries','transport-warehouse','primary-metal','arts-sports-leisure','shipbuilding-transport']

FA_ALL = ['전자/영상/통신장비등', '정보통신업', '화학물질/제품', '의료물질/의약품', '금융', '전문/과학/기술',
               '도매/소매', '기타기계/장비', '자동차', '의료/정밀기기', '식료품', '운수/창고업', '1차금속',
               '예술/스포츠/여가', '조선/기타운수', '건설업', '전기장비', '인쇄/기록매체복제', '고무/플라스틱', '기타제조업',
               '석유정제/코크스', '의복/모피', '전기/가스/증기', '부동산업', '비금속광물', '음료', '사업시설/사업지원/임대업',
               '가구', '펄프/종이', '금속가공', '하수/폐기물처리업', '숙박업', '목재/나무', '교육서비스', '섬유',
               '가죽/가방/신발', '기타개인서비스', '농업', '어업']
FA_ALL_ENG = ['Electronic, video, and communication equipment', 'Information and communication industry', 'Chemicals', 'Medical substances and medicine', 'Finance', 'Specialized, scientific, and technical services',
               'Wholesale and retail', 'Other machines and equipment', 'Automobile', 'Medical and precision equipment', 'Groceries', 'Transportation and warehouse', 'Primary metal',
               'Art, sports, and leisure services', 'Shipbuilding and other transportation', 'Construction', 'Electrical equipment', 'Printing and record media manufacturing', 'Rubber and plastic', 'Other manufacturing',
               'Petroleum refining and coke', 'Clothes and fur', 'Electric, gas, and steam', 'Real estate', 'Nonmetallic minerals', 'Beverage', 'Facility management and supporting services',
               'Furniture', 'Pulp and paper', 'Metalworking', 'Sewage and waste disposal', 'Accommodation', 'Lumber and wood', 'Education', 'Textile',
               'Leather, bag and footwear', 'Other personal services', 'Agriculture', 'Fishing']
FA_ALL_MAP = dict(zip(FA_ALL, FA_ALL_ENG))

EA_EVENTS = ['코로나','러우전쟁','환율','금리']
EA_ENG = ['Covid 19','Russia-Ukraine War','Exchange Rate','Interest Rate']
EA_IDS = ['covid-19','russia-ukraine-war','exchange-rate','interest-rate']

PLOTLY_COLORS = ['#636EFA','#EF553B','#00CC96','#AB63FA','#FFA15A','#19D3F3','#FF6692','#B6E880','#FF97FF','#FECB52']

def enc(s: str) -> str:
    s = s.replace('/', '')
    return ''.join(c if ord(c) < 128 else f'#U{ord(c):04x}' for c in s)

def clean_num(x):
    if pd.isna(x): return None
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating, float)):
        v=float(x)
        return v if math.isfinite(v) else None
    return x

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

def zscore100(vals):
    arr=np.asarray(vals,dtype=float)
    mu=np.nanmean(arr); sd=np.nanstd(arr)
    return ((arr-mu)/sd*10+100).tolist()

# News
news_manifest=[]
for topic, long_topic, eng, slug in zip(TFI_TOPICS, TFI_LONG, TFI_ENG, NEWS_IDS):
    entry={'id':slug,'label':eng,'source':topic,'periods':{}}
    encoded = enc(long_topic) + '_20050101_20230129'
    for period in ['month','week']:
        f=SRC/'out'/f'TFI_{period}_{encoded}.csv'
        if not f.exists():
            continue
        df=pd.read_csv(f,index_col=0)
        idx=[str(x) for x in df.index]
        try: start=idx.index('200601')
        except ValueError: start=0
        idx=idx[start:]
        vals=zscore100(df.iloc[start:,0].to_numpy(dtype=float))
        traces=[{'name':eng,'x':idx,'y':[clean_num(x) for x in vals],'axis':'y'}]
        sf=SRC/'out'/f'SI_month_{encoded}.csv'
        if sf.exists():
            sdf=pd.read_csv(sf,index_col=0)
            sx=[]
            if period=='month':
                sx=[str(x) for x in sdf.index]
            else:
                import datetime as dt
                for x in sdf.index:
                    s=str(x)
                    d=dt.date(int(s[:4]),int(s[4:]),15)
                    iso=d.isocalendar()
                    sx.append(str(iso.year*100+iso.week))
            traces.append({'name':str(sdf.columns[0]),'x':sx,'y':[clean_num(x) for x in sdf.iloc[:,0].tolist()],'axis':'y2'})
        outname=f'{slug}-{period}.json'
        write_json(DATA/'news'/outname, {'period':period,'field':eng,'traces':traces})
        entry['periods'][period]=f'data/news/{outname}'
    news_manifest.append(entry)
write_json(DATA/'news'/'manifest.json',news_manifest)

# Market, supports quarter (as original UI) and month if source is complete.
market_manifest=[]
for period in ['quarter','month']:
    tpfile=SRC/'out'/f'MA_timepoints_{period}.csv'
    if not tpfile.exists(): continue
    timepoints=[str(x) for x in pd.read_csv(tpfile,index_col=0,dtype=object).iloc[:,0].tolist()]
    krx=pd.read_csv(SRC/'out'/f'MA_krx_dat_{period}.csv',index_col=0)
    for slug, krx_kor, krx_eng, arfield, areng, typ in zip(MARKET_IDS,KRX_FIELDS,KRX_ENG,AR_FIELDS,AR_ENG,FIELD_TYPES):
        try:
            if typ==1:
                d=pd.read_csv(SRC/'out'/f'MA_temp_dat_t1_{period}.csv',index_col=0,header=[0,1])
                s=d.loc[arfield]
                x=[str(c[1]) for c in s.index]
                y=np.asarray(s.to_numpy(dtype=float),dtype=float)
            elif typ==2:
                d=pd.read_csv(SRC/'out'/f'MA_temp_dat_t2_{period}.csv',index_col=0)
                s=d.iloc[0]
                x=[str(c) for c in s.index]
                y=np.asarray(s.to_numpy(dtype=float),dtype=float)
            else:
                d=pd.read_csv(SRC/'out'/f'MA_temp_dat_t3_{period}.csv',index_col=[0,1])
                x=[str(i[1]) for i in d.index]
                y=np.asarray(d.iloc[:,0].to_numpy(dtype=float),dtype=float)
            y2=zscore100(y)
            kseries=krx[krx_kor]
            kx=[str(x) for x in kseries.index]
            ky=[clean_num(v) for v in kseries.tolist()]
        except Exception as e:
            print('market skip',period,slug,e)
            continue
        obj={'period':period,'field':krx_eng,'traces':[
            {'name':f'TBCI {krx_eng}','x':x,'y':[clean_num(v) for v in y2],'axis':'y'},
            {'name':f'KOSPI {areng}','x':kx,'y':ky,'axis':'y2','dash':'dash'}
        ]}
        outname=f'{slug}-{period}.json'; write_json(DATA/'market'/outname,obj)
        market_manifest.append({'id':slug,'label':krx_eng,'period':period,'path':f'data/market/{outname}'})
write_json(DATA/'market'/'manifest.json',market_manifest)

# Factor tables
factor_manifest=[]
for kor,eng,slug in zip(FA_FIELDS,FA_ENG,FA_IDS):
    e=enc(kor)
    ft=SRC/'out'/f'FA_table_{e}.csv'; fc=SRC/'out'/f'FA_colorcell_{e}.csv'
    if not ft.exists():
        print('factor missing',kor); continue
    dat=pd.read_csv(ft,index_col=0).fillna('').astype(str).to_numpy().tolist()
    colors=[]
    if fc.exists() and fc.stat().st_size>1:
        try:
            cdf=pd.read_csv(fc,index_col=0)
            for row in cdf.to_numpy():
                if len(row)>=3:
                    colors.append([int(float(row[0])),int(float(row[1])),int(float(row[2]))])
        except pd.errors.EmptyDataError: pass
    outname=f'{slug}.json'; write_json(DATA/'factor'/outname,{'field':eng,'table':dat,'colorCells':colors,'palette':PLOTLY_COLORS})
    factor_manifest.append({'id':slug,'label':eng,'path':f'data/factor/{outname}'})
write_json(DATA/'factor'/'manifest.json',factor_manifest)

# Treemap
tf=SRC/'out'/'Treemap_dat_2022q4.csv'
tdf=pd.read_csv(tf)
write_json(DATA/'factor'/'treemap-2022q4.json',{
    'quarter':'2022q4',
    'labels':[str(x) for x in tdf['names'].fillna('')],
    'parents':[str(x) for x in tdf['parents'].fillna('')],
    'values':[clean_num(x) for x in tdf['values']],
    'colors':[clean_num(x) for x in tdf['color']],
})

# Events
event_manifest=[]
for kor,eng,slug in zip(EA_EVENTS,EA_ENG,EA_IDS):
    event_entry={'id':slug,'label':eng,'source':kor,'items':{}}
    # impact
    f=SRC/'out'/f'EA_impact_{enc(kor)}.csv'
    if f.exists():
        d=pd.read_csv(f,index_col=0)
        maxv=d.max(axis=1,skipna=True)
        ids=maxv[maxv>0].sort_values(ascending=False).head(5).index.tolist()
        traces=[]
        for k in ids:
            traces.append({'name':FA_ALL_MAP.get(k,k),'x':[str(c) for c in d.columns],'y':[0 if pd.isna(v) else float(v) for v in d.loc[k].tolist()]})
        outname=f'{slug}-impact.json'; write_json(DATA/'event'/outname,{'event':eng,'item':'Impact','traces':traces})
        event_entry['items']['Impact']=f'data/event/{outname}'
    # evaluation
    fi=SRC/'out'/f'EA_eval_interest_{enc(kor)}.csv'; fr=SRC/'out'/f'EA_eval_rank_{enc(kor)}.csv'
    if fi.exists() and fr.exists():
        d=pd.read_csv(fi,index_col=0); r=pd.read_csv(fr,index_col=0)
        ids=r.sum(axis=1,skipna=True).sort_values(ascending=False).head(5).index.tolist()
        traces=[]
        for k in ids:
            traces.append({'name':FA_ALL_MAP.get(k,k),'x':[str(c) for c in d.columns],'y':[clean_num(v) for v in d.loc[k].tolist()]})
        outname=f'{slug}-evaluation.json'; write_json(DATA/'event'/outname,{'event':eng,'item':'Evaluation','traces':traces})
        event_entry['items']['Evaluation']=f'data/event/{outname}'
    event_manifest.append(event_entry)
write_json(DATA/'event'/'manifest.json',event_manifest)

write_json(DATA/'manifest.json',{
    'title':'Text-based Financial Indices Hub',
    'generatedFrom':'src.zip',
    'news':'data/news/manifest.json',
    'market':'data/market/manifest.json',
    'factor':'data/factor/manifest.json',
    'treemap':'data/factor/treemap-2022q4.json',
    'event':'data/event/manifest.json'
})
print('generated', sum(1 for _ in DATA.rglob('*.json')), 'json files')
