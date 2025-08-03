#!/usr/bin/env python3
import os
import sys
from datetime import datetime

import urllib3
from boxsdk import OAuth2
from boxsdk import Client
import requests

input_dir = '/Users/nagaraju/Desktop'
otp = '/Users/nagaraju/Desktop/box_token.txt'
id = <client_id>
client_sec = <client_secret_token>
url = 'https://api.box.com/oauth2/token'
folder_details = ''
v_folder = <folder_name>
v_file = <file_name_inside_folder>
dest_path = <file_destination_path>

#Intially need to create a refresh_token token from box.com and read the file
try:
    r = open('/Users/nagaraju/Desktop/box_token.txt', 'r')
    rf = r.read().replace('\n', '')
    print("Old_refresh_token:" + rf)
except Exception as E1:
    print(E1)

#Accessing the refresh_token and store in a variable
output_file = open(otp, 'w')
client_token = {'grant_type': 'refresh_token',
                'refresh_token': rf,
                'client_id': id,
                'client_secret': client_sec}

print(client_token)

try:
    r = requests.post(url, data=client_token, verify=False)
    print(r.json())
    print("Access_token: " + r.json()['access_token'])
    print("Refresh_token: " + r.json()['refresh_token'])
except Exception as E1:
    print(E1)

try:
    Refresh_token = r.json()['refresh_token']
    output_file = open(otp, 'w')
    print(Refresh_token)
    output_file.write(str(Refresh_token) + "\n")
    output_file.close()
except Exception as E1:
    print(E1)

token = {'grant_type': 'refresh_token',
         'refresh_token': r.json()['refresh_token'],
         'client_id': <client_id>,
         'client_secret': <client_secret_token>,
         'access_token': r.json()['access_token']}

print(token)

#Generating new Refresh_token after the login to box.com
oauth = OAuth2(
    client_id= <client_id>,
    client_secret=<client_secret_token>,
    access_token=token['access_token'],
    refresh_token=token['refresh_token'],
)

#Box.com gets authenticated
box = Client(oauth)

me = box.user().get()
print('logged in to Box as:', me.login)
print(me.response_object)
#The root folder is 0 folder
folder_id = 0
my_folder = box.folder(folder_id).get()
print('current folder', my_folder)
items = my_folder.get_items()

#Accessing the list of folders under root and see the matched folder_name, file_name defined 
newlist = []
for item in items:
    print('{0} {1} is named "{2}"'.format(item.type.capitalize(), item.id, item.name))
    get_file = box.folder(folder_details).get_items()
    if folder_details == '0':
        get_file = box.folder(folder_details).get_items()
    if item.name == v_file:
        with open(dest_path + item.name, 'wb') as open_file:
            box.file(item.id).download_to(open_file)
            open_file.close()
    else:
        if item.name.startswith(v_folder):
            newlist.append(item.id)
            get_folder_id = newlist[0]
            get_file = box.folder(get_folder_id).get_items()
            for file_list in get_file:
                print('{0} {1} is named "{2}"'.format(file_list.type.capitalize(), file_list.id, file_list.name))
                if file_list.name == v_file:
                    with open(dest_path + file_list.name, 'wb') as open_file:
                        box.file(file_list.id).download_to(open_file)
                        open_file.close()

