### Данные из рекламного кабинета TikTok 

TIKTOK_CREDENTIALS = {
    "secret": "<YOUR CLIENT SECRET>",
    "app_id": "<YOUR APP ID>",
    "auth_code": "<YOUR AUTH CODE>"
}

import json
import datetime
import os

import sqlalchemy
from sqlalchemy.dialects.mssql import pymssql
import urllib.parse

import requests
from six import string_types
from six.moves.urllib.parse import urlencode
from six.moves.urllib.parse import urlunparse

import pandas as pd
import numpy as np
import re

# Запрос на получения токена длительного доступа
def get_tiktok_access_token(tiktok_credentials):
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.post(
        url='https://ads.tiktok.com/open_api/v1.2/oauth2/access_token',
        headers=headers,
        data=str(tiktok_credentials))
    return response

# Все рекламные акккаунты, к которым есть доступ
advertiser_ids = [
    '<YOUR #1 ACCOUNT ID>',
    '<YOUR #2 ACCOUNT ID>',
    ...
]

# Макропеременные
ACCESS_TOKEN = "<YOUR ACCESS TOKEN>"
START_DATE = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(5), '%Y-%m-%d')
END_DATE = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(1), '%Y-%m-%d')
PAGE_SIZE = 1000
METRICS = [
    "campaign_name", # название кампании
    "adgroup_name", # название группы объявлений
    "spend", # потраченные деньги (валюта задаётся в рекламном кабинете)
    "impressions", # просмотры
    "reach", # количество уникальных пользователей, смотревших рекламу
    "clicks", # клики
]

# campaign > ad_group > ads поэтому тип рекламы AUCTION_ADGROUP и dimensions включает adgroup_id
def get_args(advertiser_id: str) -> dict:
    return {
        "metrics": METRICS, # список метрик, описанный выше
        "data_level": "AUCTION_ADGROUP", # тип рекламы
        "start_date": START_DATE, # начальный день запроса
        "end_date": END_DATE, # конечный день запроса
        "page_size": PAGE_SIZE, # размер страницы - количество объектов, которое возвращается за один запрос 
        "page": 1, # порядковый номер страницы (если данные не поместились в один запрос, аргумент инкрементируется)
        "advertiser_id": advertiser_id, # один из ID из advertiser_ids, который мы получили при генерации access token
        "report_type": "BASIC", # тип отчета
        "dimensions": ["adgroup_id", "stat_time_day"] # аргументы группировки, вплоть до объявления и за целый день
    }


def build_url(advertiser_id: str) -> str:
    """генерирует url на основе словаря args с аргументами запроса"""
    query_string = urlencode({k: v if isinstance(v, string_types) else json.dumps(v)
                              for k, v in get_args(advertiser_id).items()})
    scheme = "https"
    # netloc = "ads.tiktok.com"
    # Новый домен после обновления, подробнее:
    # https://ads.tiktok.com/marketing_api/docs?rid=esb88xalm6m&id=1709207085043713
    netloc = "business-api.tiktok.com"
    path = "/open_api/v1.2/reports/integrated/get/"
    return urlunparse((scheme, netloc, path, "", query_string, ""))


def get(advertiser_id: str) -> dict:
    """отправляет запрос к TikTok Marketing API
    возвращает результат в виде преобразованного json в словарь"""
    url = build_url(advertiser_id)
    headers = {"Access-Token": ACCESS_TOKEN}
    rsp = requests.get(url, headers=headers)
    return rsp.json()


def check_http_307_redirection():
    """Чтобы корректно работать на новом домене HTTP-клиент должен поддерживать редирект HTTP 307.
    Подробнее: https://ads.tiktok.com/marketing_api/docs?rid=esb88xalm6m&id=1709207085043713"""
    response = requests.post(
        url='https://httpbingo.org/redirect-to?url=https://nghttp2.org/httpbin/post&status_code=307',
        headers={'Content-Type': 'application/json'},
        data='"data":"hello world"')
    if response.status_code == 307:
        return 'WARNING! Requires Configure HTTP 307 redirection.'
    else:
        return 'OK! HTTP 307 Redirection Configured.'

# словарь, в который будем записывать ответы
result_dict = {}
# результирующий DataFrame, который будем прокидывать в бд
df = pd.DataFrame()
# проверяем корректность настройки
# check_http_307_redirection()

for advertiser_id in advertiser_ids:
    page = 1 # сначала всегда получаем данные по первой странице
    result = get(advertiser_id) # первый запрос
    if result['message'] != 'OK':
    # если ответ не пришел, переходим к следующему аккаунту
        continue
    result_dict[advertiser_id] = result['data']['list'] # сохраняем ответ на запрос к первой странице

    # пока текущая полученная страница page меньше общего количества страниц в последнем ответе result
    while page < result['data']['page_info']['total_page']:
        # увеличиваем значение страницы на 1
        page += 1
        # обновляем значение текущей страницы в словаре аргументов запроса
        args['page'] = page
        # запрашиваем ответ по текущей странице page
        result = get(advertiser_id)
        # накапливаем ответ
        result_dict[advertiser_id] += result['data']['list']
    # временный список
    adv_result_list = []
    
    # для каждого объекта
    for adv_input_row in result_dict[advertiser_id]:
        # берём словарь метрик
        metrics = adv_input_row['metrics']
        # насыщаем этот словарь словарём измерений
        metrics.update(adv_input_row['dimensions'])
        # добавляем полученный объект во временный список
        adv_result_list.append(metrics)

    # преобразуем временный словарь в DataFrame 
    result_df = pd.DataFrame(adv_result_list)
    # добавляем колонку со значением id аккаунта
    result_df['account'] = advertiser_id
    # добавляем получившийся DataFrame в результирующий
    df = df.append(result_df, ignore_index=True)

def get_country(row):
    if re.search('FR', row["campaign_name"]):
        return 'FR'
    elif re.search('ES', row["campaign_name"]):
        return 'ES'
    else:
        return 'Unknown'

# Форматирование полученных метрик
df["country"] = df.apply(get_country, axis=1)
df["spend"] = df.spend.apply(float)
df["stat_time_day"] = df["stat_time_day"].apply(pd.Timestamp).dt.date
for metric in ['impressions', 'reach', 'clicks']:
    df[metric] = df[metric].apply(int)

# Группировка
temp = (df.groupby(["stat_time_day","country"])
    [["spend","impressions","reach","clicks"]]
    .sum()
    .reset_index()
    .rename(columns={"stat_time_day": "date"})
    .assign(channel="Tiktok"))
temp["spend"] = temp.spend.apply(float).apply(round, ndigits=2)

#### Подключение к базе данных (см. Dockerfile)

hostname = os.environ.get("DB_HOST")
username = os.environ.get("DB_USER")
password = os.environ.get("DB_PWD")

SCHEMA = '<YOUR SHEMA>'
TABLE = '<YOUR TABLE>'

engine = sqlalchemy.create_engine(f'mssql+pymssql://{username}:{password}@{hostname}')

#### Удаление последних дней из базы

engine.execute(f"""delete from {SCHEMA}.{TABLE}
where date between '{START_DATE}' and '{END_DATE}'""")

#### Запись новых данных 

temp.to_sql(TABLE,
            schema=SCHEMA,
            con=engine,
            if_exists='append',
            index=False,
            chunksize=128,
            method="multi")
print("Data upload success!")