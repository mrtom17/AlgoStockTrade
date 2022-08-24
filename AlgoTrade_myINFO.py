# -*- coding: utf-8 -*-
'''
# 알고리즘 트래이딩 시스템
# Auth : mrtom17
# AlgoTrade_myINFO.py
'''
# import Lib
import pandas as pd
from datetime import datetime
from AlgoTrade_restAPI import _url_fetch
import AlgoTrade_comMon as atcm

def get_acct_balance(rtCashFlag=False):
    url = '/uapi/domestic-stock/v1/trading/inquire-balance'
    tr_id = "TTTC8434R"

    params = {
        'CANO': atcm.getTREnv().my_acct, 
        'ACNT_PRDT_CD': '01', 
        'AFHR_FLPR_YN': 'N', 
        'FNCG_AMT_AUTO_RDPT_YN': 'N', 
        'FUND_STTL_ICLD_YN': 'N', 
        'INQR_DVSN': '01', 
        'OFL_YN': 'N', 
        'PRCS_DVSN': '01', 
        'UNPR_DVSN': '01', 
        'CTX_AREA_FK100': '', 
        'CTX_AREA_NK100': ''
        }

    t1 = _url_fetch(url, tr_id, params)
    if rtCashFlag and t1.isOK():
        r2 = t1.getBody().output2
        return int(r2[0]['dnca_tot_amt'])
    
    output1 = t1.getBody().output1
    if t1.isOK() and output1:  #body 의 rt_cd 가 0 인 경우만 성공
        tdf = pd.DataFrame(output1)
        tdf.set_index('pdno', inplace=True)  
        cf1 = ['prdt_name','hldg_qty', 'ord_psbl_qty', 'pchs_avg_pric', 'evlu_pfls_rt', 'prpr', 'bfdy_cprs_icdc', 'fltt_rt']
        cf2 = ['종목명', '보유수량', '매도가능수량', '매입단가', '수익율', '현재가' ,'전일대비', '등락']
        tdf = tdf[cf1]
        tdf[cf1[1:]] = tdf[cf1[1:]].apply(pd.to_numeric)
        ren_dict = dict(zip(cf1, cf2))
        return tdf.rename(columns=ren_dict)
    elif t1.isOK():
        return pd.DataFrame()
    else:
        t1.printError()
        return pd.DataFrame()
     
def get_buyable_cash(stock_code='', qry_price=0, prd_code='01'):
    url = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
    tr_id = "TTTC8908R"

    params = {
        "CANO": atcm.getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "PDNO": stock_code,
        "ORD_UNPR": str(qry_price),
        "ORD_DVSN": "02", 
        "CMA_EVLU_AMT_ICLD_YN": "Y", #API 설명부분 수정 필요 (YN)
        "OVRS_ICLD_YN": "N"
     }

    t1 = _url_fetch(url, tr_id, params)
    if t1.isOK():
        return int(t1.getBody().output['ord_psbl_cash'])
    else:
        t1.printError()
        return 0

def get_my_complete(sdt, edt=None, prd_code='01', zipFlag=True):
    url = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
    tr_id = "TTTC8001R"

    if (edt is None):
        ltdt = datetime.now().strftime('%Y%m%d')
    else:
        ltdt = edt
        
    params = {
        "CANO": atcm.getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "INQR_STRT_DT": sdt,
        "INQR_END_DT": ltdt,
        "SLL_BUY_DVSN_CD": '00',
        "INQR_DVSN": '00',
        "PDNO": "",
        "CCLD_DVSN": "00",
        "ORD_GNO_BRNO": "",
        "ODNO":"",
        "INQR_DVSN_3": "00",
        "INQR_DVSN_1": "",
        "INQR_DVSN_2": "",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
     }

    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        tdf = pd.DataFrame(t1.getBody().output1)
        tdf.set_index('odno', inplace=True)  
        if (zipFlag):
            return tdf[['ord_dt','orgn_odno', 'sll_buy_dvsn_cd_name', 'pdno', 'ord_qty', 'ord_unpr', 'avg_prvs', 'cncl_yn','tot_ccld_amt','rmn_qty']]
        else:
            return tdf
    else:
        t1.printError()
        return pd.DataFrame()

