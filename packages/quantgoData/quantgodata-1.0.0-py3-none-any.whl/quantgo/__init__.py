"""QuantGo SDK - 本地Tushare数据接口"""
import requests,pandas as pd
__version__="1.0.0"
class QuantGoAPI:
    def __init__(s,token=None,server='http://127.0.0.1:9468',server_url=None):  # 兼容两种参数名
        s.token=token;s.server=server_url or server
    def _req(s,api,**kw):  # 通用请求方法
        r=requests.post(f'{s.server}/api',json={'api_name':api,'token':s.token,'params':kw},timeout=60)
        d=r.json();return pd.DataFrame(d.get('data',[])) if d.get('code')==0 else pd.DataFrame()
    def daily(s,ts_code='',trade_date='',start_date='',end_date='',fields=''):return s._req('daily',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    def weekly(s,ts_code='',trade_date='',start_date='',end_date='',fields=''):return s._req('weekly',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    def monthly(s,ts_code='',trade_date='',start_date='',end_date='',fields=''):return s._req('monthly',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    def daily_basic(s,ts_code='',trade_date='',start_date='',end_date=''):return s._req('daily_basic',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    def stock_basic(s,exchange='',list_status='L',fields=''):return s._req('stock_basic',exchange=exchange,list_status=list_status)
    def trade_cal(s,exchange='SSE',start_date='',end_date=''):return s._req('trade_cal',exchange=exchange,start_date=start_date,end_date=end_date)
    def stk_mins(s,ts_code='',freq='30min',start_date='',end_date=''):return s._req('stk_mins',ts_code=ts_code,freq=freq,start_date=start_date,end_date=end_date)
    def moneyflow(s,ts_code='',trade_date='',start_date='',end_date=''):return s._req('moneyflow',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    def index_basic(s,ts_code='',market='',publisher='',category=''):return s._req('index_basic',ts_code=ts_code,market=market,publisher=publisher,category=category)
    def fund_basic(s,ts_code='',market='',status=''):return s._req('fund_basic',ts_code=ts_code,market=market,status=status)
    def index_daily(s,ts_code='',trade_date='',start_date='',end_date=''):return s._req('index_daily',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    def fund_daily(s,ts_code='',trade_date='',start_date='',end_date=''):return s._req('fund_daily',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    def index_classify(s,level='',src='SW2021'):return s._req('index_classify',level=level,src=src)
    def index_member(s,index_code='',is_new=''):return s._req('index_member',index_code=index_code,is_new=is_new)  # is_new默认不过滤
    def realtime(s,ts_code=''):return s._req('realtime',ts_code=ts_code)  # 实时行情(东财)
    def margin(s,trade_date='',exchange_id='',start_date='',end_date=''):return s._req('margin',trade_date=trade_date,exchange_id=exchange_id,start_date=start_date,end_date=end_date)
    def limit_list_d(s,trade_date='',ts_code='',limit_type='',exchange='',start_date='',end_date=''):return s._req('limit_list_d',trade_date=trade_date,ts_code=ts_code,limit_type=limit_type,exchange=exchange,start_date=start_date,end_date=end_date)
    def sw_daily(s,ts_code='',trade_date='',start_date='',end_date=''):return s._req('sw_daily',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    # 宏观经济数据
    def shibor(s,start_date='',end_date=''):return s._req('shibor',start_date=start_date,end_date=end_date)
    def cn_gdp(s,start_q='',end_q=''):return s._req('cn_gdp',start_q=start_q,end_q=end_q)
    def cn_cpi(s,start_m='',end_m=''):return s._req('cn_cpi',start_m=start_m,end_m=end_m)
    def cn_ppi(s,start_m='',end_m=''):return s._req('cn_ppi',start_m=start_m,end_m=end_m)
    def cn_m(s,start_m='',end_m=''):return s._req('cn_m',start_m=start_m,end_m=end_m)
    def sf_month(s,start_m='',end_m=''):return s._req('sf_month',start_m=start_m,end_m=end_m)
    def cn_pmi(s,start_m='',end_m=''):return s._req('cn_pmi',start_m=start_m,end_m=end_m)
    def moneyflow_hsgt(s,trade_date='',start_date='',end_date=''):return s._req('moneyflow_hsgt',trade_date=trade_date,start_date=start_date,end_date=end_date)
    # 产业景气度数据
    def ths_index(s,ts_code='',name='',type=''):return s._req('ths_index',ts_code=ts_code,name=name,type=type)
    def ths_member(s,ts_code='',code='',is_new=''):return s._req('ths_member',ts_code=ts_code,code=code,is_new=is_new)
    def ths_daily(s,ts_code='',trade_date='',start_date='',end_date=''):return s._req('ths_daily',ts_code=ts_code,trade_date=trade_date,start_date=start_date,end_date=end_date)
    def moneyflow_ind(s,trade_date='',ts_code='',start_date='',end_date=''):return s._req('moneyflow_ind',trade_date=trade_date,ts_code=ts_code,start_date=start_date,end_date=end_date)
    def top_list(s,trade_date='',ts_code='',start_date='',end_date=''):return s._req('top_list',trade_date=trade_date,ts_code=ts_code,start_date=start_date,end_date=end_date)
    def top_inst(s,trade_date='',ts_code='',start_date='',end_date=''):return s._req('top_inst',trade_date=trade_date,ts_code=ts_code,start_date=start_date,end_date=end_date)
    def dc_index(s,ts_code='',name=''):return s._req('dc_index',ts_code=ts_code,name=name)
    def bo_weekly(s,date=''):return s._req('bo_weekly',date=date)
    # 市场情绪数据
    def stk_surv(s,ts_code='',surv_date='',start_date='',end_date=''):return s._req('stk_surv',ts_code=ts_code,surv_date=surv_date,start_date=start_date,end_date=end_date)
    def token_info(s):  # 查询token有效期
        r=requests.post(f'{s.server}/api',json={'api_name':'token_info','token':s.token,'params':{}},timeout=10)
        d=r.json();return d.get('data',{}) if d.get('code')==0 else {'error':d.get('msg','查询失败')}
def pro_api(token=None,server='http://127.0.0.1:9468',server_url=None):  # 兼容tushare风格+旧版参数
    return QuantGoAPI(token=token,server=server,server_url=server_url)
