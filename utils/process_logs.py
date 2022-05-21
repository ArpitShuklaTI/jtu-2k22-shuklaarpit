import urllib.request
from datetime import datetime
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.contants import HTTP_READ_TIMEOUT


def sort_by_timestamp(logs: list[str]) -> list[list[str]]:
    data: list[list[str]] = [log.split(" ") for log in logs]
    # print(data)
    data = sorted(data, key=lambda elem: elem[1])
    return data


def format_response(raw_data: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    response: list[dict[str, Any]] = []
    for timestamp, data in raw_data.items():
        entry: dict[str, Any] = {'timestamp': timestamp}
        logs: list[dict[str, int]] = []
        data: dict[str, int] = {k: data[k] for k in sorted(data.keys())}
        for exception, count in data.items():
            logs.append({'exception': exception, 'count': count})
        entry['logs'] = logs
        response.append(entry)
    return response


def aggregate(cleaned_logs: list[list[str]]) -> dict[str, dict[str, int]]:
    data: dict[str, dict[str, int]] = {}
    for log in cleaned_logs:
        [key, text] = log
        value: dict[str, int] = data.get(key, {})
        value[text] = value.get(text, 0) + 1
        data[key] = value
    return data


def transform(logs: list[list[str]]) -> list[list[str]]:
    result: list[list[str]] = []
    for log in logs:
        [_, timestamp, text] = log
        text = text.rstrip()
        timestamp: datetime.datetime = datetime.utcfromtimestamp(int(int(timestamp) / 1000))
        hours, minutes = timestamp.hour, timestamp.minute
        key = ''

        if minutes >= 45:
            if hours == 23:
                key = "{:02d}:45-00:00".format(hours)
            else:
                key = "{:02d}:45-{:02d}:00".format(hours, hours + 1)
        elif minutes >= 30:
            key = "{:02d}:30-{:02d}:45".format(hours, hours)
        elif minutes >= 15:
            key = "{:02d}:15-{:02d}:30".format(hours, hours)
        else:
            key = "{:02d}:00-{:02d}:15".format(hours, hours)

        result.append([key, text])
        print(key)

    return result


def read_data_from_url(url: str, timeout: int) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        return conn.read()


def read_logs_from_urls(urls: list[str], num_threads: int) -> list[str]:
    """
        Read multiple files through HTTP
    """
    result: list[str] = []
    with ThreadPoolExecutor(num_threads) as executor:
        futures = [executor.submit(read_data_from_url, url, HTTP_READ_TIMEOUT) for url in urls]
        for future in as_completed(futures):
            data: str = future.result()
            data: str = data.decode('utf-8')
            result.extend(data.split("\n"))
    result = sorted(result, key=lambda elem: elem[1])
    return result
