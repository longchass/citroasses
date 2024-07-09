# Design principle

sacrifice is clearly made given the goal is constricted within a single docker container

Airgap principle should be followed where the production data should not be queriable from a single host 

This database is treated as the "first response" database where it's main goal is ingestion and processing of incoming data

There is a flexible option at API level to put the data categories in beforehand through the url

Basic token security for the API is implemented

Accept transaction (GET, POST) PUT and DELETE could be implmented but deemed unecessasry for the requirements

category must be specified at the query level

one database intake and scales per API cluster

## Files and usage
Dockerfile: run and set some environment variables

main.py: pull api.py and dabatase.py and run the localhost

api.py: fastapi to handle api declaration and communication with database

database.py: postgressql database

## Database choices
    We definitely need to classify the transactions immediately at the API level. When it arrives at the database level, cleaning up o
    manually sepcifying/calssfication is a pain.
    Database should only run aggregate level job and high level cleaning.
    API is enabled to flag if a transaction is not classfied or missing. 

    We have 3 extra table table created besides the .json object so that our database is in BCNF .

    With categories it's hard to know whenever the 3 categories will ever remains the same, hence a default value created is UNVALIDATED and
    an enum table is created and will create more transactions enum type when necessary.

    Same principle should be applied to all other objects where there is some sort of aggregation or categorisation values to be used.
## Categorisation
We will catgorise the transaction as it comes

Check api.py to use get_category_enum_from_counterpart for business logic case-by-case regex classification


Check api.py to use get_category_enum_from_counterpart_nlp for using NLP processing for zero-shot classification

The default in the repo is get_category_enum_from_counterpart_nlp

## Setup for local development
    Assuming you have full source code and running a Docker Desktop setup to test changes and features, run the following steps
    - cd <location-of-this-folder>
    - docker build -t <name-that-you-want-to-name>
    - docker image list  -> Get the id of the image that you just have built
    - docker run -p 80:80 <image-id-you-got-from above>
    
    Assuming you want to scale up the instances do: (This currently doesn't work since connection is required to download the complete model weights from huggingface and cache it, upon trigger the api and instance will automatically kill itself and there is no solution to lock start up yet until this has completed)
    - cd <location-of-this-folder>
    - docker-compose up --build -d
    - docker-compose up -d --scale api=5
# Testing
There are two reccomended tool to test this API manually
- curl (CLI-based)
- postman (GUI-based)

Running the  python script to will pre-load some transactions and test.

```
python load.py
python test.py
```

## Sacrifices

- API error need better Errors objects and feedback reporting.

- Full restart of the database and not being able to pipe it into a backup or state to save. Due to single docker instance requirements. could pipe it to save on local server but this can varies if you're using cloud based or trying to save a manifest file.

- Some "smarts" logic can be done for automatic categorisation based on transactionType and counterpartName. But this is always too risky to implement without some base logic first. i.e location-based, store-based, ammount-based. It's better to ingest directly into a lakehouse and do some categorisation then. Or stream the data through ETL pipeline so the logic is always easily checked and ajustable. 

- Haven't check for faulty input for utc time
- respond id doesn't reflect actual uid in the database
- It is a bad idea to process NLP or LLM or any kind of prompt to categorise at the docker level. These are data that will be used for key metrics and business insights. It should be visible at higher level. At the very least. There should be a database reference that these docker container can reference from. The LLM can be used at a daily level or hourly level to process and categorise the transaction
- No OpenAI ChatGPT. We will use open-source to avoid vendor lock-in. There many open source tool that exists that will help us streamline and systematically evaluate and test these model and use traditional ML metrics to evaluate them. OpenAI does not offer these tools and their progress is absolutely slow.
- We currently running CPU for NLP


## Changelog

Changed bash shell script load.sh, test.sh data to python script load.py test.py