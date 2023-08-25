#
# Title:        mstodo_script.py
# Author:       @codingwatermelon
# Date:         8/25/23
#
# Function:     Transform data from MS Graph API
#
# Description:  Transform data from MS Graph API to send to
#               my LED matrix
#
# TODO:
#   - Add "sad path" measures to this code
#
# Notes:
#   - All API requests are staggered with a 2 second wait
#


import json
from os.path import exists
import requests
import datetime
import time

# Function to unload config file into variable and return it
def read_config(config_file):
    if exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
    else:
        print("[ERROR] Couldn't find file '" + config_file + "'. Ensure file exists and use 'config.json.sample' to as a template for the variables that need to be set up.")

    return config

# Function to load json config into output file for debugging purposes
def output_json_to_file(json_obj, output_file):
    try:
        with open(output_file, "w") as out:
            out.write(json.dumps(json_obj, indent=4))
        print("[INFO] Wrote json to file '" + output_file + "'")
    except:
        print("[ERROR] Could not write given json to file '" + output_file + "'")

# Function to generate access token using refresh token and returns the current access token
# This is used when the access token on file is expired
def get_access_token(config, config_file):
    scopes = ['Tasks.Read']

    # Use refresh token to get auth token
    refresh_token_endpoint = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    refresh_token_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    refresh_token_params = {
        'client_id': config["client_id"],
        'scope': " ".join(scopes),
        'refresh_token': config["refresh_token"],
        'grant_type': 'refresh_token',
        'client_secret': config["client_secret"]
    }

    print("[DEBUG] Making POST request to refresh access token...")
    
    # Note: Use 'data' param for POST-style body info and 'params' param for GET-style URL params
    # Source: https://stackoverflow.com/questions/15900338/python-request-post-with-param-data
    response = requests.post(refresh_token_endpoint, headers=refresh_token_headers, data=refresh_token_params).json()
    time.sleep(2)

    # Replace access token key on file with current access token
    # Source: https://stackoverflow.com/questions/21035762/python-read-json-file-and-modify
    with open(config_file, "r+") as f:
        data = json.load(f)
        data['curr_access_token'] = response["access_token"]
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    print("[INFO] Generated new access token.")

    return response["access_token"]

# Set variables
base_path = "T:\code\matrix\MSToDo-API-Scripts"
config_file = base_path + "\config.json"
config = read_config(config_file)
access_token = config["curr_access_token"]

authority_url = 'https://login.microsoftonline.com/consumers/'
graph_url = 'https://graph.microsoft.com/v1.0/'

complete = False

while not complete:
    # Use auth token to run API requests
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Tasks for "Tasks" list
    endpoint = graph_url + 'me/todo/lists/AQMkADAwATMwMAItZDE3NC04ZGIwLTAwAi0wMAoALgAAA5xW9ScynKZAl6KRnYxA_zEBAEJgWa_uuMhKtmNJGgQJ-1MAByfIjzEAAAA=/tasks'

    #endpoint = graph_url + 'me/todo/lists'

    print("[DEBUG] Making GET request for info...")
    response = requests.get(endpoint, headers=headers).json()
    time.sleep(2)

    if 'error' in response:
        print("[INFO] Access token expired. Generating new access token...")
        access_token = get_access_token(config, config_file)
        config = read_config(config_file)
    else:
        output_json_to_file(response, base_path + "\\Archive\\" + datetime.datetime.now().strftime("%m%d%y-%H%M%S") + "_test.json")

        tasks = {}

        for task in response["value"]:
            # Display "high" importance tasks only (until MS Graph API gets updated to allow me to get 'My Day' tasks)
            if task["importance"] == "high":

                # TODO Order tasks by due date 
                # if "dueDateTime" in task and datetime.datetime.strptime(task["dueDateTime"]["dateTime"].split("T")[0], "%Y-%m-%d").date() == datetime.datetime.now().date():
            
                # Handle duplicate task names
                taskName = task["title"]
                i = 1

                while taskName in tasks:
                    taskName = task["title"] + " (" + str(i) + ")"
                    i+=1

                # Use reminder time as "start" time for task
                startTime = task["reminderDateTime"]["dateTime"].replace("T", " ").split(".")[0] if "reminderDateTime" in task else "none"

                # Use body (notes) as tags (e.g., time duration for task, method of execution for task (e.g., pomodoro))                    
                tags = task["body"]["content"].split("\n") if "body" in task else []

                tasks[taskName] = {
                    "startTime": startTime,   # e.g., 2023-08-25T16:00:00.0000000
                    "tags": tags
                }

                #if "checklistItems" in task:
                #    for item in task["checklistItems"]:
                #        print(item["displayName"])

        print(tasks)

        complete = True
    

