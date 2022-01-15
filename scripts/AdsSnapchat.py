### Данные из рекламного кабинета Snap 

SNAP_CREDENTIALS = {
    "client_id": "<YOUR CLIIENT ID>",
    "client_secret": "<YOUR CLIENT SECRET>",
    "redirect_url": "<YOUR URL>",
    "refresh_token": "<YOUR REFRESH TOKEN>",
    "organization_id": "<YOUR ORGANIZATION ID>",
    "ad_account_id": "<YOUR ACCOUNT ID>",
}

import sqlalchemy
from sqlalchemy.dialects.mssql import pymssql
import urllib.parse

import json
import pytz
from requests_oauthlib import OAuth2Session
import requests
import os

import datetime
import pandas as pd
import numpy as np

# The difference between start and end date must be less than 31 days
START_DATE = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(5), '%Y-%m-%d')
END_DATE = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')

def get_snapchat_refresh_token(snap_credentials):
    """Generate long-lived snapchat refresh token"""
    scope = ['snapchat-marketing-api']
    authorize_url = 'https://accounts.snapchat.com/login/oauth2/authorize'
    access_token_url = 'https://accounts.snapchat.com/login/oauth2/access_token'
    # User Auth via Redirect     
    oauth = OAuth2Session(
        client_id=snap_credentials['client_id'],
        redirect_uri=snap_credentials['redirect_url'],
        scope=scope
    )
    # Return the url     
    authorization_url, state = oauth.authorization_url(authorize_url)
    print('Please go to %s and authorize access.' % authorization_url)
    # Use the authorization_url for get token
    authorization_response = input('Enter the full callback URL: ')
    token = oauth.fetch_token(
        token_url=access_token_url,
        authorization_response=authorization_response,
        client_secret=snap_credentials['client_secret'],
        scope=scope
    )
    return oauth.token['refresh_token']

def get_snapchat_access_token(snap_credentials):
    """Generate short-lived snapchat access token"""
    access_url = 'https://accounts.snapchat.com/login/oauth2/access_token'
    access_params = {
        'client_id': snap_credentials['client_id'],
        'client_secret': snap_credentials['client_secret'],
        'code': snap_credentials['refresh_token'],
        'grant_type': 'refresh_token',
    }
    res = requests.post(
        url=access_url,
        params=access_params
    )
    return res.json()['access_token']

def get_all_ad_accounts(access_token, organization_id):
    """Get all available accounts for credentials in the form of a list"""
    url_accounts = 'https://adsapi.snapchat.com/v1/organizations/%s/adaccounts' % (organization_id)
    headers = {'Authorization': 'Bearer %s' % (access_token)}
    res = requests.get(
        url=url_accounts,
        headers=headers
    )
    account_ids = []
    for adaccount in res.json()['adaccounts']:
        account_ids.append(adaccount['adaccount']['id'])
    return account_ids

def get_all_campaigns(access_token, ad_accounts_id):
    """Get all campaigns running on the account in the form of a list
    The spend metric is the only metric available for the ad account entity
    so was select the campaign entity"""
    url_campaigns = 'https://adsapi.snapchat.com/v1/adaccounts/%s/campaigns' % (ad_accounts_id)
    headers = {'Authorization': 'Bearer %s' % (access_token)}
    res = requests.get(
        url=url_campaigns,
        headers=headers
    )
    campaign_ids = []
    if res.json()['request_status'] == 'SUCCESS':
        for campaign in res.json()['campaigns']:
            campaign_ids.append(campaign['campaign']['id'])
    return campaign_ids

def get_report_from_campaign_id(access_token, campaign_id):
    """Get stats of a specific campaign_id"""
    url_reporting = 'https://adsapi.snapchat.com/v1/campaigns/%s/stats' % campaign_id
    headers = {'Authorization': 'Bearer %s' % (access_token)}
    # Define time intervals
    start_time = (pytz
        .timezone('Europe/Moscow')
        .localize(datetime.datetime.strptime(START_DATE, '%Y-%m-%d'))
        .isoformat()
    )
    end_time = (pytz
        .timezone('Europe/Moscow')
        .localize(datetime.datetime.strptime(END_DATE, '%Y-%m-%d'))
        .isoformat()
    )
    # Create Get request
    params = {
        'fields': 'spend,impressions,swipes',
        'report_dimension': 'country',
        'start_time': start_time,
        'end_time': end_time,
        'granularity': 'DAY',
    }
    res = requests.get(
        url=url_reporting,
        params=params,
        headers=headers
    )
    # Parse the response
    df = pd.DataFrame()
    for item in res.json()['timeseries_stats'][0]['timeseries_stat']['timeseries']:
        if item['dimension_stats'] == []:
            continue
        metrics = {
            'campaign_id': campaign_id,
            'start_time': item['start_time'],
            'end_time': item['end_time'],
            'country': item['dimension_stats'][0]['country'],
            'impressions': item['dimension_stats'][0]['impressions'],
            'swipes': item['dimension_stats'][0]['swipes'],
            'spend': item['dimension_stats'][0]['spend'] / 1000000
        }
        df = df.append(metrics, ignore_index=True)
    return df

def main(snap_credentials):
    snap = pd.DataFrame()
    print('Getting Snapchat API access token...')
    access_token = get_snapchat_access_token(snap_credentials)
    print('Getting all accounts...')
    account_ids = get_all_ad_accounts(access_token, snap_credentials['organization_id'])
    print('Getting all campaigns from Snapchat API...')
    for ad_account_id in account_ids:
        campaign_ids = get_all_campaigns(access_token, ad_account_id)
        print('Getting stats by each campaign from Snapchat API...')
        for campaign_id in campaign_ids:
            new = get_report_from_campaign_id(
                access_token,
                campaign_id,
            )
            snap = pd.concat([snap, new])
    return snap

df = main(SNAP_CREDENTIALS)

# Форматирование полученных метрик
df["start_time"] = df["start_time"].apply(pd.Timestamp).dt.date
for metric in ['impressions', 'swipes']:
    df[metric] = df[metric].apply(int)

# Группировка
temp = (df.groupby(["start_time","country"])
    [["spend","impressions","swipes"]]
    .sum()
    .reset_index()
    .rename(columns={"start_time": "date", "swipes": "clicks"})
    .assign(channel="Snapchat"))
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