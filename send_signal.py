import datetime
import json
import os
import time

from src.telegram_api import send_signal
from src.config_handler import TLG_TOKEN, TLG_CHANNEL_ID


def read_signal_data(file):
    if os.path.isfile(file) is False:  # file not exists
        print(f'File  "{file}" not exists.')
        return None
    with open(file, 'r', encoding='utf-8') as f:
        signal_data = json.load(f)
    return signal_data


if __name__ == "__main__":
    current_date = datetime.date.today().isoformat()
    signal_data = read_signal_data(f'signals/{current_date}.txt')
    if signal_data:
        signal_str = ''
        while len(signal_data) > 0:
            signal = signal_data.popitem()
            signal_str += f'{signal[0]}: {signal[1]}\n'
            if len(signal_str) > 4000:# размер сообщения близок к максимальному => отправляем
                send_signal(signal_data, TLG_TOKEN, TLG_CHANNEL_ID)
                time.sleep(1)
        if len(signal_str) > 0:
            send_signal(signal_str, TLG_TOKEN, TLG_CHANNEL_ID)













