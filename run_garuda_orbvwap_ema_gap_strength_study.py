"""GARUDA — ORB+VWAP + EMA9/21 separation-strength research study.
Research only. Same frozen ORB+VWAP entries; 50% ORB SL; 2R target; no BE/trailing.
"""
from pathlib import Path
import pandas as pd
from backtesting.slippage import apply_slippage
from backtesting.transaction_costs import calculate_transaction_costs

ROOT=Path(__file__).resolve().parent; RAW=ROOT/'data'/'raw'; RESEARCH=ROOT/'data'/'research'
SYMBOLS=['INFY','RELIANCE','ICICIBANK','TMPV','ASHOKLEY','OLAELEC','SUZLON']
THRESHOLDS=[0.00,0.05,0.10,0.20,0.30,0.50]; SL_FRAC=.50; TARGET_R=2.; SLIP=.05; COST=.10
OUT_DETAIL=RESEARCH/'garuda_orbvwap_ema_gap_strength_detail.csv'
OUT_SUMMARY=RESEARCH/'garuda_orbvwap_ema_gap_strength_summary.csv'
OUT_SYMBOL=RESEARCH/'garuda_orbvwap_ema_gap_strength_by_symbol.csv'
OUT_TIME=RESEARCH/'garuda_orbvwap_ema_gap_strength_by_time.csv'

def load_price(s):
 p=RAW/f'{s}_5MIN_REAL.csv'; df=pd.read_csv(p)
 df['datetime']=pd.to_datetime(df['datetime'],utc=True).dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
 df=df.sort_values('datetime').reset_index(drop=True)
 df['ema9']=df.close.ewm(span=9,adjust=False,min_periods=9).mean(); df['ema21']=df.close.ewm(span=21,adjust=False,min_periods=21).mean()
 return df

def load_frozen(s):
 p=RESEARCH/f'{s}_frozen_entries_1y.csv'
 if p.exists(): return pd.read_csv(p)
 p=RESEARCH/'garuda_orbvwap_1year_entry_diagnostic_detail.csv'; df=pd.read_csv(p); return df[df.symbol.eq(s)].copy()

def net_pnl(ep,xp,d):
 gross=xp-ep if d=='BUY' else ep-xp
 return gross-calculate_transaction_costs(entry_price=ep,exit_price=xp,quantity=1,cost_rate_pct=COST)

def simulate(sess,d,idx,ep,sl,tgt):
 for i in range(idx,len(sess)):
  c=sess.iloc[i]; hi=float(c.high); lo=float(c.low)
  hs=lo<=sl if d=='BUY' else hi>=sl; ht=hi>=tgt if d=='BUY' else lo<=tgt
  if hs: return c.datetime,sl,'STOP_LOSS',bool(ht)
  if ht: return c.datetime,tgt,'TARGET',False
 c=sess.iloc[-1]; return c.datetime,float(c.close),'END_OF_DAY',False

def ok(d,e9,e21,t):
 if pd.isna(e9) or pd.isna(e21): return False
 q=t/100
 return e9>e21*(1+q) if d=='BUY' else e9<e21*(1-q)

def main():
 print('='*110); print('GARUDA — ORB+VWAP + EMA9/21 SEPARATION STRENGTH STUDY'); print('='*110)
 print('Stop: 50% ORB range | Target: 2R | Thresholds:',', '.join(f'{x:.2f}%' for x in THRESHOLDS)); print('RESEARCH ONLY')
 rows=[]
 for s in SYMBOLS:
  px=load_price(s); fr=load_frozen(s); print(f'{s:<12}: frozen={len(fr)}')
  sessions={d:g.sort_values('datetime').reset_index(drop=True) for d,g in px.groupby(px.datetime.dt.date)}
  for _,r in fr.iterrows():
   td = pd.Timestamp(r.trade_date).date()
   d = str(r.direction)

   st = (
      pd.to_datetime(r.signal_candle_time, utc=True)
      .tz_convert("Asia/Kolkata")
      .tz_localize(None)
   )

   et = (
      pd.to_datetime(r.entry_candle_time, utc=True)
      .tz_convert("Asia/Kolkata")
      .tz_localize(None)
   )

   sess = sessions.get(td)
   if sess is None: continue
   sm=sess[sess.datetime.eq(st)]; em=sess[sess.datetime.eq(et)]
   if sm.empty or em.empty: continue
   sig=sm.iloc[0]; ent=em.iloc[0]; ep=apply_slippage(float(ent.open),d,SLIP,True); e9=float(sig.ema9); e21=float(sig.ema21)
   orb=sess[(sess.datetime.dt.strftime('%H:%M')>='09:15')&(sess.datetime.dt.strftime('%H:%M')<'09:30')]
   if orb.empty: continue
   oh=float(orb.high.max()); ol=float(orb.low.min()); rr=oh-ol
   if rr<=0: continue
   dist=rr*SL_FRAC; sl=ep-dist if d=='BUY' else ep+dist; risk=abs(ep-sl); tgt=ep+TARGET_R*risk if d=='BUY' else ep-TARGET_R*risk
   xt,xp,xr,amb=simulate(sess,d,int(em.index[0]),ep,sl,tgt); pnl=net_pnl(ep,xp,d); nr=pnl/risk
   for t in THRESHOLDS:
    label='EMA_REGIME_0PCT' if t==0 else f"EMA_GAP_{str(t).replace('.','P')}PCT"
    rows.append(dict(symbol=s,trade_date=td,direction=d,signal_candle_time=st,entry_candle_time=et,entry_hour=et.strftime('%H:%M'),ema9=e9,ema21=e21,ema_gap_pct=((e9-e21)/e21*100 if e21 else float('nan')),threshold_pct=t,ema_regime_ok=ok(d,e9,e21,t),entry_price=ep,orb_high=oh,orb_low=ol,orb_range=rr,stop_loss=sl,initial_risk=risk,target=tgt,exit_time=xt,exit_price=xp,exit_reason=xr,ambiguous=amb,net_pnl=pnl,net_r=nr,variant=label))
   detail = pd.DataFrame(rows)

   if detail.empty:
      raise RuntimeError(
         "No research rows generated. "
         "Check frozen signal/entry timestamps against raw 5-minute data."
      )

   filt = detail[detail["ema_regime_ok"]].copy()
   sums = []
 for v,g in filt.groupby('variant'):
  pos=g.loc[g.net_pnl>0,'net_pnl'].sum(); neg=-g.loc[g.net_pnl<0,'net_pnl'].sum()
  sums.append(dict(variant=v,threshold_pct=float(g.threshold_pct.iloc[0]),trades=len(g),stop_loss=(g.exit_reason=='STOP_LOSS').sum(),target=(g.exit_reason=='TARGET').sum(),end_of_day=(g.exit_reason=='END_OF_DAY').sum(),win_rate_pct=(g.exit_reason=='TARGET').mean()*100,total_net_pnl=g.net_pnl.sum(),avg_net_pnl=g.net_pnl.mean(),total_net_r=g.net_r.sum(),avg_net_r=g.net_r.mean(),profit_factor=pos/neg if neg else float('inf')))
 summary=pd.DataFrame(sums).sort_values('threshold_pct'); by_symbol=filt.groupby(['variant','threshold_pct','symbol']).agg(trades=('net_r','size'),total_net_pnl=('net_pnl','sum'),avg_net_pnl=('net_pnl','mean'),total_net_r=('net_r','sum'),avg_net_r=('net_r','mean'),targets=('exit_reason',lambda x:(x=='TARGET').sum()),stop_losses=('exit_reason',lambda x:(x=='STOP_LOSS').sum()),eod=('exit_reason',lambda x:(x=='END_OF_DAY').sum())).reset_index(); by_time=filt.groupby(['variant','threshold_pct','entry_hour']).agg(trades=('net_r','size'),total_net_pnl=('net_pnl','sum'),avg_net_pnl=('net_pnl','mean'),total_net_r=('net_r','sum'),avg_net_r=('net_r','mean')).reset_index()
 RESEARCH.mkdir(parents=True,exist_ok=True); detail.to_csv(OUT_DETAIL,index=False); summary.to_csv(OUT_SUMMARY,index=False); by_symbol.to_csv(OUT_SYMBOL,index=False); by_time.to_csv(OUT_TIME,index=False)
 print('\n'+'='*110); print('RESULTS — EMA SEPARATION STRENGTH'); print('='*110); print(summary.to_string(index=False)); base=len(detail[detail.threshold_pct.eq(0)]); print('\nRETENTION'); print(summary[['threshold_pct','trades']].assign(retention_pct=lambda x:x.trades/base*100).to_string(index=False)); print('\nSaved:'); [print(' ',p) for p in [OUT_DETAIL,OUT_SUMMARY,OUT_SYMBOL,OUT_TIME]]
if __name__=='__main__': main()
