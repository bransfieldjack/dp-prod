#!/bin/bash

set -o allexport; source .env; set +o allexport # Loads the .env file variables for reference in this script. 

# This block handles downloading the postgres 'users.sql' and 'samples.sql' from an AWS S3 bucket location or any URI that can be substituted into the .env file. 
cd ./postgres/postgres-volume && \
wget ${USERS_TABLE} && \
wget ${SAMPLES_TABLE} && \
wget ${ATLAS_TABLE}
echo "POSTGRES data loaded." && \
cd .. && \
cd .. && \

# This block handles downloading the mongo 'annotator_interactions.bson' and 'datasets collections.bson' from an AWS S3 bucket location or any URI that can be substituted into the .env file. 
cd ./mongo/mongo-volume && \
mkdir dumps && \
cd dumps && \
mkdir dataportal_prod_governance && \
cd dataportal_prod_governance && \
wget ${ANNOTATOR_INTERACTIONS_BSON} && \
wget ${ANNOTATOR_INTERACTIONS_META_JSON} && \
cd .. && \
cd .. && \
cd dumps && \
mkdir dataportal_prod_meta && \
cd dataportal_prod_meta && \
wget ${DATASETS_BSON} && \
wget ${DATASETS_METADATA_JSON} && \
cd ..
cd ..
cd ..

echo "MONGO data loaded."
echo "Data load finished."

pwd

docker exec postgres /bin/sh -c "cd /var/lib/postgresql/data && psql dataportal < users.sql && psql dataportal < samples.sql && psql dataportal < atlas.sql " && \

echo "POSTGRES tables created." && \

docker exec mongo /bin/sh -c "cd /data/db/dumps && mongorestore dataportal_prod_governance/annotator_interactions.bson" && \
docker exec mongo /bin/sh -c "cd /data/db/dumps && mongorestore dataportal_prod_meta/datasets.bson" && \

echo "MONGO documents created. "
echo "Data load for both POSTGRES and MONGO complete."

# Download the certificates and place them in the nginc config folder in the ngnix container.

cd ./nginx/data/certs && \
wget ${SSL_CERT} && \
wget ${SSL_KEY} && \

echo "Script finished. "


