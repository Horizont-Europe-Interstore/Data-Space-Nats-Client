import os
import asyncio
import json
import nats
from nats.errors import TimeoutError
import datetime
import logging
from logging.config import dictConfig
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
servers =os.getenv("NATS_URL")
pubEnabled = os.getenv("PUB_ENABLED")
frequencypublisher= os.getenv("PUBLISHER_FREQUENCY") 
async def main():
    if pubEnabled == "true":
        nc = await nats.connect(servers)
        #i = 0
        while True:
            try:
                message = str(datetime.datetime.now())
                #message={"name": "Alice", "age": i}
                #i+=1
                #await nc.publish("topics.firstTopic", b"firstTopic")
                await nc.publish("topics.firstTopic", message.encode())
                logging.info("Sending the message: " + message + " by the topic: firstTopic ")
               
                
                message = str(datetime.datetime.now())
                await nc.publish("topics.secondTopic", message.encode())
                logging.info("Sending the message: " +message+ " by the topic: secondTopic ")
                await asyncio.sleep(float(frequencypublisher))
            except TimeoutError:
                pass
   
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())


