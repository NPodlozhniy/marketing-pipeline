### Данные о выданных картах

import sqlalchemy
from sqlalchemy.dialects.mssql import pymssql

import datetime
import urllib.parse
import os

import numpy as np
import pandas as pd
import re

#### Подключение к базе данных (см. Dockerfile)

hostname = os.environ.get("DB_HOST")
username = os.environ.get("DB_USER")
password = os.environ.get("DB_PWD")

#### Считывание данных 

engine = sqlalchemy.create_engine(f'mssql+pymssql://{username}:{password}@{hostname}')

#### Целевые действия, что вам необходимо добавить к выгрузке рекламы из кабинетов
df_acquisition = pd.read_sql("""
select
    Date
    ,Channel
    ,Country
    , ...
from
    ...
;
""", engine, parse_dates=['Date'])

# Предобработка данных

df_acquisition["Date"] = df_acquisition["Date"].dt.date
# <YOUR CODE>

#### Прокидываем в Google Sheets

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from df2gspread import df2gspread as d2g

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('./transferbot.json', scopes=scope)
gc = gspread.authorize(credentials)
spreadsheet_key = "<YOUR SPREADSHEET KEY>"

#### Загружаем инфу по выданным картам

wks_name = "Issue"
d2g.upload(df_acquisition,
           spreadsheet_key,
           wks_name=wks_name,
           col_names=True,
           row_names=False,
           credentials=credentials,
           df_size=True)

#### Загружаем инфу по рекламным кабинетам и гугл аналитике

tiktok = pd.read_sql("""
select *
from ...
""", engine, parse_dates=['date'])

facebook = pd.read_sql("""
select *
from ...
""", engine, parse_dates=['date'])

snapchat = pd.read_sql("""
select *
from ...
""", engine, parse_dates=['date'])

ga = pd.read_sql("""
select *
from ...
""", engine, parse_dates=['date'])

d2g.upload(tiktok,
           spreadsheet_key,
           wks_name="TikTok",
           col_names=False,
           row_names=False,
           clean=False,
           credentials=credentials,
           start_cell='A2',
           df_size=True)

d2g.upload(facebook,
           spreadsheet_key,
           wks_name="Facebook",
           col_names=False,
           row_names=False,
           clean=False,
           credentials=credentials,
           start_cell='A2',
           df_size=True)

d2g.upload(snapchat,
           spreadsheet_key,
           wks_name="Snap",
           col_names=False,
           row_names=False,
           clean=False,
           credentials=credentials,
           start_cell='A2',
           df_size=True)

d2g.upload(ga,
           spreadsheet_key,
           wks_name="GA",
           col_names=False,
           row_names=False,
           clean=False,
           credentials=credentials,
           start_cell='A2',
           df_size=True)
print("Data upload success!")

#### Обновляем ноутбуки в Tableau

import tableauserverclient as TSC
import xml.etree.ElementTree as ET
import time

USERNAME = "<YOUR TABLEAU USERNAME>"
PASSWORD = "<YOUR TABLEAU PASSWORD>"
SITENAME = "<NAME OF YOUR TABLEAU SERVER SITE>"
SERVER_URL = "<HOST OF YOUR TABLEAU SERVER SITE>"
WORBOOK_NAME = "<YOUR WORKBOOK NAME>"

tableau_auth = TSC.TableauAuth(USERNAME, PASSWORD, SITENAME)
server = TSC.Server(SERVER_URL, use_server_version=True)

def refresh_workbook(name):
    """Refresh given workbook if datasource is run out of date"""
    with server.auth.sign_in(tableau_auth): # sign in
        tasks = server.tasks.get()[0] # all site tasks
        for task in tasks: # if the name is correct and there has been no update today
            target = task.target 
            if target.type == 'workbook':
                workbook = server.workbooks.get_by_id(target.id)
            if workbook.name == name:
                # refresh if only datasource is run out of date
                if workbook.updated_at.date() < datetime.date.today():
                    runner = server.tasks.run(task)
                    # after running the task get processing job 
                    xml_root = ET.fromstring(runner.decode())
                    for child_of_root in xml_root:
                        if child_of_root.tag == '{http://tableau.com/api}job':
                            job_id = child_of_root.attrib.get("id")
                    # wait until a given job succesfully finishes
                    server.jobs.wait_for_job(job_id)
                    time.sleep(10)
                # date of last workbook refreshing bring to Moscow time zone
                return (server.workbooks.get_by_id(target.id).updated_at +
                        datetime.timedelta(hours=3)).strftime(f"%m/%d/%Y %H:%M:%S")

print("Tableau workbook Marketing refreshed at", refresh_workbook(WORBOOK_NAME))