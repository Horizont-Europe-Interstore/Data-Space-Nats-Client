# Nats Client for Energy Data Space Framework

## Getting started

This project's aim is giving the possibility to receive message using NATS, by different topics, and automatically uploading them on the Energy Data Space Connector. Topics are mapped with respect to services and multiple services can be mapped with the same topic. This scenario is usefull when for example there is the necessity to pub data from the same source into multiple services in the connector.

## How to launch it
1) Download this repository
2) Set the .env parameters
3) Launch the Interstore platform project
3) Under the root folder launch the command docker compose up -d

## Architecture
There are three components.

### Publisher
This component is intended only for testing purpose and could be disabled if you don't need it. If you don't have a real source of data and you want to test the NATS Client you can simply enable it in the env file, if it is enabled sends data into two topics (firstTopic and secondTopics) fake data.
### NATS
Just a NATS server used in pub/sub modality without JetStream. This means that unread message are lost forever. For further information have a look to https://docs.nats.io/ .

### Subscriber
This component acts as a middleware, first of all retrieves all the services in which the technical user can pub data. Then creates a map between services and topics. Each topic has a specific updating frequency that could be customized in the service's page. At each iteration all the topics are analyzed and if the timer associated to it is expired and if data are present in the topic the saveData function is called. 
This function builds a string with informations like topic and updating frequency and uploads it into the connector. If the upload reaches the success then timer is resetted and the string is flushed.



## ENV file configuration
Above there is an example.
- NATS_URL This is the url of the NATS server
- DATA_AUTH_USR this is the username for the user used to upload data
- DATA_AUTH_PSSWR this is the password for the user used to upload data
- URL_LOCAL_API api for the local api, used for uploading and downloading files
- URL_AUTH url for authorizing into Energy Data Space Framework Platform (used to obtain list of available service)
- URL_SERVICES used to obtain list of available service (type data)
- URL_PUSH_SERVICES used to obtain list of available service (type push)
- UPDATING_SERVICES_FREQUENCY frequency of service refreshing
- BASE_FILENAME=Data_from_NATS_ Base filename of data uploaded to the Data Space Connector (a timestamp and the .txt suffix are added automatically)
- PUBLISHER_FREQUENCY pub component could be enabled by using PUB_ENABLED if you don't have a real source of data
- PUB_ENABLED= "true"






