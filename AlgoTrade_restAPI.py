# -*- coding: utf-8 -*-
'''
# 알고리즘 트래이딩 시스템
# Auth : mrtom17
# AlgoTrade_restAPI.py
'''
# import Lib
from collections import namedtuple
import requests , json
import AlgoTrade_comMon as atcm

class APIResp:
    def __init__(self, resp):
        self._rescode = resp.status_code
        self._resp = resp
        self._header = self._setHeader()
        self._body = self._setBody()
        self._err_code = self._body.rt_cd
        self._err_message = self._body.msg1
        
    def getResCode(self):
        return self._rescode   
     
    def _setHeader(self):
        fld = dict()
        for x in self._resp.headers.keys():
            if x.islower():
                fld[x] = self._resp.headers.get(x)
        _th_ =  namedtuple('header', fld.keys())
        
        return _th_(**fld)
    
    def _setBody(self):
        _tb_ = namedtuple('body', self._resp.json().keys())
        
        return  _tb_(**self._resp.json())

    def getHeader(self):
        return self._header
    
    def getBody(self):
        return self._body
    
    def getResponse(self):
        return self._resp
    
    def isOK(self):
        try:
            if(self.getBody().rt_cd == '0'):
                return True
            else:
                return False
        except:
            return False
        
    def getErrorCode(self):
        return self._err_code
    
    def getErrorMessage(self):
        return self._err_message
    
    def printAll(self):
        print("<Header>")
        for x in self.getHeader()._fields:
            print(f'\t-{x}: {getattr(self.getHeader(), x)}')
        print("<Body>")
        for x in self.getBody()._fields:        
            print(f'\t-{x}: {getattr(self.getBody(), x)}')
            
    def printError(self):
        print('-------------------------------\nError in response: ', self.getResCode())
        print(self.getBody().rt_cd, self.getErrorCode(), self.getErrorMessage()) 
        print('-------------------------------')           


########### API call wrapping
def _url_fetch(api_url, ptr_id, params, appendHeaders=None, postFlag=False, hashFlag=True):
    
    url = f"{atcm.getTREnv().my_url}{api_url}"
    
    headers = atcm._getBaseHeader()
    #추가 Header 설정
    tr_id = ptr_id
    if ptr_id[0] in ('T', 'J', 'C'):
        if atcm.isPaperTrading():
            tr_id = 'V' + ptr_id[1:]

    headers["tr_id"] = tr_id
    headers["custtype"] = "P"
    
    if appendHeaders is not None:
        if len(appendHeaders) > 0:
            for x in appendHeaders.keys():
                headers[x] = appendHeaders.get(x)

    if(atcm._DEBUG):
        atcm.msgout('< Sending Info >')
        atcm.msgout(f"URL: {url}, TR: {tr_id}")
        atcm.msgout(f"<header>\n{headers}")
        atcm.msgout(f"<body>\n{params}")
        
    if (postFlag):
        if(hashFlag): atcm.set_order_hash_key(headers, params)
        res = requests.post(url, headers=headers, data=json.dumps(params))
    else:
        res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        ar = APIResp(res)
        #if (atcm._DEBUG): ar.printAll()
        return ar
    else:
        atcm.msgout("Error Code : " + str(res.status_code) + " | " + res.text)
        #print("Error Code : " + str(res.status_code) + " | " + res.text)
        return None

     