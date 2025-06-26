import os
import asyncio
import requests
import nats
import json
from nats.errors import TimeoutError
import base64
import time
import logging
from logging.config import dictConfig
isFirstIteration = True

servers = os.getenv("NATS_URL")
dataAuthUsername = os.getenv("DATA_AUTH_USR")
dataAuthPassword = os.getenv("DATA_AUTH_PSSWR")
urlAuth = os.getenv("URL_AUTH")
urlServices = os.getenv("URL_SERVICES")
urlLocalApi = os.getenv("URL_LOCAL_API")
urlPushServices = os.getenv("URL_PUSH_SERVICES")
updatingServicesFrequency = os.getenv("UPDATING_SERVICES_FREQUENCY", 60) 
baseFilename = os.getenv("BASE_FILENAME", "Data_from_NATS")

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

Token=None

def auth():
    global Token
    response = requests.post(urlAuth, json= {"username": dataAuthUsername, "password": dataAuthPassword})
    Token= json.loads(response.text)["accessToken"]
    return json.loads(response.text)["accessToken"]

async def fetch_service_data(isFirstIteration):
    global topics
    while True:
        auth()
        response = requests.get(f"{urlServices}0?cf_type=data", headers={"Authorization": f"Bearer {Token}"})
        response2= requests.get(f"{urlPushServices}0?status=accept&cf_type=push", headers={"Authorization": f"Bearer {Token}"})
        totalPages=response.json()["totalPages"]
        totalPages2=response.json()["totalPages"]
        servicesToBeMapped=response.json()["listContent"]  +response2.json()["listContent"]
        if totalPages > 1:
            for currentPage in  range(1, totalPages):
                response = requests.get(f"{urlServices}{currentPage}", headers={"Authorization": f"Bearer {Token}"})
                servicesToBeMapped = servicesToBeMapped + response.json()["listContent"]
        if totalPages2 > 1:
            for currentPage in  range(1, totalPages2):
                response2= requests.get(f"{urlPushServices}{currentPage}?status=accept&cf_type=push", headers={"Authorization": f"Bearer {Token}"})
                servicesToBeMapped = servicesToBeMapped + response2.json()["listContent"]
        topics={}
        counterMultipleServiceForOneTopic={}
        for element in servicesToBeMapped: 
            topic = element["cf_topic"] 
            if (topic):
                if topic not in topics:
                    topics[topic]=[]

                if element["cf_type"]== "push" :

                    code =  element ["category_code"]
                else:
                    code = element ["cf_code_3"]

                id= element["cf_id"]
                if element["cf_updating_frequency"]:
                    updatingFrequency = element["cf_updating_frequency"]
                else:
                    updatingFrequency = 60

                topicInfo={
                    "code": code,
                    "id": id,
                    "updatingFrequency":updatingFrequency
                }
                topics[topic].append(topicInfo)

        logging.info(topics)

        if isFirstIteration:
            isFirstIteration = False
            return topics
        else:
            await asyncio.sleep(float(updatingServicesFrequency))

def saveData(data, subject, targetServiceId,targetServiceCode, frequency ):
    global Token
    dataBase64 = base64.b64encode(data)
    dataBase64Str = dataBase64.decode('utf-8')

    jsonData = { 
        "title": subject.split(".")[1],
        "description": f"Data automatically uploaded from the NATS server, the file contains the data acquired in {frequency} seconds",
        "filename": baseFilename + time.strftime("%Y%m%d-%H%M%S") + ".txt",
        "file": f"data:text/plain;base64,{dataBase64Str}",
        "fileSize": len(f"data:text/plain;base64,{dataBase64Str}"),
        "data_offering_id": targetServiceId,
        "code": targetServiceCode,
    }
    logging.info(jsonData)
    response=requests.post(urlLocalApi, headers={"Authorization": f"Bearer {Token}"}, json=jsonData)
    if response.status_code!= 200 :
        auth()
        response=requests.post(urlLocalApi, headers={"Authorization": f"Bearer {Token}"}, json=jsonData)
        if response.status_code!=200:
            logging.info(f"Error while saving into connector, error: {response.status_code}")
    return response.status_code


def save(buildedMessages,repeatedTopicsUnderTopic):
    if time.time() -  buildedMessages[repeatedTopicsUnderTopic["id"]][1]  >= repeatedTopicsUnderTopic["updatingFrequency"] and buildedMessages[repeatedTopicsUnderTopic["id"]][0]: 

        result = saveData(buildedMessages[repeatedTopicsUnderTopic["id"]][0], buildedMessages[repeatedTopicsUnderTopic["id"]][2], repeatedTopicsUnderTopic["id"], repeatedTopicsUnderTopic["code"],repeatedTopicsUnderTopic["updatingFrequency"]) ## target service parameters
        if result == 200:
            logging.info ("Data have been saved into connector")
            buildedMessages[repeatedTopicsUnderTopic["id"]][0] = bytearray(b'') ## Reset the string
            buildedMessages[repeatedTopicsUnderTopic["id"]][1] = time.time() ## Reset the timer
        else:
            logging.info("Some error occurred while saving data into connector" + str(result))


async def main():
    global topics
    """ async def error_cb(e):
        print(f'There was an error while connecting: {e}') """
    try: 
        nc = await nats.connect(servers)
    except Exception as e:
        logging.info (f'There was an error while connecting: {e}')
    nc = await nats.connect(servers)
    auth() 
    topics = await fetch_service_data(True)
    fetch_task = asyncio.create_task(fetch_service_data(False))
    sub = await nc.subscribe("topics.*")
    currentTime=time.time()
    buildedMessages={} ## Initialization : [emptystring, ongoing timer]
    for topic in topics.keys(): ## keys are topic's names
        for repeatedTopicsUnderTopic in topics[topic]:
            buildedMessages[repeatedTopicsUnderTopic["id"]]= [bytearray(b''), currentTime,""]

    while True:
        msg=""
        try:
            msg=await sub.next_msg(timeout=0.2)
            logging.info(f"Subscriber has received this message: {msg.data} By this topic: {msg.subject}")
            """ print(msg.data)
            print("By this topic:")
            print(msg.subject) """
            nameOfTheService= msg.subject.split(".")[1] 
            if nameOfTheService in topics: 

                for repeatedTopicsUnderTopic in topics[nameOfTheService]:
                    # Initilize value for service if not present..
                    if repeatedTopicsUnderTopic["id"] not in buildedMessages:
                        buildedMessages[repeatedTopicsUnderTopic["id"]]=[bytearray(b''), time.time(),""]

                    buildedMessages[repeatedTopicsUnderTopic["id"]][0] += msg.data
                    buildedMessages[repeatedTopicsUnderTopic["id"]][0] +=b"\n"
                    buildedMessages[repeatedTopicsUnderTopic["id"]][2] = msg.subject
                    #logging.debug(buildedMessages[repeatedTopicsUnderTopic["id"]])
                    save(buildedMessages,repeatedTopicsUnderTopic)

        except TimeoutError:
            save(buildedMessages,repeatedTopicsUnderTopic)
            pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())