# -*- coding: utf-8 -*-
'''
# 알고리즘 트래이딩 시스템
# Auth : mrtom17
# AlgoTrade_tradeINFO.py
'''
# import Lib
import pandas as pd
from AlgoTrade_restAPI import _url_fetch
import AlgoTrade_comMon as atcm

def get_current_price(stock_no):
    url = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100"

    params = {
        'FID_COND_MRKT_DIV_CODE': atcm._getStockDiv(stock_no), 
        'FID_INPUT_ISCD': stock_no
        }
    
    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        return t1.getBody().output
    else:
        t1.printError()
        return dict()

def get_stock_investor(stock_no):
    url = "/uapi/domestic-stock/v1/quotations/inquire-investor"
    tr_id = "FHKST01010900"

    params = {
        "FID_COND_MRKT_DIV_CODE": atcm._getStockDiv(stock_no),
        "FID_INPUT_ISCD": stock_no
    }

    t1 = _url_fetch(url, tr_id, params)
    
    if t1.isOK():
        hdf1 = pd.DataFrame(t1.getBody().output)
        
        chosend_fld = ['stck_bsop_date', 'prsn_ntby_qty', 'frgn_ntby_qty', 'orgn_ntby_qty']
        renamed_fld = ['Date', 'PerBuy', 'ForBuy', 'OrgBuy']
        
        hdf1 = hdf1[chosend_fld]
        ren_dict = dict()
        i = 0
        for x in chosend_fld:
            ren_dict[x] = renamed_fld[i]
            i += 1
        
        hdf1.rename(columns = ren_dict, inplace=True)
        hdf1[['Date']] = hdf1[['Date']].apply(pd.to_datetime)  
        hdf1[['PerBuy','ForBuy','OrgBuy']] = hdf1[['PerBuy','ForBuy','OrgBuy']].apply(pd.to_numeric) 
        hdf1['EtcBuy'] = (hdf1['PerBuy'] + hdf1['ForBuy'] + hdf1['OrgBuy']) * -1
        hdf1.set_index('Date', inplace=True)
        return hdf1
    else:
        t1.printError()
        return pd.DataFrame() 

def get_stock_history(stock_no, gb_cd='D'):
    url = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = "FHKST01010400"

    params = {
        "FID_COND_MRKT_DIV_CODE": atcm._getStockDiv(stock_no),
        "FID_INPUT_ISCD": stock_no,
        "FID_PERIOD_DIV_CODE": gb_cd, 
        "FID_ORG_ADJ_PRC": "0000000001"
    }

    t1 = _url_fetch(url, tr_id, params)
    
    if t1.isOK():
        return pd.DataFrame(t1.getBody().output)
    else:
        t1.printError()
        return pd.DataFrame()

def get_stock_history_by_ohlcv(stock_no, gb_cd='D', adVar=False):
    hdf1 = get_stock_history(stock_no, gb_cd)
    
    chosend_fld = ['stck_bsop_date', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr', 'acml_vol']
    renamed_fld = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    hdf1 = hdf1[chosend_fld]
    ren_dict = dict()
    i = 0
    for x in chosend_fld:
        ren_dict[x] = renamed_fld[i]
        i += 1
    
    hdf1.rename(columns = ren_dict, inplace=True)
    hdf1[['Date']] = hdf1[['Date']].apply(pd.to_datetime)  
    hdf1[['Open','High','Low','Close','Volume']] = hdf1[['Open','High','Low','Close','Volume']].apply(pd.to_numeric)  
    hdf1.set_index('Date', inplace=True)
    
    if(adVar):
        hdf1['inter_volatile'] = (hdf1['High']-hdf1['Low'])/hdf1['Close'] 
        hdf1['pct_change'] = (hdf1['Close'] - hdf1['Close'].shift(-1))/hdf1['Close'].shift(-1) * 100

    
    return hdf1
