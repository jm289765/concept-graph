#!/bin/sh

###############################
#            config           #

# relative path to directory with redis files in it
REDIS_PATH="./_redis"
# relative paths redis server and config from REDIS_PATH directory
REDIS_SERVER="./redis-server.exe"
REDIS_CONF="./redis.conf"

# relative path to solr directory
SOLR_PATH="./_solr/solr-8.11.2/bin"
# relative path to solr server binary from SOLR_PATH directory
SOLR_SERVER="./solr.cmd"

# relative path to main.py
MAIN_PATH="./main.py"

#          end config         #
###############################

echo "concept-graph server starter"

BASE_DIR=$(dirname "$0")

echo "starting redis..."
cd $REDIS_PATH
echo $PWD
$REDIS_SERVER $REDIS_CONF &
echo "redis started"
cd $BASE_DIR

echo "starting solr..."
cd $SOLR_PATH
$SOLR_SERVER start
echo "solr started"
cd $BASE_DIR

# don't need to wait for redis to finish since solr takes longer to load.
echo "waiting 2 seconds for solr to finish loading"
sleep 2
echo "starting main server..."
py $MAIN_PATH
