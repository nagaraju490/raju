#!/usr/bin/env python3

import os
import sys
from datetime import datetime,date
import urllib3
from boxsdk import OAuth2
from boxsdk import Client
from boxsdk.config import Proxy
import requests
from retrying import retry
from os import listdir
from os.path import isfile, join
import csv
from openpyxl import Workbook
import configparser
import traceback
import ast


def get_variables():
        global input_dir,v_id,v_client_sec,v_url,v_file_src_path,v_folder_id,v_time,v_max_attempts
        input_dir=<input_folder_details>
        v_id=<client_id>
        v_client_sec=<client_id>
        v_url='https://api.box.com/oauth2/token'
        v_file_src_path=<source_folder_name_file_name>
        v_folder_id=<source_folder_name>
        v_time=<define sleep time>
        v_max_attempts=<no_of_retry_attempts>
try:
    print("Calling get variables function")
    get_variables()
except Exception as E1:
    print(E1)
    print(traceback.format_exc())
    sys.exit(1)

#printing the variables
print("Id is: " + v_id)
print("Client secret is: " + v_client_sec)
print("URL is: " + v_url)
print("Selected folder is : " + v_folder_id)
print("Selected source file path is : " + v_file_src_path)


def upload_file_to_box(client, folder_id, filename):
    folder = client.folder(folder_id=folder_id)
    print(f'current folder: {folder}')
    items = folder.get_items()
    for item in items:
        if item.name == filename:
            updated_file = client.file(item.id).update_contents(v_file_src_path)
            print('File "{0}" has been updated'.format(updated_file.name))
            return
    uploaded_file = folder.upload(v_file_src_path)
    print('File "{0}" has been uploaded'.format(uploaded_file.name))
    
@retry(stop_max_attempt_number=int(v_max_attempts),wait_fixed=int(v_time))
def request_data():
    try:
        r = open(input_dir+'/token.txt', 'r')
        rf = r.read().replace('\n', '')
        print("Old_refresh_token:" + rf)
    except Exception as E1:
        print(E1)
        print(traceback.format_exc())
    output_file = open(input_dir+'/token.txt', 'w')
    client_token = {'grant_type': 'refresh_token',
                    'refresh_token': rf,
                    'client_id': v_id,
                    'client_secret': v_client_sec}

    print(client_token)
    folder_details = ''

    try:
        r = requests.post(v_url, data=client_token)
        print(r.json())
        print("Access_token: " + r.json()['access_token'])
        print("Refresh_token: " + r.json()['refresh_token'])
    except Exception as E1:
        print(E1)
        print(traceback.format_exc())

    try:
        Refresh_token = r.json()['refresh_token']
        output_file = open(input_dir+'/token.txt', 'w')
        output_file.write(str(Refresh_token) + "\n")
        output_file.close()
    except Exception as E1:
        print(E1)
        print(traceback.format_exc())

    token = {'grant_type': 'refresh_token',
             'refresh_token': r.json()['refresh_token'],
             'client_id': v_id,
             'client_secret': v_client_sec,
             'access_token': r.json()['access_token']}

    print(token)

    oauth = OAuth2(
        client_id=v_id,
        client_secret=v_client_sec,
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
    )

    try:
        box = Client(oauth)
        me = box.user().get()
        print(f'logged in to Box as: {me.login}')
        print(me.response_object)
        dest_file_name = v_file_src_path.split('/')[-1]
        upload_file_to_box(box,v_folder_id,dest_file_name)
        print("File uploaded successfully")
    except Exception as E1:
        print(E1)
        print(traceback.format_exc())


print("Start - accessing the data from box")
request_data()
print("Completed - accessing the data from box")
