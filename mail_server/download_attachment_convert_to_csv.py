#!/usr/bin/env python3
"""
This script is used to convert a pdf file received as mail attachment
to csv file.
"""
from datetime import date, datetime
import traceback
import sys
import os
import warnings
from imbox import Imbox
import tabula
warnings.filterwarnings("ignore")

def get_variables():
    """
    This function is for getting all necessary urls, parameters, headers and
    common variable values
    :return:
    """
    global INPUT_DIR, HOST, USERNAME, PASSWORD, SUBJECT, SENT_FROM, OUTPUT_FILE, INPUT_FILE, DT
    INPUT_DIR = <where attachment to be downloaded>
    HOST = <mail_server_hostname>
    USERNAME = <username>
    PASSWORD = <password>
    SUBJECT = <subject of the mail to grep accurate mail>
    SENT_FROM = <sender mail details>
    OUTPUT_FILE = <Name of the attachment/file_name>
    INPUT_FILE = <convert the pdf attachment to csv file_name>
    DT = <date_details>
try:
    get_variables()
except Exception as err:
    print(err)
    print(traceback.format_exc())
    sys.exit(1)


def pdf_to_csv():
    """
    Downloads PDF file from mail attachment and converts it into CSV 
    """

    print("Inside PDF to CSV conversion")
    print(f"Host: {HOST}")
    print(f"Subject: {SUBJECT}")
    print(f"Sent_from: {SENT_FROM}")
    print(f"Attachment file name: {INPUT_FILE}")
        
    mail = Imbox(HOST, username=USERNAME, password=PASSWORD, ssl=True, ssl_context=None, starttls=False)
    """
    Defaults to inbox
    """
    messages = mail.messages(subject=SUBJECT, sent_from=SENT_FROM, unread=True, date__gt=date(int(DT[0]), int(DT[1]), int(DT[2])))
    
    att_found = False
    
    for (uid, message) in messages:
        mail.mark_seen(uid)
    
        for idx, attachment in enumerate(message.attachments):
            if INPUT_FILE == attachment.get('filename'):
                try:
                    print(message.subject)
                    print(message.headers)
                    att_fn = attachment.get('filename')
                    pdf_path = f"{INPUT_DIR}/{att_fn}"
                    csv_path = f"{INPUT_DIR}/{OUTPUT_FILE}.txt"
                    print(pdf_path)
                    with open(pdf_path, "wb") as fp:
                        fp.write(attachment.get('content').read())
                    tabula.convert_into(pdf_path, csv_path, output_format="csv", pages='all')
                    att_found = True
                except Exception as err:
                    print(err)
                    print(traceback.format_exc())
                    sys.exit(1)

    if att_found:
        print("Attachment file downloaded successfully")
    else:
        print("No Attachment file found for given attachment file name")
    
    mail.logout()


def main():
    """
    Main Function acts as starting point for the script
    :return:
    """
    global MSG
    global FH

    try:
        pdf_to_csv()
        print("Completed pdf_to_csv function")
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        sys.exit("Error while " + MSG)


main()
