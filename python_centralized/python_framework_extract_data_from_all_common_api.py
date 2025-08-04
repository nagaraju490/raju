"""
This is a generic python script which is used to extract data from API endpoint,
preprocess that data and store it into a text file to be loaded into Target Database.
"""
from datetime import date, datetime
import traceback
import sys
import os
import json
import warnings
import threading
import ast
import yaml
import requests
from retrying import retry

warnings.filterwarnings("ignore")


def log_info(logmsg):
    """
    Standardizes Log Messages and printing in respective log_files
    :param logmsg: message to be printed in Logfile
    :return:
    """
    with open(LOGFILE, 'a+', encoding="utf-8") as file_handler:
        file_handler.write(date.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S") + f" : Info : {logmsg}" + "\n")


def sync_sys_args():
    """
    Replaces the values in CONFIG_DATA attributes (which can be passed
    as a string of comma separated values e.g.- "DATA_HEADERS,DATA_PARAMS")
    for the matching keys with key-value pairs from dict passed as sys_arg[2]

    :return:
    """
    for arg_key, arg_value in SYS_ARGS.items():
        for config_data_attr in CONFIG_DATA["SYNC_SYS_ARGS_FOR"].split(','):
            for key, value in CONFIG_DATA[config_data_attr].items():
                if key == arg_key:
                    CONFIG_DATA[config_data_attr][arg_key] = arg_value


def get_env_variables():
    """
    Fetches all the environment and config variables
    necessary for the script to proceed

    :return:
    """
    global INPUT_DIR, CONFIG_DIR, LOGFILE, CONFIG_DATA, SYS_ARGS
    try:
        INPUT_DIR = os.environ["INPUT_DIR"]
        CONFIG_DIR = os.environ["CONFIG_DIR"]
        LOGFILE = os.environ["LOGFILE"]
        config_file = CONFIG_DIR + '/' + os.environ["CONFIG_FILE"]
        config_name = sys.argv[1]
        SYS_ARGS = ast.literal_eval(sys.argv[2]) if len(sys.argv) > 2 else {}
        with open(config_file, 'r', encoding="utf-8") as yaml_file:
            yaml_doc = yaml.safe_load(yaml_file)
            print(yaml_doc)
            CONFIG_DATA = yaml_doc[config_name]
        sync_sys_args()
        print(CONFIG_DATA)
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        sys.exit(1)


get_env_variables()


def clean(data):
    """
    Prepares individual data field values
    using CLEAN_REPLACEMENT_PAIRS to be written to output file,
    in order to prevent any exceptions while Loading to Snowflake
    :param data: Individual attribute values
    :return: Returns Cleaned attribute values
    """
    if isinstance(data, str):
        for original, replacement in CONFIG_DATA["CLEAN_REPLACEMENT_PAIRS"].items():
            data = data.replace(original, replacement)
        return data
    if isinstance(data, list):
        return [clean(item) for item in data]
    if isinstance(data, dict):
        return {clean(key): clean(value) for (key, value) in data.items()}
    return data


@retry(stop_max_attempt_number=int(CONFIG_DATA["MAX_NUMBER_OF_RETRIES"]), wait_fixed=int(CONFIG_DATA["SLEEP_TIME"]))
def request_post(url, headers, json_data, data, params):
    """
    This function is for extracting the response for post request

    :param url: url for the api endpoint
    :param headers: headers for the  api request
    :param json_data: json for the api request
    :param data: data for the api request
    :param params: params for the api request
    :return: Response text
    """
    global MSG
    MSG = "Inside post request api call"
    log_info(MSG)
    log_info(f'Url: {url}')
    log_info(f'Headers: {headers}')
    log_info(f'Json Data: {json_data}')
    log_info(f'Data: {data}')
    log_info(f'Data_Params: {params}')

    response = requests.post(url, headers=headers, json=json_data, data=data, params=params)

    if response.status_code == 200:
        log_info("Request Success")
    else:
        log_info(f"response.text: {response.text}")
        raise requests.exceptions.RequestException(response.text)

    return response.text


def request_idms_token(url, headers, json_data):
    """
    This function is for extracting idms token

    :param url: url for the idms token api endpoint
    :param headers: headers for the idms token api request
    :param json_data: json for idms token the api request
    :return: String Idms token
    """
    global MSG
    MSG = "Inside idms token extract"
    log_info(MSG)
    log_info(f'IDMS Url: {url}')
    log_info(f'IDMS Headers: {headers}')
    log_info(f'IDMS Data: {json_data}')
    response = requests.post(url, headers=headers, json=json_data)
    token_data = response.json()
    token = token_data["token"]
    log_info(f"IDMS Token : {token}")
    return token


def request_session_token(url, headers):
    """
    This function is for extracting session token

    :param url: url for the session token api endpoint
    :param headers: headers for the session token api request
    :return: String Session token
    """
    global MSG
    MSG = "Inside session token extract"
    log_info(MSG)
    log_info(f"Session url: {url}")
    log_info(f"Session headers: {headers}")
    response = requests.get(url=url, headers=headers)
    session_data = response.json()
    session_tok = session_data["session_token"]
    log_info(f"session_tok: {session_tok}")
    return session_tok


@retry(stop_max_attempt_number=int(CONFIG_DATA["MAX_NUMBER_OF_RETRIES"]), wait_fixed=int(CONFIG_DATA["SLEEP_TIME"]))
def request_data(url, headers, params):
    """
    Fetches data from api

    :param url: url for the api endpoint
    :param headers: headers for the api request
    :param params: params for the api request
    :return: Returns a dict containing data fetched from response
    """
    global MSG
    MSG = "Inside data api call"
    log_info(MSG)
    log_info(f"Data url: {url}")
    log_info(f"Headers: {headers}")
    log_info(f"Params: {params}")

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        log_info("Request Success")
    elif response.status_code == 401:
        log_info("response.text {}".format(response.text))
        if CONFIG_DATA["IDMS_TOKEN"]:
            log_info("Calling idms_token function")
            idms_tok = request_idms_token(CONFIG_DATA["IDMS_URL"], CONFIG_DATA["IDMS_HEADERS"], CONFIG_DATA["IDMS_DATA"])
            if CONFIG_DATA["SESSION_TOKEN"]:
                CONFIG_DATA["SESSION_HEADERS"][CONFIG_DATA["IDMS_TOKEN_KEY"]] = idms_tok
            else:
                CONFIG_DATA["DATA_HEADERS"][CONFIG_DATA["IDMS_TOKEN_KEY"]] = idms_tok
        if CONFIG_DATA["SESSION_TOKEN"]:
            log_info("Calling session_token function")
            session_tok = request_session_token(CONFIG_DATA["SESSION_URL"], CONFIG_DATA["SESSION_HEADERS"])
            CONFIG_DATA["DATA_HEADERS"][CONFIG_DATA["SESSION_TOKEN_KEY"]] = session_tok
        raise requests.exceptions.RequestException(response)
    elif response.status_code == 400:
        log_info("Bad request from API")
        if CONFIG_DATA["ENDPOINT"] in 'software,model,profile':
            sys.exit(0)
        else:
            log_info(f"response.text: {response.text}")
            raise requests.exceptions.RequestException(response.text)
    else:
        log_info(f"response.text: {response.text}")
        raise requests.exceptions.RequestException(response.text)

    response_json = response.json()
    return response_json


def flatten_json(json_obj, level=1):
    """
    Flattens a nested JSON structure up to a specified level.
    :param json_obj: json object to be flattened
    :param level: depth to which the nested data needs to be flattened
    :return: dict object with the flattened objects
    """

    def flatten(current_json_obj, name='', current_level=1):
        """
        Updating an empty dict with the flattened key value pairs
        """
        if isinstance(current_json_obj, dict) and current_level <= level:
            for key in current_json_obj:
                flattened[name + key] = current_json_obj[key]
                flatten(current_json_obj[key], name + key + '_', current_level + 1)
        elif isinstance(current_json_obj, list) and current_level <= level:
            if any(isinstance(value, dict) for value in current_json_obj):
                flattened[name[:-1]] = current_json_obj
            else:
                flattened[name[:-1]] = ','.join(current_json_obj)
        else:
            flattened[name[:-1]] = current_json_obj

    flattened = {}
    if level > 0:
        flatten(json_obj)
    else:
        return json_obj
    return flattened


def data_writing(response_json_data):
    """
    Processes the data and writes the processed data into Output file
    :param response_json_data: Python object (mostly list of dicts) containing unprocessed data
    :return:
    """
    data_rows = []
    response_json_data = response_json_data if isinstance(response_json_data, list) else [response_json_data]
    if CONFIG_DATA.get("EXTRACT_ATTRIBUTES", False):
        merged_data = []
        for item in response_json_data:
            if isinstance(item, dict):
                outer = {k: v for k, v in item.items() if k != "attributes"}
                attrs = item.get("attributes", {})
                merged = {**outer, **attrs}
                merged_data.append(merged)
            else:
                merged_data.append(item)

        response_json_data = merged_data
    for data in response_json_data:
        data_list = []
        data_attr = flatten_json(data, level=CONFIG_DATA["FLATTEN_LEVEL"])
        for column in CONFIG_DATA["DATA_ATTRIBUTES"].split(','):
            if column in data_attr and isinstance(data_attr[column], list):
                if any(isinstance(col_list, dict) for col_list in data_attr[column]):
                    data_list.append(json.dumps(data_attr[column]))
                else:
                    data_list.append(','.join(clean(data_attr[column])))
            elif column in data_attr and isinstance(data_attr[column], dict):
                data_list.append(json.dumps(data_attr[column]))
            elif column in data_attr:
                data_list.append(str(clean(data_attr[column])))
            else:
                data_list.append("")

        data_rows.append(CONFIG_DATA["DELIMITER"].encode('utf-8').decode('unicode_escape').join(data_list))

    with threading.Lock():
        with open(INPUT_DIR + '/' + CONFIG_DATA["OUTPUT_FILE"], 'a', encoding="utf-8") as data_file:
            data_file.write("\n".join(data_rows) + "\n")


#For the splunk the data structure is diffrent so had to create separate function
def splunk_data_extraction():
    """
    Handles the Splunk data extraction frequency and
    extracts data from Splunk post API response

    :return:
    """
    pull_hour1 = 0
    pull_hour2 = 0 if CONFIG_DATA["SPLUNK_DATA"]["FREQUENCY"] == 'HOURLY' else 23
    pull_date = SYS_ARGS['START_DATE']
    while int(pull_hour2) < 24:
        if int(pull_hour2) < 10:
            date_range = 'earliest=' + pull_date + ':0' + str(pull_hour1) + ':00:00 latest=' + pull_date + \
                         ':0' + str(pull_hour2) + ':59:59 '
        else:
            date_range = 'earliest=' + pull_date + ':' + str(pull_hour1) + ':00:00 latest=' + pull_date + \
                         ':' + str(pull_hour2) + ':59:59 '
        post_data = CONFIG_DATA["SPLUNK_DATA"]["POST_DATA"].split(':')
        data_format = post_data[0] + date_range + post_data[1]
        log_info('Date range for which the api requesting the data is : ' + data_format)
        response = request_post(CONFIG_DATA["DATA_URL"], CONFIG_DATA["DATA_HEADERS"], None, data_format, None)
        response_data_fixed = '[' + response.replace('}\n{', '},{') + ']'
        # Parse the fixed response data
        dict_list = json.loads(response_data_fixed)
        dict_list = [{"date": pull_date, **i} for i in dict_list]
        data_writing(dict_list)
        pull_hour1 = int(pull_hour1) + 1
        pull_hour2 = int(pull_hour2) + 1


def data_extraction(offset, num_threads=1):
    """
    This function extracts data from API response
    :param offset: The offset for data extraction
    :param num_threads: No. of threads for data extraction
    :return:
    """
    global MSG
    MSG = "Inside data extraction"
    log_info(MSG)
    try:
        if CONFIG_DATA["IDMS_TOKEN"]:
            log_info("Calling idms_token function")
            idms_tok = request_idms_token(CONFIG_DATA["IDMS_URL"], CONFIG_DATA["IDMS_HEADERS"], CONFIG_DATA["IDMS_DATA"])
            if CONFIG_DATA["SESSION_TOKEN"]:
                CONFIG_DATA["SESSION_HEADERS"][CONFIG_DATA["IDMS_TOKEN_KEY"]] = idms_tok
            else:
                CONFIG_DATA["DATA_HEADERS"][CONFIG_DATA["IDMS_TOKEN_KEY"]] = idms_tok
        if CONFIG_DATA["SESSION_TOKEN"]:
            log_info("Calling session_token function")
            session_tok = request_session_token(CONFIG_DATA["SESSION_URL"], CONFIG_DATA["SESSION_HEADERS"])
            CONFIG_DATA["DATA_HEADERS"][CONFIG_DATA["SESSION_TOKEN_KEY"]] = session_tok
    except Exception as request_data_err:
        log_info(traceback.format_exc())
        log_info(request_data_err)
        raise Exception(request_data_err)
    while 1:
        if CONFIG_DATA["NEXT_PAGE_DETAILS"]:
            CONFIG_DATA["DATA_PARAMS"]['page[limit]'] = CONFIG_DATA["DATA_LIMIT"]
            CONFIG_DATA["DATA_PARAMS"]['page[offset]'] = offset
        try:
            log_info("Calling request_data function")
            if CONFIG_DATA["DATA_FUNCTION_TYPE"] == 'POST':
                response_json = request_post(CONFIG_DATA["DATA_URL"], CONFIG_DATA["DATA_HEADERS"],
                                             CONFIG_DATA["DATA_JSON"], CONFIG_DATA["DATA_OTHER"],
                                             CONFIG_DATA["DATA_PARAMS"])
                response_json = json.loads(response_json)
            else:
                response_json = request_data(CONFIG_DATA["DATA_URL"], CONFIG_DATA["DATA_HEADERS"],
                                             CONFIG_DATA["DATA_PARAMS"])
        except Exception as request_data_err:
            log_info(traceback.format_exc())
            log_info(request_data_err)
            raise Exception(request_data_err)

        response_json_data = response_json.get(CONFIG_DATA["RESPONSE_DATA_KEY"]) \
            if CONFIG_DATA["RESPONSE_DATA_KEY"] else response_json
        if not response_json_data:
            log_info("Data is not available")
            break

        data_writing(response_json_data)

        if not CONFIG_DATA["NEXT_PAGE_DETAILS"]:
            break

        offset += num_threads * CONFIG_DATA["DATA_LIMIT"]


def main():
    """
    Main Function acts as starting point for the script
    :return:
    """
    global MSG

    try:
        MSG = "Attempting to Open Logfile"
        log_info(MSG)
        MSG = "Applying lock synchronization"
        log_info(MSG)
        MSG = "Calling data_extraction function"
        log_info(MSG)
        if CONFIG_DATA["MULTITHREADING"]:
            log_info("Applying Mutithreading")
            offsets = [CONFIG_DATA["DATA_OFFSET"] + i * CONFIG_DATA["DATA_LIMIT"]
                       for i in range(CONFIG_DATA["NUM_THREADS"])]
            threads = []
            for offset in offsets:
                thread = threading.Thread(target=data_extraction, args=(offset, CONFIG_DATA["NUM_THREADS"]))
                threads.append(thread)
                thread.start()
            # Wait for all threads to finish
            for thread in threads:
                thread.join()
        else:
            if CONFIG_DATA["APP"] == 'SPLUNK':
                splunk_data_extraction()
            else:
                data_extraction(CONFIG_DATA["DATA_OFFSET"])
        log_info("Data extracted successfully")
    except Exception as err:
        log_info(traceback.format_exc())
        log_info(err)
        sys.exit("Error while " + MSG)

if __name__ == "__main__":
    main()
