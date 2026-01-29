# 這是用來從永豐的網站下載所有的 ticks。為的是模擬每天放空的真實情況
import sys
import datetime
import time
import signal
import shioaji as sj
from shioaji import contracts
from shioaji import constant
import json
import requests
import os
import platform
import queue
import threading
import configparser
import gzip
from datetime import timedelta, date
import pandas as pd
import platform
from mypylib import get_all_stock_code_name_dict
from time import sleep
from pathlib import Path

from mypylib.keys import SHIOAJI_API_KEY, SHIOAJI_SECRET_KEY

list_all_symbol = get_all_stock_code_name_dict()
print(list_all_symbol)

dir_basepath = '.'
start_date = date(2022, 1, 1)
end_date = datetime.datetime.today().date()
security_type_downloaded = 0

# 斷點續傳相關
RESUME_FILE = 'resume_progress.txt'
current_symbol = None


def signal_handler(sig, frame):
    """處理 Ctrl-C，儲存當前進度"""
    global current_symbol
    if current_symbol:
        resume_path = f'{dir_basepath}/{RESUME_FILE}'
        with open(resume_path, 'w') as f:
            f.write(current_symbol)
        print(f'\n\nInterrupted! Progress saved at symbol: {current_symbol}')
        print(f'Resume file: {resume_path}')
    sys.exit(0)


def load_resume_symbol():
    """讀取上次中斷的位置"""
    resume_path = f'{dir_basepath}/{RESUME_FILE}'
    if os.path.isfile(resume_path):
        with open(resume_path, 'r') as f:
            symbol = f.read().strip()
        if symbol:
            print(f'Found resume file, will resume from symbol: {symbol}')
            return symbol
    return None


def clear_resume_file():
    """完成後刪除 resume 檔案"""
    resume_path = f'{dir_basepath}/{RESUME_FILE}'
    if os.path.isfile(resume_path):
        os.remove(resume_path)
        print('All downloads completed, resume file removed.')


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def contracts_cb(security_type):
    global security_type_downloaded
    security_type_downloaded += 1
    print(f"{repr(security_type)} fetch done.")


def login(api_key=SHIOAJI_API_KEY,
          secret_key=SHIOAJI_SECRET_KEY,
          ca_path="certificate/SinopacKen.pfx",
          ca_password='H121933940',
          person_id='H121933940'):
    api = sj.Shioaji()
    api.login(api_key, secret_key, contracts_cb=contracts_cb)
    while True:
        if security_type_downloaded != 4:
            sleep(1)
            continue
        break
    return api


def do_redownload(api, dir_basepath, symbol, date_str):
    print(f'Re-downlaod {symbol} on {date_str}')
    ticks = api.ticks(api.Contracts.Stocks[symbol], date_str)
    df = pd.DataFrame({**ticks})
    # print(df)
    df.ts = pd.to_datetime(df.ts)
    df.to_csv(f'{dir_basepath}/{symbol}/{date_str}.csv', mode='w+')


def get_trading_days_from_0050(dir_basepath):
    """從 0050 資料夾取得所有交易日清單"""
    path_0050 = f'{dir_basepath}/0050'
    if not os.path.isdir(path_0050):
        return []

    files = os.listdir(path_0050)
    trading_days = []
    for f in files:
        if f.endswith('.csv') and f.startswith('20'):
            trading_days.append(f.replace('.csv', ''))
    trading_days.sort()
    return trading_days


def update_0050_backward(api, dir_basepath, start_date, end_date):
    """反向更新 0050（從最新日期往回下載到已有記錄為止），建立交易日參考"""
    symbol = '0050'
    base_path = f'{dir_basepath}/{symbol}'

    if not os.path.isdir(base_path):
        os.mkdir(base_path)

    # 建立日期清單並反向
    all_dates = []
    for single_date in date_range(start_date, end_date):
        if single_date.weekday() in (5, 6):
            continue
        all_dates.append(single_date.strftime("%Y-%m-%d"))

    # 反向下載（從最新往回）
    for date_str in reversed(all_dates):
        file_path = f'{base_path}/{date_str}.csv'

        # 遇到已存在的檔案就停止，代表已追上之前的記錄
        if os.path.isfile(file_path):
            break

        # 下載並儲存
        bool_tick_downloaded = False
        while not bool_tick_downloaded:
            try:
                ticks = api.ticks(api.Contracts.Stocks[symbol], date_str)
                bool_tick_downloaded = True
            except Exception as e:
                print(f'Error downloading {symbol} on {date_str}: {str(e)}')
                time.sleep(60)
                api = login()
                print("Finish re-login")

        if len(ticks.ts) == 0:
            time.sleep(1)
            continue

        df = pd.DataFrame({**ticks})
        df.ts = pd.to_datetime(df.ts)
        df.to_csv(file_path, mode='w+')
        print(f'{symbol} {date_str}')
        time.sleep(1)

    return api


def update_stock_forward(api, dir_basepath, symbol, trading_days):
    """正向更新已有資料的股票，檢測是否下市"""
    base_path = f'{dir_basepath}/{symbol}'

    # 找出最後一筆記錄
    files = [f for f in os.listdir(base_path) if f.endswith('.csv') and f.startswith('20')]
    files.sort()

    if not files:
        return api, False  # 沒有資料，需要反向更新

    last_date = files[-1].replace('.csv', '')

    # 找出需要下載的交易日（在 last_date 之後的）
    days_to_download = [d for d in trading_days if d > last_date]

    consecutive_empty = 0

    for date_str in days_to_download:
        file_path = f'{base_path}/{date_str}.csv'

        if os.path.isfile(file_path):
            consecutive_empty = 0
            continue

        bool_tick_downloaded = False
        while not bool_tick_downloaded:
            try:
                ticks = api.ticks(api.Contracts.Stocks[symbol], date_str)
                bool_tick_downloaded = True
            except Exception as e:
                print(f'Error downloading {symbol} on {date_str}: {str(e)}')
                time.sleep(60)
                api = login()
                print("Finish re-login")

        if len(ticks.ts) == 0:
            consecutive_empty += 1
            if consecutive_empty >= 5:
                # 標記為下市
                with open(f'{base_path}/dead.txt', 'w') as f:
                    f.write(f'Marked as dead on {datetime.datetime.now()}')
                print(f'{symbol} marked as DEAD')
                return api, True
            time.sleep(1)
            continue

        consecutive_empty = 0
        df = pd.DataFrame({**ticks})
        df.ts = pd.to_datetime(df.ts)
        df.to_csv(file_path, mode='w+')
        print(f'{symbol} {date_str}')
        time.sleep(1)

    return api, True


def update_stock_backward(api, dir_basepath, symbol, trading_days):
    """反向更新新股票，直到找到上市前"""
    base_path = f'{dir_basepath}/{symbol}'

    if not os.path.isdir(base_path):
        os.mkdir(base_path)

    # 反向遍歷交易日
    reversed_days = list(reversed(trading_days))

    consecutive_empty = 0

    for date_str in reversed_days:
        file_path = f'{base_path}/{date_str}.csv'

        # 遇到已存在的檔案就停止，代表已追上之前的記錄
        if os.path.isfile(file_path):
            break

        bool_tick_downloaded = False
        while not bool_tick_downloaded:
            try:
                ticks = api.ticks(api.Contracts.Stocks[symbol], date_str)
                bool_tick_downloaded = True
            except Exception as e:
                print(f'Error downloading {symbol} on {date_str}: {str(e)}')
                time.sleep(60)
                api = login()
                print("Finish re-login")

        if len(ticks.ts) == 0:
            consecutive_empty += 1
            if consecutive_empty >= 5:
                print(f'{symbol} reached before IPO, stopping')
                return api
            time.sleep(1)
            continue

        consecutive_empty = 0
        df = pd.DataFrame({**ticks})
        df.ts = pd.to_datetime(df.ts)
        df.to_csv(file_path, mode='w+')
        print(f'{symbol} {date_str}')
        time.sleep(1)

    return api


def recheck_all_ticks(dir_basepath):
    dirs = os.listdir(dir_basepath)
    dirs.sort()
    for _dir in dirs:
        if _dir.startswith('.'):
            continue
        if _dir == 'cache':
            continue
        if not os.path.isdir(f'{dir_basepath}/{_dir}'):
            continue
        # if _dir < '3171':
        #     continue
        print(_dir)

        files = os.listdir(f'{dir_basepath}/{_dir}')
        files.sort()
        for file in files:
            if not file.endswith('csv'):
                continue
            file_full_path = f'{dir_basepath}/{_dir}/{file}'
            # print(file_full_path)
            try:
                df = pd.read_csv(file_full_path, low_memory=False)
            except Exception as e:
                print(f'{file_full_path} {e}')
                do_redownload(api, dir_basepath, _dir, file.split('.')[0])
                continue

            ret = df[df['ts'] == 'ts']
            if ret.empty:
                continue

            # Data duplicated
            if (df.shape[0] - 1) / 2 == ret.index[0]:
                upper = df.iloc[:ret.index[0], 1:]
                lower = df.iloc[ret.index[0] + 1:, 1:]
                lower.index = range(0, lower.shape[0])

                if upper.equals(lower):
                    print(f'{_dir} {file} data duplicated')
                    df = pd.DataFrame({**upper})
                    if os.path.exists(file_full_path):
                        os.remove(file_full_path)
                    df.to_csv(file_full_path, mode='w+')

                continue
            else:
                do_redownload(api, dir_basepath, _dir, file.split('.')[0])
                sleep(1)


if __name__ == '__main__':

    # Ken
    if True:
        api = login()
    else:
        # William
        api = login(api_key='C8Uk3Vj1AVM6xoSmz3B9h2LWmga4S2CGkYQTY29Pphk9',
                    secret_key='2EeCpaJe6VrHuhk72z53oM4pH1bF2NhLp1wCyX3oWrva')

    if not os.path.isdir(dir_basepath):
        os.mkdir(dir_basepath)

    # Check command line arguments
    if len(sys.argv) == 1:
        # Original functionality - download all symbols
        pass
    elif len(sys.argv) >= 2 and sys.argv[1] == '-check':
        # Check for incomplete data
        redownload = '-redownload' in sys.argv
        
        dirs = os.listdir(dir_basepath)
        dirs.sort()
        for _dir in dirs:
            if _dir.startswith('.') or _dir.startswith('0') or _dir == 'cache' or not os.path.isdir(f'{dir_basepath}/{_dir}'):
                continue
            
            files = os.listdir(f'{dir_basepath}/{_dir}')
            files.sort()
            for file in files:
                if not file.endswith('csv'):
                    continue
                file_date = file.split('.')[0]
                if file_date < '2022-01-01':
                    continue
                file_full_path = f'{dir_basepath}/{_dir}/{file}'
                try:
                    df = pd.read_csv(file_full_path, low_memory=False)
                except Exception as e:
                    print(f'Error reading {file_full_path}: {e}')
                    continue

                # Check for missing 13:30:00 time
                if not any(df['ts'].str.contains('13:30:00')):
                    print(f'Incomplete data for {_dir} on {file_date}')
                    if redownload:
                        do_redownload(api, dir_basepath, _dir, file_date)
                        print(f'Re-downloaded {_dir} on {file_date}')
                        sleep(1)

        exit(0)
    elif len(sys.argv) >= 2 and sys.argv[1] == '-ticktype':
        # Check for missing tick_type column
        dirs = os.listdir(dir_basepath)
        dirs.sort()
        for _dir in dirs:
            if len(_dir) != 4 or not _dir.isdigit():
                continue

            files = os.listdir(f'{dir_basepath}/{_dir}')
            files.sort()
            for file in files:
                if not file.startswith('20') or not file.endswith('csv'):
                    continue
                file_date = file.split('.')[0]
                if file_date < '2020-01-01':
                    continue
                file_full_path = f'{dir_basepath}/{_dir}/{file}'
                try:
                    df = pd.read_csv(file_full_path, low_memory=False)
                except Exception as e:
                    print(f'Error reading {file_full_path}: {e}')
                    continue

                # Check for missing tick_type column
                if 'tick_type' not in df.columns:
                    print(f'Missing tick_type for {_dir} on {file_date}')
                    do_redownload(api, dir_basepath, _dir, file_date)
                    print(f'Re-downloaded {_dir} on {file_date}')
                    sleep(1)

        exit(0)
    elif len(sys.argv) == 3:
        # New functionality - download specific symbol and date
        symbol = sys.argv[1]
        date_str = sys.argv[2]
        
        try:
            # Validate date format
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
            
            # Create directory for symbol if it doesn't exist
            base_symbol_path = f'{dir_basepath}/{symbol}'
            if not os.path.isdir(base_symbol_path):
                os.mkdir(base_symbol_path)
            
            # Download ticks for specific symbol and date
            contract = api.Contracts.Stocks[symbol]
            ticks = api.ticks(contract, date_str)
            
            if len(ticks.ts) == 0:
                print(f'No data available for {symbol} on {date_str}')
                exit(0)
            
            # Save to CSV
            df = pd.DataFrame({**ticks})
            df.ts = pd.to_datetime(df.ts)
            output_file = f'{dir_basepath}/{symbol}/{date_str}.csv'
            df.to_csv(output_file, mode='w+')
            print(f'Successfully downloaded {symbol} data for {date_str}')
            exit(0)
            
        except ValueError:
            print("Error: Date must be in YYYY-MM-DD format")
            exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            exit(1)
    else:
        print("Usage:")
        print("  No arguments: Download all symbols")
        print("  check: Check and fix existing data")
        print("  <symbol> <date>: Download specific symbol data for date (YYYY-MM-DD)")
        exit(1)

    # 註冊 Ctrl-C handler
    signal.signal(signal.SIGINT, signal_handler)

    # 檢查是否有需要 resume 的進度
    resume_symbol = load_resume_symbol()
    skip_until_resume = resume_symbol is not None

    # 1. 先更新 0050（作為交易日參考，從最新日期往回下載）
    print("=== Updating 0050 (reference) ===")
    api = update_0050_backward(api, dir_basepath, start_date, end_date)

    # 2. 取得交易日清單
    trading_days = get_trading_days_from_0050(dir_basepath)
    print(f"Total trading days: {len(trading_days)}")

    if len(trading_days) == 0:
        print("Error: No trading days found from 0050. Please check 0050 data.")
        exit(1)

    # 3. 更新其他股票
    list_contract = list(api.Contracts.Stocks.OTC) + list(api.Contracts.Stocks.TSE)

    for x in list_contract:
        if len(x.code) != 4:
            continue

        symbol = x.code

        # 跳過 0050（已處理）
        if symbol == '0050':
            continue

        # 跳過特定股票
        if symbol in ['4804', '7642']:
            continue

        # 如果有 resume，跳過直到找到上次中斷的股票
        if skip_until_resume:
            if symbol == resume_symbol:
                skip_until_resume = False
                print(f'Resuming from symbol: {symbol}')
            else:
                continue

        # 記錄當前處理的股票（供 Ctrl-C handler 使用）
        current_symbol = symbol

        base_path = f'{dir_basepath}/{symbol}'

        # 檢查是否已標記為下市
        if os.path.isfile(f'{base_path}/dead.txt'):
            print(f'{symbol} is dead, skipping')
            continue

        # 檢查是否有現有資料
        has_data = os.path.isdir(base_path) and any(
            f.endswith('.csv') and f.startswith('20')
            for f in os.listdir(base_path)
        )

        if has_data:
            # 正向更新
            print(f'{symbol} - forward update')
            api, _ = update_stock_forward(api, dir_basepath, symbol, trading_days)
        else:
            # 反向更新（新股票）
            print(f'{symbol} - backward update (new stock)')
            api = update_stock_backward(api, dir_basepath, symbol, trading_days)

    # 全部完成，刪除 resume 檔案
    clear_resume_file()
    print("=== All downloads completed ===")
