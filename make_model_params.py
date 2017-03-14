#! /usr/bin/env python

import csv
import os
import logging
import time
import argparse
import subprocess
import json
from datetime import datetime

import psutil

search_def = {
    "includedFields": [
        {
            "fieldName": "timestamp",
            "fieldType": "datetime"
        },
        {
            "fieldName": "memory",
            "fieldType": "float",
            "maxValue": 100.0,
            "minValue": 0.0
        }
    ],
    "inferenceArgs": {
        "predictedField": "memory",
        "predictionSteps": [
            1
        ]
    },
    "inferenceType": "TemporalAnomaly",
    "iterationCount": -1,
    "streamDef": {
        "info": "memory",
        "streams": [
            {
                "columns": [
                    "*"
                ],
                "info": "Memory",
                "source": "file:///swarmdef/memory.csv"
            }
        ],
        "version": 1
    },
    "swarmSize": "medium"
}

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Create a model_params file")

    parser.add_argument("-o", dest="outfile", action="store", help="Output file", default="model_params.py")
    parser.add_argument("-n", dest="datapoints", action="store", help="Data points", type=int, default=100)

    args = parser.parse_args()

    if not os.path.isdir("swarmdef"):
        os.mkdir("swarmdef")

    with open("swarmdef/search_def.json", "w") as jsonfile:
        jsonfile.write(json.dumps(search_def))

    with open("swarmdef/memory.csv", "w") as csvfile:
        logging.info("Writing to memory.csv")
        fieldnames = ['timestamp', 'memory']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'timestamp': "datetime", 'memory': "float"})
        writer.writerow({'timestamp': "", 'memory': ""})
        for i in range(args.datapoints):
            date = datetime.now()
            memory = (float(psutil.virtual_memory().used)/float(psutil.virtual_memory().total)) * 100
            logging.info("Writing %s -> %s" % (date, memory))
            writer.writerow({'timestamp': date, 'memory': memory})
            time.sleep(1)
        logging.info("Done writing memory.csv!")

    res = subprocess.call("docker rm -f nupic-mysql".split())
    res = subprocess.call("docker rm -f nupic".split())
    logging.info("Launching nupic-mysql container")
    res = subprocess.call("docker run --name nupic-mysql -e MYSQL_ROOT_PASSWORD=nupic -p 3306:3306 -d mysql:5.6".split())
    time.sleep(5)
    res = subprocess.call("docker run --name nupic -v {}/swarmdef:/swarmdef -e NTA_CONF_PROP_nupic_cluster_database_passwd=nupic -e NTA_CONF_PROP_nupic_cluster_database_host=mysql --link nupic-mysql:mysql numenta/nupic python /usr/local/src/nupic/scripts/run_swarm.py /swarmdef/search_def.json --maxWorkers=4 --overwrite".format(os.getcwd()).split())
    res = subprocess.call("docker rm -f nupic-mysql".split())
    res = subprocess.call("docker rm -f nupic".split())
