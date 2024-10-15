#!/bin/bash

#####################
# setup environment #
#####################

mkdir -p $PROJECT_DIR/airflow/logs
mkdir -p $PROJECT_DIR/airflow/plugins
mkdir -p $PROJECT_DIR/airflow/db
mkdir -p $PROJECT_DIR/airflow/common

AIRFLOW_CFG_FILE="$PROJECT_DIR/airflow/airflow.cfg"

if ! [[ -e "$AIRFLOW_CFG_FILE" ]]; then
  echo "creating empty file at $AIRFLOW_CFG_FILE"
  touch "$AIRFLOW_CFG_FILE"
fi

# Create an empty SQLite database file if it does not exist
DBFILE="airflow.db"
FQDBFILE="$PROJECT_DIR/airflow/db/$DBFILE"
if [ ! -f "$FQDBFILE" ]; then
  touch "$FQDBFILE"
  echo "SQLite database file $FQDBFILE created."
else
  echo "SQLite database file $FQDBFILE already exists."
fi

export AIRFLOW_HOME_DIR="opt/airflow"
export WORKING_DIR=${PROJECT_DIR}/working_example
export RAW_DATA_DIR=${PROJECT_DIR}/example_rawdata

###############################
# initialize airflow database #
###############################
cd $PROJECT_DIR/docker

docker-compose run --rm airflow-webserver airflow db init

# Create admin user
docker-compose run --rm airflow-webserver airflow users create \
  --username admin \
  --password admin \
  --firstname Firstname \
  --lastname Lastname \
  --role Admin \
  --email admin@example.com

cd $PROJECT_DIR

#################
# start airflow #
#################
compose() {
  docker-compose -f $PROJECT_DIR/docker/docker-compose.yml up
}

decompose() {
  docker-compose -f $PROJECT_DIR/docker/docker-compose.yml down
}

compose;
decompose;