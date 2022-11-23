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

def _get_buyable_currency():

    global buy_percent, total_cash , buy_amount

    atcm.auth(svr,product='01')
    buy_percent = atcm._cfg['buypercent']
    base_cach = atcm._cfg['basecash']
    total_cash = int(mystock.get_buyable_cash())
    if total_cash > base_cach:
        total_cash = base_cach
    else:
        total_cash = total_cash
    buy_amount = total_cash * buy_percent
    msgout('----------------100% 증거금 주문 가능 금액 :'+str(total_cash))
    msgout('----------------종목별 주문 비율 :'+str(buy_percent))
    msgout('----------------종목별 주문 금액 :'+str(buy_amount))
   
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
                if df.iloc[0]['Volume'] > 0:
                    today_open = df.iloc[0]['Open']
                    lastday = df.iloc[1]
                else:
                    continue
            else:
                continue
            lastday_high = lastday['High']
            lastday_low = lastday['Low']

            _target_price = today_open + (lastday_high - lastday_low) * bestk

            stock_data = trinfo.get_current_price(stock)
            aspr_unit = int(stock_data['aspr_unit'])
            _t_price = int(_target_price/aspr_unit)
            target_price = _t_price * aspr_unit            

            _stock_output = {'stock' : stock ,'target_p' : int(target_price)}
            stock_output.append(_stock_output)
            time.sleep(1)
        msgout(stock_output)
        return stock_output
    except Exception as ex:
        msgout("`get_buy_stock_info() -> exception! " + str(ex) + "`")
        return None      

# 초과 수익 혹은 최저 수익으로 매도 가능 주식 check
def _check_profit():
    try:
        # 보유한 주식과 예수금을 반환한다.
        mystocklist = mystock.get_acct_balance()
        mystockcnt = int(len(mystocklist))

        stocks= []
        if mystockcnt > 0:
            for i in range(0,mystockcnt):
                stock_code = mystocklist.iloc[i].name
                stock_psbl_qty = mystocklist.iloc[i]['매도가능수량']
                stock_cur_price = mystocklist.iloc[i]['현재가']
                profit_percent = mystocklist.iloc[i]['수익율']
                current_price = int(trinfo.get_current_price(stock_code)['stck_prpr'])
                yesterday_sign = int(trinfo.get_current_price(stock_code)['prdy_vrss_sign'])

                #print(stock_code,stock_psbl_qty,stock_cur_price,profit_percent,current_price,yesterday_sign)
                #print(mystocklist)
                if profit_percent > 20.1 or (profit_percent <= -3.0 and yesterday_sign == 5):
                    stocks.append({'sell_code': stock_code, 'sell_qty': stock_psbl_qty,'sell_percent': profit_percent,'sell_price': stock_cur_price})
                #time.sleep(1)
            return stocks
        else:
            return None
    except Exception as ex:
        msgout("_check_profit() -> exception! " + str(ex))  

# 전일 주식 매도 가능 여부 확인
def _start_sellable_stock():
    try:
        # 보유한 주식과 예수금을 반환한다.
        mystocklist = mystock.get_acct_balance()
        mystockcnt = int(len(mystocklist))
        stocks= []
        if mystockcnt > 0:
            for i in range(0,mystockcnt):
                stock_code = mystocklist.iloc[i].name
                stock_name = mystocklist.iloc[i]['종목명']
                stock_psbl_qty = mystocklist.iloc[i]['매도가능수량']
                stock_cur_price = mystocklist.iloc[i]['현재가']
                profit_percent = mystocklist.iloc[i]['수익율']
                updown_percent = mystocklist.iloc[i]['등락율']

                if updown_percent >= 2.0:
                    non_buy_list.append(stock_code)
                    msgout('_start_sellable_stock --> 전일 주식 매도 중지 '+str(stock_name)+' 등락율('+str(updown_percent)+')')
                else:
                    stocks.append({'sell_code': stock_code, 'sell_qty': stock_psbl_qty,'sell_percent': profit_percent,'sell_price': stock_cur_price})

            return stocks
        else:
            return None
    except Exception as ex:
        msgout("_start_sellable_stock() -> exception! " + str(ex))

# 주식 매수 
def _buy_stock(infos):
    try:
        global buy_done_list

        stock = infos['stock']
        target_price = infos['target_p']

        if stock in buy_done_list: 
            return False

        current_price = int(trinfo.get_current_price(stock)['stck_prpr'])
        yesterday_sign = int(trinfo.get_current_price(stock)['prdy_vrss_sign'])
        buy_qty = 0

        if current_price > 0:
            buy_qty = int(buy_amount // target_price)
        if buy_qty < 1:
            return False

        # 변동성 돌파 매매 전략 실행
        if current_price >= target_price:
            msgout('현금주문 가능금액 : '+ str(buy_amount))
            msgout(str(stock) + '는 현재가 ('+str(current_price)+')이고  주문 가격 (' + str(target_price) +') ' + str(buy_qty) + ' EA : meets the buy condition!`')
            ret = atof.do_buy(str(stock) , buy_qty, target_price)
            if ret:
                msgout('변동성 돌파 매매 성공 -> 주식('+str(stock)+') 매수가격 ('+str(target_price)+') 전일 대비 사인 5:하락, 2:상승 ('+str(yesterday_sign)+')')
                buy_done_list.append(stock)
            else:
                msgout('변동성 돌파 매매 실패 -> 주식('+str(stock)+')')
                non_buy_list.append(stock)

    except Exception as ex:
        msgout("`_buy_stock("+ str(stock) + ") -> exception! " + str(ex) + "`")   

# 개별 주식 매도
def _sell_each_stock(stocks):
    # 보유한 모든 종목을 당일 종가 혹은 다음날 시작가에 매도 
    try:
        if stocks is None or int(len(stocks)) == 0:
            return False

        for s in stocks:
            ticker = s['sell_code']
            ticker_qty = s['sell_qty']
            ticker_percent = s['sell_percent']
            ticker_price_s = s['sell_price']
            ticker_price_n = int(trinfo.get_current_price(ticker)['stck_prpr'])
            if ticker_qty != 0:
                if ticker_price_n > ticker_price_s:
                    current_price = ticker_price_n
                else:
                    current_price = ticker_price_s

                ret = atof.do_sell(ticker, ticker_qty, current_price)
                if ret:
                    msg = '변동성 돌파 매도 주문(이익율 '+str(ticker_percent)+'% 달성) 성공 ->('+str(ticker)+')('+str(current_price)+')'
                    msgout(msg)
                    atcm.send_slack_msg("#stock",msg)
                else:
                    msg = '변동성 돌파 매도 주문(이익율 '+str(ticker_percent)+'% 달성) 실패 ->('+str(ticker)+')'
                    msgout(msg)
                    atcm.send_slack_msg("#stock",msg)
        return True
    except Exception as ex:
        msgout("_sell_each_stock() -> exception! " + str(ex))

# 주식 전량 매도
def _sell_stock():
    # 보유한 모든 종목을 당일 종가 혹은 다음날 시작가에 매도
    global ret 
    try:
        while True:
            stocks = get_mystock_balance('ALL')
            total_qty = 0
            for s in stocks:
                total_qty += s['qty']

            if total_qty == 0:
                return True

            for s in stocks:
                ticker = s['code']
                company = s['name']
                q_cnt = s['qty']

                if q_cnt == 0:
                    continue
                else:
                    current_price = int(trinfo.get_current_price(ticker)['stck_prpr'])
                    ret = atof.do_sell(ticker, q_cnt, current_price)
                    if ret:
                        msgout('변동성 돌파 매도 주문 성공 ->('+str(company)+')('+str(current_price)+')')
                    else:
                        msgout('변동성 돌파 매도 주문 실패 ->('+str(company)+')')
                time.sleep(0.1)
            time.sleep(30)
    except Exception as ex:
        msgout("_sell_stock() -> exception! " + str(ex))

if '__main__' == __name__:
    try:
        atcm.auth(svr,product='01')
        stock_list = atcm._cfg2['stlist']
        notwork_days = atcm._cfg['nodaylist']
        target_stock_values = []
        buy_done_list = []
        non_buy_list = []
        sell_stock_list = []
        target_buy_count = atcm._cfg['targetbuycount']
        buy_percent = 0
        total_cash = 0
        soldout = False

        while True:
            # 거래 가능 시간 정의
            t_now = datetime.now()
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=1, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
            today = datetime.today().weekday()
            holiday = datetime.today().strftime('%Y-%m-%d')

            # Message 정의 
            msg_end = '['+str(t_now)+'] Kospi & Kosdaq Closed Process self- destructed'
            msg_week = 'Today is', 'Saturday.' if today == 5 else 'Sunday.'
            msg_resell = '`sell_all() returned True -> 전날 잔여 주식 매도!`'
            msg_proc = 'The AlogoTrading process is still alive'
            msg_sellall = '`sell_all() returned True -> self-destructed!`'
            msg_holiday = 'Today is Holiday'

            # 장이 열리지 않는 날은 Exit
            if holiday in notwork_days:
                msgout(msg_holiday)
                atcm.send_slack_msg("#stock",msg_holiday)
                sys.exit(0)

            # 주말 , 주일은 Exit
            if today == 5 or today == 6:
                msgout(msg_week)
                atcm.send_slack_msg("#stock",msg_week)
                sys.exit(0)
            
             # 09:00 ~ 15:15 주식 거래 시작
            if t_9 < t_now < t_sell:
                # 09:00 ~ 09:01
                # 장 시작, 전일 판매하지 못한 잔여 주식 현재가에 매도           
                if t_9 < t_now < t_start and soldout == False:
                    soldout = True
                    sellable_stocks = _start_sellable_stock()
                    if _sell_each_stock(sellable_stocks) == True:
                        msgout(msg_resell)
                        atcm.send_slack_msg("#stock",msg_resell)
                # 주식 구매 가능 예수금을 가져온다
                if total_cash > 0 and buy_percent == atcm._cfg['buypercent']:
                    pass
                else:
                    _get_buyable_currency()
                
                # 매수할 타깃 주식을 가져온다.
                stocks_cnt = int(len(stock_list))
                target_cnt = int(len(target_stock_values))
                if stocks_cnt >= target_cnt:
                    pass
                else:
                    target_stock_values = get_buy_stock_info(stock_list)

                # 주식 매수 목표 갯수 보다 작으면 매수 진행
                if len(buy_done_list) < target_buy_count:
                    for bstock in target_stock_values:
                        if bstock['stock'] in buy_done_list or bstock['stock'] in non_buy_list:
                            continue

                        if len(buy_done_list) < target_buy_count:
                            _buy_stock(bstock)
                        else:
                            pass
                        time.sleep(1)
                # 매시 30분 마다 프로세스 확인 메시지(슬랙)를 보낸다
                if t_now.minute == 30 and 0 <= t_now.second <=14:

                    if t_now.hour > 12:
                        sell_stock_list = _check_profit()

                    if sell_stock_list is None or len(sell_stock_list) == 0:
                        atcm.send_slack_msg("#stock",msg_proc)
                    else:
                        _sell_each_stock(sell_stock_list)

                    time.sleep(1)

            # 변동성 매매 전략으로 주식 매도
            # 15:15 ~ 15:20
            if t_sell < t_now < t_exit:
                if _sell_stock() == True:
                    msgout(msg_sellall)
                    atcm.send_slack_msg("#stock",msg_sellall)
                    sys.exit(0)
            # 변동성 매매 프로세스 종료
            # 15:20 ~    
            if t_exit < t_now:
                msgout(msg_end)
                atcm.send_slack_msg("#stock",msg_end)
                sys.exit(0)
            time.sleep(3)
    except Exception as ex:
        msgout('`main -> exception! ' + str(ex) + '`')

