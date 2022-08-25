# -*- coding: utf-8 -*-
'''
# 알고리즘 트래이딩 시스템
# Auth : mrtom17
# AlgoTrade3.py
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

# Function 정의

# 주식 보유 잔고를 가져온다
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

# 주식 리스트에서 Target Price 를 리턴한다        
def get_buy_stock_info(stock_list):
    try:
        stock_output = []
        for std in stock_list:
            stock = std[0]
            bestk = std[1]
            t_now = datetime.now()
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
            _target_price = today_open + (lastday_high - lastday_low) * bestk

            stock_data = trinfo.get_current_price(stock)
            aspr_unit = int(stock_data['aspr_unit'])
            _t_price = int(_target_price/aspr_unit)
            target_price = _t_price * aspr_unit            

            _stock_output = {'stock' : stock ,'target_p' : int(target_price) , 'ma5' : _target_price, 'ma10' : _t_price}
            stock_output.append(_stock_output)
            time.sleep(1)
        return stock_output

    except Exception as ex:
        msgout("`get_buy_stock_info() -> exception! " + str(ex) + "`")
        return None      

# 초과 수익으로 매도 가능 주식 check
def _check_profit():
    # 보유한 모든 종목을 당일 종가 혹은 다음날 시작가에 매도 
    try:
        # 보유한 주식과 예수금을 반환한다.
        mystocklist = mystock.get_acct_balance()
        stocks= []
        for i in range(0,len(mystocklist)):
            stock_code = mystocklist.iloc[i].name
            stock_psbl_qty = mystocklist.iloc[i]['매도가능수량']
            stock_cur_price = mystocklist.iloc[i]['현재가']
            profit_percent = mystocklist.iloc[i]['수익율']
            if profit_percent > 9.5:
                stocks.append({'sell_code': stock_code, 'sell_qty': stock_psbl_qty,'sell_price': stock_cur_price})
            time.sleep(1)
        return stocks
    except Exception as ex:
        msgout("_check_profit() -> exception! " + str(ex))  

# 주식 매수 
def _buy_stock(infos):
    try:
        global buy_done_list

        stock = infos['stock']
        target_price = infos['target_p']
        ma5 = infos['ma5']
        ma10 = infos['ma10']

        if stock in buy_done_list: 
            return False

        current_price = int(trinfo.get_current_price(stock)['stck_prpr'])
        buy_qty = 0

        if current_price > 0:
            buy_qty = int(buy_amount // target_price)
        if buy_qty < 1:
            return False

        #stock_name, stock_qty = get_mystock_balance(stock)

        # 변동성 돌파 매매 전략 실행
        #print(stock,current_price,target_price)
        if current_price >= target_price:
            msgout('현금주문 가능금액 : '+ str(buy_amount))
            msgout(str(stock) + '는 현재가 ('+str(current_price)+')이고  주문 가격 (' + str(target_price) +') ' + str(buy_qty) + ' EA : meets the buy condition!`')
            ret = atof.do_buy(str(stock) , buy_qty, target_price)
            if ret:
                msgout('변동성 돌파 매매 성공 -> 주식('+str(stock)+') 매수가격 ('+str(target_price)+')')
                buy_done_list.append(stock)
                return True
            else:
                msgout('변동성 돌파 매매 실패 -> 주식('+str(stock)+')')
    except Exception as ex:
        msgout("`_buy_stock("+ str(stock) + ") -> exception! " + str(ex) + "`")   

# 초과 수익 달성 주식 장중 매도
def _sell_each_stock(stocks):
    # 보유한 모든 종목을 당일 종가 혹은 다음날 시작가에 매도 
    try:
        for s in stocks:
            if s['sell_qty'] != 0:
                current_price_n = int(trinfo.get_current_price(s['sell_code'])['stck_prpr'])
                current_price_s = s['sell_price']
                if current_price_n > current_price_s:
                    current_price = current_price_n
                else:
                    current_price = current_price_s

                ret = atof.do_sell(s['sell_code'], s['sell_qty'], current_price)
                if ret:
                    msgout('변동성 돌파 매도 주문(이익율 4.8% 달성) 성공 ->('+str(s['sell_code'])+')('+str(current_price)+')')
                    return True
                else:
                    msgout('변동성 돌파 매도 주문(이익율 4.8% 달성) 실패 ->('+str(s['sell_code'])+')')
                    return False
    except Exception as ex:
        msgout("_sell_each_stock() -> exception! " + str(ex))

# 주식 매도
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
        target_stock_values = []
        buy_done_list = []
        target_buy_count = 5
        buy_percent = 0.19
        total_cash = int(mystock.get_buyable_cash())
        buy_amount = total_cash * buy_percent
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
                if target_stock_values:
                    pass
                else:
                    target_stock_values = get_buy_stock_info(stock_list)

            if t_start < t_now < t_sell:
                # 임시
                if target_stock_values:
                    pass
                else:
                    target_stock_values = get_buy_stock_info(stock_list)
                if len(buy_done_list) < target_buy_count:
                    for bstock in target_stock_values:
                        if bstock['stock'] in buy_done_list:
                            pass
                        if len(buy_done_list) < target_buy_count:
                            _buy_stock(bstock)
                        else:
                            pass
                        time.sleep(1)
                if len(buy_done_list) > 0:
                    sellable_stock =_check_profit()
                    if len(sellable_stock) > 0:
                        _sell_each_stock(sellable_stock)
                if t_now.minute == 30 and 0 <= t_now.second <=20:
                    atcm.send_slack_msg("#stock",msg_proc)
                    time.sleep(1)
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

