import argparse

from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools

import sqlalchemy
from sqlalchemy.dialects.mssql import pymssql
import urllib.parse

import pandas as pd
import datetime
import os

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URL = ('https://analyticsreporting.googleapis.com/$discovery/rest')
KEY_FILE_LOCATION = './gadatabot.json'
SERVICE_ACCOUNT_EMAIL = '<YOUR CLIENT EMAIL>'
VIEW_ID = '<YOUR VIEW ID>'

def initialize_analyticsreporting():
    """Initializes an analytics reporting service object.

  Returns:
    analytics an authorized analyticsreporting service object.
  """

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        filename=KEY_FILE_LOCATION,
        scopes=SCOPES)

    http = credentials.authorize(httplib2.Http())

    # Build the service object.
    analytics = build('analytics',
                      'v4',
                      http=http,
                      discoveryServiceUrl=DISCOVERY_URL)

    return analytics

def get_report(analytics, startDate, endDate):
    """Use the Analytics Service Object to query the Analytics Reporting API V4."""
    return analytics.reports().batchGet(
# Get sessions number from the last 30 days
    body={
        'reportRequests': [
            {
                'viewId': VIEW_ID,
                'dateRanges': [{'startDate': startDate, 'endDate': endDate}],
                'samplingLevel': 'LARGE',
                'metrics': [
                    {'expression': 'ga:sessions'},
                ],
                'dimensions': [
                    {'name': 'ga:date'},
                    {'name': 'ga:country'},
                    {'name': 'ga:source'},
                    {'name': 'ga:medium'},
                    {'name': 'ga:campaign'},
                ],
                'filtersExpression': 'ga:country=~France|Spain',
                'orderBys': [{'fieldName': 'ga:sessions', 'sortOrder': 'DESCENDING'}], 
                'pageSize': 10000
            }]
    }
    ).execute()

def print_response(response):
    """Parses and prints the Analytics Reporting API V4 response."""

    dim, val = [], []

    for report in response.get('reports', []):
        columnHeader = report.get('columnHeader', {})
        dimensionHeaders = columnHeader.get('dimensions', [])
        metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
        rows = report.get('data', {}).get('rows', [])

        for row in rows:

            dimensions = row.get('dimensions', [])
            dateRangeValues = row.get('metrics', [])
            dim.append(dimensions)

            for header, dimension in zip(dimensionHeaders, dimensions):
                # print(header + ': ' + dimension)
                pass
            for i, values in enumerate(dateRangeValues):
                val.append([int(x) for x in values.get('values')])
                # print('Date range (' + str(i) + ')')
                pass
                for metricHeader, value in zip(metricHeaders, values.get('values')):
                    # print(metricHeader.get('name') + ': ' + value)
                    pass
    dimensions = [x[3:] for x in dimensionHeaders]
    measures = [x.get('name')[3:] for x in metricHeaders]
    return pd.DataFrame(data=dim,
                        columns=dimensions).join(pd.DataFrame(data=val,
                                                              columns=measures))

def main(startDate, endDate):
    """Calls all written function one by one and returns composition result"""
    analytics = initialize_analyticsreporting()
    response = get_report(analytics, startDate, endDate)
    return print_response(response)

#### Данные по привлечению в платных каналах

if __name__ == '__main__':
    df = main('3daysAgo', 'yesterday')
    df["date"] = pd.to_datetime(df["date"])

def get_channel(row):
    """Returns the channel of acquisition by utm-ticks"""
    if row["source"] == 'facebook' and row["medium"] == 'cpc':
        return 'Facebook'
    elif row["source"] == 'snapchat' and row["medium"] == 'cpc':
        return 'Snapchat'
    elif row["source"] == 'tiktok' and row["medium"] == 'cpc':
        return 'Tiktok'

df["channel"] = df.apply(get_channel, axis=1)

temp = (df.groupby(["date", "country", "channel"])
            [["sessions"]]
            .sum()
            .reset_index()
       )

temp["date"] = temp["date"].dt.date

#### Подключение к базе данных (см. Dockerfile)

hostname = os.environ.get("DB_HOST")
username = os.environ.get("DB_USER")
password = os.environ.get("DB_PWD")

SCHEMA = '<YOUR SHEMA>'
TABLE = '<YOUR TABLE>'

engine = sqlalchemy.create_engine(f'mssql+pymssql://{username}:{password}@{hostname}')

#### Удаление последних дней из базы

START_DATE = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(3), '%Y-%m-%d')
END_DATE = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(1), '%Y-%m-%d')

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