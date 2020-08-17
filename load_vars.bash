#!/bin/bash

# A script to load all the variables from the .env file into the current environment. 
# Run flask with: python -m flask run --host=0.0.0.0 --port=5001

while read p; do
  VAR_ENV_VAR="$p"
  VAR_ENV_VAR_DESC=" - LOADED"
  VAR_OUT="$VAR_ENV_VAR $VAR_ENV_VAR_DESC"
  export "$p"
  echo "$VAR_OUT"
done < .env

