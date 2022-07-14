# -*- coding: utf-8 -*-
'''
# 알고리즘 트래이딩 시스템
# Auth : mrtom17
# AlgoTrade_comMon.py
'''
# import Lib
import yaml, copy , requests , json , os
from collections import namedtuple
from datetime import datetime

# HTTP 연결 기본 정보를 정의 한다.
conf_file = '~/AlgoStockTrade/configini.yaml'
with open(conf_file, encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

_TRENV = tuple()
_last_auth_time = datetime.now()
_autoReAuth = False
_DEBUG = True
_isPaper = True

_base_headers = {
    "Content-Type": "application/json",
    "Accept": "text/plain",
    "charset": "UTF-8",
    'User-Agent': _cfg['my_agent'] 
}

def _getBaseHeader():
    if _autoReAuth: reAuth()
    return copy.deepcopy(_base_headers)


def _setTRENV(cfg):
    nt1 = namedtuple('KISEnv', ['my_app','my_sec','my_acct', 'my_prod', 'my_token', 'my_url','myslack_token'])
    d = {
        'my_app': cfg['my_app'],
        'my_sec': cfg['my_sec'],
        'my_acct': cfg['my_acct'],
        'my_prod': cfg['my_prod'],
        'my_token': cfg['my_token'],
        'my_url' : cfg['my_url'],
        'myslack_token' : cfg['myslack_token']
    }
    
    global _TRENV 
    _TRENV = nt1(**d)

def isPaperTrading():
    return _isPaper

def _getStockDiv(stock_no):
    return 'J'


def changeTREnv(token_key, svr='prod', product='01'):
    cfg = dict()

    global _isPaper
    if svr == 'prod':
        ak1 = 'my_app'
        ak2 = 'my_sec'
        _isPaper = False
    elif svr == 'vps':
        ak1 = 'paper_app'
        ak2 = 'paper_sec'
        _isPaper = True
        
    cfg['my_app'] = _cfg[ak1]
    cfg['my_sec'] = _cfg[ak2]   
    
    if svr == 'prod' and product == '01':
        cfg['my_acct'] = _cfg['my_acct_stock']
    elif svr == 'prod' and product == '03':
        cfg['my_acct'] = _cfg['my_acct_future']
    elif svr == 'vps' and product == '01':        
        cfg['my_acct'] = _cfg['my_paper_stock']
    elif svr == 'vps' and product == '03':        
        cfg['my_acct'] = _cfg['my_paper_future']

    cfg['my_prod'] = product
    cfg['my_token'] = token_key
    cfg['my_url'] = _cfg[svr]
    cfg['myslack_token'] = _cfg['myslack_token']
    
    _setTRENV(cfg)
    
            
def _getResultObject(json_data):
    _tc_ = namedtuple('res', json_data.keys())
            
    return _tc_(**json_data)
    
def auth(svr='prod', product='01'):

    p = {
        "grant_type": "client_credentials",
    }
    #print(svr)
    if svr == 'prod':
        ak1 = 'my_app'
        ak2 = 'my_sec'
    elif svr == 'vps':
        ak1 = 'paper_app'
        ak2 = 'paper_sec'
        
    p["appkey"] = _cfg[ak1]
    p["appsecret"] = _cfg[ak2]
    

    url = f'{_cfg[svr]}/oauth2/tokenP'

    res = requests.post(url, data=json.dumps(p), headers=_getBaseHeader())
    rescode = res.status_code
    if rescode == 200:
        my_token = _getResultObject(res.json()).access_token
    else: 
        msgout('Get Authentification token fail!\nYou have to restart your app!!!')
        return
 
    changeTREnv(f"Bearer {my_token}", svr, product)
    
    _base_headers["authorization"] = _TRENV.my_token
    _base_headers["appkey"] = _TRENV.my_app
    _base_headers["appsecret"] = _TRENV.my_sec
    
    global _last_auth_time
    _last_auth_time = datetime.now()
    
    if (_DEBUG):
        msg = f'[{_last_auth_time}] => get AUTH Key completed!'
        msgout(msg)
    
#end of initialize
def reAuth(svr='prod', product='01'):
    n2 = datetime.now()
    if (n2-_last_auth_time).seconds >= 86400:
        auth(svr, product)

def getEnv():
    return _cfg
def getTREnv():
    return _TRENV

def set_order_hash_key(h, p):
   
    url = f"{getTREnv().my_url}/uapi/hashkey"
  
    res = requests.post(url, data=json.dumps(p), headers=h)
    rescode = res.status_code
    if rescode == 200:
        h['hashkey'] = _getResultObject(res.json()).HASH
    else:
        #print("Error:", rescode)
        msgout("Error:"+rescode)


LOG_FILE_DIR = 'log'
LOG_FILE_NAME = 'log/kis_trade_hist.log'

def msgout(msg) -> None:
    if os.path.exists(LOG_FILE_NAME):
        with open(LOG_FILE_NAME, 'at', encoding='utf-8') as lfile:
            logmsg = datetime.now().strftime('[%y-%m-%d %H:%M:%S] ') + str(msg) + '\n'
            lfile.write(logmsg)
            lfile.close()
    else:
        os.mkdir(LOG_FILE_DIR)
        with open(LOG_FILE_NAME, 'at', encoding='utf-8') as lfile:
            logmsg = datetime.now().strftime('[%y-%m-%d %H:%M:%S] ') + str(msg) + '\n'
            lfile.write(logmsg)
            lfile.close()

def send_slack_msg(channel, text):
    myToken = _cfg['myslack_token']
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+myToken},
        data={"channel": channel,"text": text}
    )
    
