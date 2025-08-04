#!/usr/bin/env python3
"""
This script extracts transfer order data from source API
"""
from datetime import date, datetime, timedelta
import traceback
import sys
import os
import configparser
import json
import ast
import warnings
import time
import requests
from retrying import retry
warnings.filterwarnings("ignore")

def parse_special_characters(data):
    """
    Prepare individual data field values to be written to output file,
    in order to prevent any exceptions while Loading to Target database
    :param data: Individual attribute values
    :return:
    """
    if isinstance(data, str):
        return data.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ').replace('"', ' ').replace('\\', ' ').replace('\034', '')
    if isinstance(data, list):
        return [parse_special_characters(item) for item in data]
    if isinstance(data, dict):
        return {parse_special_characters(key): parse_special_characters(value) for (key, value) in data.items()}
    return data

def get_variables():
    """
    This function is for getting all necessary urls, parameters, headers and
    common variable values
    :return:
    """
    global INPUT_DIR, MAX_NUMBER_OF_RETRIES, SLEEP_TIME, TOKEN_URL, TOKEN_HEADERS, TOKEN_DATA, DATA_URL, DATA_HEADERS, LOAD_START_DATE, LOAD_END_DATE, ATTRIBUTES
    INPUT_DIR = <input_path_details>
    MAX_NUMBER_OF_RETRIES = <define the count>
    SLEEP_TIME = <sleep_time>
    TOKEN_URL = <token_details>
    TOKEN_HEADERS = {'accept': 'application/json', 'cache-control': 'no-cache', 'content-type': 'application/json'}
    TOKEN_DATA = <define_token_related_details>
    DATA_URL = 'url_details'
    DATA_HEADERS = {"Content-Type": "application/json", "token_details": 'token', "app_id": "app_id_details"}
    ATTRIBUTES = <list of attributes to extract>
    LOAD_START_DATE = <start_date>
    LOAD_END_DATE = <end_date>
try:
    get_variables()
except Exception as E1:
    print(E1)
    print(traceback.format_exc())
    sys.exit(1)

@retry(stop_max_attempt_number=int(MAX_NUMBER_OF_RETRIES), wait_fixed=int(SLEEP_TIME))
def genToken(token_url, token_headers, token_data):
    """
    This function is used for generating source token
    :param token_url:
    :param token_headers:
    :param token_data:
    :return:
    """
    try:
        global RESPONSE
        RESPONSE = requests.post(url=token_url, headers=token_headers, json=token_data, verify=False)
    except Exception as err:
        raise requests.exceptions.RequestException(RESPONSE)
    if RESPONSE.status_code == 200:
        print("Request Success")
    else:
        print(RESPONSE.text)
        raise requests.exceptions.RequestException(RESPONSE)
    try:
        global TOKEN
        TOKEN = RESPONSE.json()['token']
    except Exception as err:
        print(err)
        print(traceback.format_exc())

@retry(stop_max_attempt_number=int(MAX_NUMBER_OF_RETRIES), wait_fixed=int(SLEEP_TIME))
def request_data(data_url, data_headers, json_data):
    """
    This function extracts data from source API
    :param data_url:
    :param data_headers:
    :param json_data:
    :return:
    """
    print("Inside request_data func")
    print('request_data block')
    print("json_data : {}".format(json_data))
    print(f'data_url: {data_url} , data_headers: {data_headers}') 
    try:
        global RESPONSE
        time.sleep(1)
        RESPONSE = requests.post(url=data_url, headers=data_headers, json=json_data, verify=False)

    except Exception as err:
        print(err)
        print(traceback.format_exc())
        raise requests.exceptions.RequestException(RESPONSE)

    if RESPONSE.status_code == 200:
        print("Request Success")
    else:
        print(RESPONSE.text)
        raise requests.exceptions.RequestException(RESPONSE)
    try:
        global RESPONSE_DATA
        RESPONSE_DATA = RESPONSE.json()

    except Exception as err:
        print(err)
        print(traceback.format_exc())
        raise requests.exceptions.RequestException(RESPONSE)

def data_extraction():
    """
    This function invokes request_data func for data extraction using pagination logic
    :return:
    """
    print("Inside data_extraction function")
    DATA_HEADERS["http_header"] = TOKEN
    data_file = open(INPUT_DIR + '/input_file.txt', 'w')
    count = 100
    offset = 0
    while 1:
        json_data = {
            "module": "module_name",
            "number": "If looking to extract data for one ticket then update ticket_details",
            "query": "Query_generated_from_source_api".format(LOAD_START_DATE, LOAD_END_DATE),
            "count": count,
            "offset": offset
        }
        print('TESTING: In data_extraction')
        print(f'Data_url: {DATA_URL} , data_headers: {DATA_HEADERS} , json_data {json_data}')
        try:
            request_data(DATA_URL, DATA_HEADERS, json_data)
        except Exception as err:
            print(err)
            print(traceback.format_exc())

        if "data" in RESPONSE_DATA["result"] and len(RESPONSE_DATA["result"]["data"]) == 0:
            print("No data available, exiting!")
            break
        if "data" in RESPONSE_DATA["result"] and RESPONSE_DATA["result"]["data"]:
            for row in RESPONSE_DATA["result"]["data"]:
                data_list = []
                for col in ATTRIBUTES.split(','):
                    if col in row and isinstance(row[col], list):
                        if any(isinstance(i, dict) for i in row[col]):
                            data_list.append(json.dumps(row[col]))
                        else:
                            data_list.append(','.join(row[col]))
                    elif col in row and isinstance(row[col], dict):
                        data_list.append(json.dumps(row[col]))
                    elif col in row:
                        data_list.append(parse_special_characters(str(row[col])))
                    else:
                        data_list.append("")
                data_file.write('\034'.join(data_list) + '\n')
        offset += 1
def main():
    """
    Main Function acts as starting point for the script
    :return:
    """
    global MSG
    global FH
    try:
        MSG = "Attempting to Open Logfile"
        print(MSG)
        MSG = "Calling genToken function"
        print(MSG)
        genToken(TOKEN_URL, TOKEN_HEADERS, TOKEN_DATA)
        MSG = "Calling data_extraction function"
        print(MSG)
        data_extraction()
        print("Data extracted successfully")

    except Exception as E1:
        print(E1)
        print(traceback.format_exc())
        sys.exit("Error while " + MSG)
main()

