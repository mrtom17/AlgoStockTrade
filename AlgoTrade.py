# -*- coding: utf-8 -*-
'''
# 알고리즘 트래이딩 시스템
# Auth : mrtom17
# AlgoTrade.py
'''
# import Lib
import argparse, sys
from datetime import datetime
import time

import AlgoTrade_comMon as atcm
import AlgoTrade_myINFO as mystock
import AlgoTrade_tradeINFO as trinfo
import AlgoTrade_orderFUNC as atof


# 필요한 arg 정의 한다
parser = argparse.ArgumentParser()
parser.add_argument('--svr', type=str, default='vps' , help='실전투자 prod, 모의투자 vps')
parser.add_argument('--mode', type=bool, default=False, help='True 는 Debug 모드 False 는 상용 모드')
args = parser.parse_args()

# 필요한 인자를 정의 한다
# 실전 투자 혹은 모의 투자인지 정의 한다
svr = args.svr
atcm._DEBUG = args.mode
cashout = False

# 공통 Function 정의
msgout = atcm.msgout

def get_mystock_balance(stock):
    # 보유한 주식과 예수금을 반환한다.
    mystocklist = mystock.get_acct_balance()
    stocks= []
    for i in range(0,len(mystocklist)):
        stock_code = mystocklist.iloc[i].name
        stock_name = mystocklist.iloc[i]['종목명']
        stock_qty = mystocklist.iloc[i]['매도가능수량']
        
        if stock == 'ALL':
            stocks.append({'code': stock_code, 'name': stock_name, 
            'qty': stock_qty})

        if stock_code == stock:
            return stock_name,stock_qty

    if stock == 'ALL':
        return stocks
    else:
        return None , 0



def set_stock_target_price(stock , bestk=0.5):
    # 매수 목표가를 반환해 준다
    # 20일 이동 평균가를 반환해 준다
    try:
        ma5 = ''
        str_today = t_now.replace(hour=0, minute=0, second=0, microsecond=0)
        df = trinfo.get_stock_history_by_ohlcv(stock,adVar=True)
        if str_today == df.iloc[0].name:
            today_open = df.iloc[0]['Open']
            lastday = df.iloc[1]
        else:
            lastday = df.iloc[0]
            today_open = df.iloc[1]['Close']
        lastday_high = lastday['High']
        lastday_low = lastday['Low']
        closes = df['Close'].sort_index()
        _ma5 = closes.rolling(window=5).mean()
        _ma10 = closes.rolling(window=10).mean()

        ma5 = _ma5.iloc[-1]
        ma10 = _ma10.iloc[-1]
        target_price = today_open + (lastday_high - lastday_low) * bestk
        return int(target_price) , int(ma5), int(ma10)
    except Exception as ex:
        msgout("`get_target_price() -> exception! " + str(ex) + "`")
        return None , None , None



# 주식 매수 
def _buy_stock(stock,bestk=0.5):
    try:
        global buy_done_list 
        if stock in buy_done_list: 
            return False
        target_price, ma5, ma10 = set_stock_target_price(stock,bestk)
        current_price = int(trinfo.get_current_price(stock)['stck_prpr'])
        buy_qty = 0
        if current_price > 0:
            buy_qty = int(buy_amount // current_price)
        if buy_qty < 1:
            return False
        stock_name, stock_qty = get_mystock_balance(stock)

        # 변동성 돌파 매매 전략 실행
        if current_price > target_price and current_price > ma5 and current_price > ma10:
            msgout(str(stock) + '는 주문 수량 (' + str(buy_qty) +') EA : ' + str(current_price) + ' meets the buy condition!`')
            if stock_qty == 0:
                ret = atof.do_buy(str(stock) , buy_qty, current_price)
                if ret:
                    msgout('변동성 돌파 매매 성공 -> 주식('+str(stock)+') 매수가격 ('+str(current_price)+')')
                    buy_done_list.append(stock)
                else:
                    msgout('변동성 돌파 매매 실패 -> 주식('+str(stock)+')')
                    return False
            msgout('현금주문 가능금액 : '+ str(buy_amount))
    except Exception as ex:
        msgout("`_buy_stock("+ str(stock) + ") -> exception! " + str(ex) + "`")   



def _sell_stock():
    # 보유한 모든 종목을 당일 종가 혹은 다음날 시작가에 매도 
    try:
        while True:
            stocks = get_mystock_balance('ALL')
            total_qty = 0
            for s in stocks:
                total_qty += s['qty']
            if total_qty == 0:
                return True
            for s in stocks:
                if s['qty'] != 0:
                    current_price = int(trinfo.get_current_price(s['code'])['stck_prpr'])
                    ret = atof.do_sell(s['code'], s['qty'], current_price)
                if ret:
                    msgout('변동성 돌파 매도 주문 성공 ->('+str(s['code'])+')('+str(current_price)+')')
                else:
                    msgout('변동성 돌파 매도 주문 실패 ->('+str(s['code'])+')')
                time.sleep(1)
            time.sleep(30)
    except Exception as ex:
        msgout("sell_all() -> exception! " + str(ex))


if '__main__' == __name__:
    try:
        atcm.auth(svr,product='01')
        stock_list = atcm._cfg['stlist']
        buy_done_list = []
        target_buy_count = 5
        buy_percent = 0.19
        total_cash = int(mystock.get_buyable_cash())
        buy_amount = total_cash * buy_percent
        stocks_cnt = len(get_mystock_balance('ALL'))
        target_buy_count = target_buy_count - stocks_cnt
        msgout('----------------100% 증거금 주문 가능 금액 :'+str(total_cash))
        msgout('----------------종목별 주문 비율 :'+str(buy_percent))
        msgout('----------------종목별 주문 금액 :'+str(buy_amount))
        soldout = False
        while True:
            # 거래 가능 시간 정의
            t_now = datetime.now()
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
            today = datetime.today().weekday()

            # Message 정의 
            msg_end = '['+str(t_now)+'] Kospi & Kosdaq Closed Process self- destructed'
            msg_week = 'Today is', 'Saturday.' if today == 5 else 'Sunday.'
            msg_resell = '`sell_all() returned True -> 전날 잔여 주식 매도!`'
            msg_proc = 'The AlogoTrading process is still alive'
            msg_sellall = '`sell_all() returned True -> self-destructed!`'

            if today == 5 or today == 6:
                msgout(msg_week)
                atcm.send_slack_msg("#stock",msg_week)
                sys.exit(0)
            if t_9 < t_now < t_start and soldout == False:
                soldout = True
                if _sell_stock() == True:
                    msgout(msg_resell)
                    atcm.send_slack_msg("#stock",msg_resell)
            if t_start < t_now < t_sell:
                for std in stock_list:
                    stock_no = std[0]
                    stock_k = std[1]
                    if len(buy_done_list) < target_buy_count:
                        _buy_stock(stock_no,stock_k)
                        time.sleep(1)
                if t_now.minute == 30 and 0 <= t_now.second <=5:
                    stocks_cnt = len(get_mystock_balance('ALL'))
                    atcm.send_slack_msg("#stock",msg_proc)
                    time.sleep(5)
            if t_sell < t_now < t_exit:
                if _sell_stock() == True:
                    msgout(msg_sellall)
                    atcm.send_slack_msg("#stock",msg_sellall)
                    sys.exit(0)
            if t_exit < t_now:
                msgout(msg_end)
                atcm.send_slack_msg("#stock",msg_end)
                sys.exit(0)
            time.sleep(3)
    except Exception as ex:
        msgout('`main -> exception! ' + str(ex) + '`')

