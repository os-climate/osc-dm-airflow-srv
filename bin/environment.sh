#!/bin/bash

#####
#
# environment.sh - Setup common environment variables
#
# Author: Davis Broda, 15205060+DavisBroda@users.noreply.github.com, 2024-10-08
#
# Parameters:
#   N/A
#
#####

if [ -z ${HOME_DIR+x} ] ; then
    echo "HOME_DIR environment variable has not been set (should be setup in your profile)"
    exit 1
fi

# TODO: rename to osc naming convention
export ROOT_DIR="$HOME_DIR"
export PROJECT="osc-dm-airflow-srv"
export PROJECT_DIR="$ROOT_DIR/$PROJECT"

$PROJECT_DIR/bin/show.sh