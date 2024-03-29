from src.binance_api import load_futures_list
import multiprocessing
from binance import Client
from binance.enums import HistoricalKlinesType
import json
import datetime
import src.logger as custom_logging
from src.config_handler import TIMEFRAMES, BINANCE_API_KEY, BINANCE_Secret_KEY


THREAD_CNT = 1  # 3 потока на ядро


def check_history_bars_for_pattern(pair, bars: list) -> str:
    """
    Поиск свечного паттерна в барах истории
    :param bars:
    :return:
    """
    if len(bars) < 3:
        print(f'{pair}: Bar count = {len(bars)}.')
        return ""
    _time = []
    close = []
    volume = []

    for bar in bars:
        value = datetime.datetime.fromtimestamp(bar[0]/1000)
        # print(value.strftime('%Y-%m-%d %H:%M:%S'))
        _time.append(value.strftime('%Y-%m-%d %H:%M:%S'))
        close.append(float(bar[4]))
        volume.append(float(bar[5]))

    # проверяем значения на паттерны
    if close[2] > close[1] > close[0] and volume[2] < volume[1]:
        # цена 2 дня росла, а объемы падали
        custom_logging.info(
            f'{pair}: CLOSE: {close[2]} > {close[1]} > {close[0]} VOL: {volume[2]} < {volume[1]} => SHORT')
        return "SHORT"
    elif close[2] < close[1] < close[0] and volume[2] < volume[1]:
        # цена 2 дня падала и объемы тоже падали
        custom_logging.info(
            f'{pair}: CLOSE: {close[2]} < {close[1]} < {close[0]} VOL: {volume[2]} < {volume[1]} => LONG')
        return "LONG"
    return ""


def load_history_bars(task):
    """
    Load historical bars
    :return:
    """
    result = dict()
    pair = task[0]
    api_key = task[1]
    secret_key = task[2]
    all_timeframes = task[3]
    is_spot = task[4]
    client = Client(api_key, secret_key)

    try:
        result['id'] = pair
        for timeframe in all_timeframes:
            if timeframe == '1d':
                st_time = "4 day ago UTC"
            else:
                print('Unknown timeframe:', timeframe)
                custom_logging.error(f'Load history bars error: unknown timeframe "{timeframe}"')
                continue

            bars = []
            try:
                if is_spot:
                    bars = client.get_historical_klines(pair, timeframe, st_time, HistoricalKlinesType.SPOT)

                else:
                    bars = client.get_historical_klines(pair, timeframe, st_time,
                                                        klines_type=HistoricalKlinesType.FUTURES)

            except Exception as e:
                print(pair, ':', e)

            if len(bars) == 0:
                print(f" 0 bars has been gathered from server. client.get_historical_klines({pair}, {timeframe}, "
                      f"{st_time})")
                result[timeframe] = 0
                continue
            signal = check_history_bars_for_pattern(pair, bars)
            result["signal"] = signal
        return result
    except Exception as e:
        print("Exception when calling load_history_bars: ", e)
        return None


def load_futures_history_bars_end(responce_list):
    data = dict()
    for responce in responce_list:
        id = responce['id']
        del responce['id']
        if responce['signal'] != '':
            data[id] = responce['signal']
    # print(data)

    try:
        with open(f"signals/{datetime.date.today().isoformat()}.txt", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4, separators=(',', ': '))
            print('Signals data  stored to file.')
            custom_logging.info(f'New signals data  stored to file "signals/{datetime.date.today().isoformat()}.txt".')
            custom_logging.info(f'**************************************************************************************')
    except Exception as e:
        print("load_futures_history_bars_end exception:", e)
        custom_logging.error(f'load_futures_history_bars_end exception: {e}')



if __name__ == '__main__':
    futures_list = load_futures_list()
    print('Futures count:', len(futures_list))
    tasks = []
    try:
        custom_logging.info('Gathering history candles data...')
        for symbol in futures_list:
            tasks.append((symbol, BINANCE_API_KEY, BINANCE_Secret_KEY, TIMEFRAMES, False))
        with multiprocessing.Pool(multiprocessing.cpu_count() * THREAD_CNT) as pool:
            pool.map_async(load_history_bars, tasks, callback=load_futures_history_bars_end)
            pool.close()
            pool.join()
    except Exception as ex:
        print("Load history bars exception:", ex)
        custom_logging.error(f"Load history bars exception: {ex}")

