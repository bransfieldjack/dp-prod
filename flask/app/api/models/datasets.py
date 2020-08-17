import os, pandas, json
from flask import jsonify
from app import app
import psycopg2
from . import _runSql
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps

postgres_username = app.config['POSTGRES_USERNAME'] # os.environ["POSTGRES_USERNAME"]
postgres_password = app.config["POSTGRES_PASSWORD"]
postgres_database_name = app.config["POSTGRES_DATABASE_NAME"]
postgres_host = app.config["POSTGRES_HOST"]
postgres_port = app.config["POSTGRES_PORT"]
postgres_uri = app.config["PSQL_URI"]
path_to_expression_files = app.config["PATHTOEXPRESSIONFILES"]
conn = psycopg2.connect(postgres_uri)
cursor = conn.cursor()
mongo_uri = app.config["MONGO_URI"]


# ----------------------------------------------------------
# Dataset class
# ----------------------------------------------------------

class Dataset(object):
    """Main class to encapsulate a dataset in Stemformatics. 
    Each dataset has a unique id, and we can associate 4 types of entities to a dataset:
    1. dataset metadata: information about the dataset, such as description, pubmed_id, etc.
    2. sample metadata: come from sample annotation, such as cell type, tissue, organism, etc.
    3. expression data: may be raw counts, cpm, etc.
    4. processing details: information about how the dataset was processed.
    """

    @staticmethod
    def metadataTableBasicKeys():
        """Return a list of key names for the metadata table, which form a subset of all keys. Useful when hiding all 
        the other keys which may are not often used.
        """
        return ["Title", "Authors", "Description", "PubMed ID", "Contact Name", "Contact Email", "Release Date", "dataType", "Platform"]

    def __init__(self, datasetId):
        """Initialise a dataset with Id. Note that id is an integer, and will be coherced into one.
        """
        self.datasetId = int(datasetId)
        self._metadataTable = None
        self._sampleTable = None
        self._expressionMatrix = {}

    def __repr__(self):
        return "<Dataset id={0.datasetId}>".format(self)

    def __eq__(self, other):
        return self.datasetId==other.datasetId

    def name(self):
        """It's often useful to have a short human readable name for a dataset, which is unique. Eg: "Ruiz_2012_22991473".
        """
        value = self.metadataTable().at["handle", "ds_value"]
        return value if value else self.metadataTable().at["Title", "ds_value"]

    def isPrivate(self):
        """Return true if this dataset is private.
        """
        myclient = pymongo.MongoClient(mongo_uri) # Mongo container name is 'mongo'. # local mongodb server.   # Connects to the mongodb daabase and returns everything.
        database = myclient["dataportal_prod_meta"]
        collection = database["datasets"]
        result = collection.find({"dataset_id": self.datasetId})
        return dumps(result)

    # dataset metadata -------------------------------------
    def metadataTable(self, keys="basic"):
        """
        Return a table of dataset metadata, such as description and pubmed id as a pandas DataFrame object.
        Example:
            > print(Dataset(6169).metadataTable().head())
                                                               ds_value
            ds_name
            cellularProteinExpression                              NULL
            Experimental Design        transcription profiling by array
            Platform                        Affymetrix HuGene-1_0-ST V1
            GEO Accession                                      GSE39210
            detectionThreshold                                     4.13
        """
        if self._metadataTable is None: # make a query and construct the DataFrame and cache it
            myclient = pymongo.MongoClient(mongo_uri) # Mongon container name is 'mongo'. # local mongodb server.   # Connects to the mongodb daabase and returns everything.
            database = myclient["dataportal_prod_meta"]
            collection = database["datasets"]
            result = collection.find({"dataset_id": self.datasetId})
            self._metadataTable = dumps(result)
            return self._metadataTable 

    def dataType(self):
        """Return one of ("microarray","RNAseq","sc_RNAseq","other"). Based on data_type_id field in datasets table.
        """
        return self.metadataTable().at["dataType","ds_value"]

    def updateMetadataValue(self, key, value, auditInstance=None):
        """
        Update values in dataset metadata matching key. Returns the number of records affected.
        If auditInstance is supplied, we also record this update.
        """
        if auditInstance:
            # get current value
            result = cursor.execute("select ds_value from dataset_metadata where ds_name=%s and ds_id=%s", (key, self.datasetId))
            value_from = result[0][0] if len(result)>0 else None
            auditInstance.record("dataset_metadata", "ds_value", value_from, value, "ds_name='%s' and ds_id=%s" % (key, self.datasetId))
        return _runSql("update dataset_metadata set ds_value=%s where ds_name=%s and ds_id=%s", (value, key, self.datasetId), type="update")

    def pieData(self, column):
        sample_type = _runSql("select distinct({}) from samples where dataset_id={}".format(column, self.datasetId))
        sample_id = _runSql("select distinct(sex) from samples where dataset_id={}".format(self.datasetId))
        return {"sample_type": sample_type, "sample_id": sample_id}

    def summaryTable(self):
        """
        Return a pandas DataFrame object that summarises all the datasets in the system. 
        This function should move outside this class, as it is not specific to one dataset.
        Example:
            > 
        """
        result = _runSql("select dataset_id, title, authors, description, generic_sample_type, handle, pubmed from merged_samples;")
        df = pandas.DataFrame(result, columns=["dataset_id", "title", "authors", "description", "generic_sample_type", "handle", "pubmed"]) #, "author", "description"])
        df.drop_duplicates("dataset_id", inplace = True) # Drop duplicated records. 
        return df
        
    def summaryTableSearch(self, searchTerm):
        """
        Returns a dataframe for a searched text term: "mouse, parental cell type etc."
        Search document index has been set for the merged_samples table with the following: 
        'update merged_samples set search_document = to_tsvector(dataset_id || ' ' || disease_state || ' ' || tissue_organism_part || ' ' || parental_cell_type ||
        ' ' || final_cell_type || ' ' || disease_state || ' ' || organism || ' ' || handle || ' ' || title || ' ' || authors || ' ' || description);' 
        """
        search = str(searchTerm)
        # result = _runSql("select dataset_id, tissue_organism_part, parental_cell_type, final_cell_type, disease_state, organism, handle, title, authors, description from merged_samples where to_tsvector(dataset_id || ' ' || disease_state || ' ' || tissue_organism_part || ' ' || parental_cell_type || ' ' || final_cell_type || ' ' || disease_state || ' ' || organism || ' ' || handle || ' ' || title || ' ' || authors || ' ' || description) @@ to_tsquery('{}')".format(search))
        result = _runSql("select dataset_id, title, authors, description from merged_samples where search_document @@ to_tsquery('{}')".format(search))
        # 
        df = pandas.DataFrame(result, columns=["dataset_id", "title", "authors", "description"])
        df.drop_duplicates("dataset_id", inplace = True) # Drop duplicated records. 
        print(df)
        return df

    # sample metadata -------------------------------------
    def sampleTable(self):
        """
        Return samples in the dataset as a pandas DataFrame object.
        """

        if self._sampleTable is None:   # make a query, construct the DataFrame and cache it
            # result = cursor.execute("select sample_id, replicate_group_id, sample_name, sample_name_long, sample_type, sample_type_long, generic_sample_type, generic_sample_type_long, sample_description, tissue_organism_part, parental_cell_type, final_cell_type, cell_line, reprogramming_method, developmental_stage, media, disease_state,labelling, genetic_modification, facs_profile, age, sex, organism, chip_type, dataset_id from samples where dataset_id=%s", (self.datasetId,))# < -- Correct statement but because dataset_id columns not yet loaded into the database, using this query instead (limit 100). 
            # data = cursor.fetchall()
            data = _runSql("select sample_id, replicate_group_id, sample_name, sample_name_long, sample_type, sample_type_long, generic_sample_type, generic_sample_type_long, sample_description, tissue_organism_part, parental_cell_type, final_cell_type, cell_line, reprogramming_method, developmental_stage, media, disease_state,labelling, genetic_modification, facs_profile, age, sex, organism, chip_type, dataset_id from samples where dataset_id=%s", (self.datasetId,))
            df = pandas.DataFrame(data)  # empty DataFrame with id as index
            df.columns=['sample_id', 'replicate_group_id', 'sample_name', 'sample_name_long', 'sample_type', 'sample_type_long', 'generic_sample_type', 'generic_sample_type_long', 'sample_description', 'tissue_organism_part', 'parental_cell_type', 'final_cell_type', 'cell_line', 'reprogramming_method', 'developmental_stage', 'media', 'disease_state', 'labelling', 'genetic_modification', 'facs_profile', 'age', 'sex', 'organism', 'chip_type', 'dataset_id']
            # df.set_index('sample_id', inplace=True)
        self._sampleTable = df
        # df.drop_duplicates(inplace = True) #"sample_id", inplace = True) # Drop duplicated records. 
        return self._sampleTable


    def atlasSampleTable(self):
        """
        Return atlas samples in the dataset as a pandas DataFrame object.
        """
        if self._sampleTable is None:   # make a query, construct the DataFrame and cache it
            # result = cursor.execute("select sample_id, replicate_group_id, sample_name, sample_name_long, sample_type, sample_type_long, generic_sample_type, generic_sample_type_long, sample_description, tissue_organism_part, parental_cell_type, final_cell_type, cell_line, reprogramming_method, developmental_stage, media, disease_state,labelling, genetic_modification, facs_profile, age, sex, organism, chip_type, dataset_id from samples where dataset_id=%s", (self.datasetId,))# < -- Correct statement but because dataset_id columns not yet loaded into the database, using this query instead (limit 100). 
            # data = cursor.fetchall()
            
            data = _runSql("select sample_id, annotator, evidence, blood_tier1, blood_tier2, blood_tier3, imac_tier1, imac_tier2, imac_tier3, phenotype, activation_status, display_metadata, include_blood, include_imac, dataset_id from atlas where dataset_id=%s", (self.datasetId,))
            df = pandas.DataFrame(data)  # empty DataFrame with id as index
            
            df.columns=["sample_id", "annotator", "evidence", "blood_tier1", "blood_tier2", "blood_tier3", "imac_tier1", "imac_tier2", "imac_tier3", "phenotype", "activation_status", "display_metadata", "include_blood", "include_imac", "dataset_id"]
            # df.set_index('sample_id', inplace=True)
            df.drop_duplicates(inplace = True)  # There are duplicate records in the atlas table - to be addressed in future table versions. 
        self._sampleTable = df
        # df.drop_duplicates(inplace = True) #"sample_id", inplace = True) # Drop duplicated records. 
        return self._sampleTable


    def numberOfSamples(self):
        """Return the number of samples in this dataset.
        """
        return len(self.sampleTable()) 

    def updateSampleValue(self, key, sampleIds, value):
        """
        Update values in samples in this dataset matching key and sampleIds. Returns the number of sampleIds affected.
        Example:
            > print(Dataset(6313).updateSampleValue("Organism", ["GSM1026799"], "Mus musculus")
            > 1
        """
        results = []
        for sampleId in sampleIds:       
            # get current value
            result = _runSql("select {} from samples where sample_id=%s and dataset_id=%s".format(key), (sampleId, self.datasetId))
            results.append(_runSql("update samples set {}=%s where dataset_id=%s and sample_id=%s;".format(key), (value, self.datasetId, sampleId,), type="update"))                           
            value_from = result[0][0] if len(result)>0 else None

            print("New Value", value)
            print("Original", value_from)
            print("Updated: ", results)
            
        return {"Updated": value, "Original": value_from}

    def updateAtlasValue(self, key, sampleIds, value):
        """
        Updates a record in the atlas table. 
        """
        results = []
        for sampleId in sampleIds:       
            # get current value
            result = _runSql("select {} from atlas where sample_id=%s and dataset_id=%s".format(key), (sampleId, self.datasetId))
            results.append(_runSql("update atlas set {}=%s where dataset_id=%s and sample_id=%s;".format(key), (value, self.datasetId, sampleId,), type="update"))                           
            value_from = result[0][0] if len(result)>0 else None

            print("New Value", value)
            print("Original", value_from)
            print("Updated: ", results)
            
        return {"Updated": value, "Original": value_from}
            
    # expression data -------------------------------------
    def expressionMatrix(self, key):
        """Return expression matrix for this dataset as a pandas DataFrame.
        Ran the following code and found that for this dataset (58302,24), it took 0.167 sec using read_csv and 0.127 sec using read_hdf
        (on my laptop).
        import time
        t0 = time.time()
        df = pandas.read_csv(os.path.join(path_to_expression_files, "7283_gene_count_frags.txt"), sep="\t", index_col=0)
        print(time.time()-t0)
        t1 = time.time()
        df = pandas.read_hdf(os.path.join(path_to_expression_files, "7283.h5"), "/dataframe/counts")
        print(time.time()-t1)
        """
        if key not in self._expressionMatrix:
            self._expressionMatrix[key] = pandas.read_csv(self.expressionFilePath(key), sep="\t", index_col=0)
        return self._expressionMatrix[key]
        
    def expressionFilePath(self, key):
        """Return the full path to the expression file.
        """
        return os.path.join(path_to_expression_files, "%s.%s.tsv" % (self.datasetId,key))

    def expressionValues(self, geneIds):
        """Return expression values for a list of gene Ids. We will use .gene.tsv files for microarray datasets.
        """
        pass

# ----------------------------------------------------------
# Functions without class
# ----------------------------------------------------------
def exportGeneIdProbeIdMapping():
    """Use this function to export a file which is has geneId,probeId columns.
    """
    conn = psycopg2.connect(postgres_uri)
    cursor = conn.cursor()
    cursor.execute("select distinct from_id,to_id from stemformatics.feature_mappings where db_id=59")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    pandas.DataFrame(result, columns=["geneId","probeId"]).to_csv("/mnt/data/portal_data/GeneIdProbeIdMapping.tsv", sep="\t", index=False)

# ----------------------------------------------------------
# Nosetests
# ----------------------------------------------------------
def test_metadataTable():
    ds = Dataset(6991)
    print(ds.metadataTable(keys="full"))
    print("###(%s)###" % ds.isPrivate())

def test_expressionMatrix():
    ds = Dataset(5001)
    df = ds.expressionMatrix()
    print(df.head())
    print(ds.expressionMatrix(key="genes").head())

def test_expressionValues():
    ds = Dataset(5001)
    print(ds.expressionValues(["ENSG00000165406"]))
