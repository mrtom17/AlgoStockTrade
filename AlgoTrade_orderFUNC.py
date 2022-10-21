# -*- coding: utf-8 -*-
'''
# 알고리즘 트래이딩 시스템
# Auth : mrtom17
# AlgoTrade_orderFUNC.py
'''
# import Lib
import pandas as pd
import time
from AlgoTrade_restAPI import _url_fetch
import AlgoTrade_comMon as atcm

def do_order(stock_code, order_qty, order_price, prd_code="01", buy_flag=True, order_type="00"):
    url = "/uapi/domestic-stock/v1/trading/order-cash"

    if buy_flag:
        tr_id = "TTTC0802U"  #buy
    else:
        tr_id = "TTTC0801U"  #sell

    params = {
        'CANO': atcm.getTREnv().my_acct, 
        'ACNT_PRDT_CD': prd_code, 
        'PDNO': stock_code, 
        'ORD_DVSN': order_type, 
        'ORD_QTY': str(order_qty), 
        'ORD_UNPR': str(order_price), 
        'CTAC_TLNO': '', 
        'SLL_TYPE': '01', 
        'ALGO_NO': ''
        }
    
    t1 = _url_fetch(url, tr_id, params, postFlag=True, hashFlag=True)

    if t1.isOK():
        return t1
    else:
        t1.printError()
        return t1

def do_sell(stock_code, order_qty, order_price, prd_code="01", order_type="00"):
    t1 = do_order(stock_code, order_qty, order_price, buy_flag=False, order_type=order_type)
    return t1.isOK()

def do_buy(stock_code, order_qty, order_price, prd_code="01", order_type="00"):
    t1 = do_order(stock_code, order_qty, order_price, buy_flag=True, order_type=order_type)
    return t1.isOK()

def get_orders(prd_code='01'):
    url = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"

    tr_id = "TTTC8036R"

    params = {
        "CANO": atcm.getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "CTX_AREA_FK100": '',
        "CTX_AREA_NK100": '',
        "INQR_DVSN_1": '0',
        "INQR_DVSN_2": '0'
        }

    t1 = _url_fetch(url, tr_id, params)    
    if t1.isOK():  
        tdf = pd.DataFrame(t1.getBody().output)
        tdf.set_index('odno', inplace=True)   
        cf1 = ['pdno', 'ord_qty', 'ord_unpr', 'ord_tmd', 'ord_gno_brno','orgn_odno']
        cf2 = ['종목코드', '주문수량', '주문가격', '시간', '주문점', '원번호']
        tdf = tdf[cf1]
        ren_dict = dict(zip(cf1, cf2))

        return tdf.rename(columns=ren_dict)
        
    else:
        t1.printError()
        return pd.DataFrame()
    
def _do_cancel_revise(order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn):
    url = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
    
    tr_id = "TTTC0803U"

    params = {
        "CANO": atcm.getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "KRX_FWDG_ORD_ORGNO": order_branch, 
        "ORGN_ODNO": order_no,
        "ORD_DVSN": order_dv,
        "RVSE_CNCL_DVSN_CD": cncl_dv, #취소(02)
        "ORD_QTY": str(order_qty),
        "ORD_UNPR": str(order_price),
        "QTY_ALL_ORD_YN": qty_all_yn
    }

    t1 = _url_fetch(url, tr_id, params=params, postFlag=True)  
    
    if t1.isOK():
        return t1
    else:
        t1.printError()
        return None


def do_cancel(order_no, order_qty, order_price="01", order_branch='06010', prd_code='01', order_dv='00', cncl_dv='02',qty_all_yn="Y"):
    return _do_cancel_revise(order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn)


def do_revise(order_no, order_qty, order_price, order_branch='06010', prd_code='01', order_dv='00', cncl_dv='01', qty_all_yn="Y"):
    return _do_cancel_revise(order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn)

def do_cancel_all():
    tdf = get_orders()
    od_list = tdf.index.to_list()
    qty_list = tdf['주문수량'].to_list()
    price_list = tdf['주문가격'].to_list()
    branch_list = tdf['주문점'].to_list()
    cnt = 0
    for x in od_list:
        ar = do_cancel(x, qty_list[cnt], price_list[cnt], branch_list[cnt])
        cnt += 1
        print(ar.getErrorCode(), ar.getErrorMessage())
        time.sleep(.2)

