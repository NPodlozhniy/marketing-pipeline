### Данные из рекламного кабинета Facebook 

from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adreportrun import AdReportRun
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.adaccountuser import AdAccountUser as AdUser

import sqlalchemy
from sqlalchemy.dialects.mssql import pymssql
import urllib.parse
import datetime
import os
from itertools import chain
import pandas as pd
import numpy as np
import time

# Макропеременные
MY_ACCESS_TOKEN = '<YOUR ACCESS TOKEN>'
MY_APP_ID = '<YOUR APP ID>'
MY_APP_SECRET = '<YOUR APP SECRET>'
START_DATE = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(5), '%Y-%m-%d')
END_DATE = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(1), '%Y-%m-%d')


# Инициализация
FacebookAdsApi.init(MY_APP_ID, MY_APP_SECRET, MY_ACCESS_TOKEN)
me = AdUser(fbid='me')
my_accounts = list(me.get_ad_accounts())

# Узнать часовой пояс аккаунта
# my_accounts[0].api_get(fields=[AdAccount.Field.timezone_name])

fields = [
    AdsInsights.Field.spend,
    AdsInsights.Field.impressions,
    AdsInsights.Field.reach,
    AdsInsights.Field.clicks]

count = 1

def wait_for_async_job(async_job):
    global count
    async_job = async_job.api_get()
    while async_job[AdReportRun.Field.async_status] != 'Job Completed' or async_job[
        AdReportRun.Field.async_percent_completion] < 100:
        time.sleep(30)
        async_job = async_job.api_get()
    else:
        print("Job " + str(count) + " completed")
        count += 1
    return async_job.get_result(params={"limit": 1000})

def get_insights(account):
    account = AdAccount(account["id"])
    i_async_job = account.get_insights(
        params={
            'time_range': {'since': START_DATE, 'until': END_DATE},
            'level': 'account',
            'breakdowns': ['country'],
            'date_preset': 'last_7d',
            'time_increment': 1},
            fields=fields,
            is_async=True)
    results = [dict(item) for item in wait_for_async_job(i_async_job)]
    return results

# Получаем данные из всех аккаунтов
insights_lists = []
for account in my_accounts:
    insights_lists.append(get_insights(account))
# Укладываем их в DataFrame
df = pd.DataFrame(list(chain.from_iterable(insights_lists)),
                  columns=["date_start", "country", "spend", "impressions", "reach", "clicks"])

def get_country(row):
    if row["country"] == 'FR':
        return 'France'
    elif row["country"] == 'ES':
        return 'Spain'
    else:
        return 'Unknown'

# Форматирование полученных метрик
df["country"] = df.apply(get_country, axis=1)
df["date_start"] = df["date_start"].apply(pd.Timestamp).dt.date
df["spend"] = df.spend.apply(float)
for metric in ["impressions", "reach", "clicks"]:
    df[metric] = df[metric].apply(int)

# Группировка
temp = (df.groupby(["date_start","country"])
    [["spend","impressions","reach","clicks"]]
    .sum()
    .reset_index()
    .rename(columns={"date_start": "date"})
    .assign(channel="Facebook"))
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