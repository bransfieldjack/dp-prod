![logo](https://dataportal-data.s3-ap-southeast-2.amazonaws.com/static/images/test_logo.PNG)

[![Build Status](https://travis-ci.com/s4madmin/dp-prod.svg?branch=master)](https://travis-ci.com/s4madmin/Stemformatics-Dataportal)

# Stemformatics Dataportal API 

Source code for the [Stemformatics Dataportal](https://api.stemformatics.org/). 
The dataportal is a centralised API and data store of all the datasets contained in Stemformatics. 
The API facilitates external access to both public and private datasets that exist in [stemformatics](https://www.stemformatics.org/). 


#### See [Dataportal-documentation](http://dataportal-documentation.s3-website-ap-southeast-2.amazonaws.com/ "Documentation")

## Getting Started

#### Dev/Testing:

If using a development env like conda, you should first install all the dependencies in the requirements.txt file.
You can run an adhoc, non-production grade instance using "python run.py"

Or:

 - export APP_SETTINGS=.../development_config.cfg
 - python -m flask run --host=0.0.0.0 --port=5001

#### Docker: 
Load any/all your environment variables into the cloned repo location. (Dont forget to update .cfg file - app no longer uses .env file for config)
The simplest way to do this is to use a .env file, but you can run export VAR=VALUE if you like. 
If you are using a .env file, run the load_vars.sh script to automate loading the environment variables. 

Start the docker build: 

```
docker-compose up
```

Once the build completes you will need to load the PSQL and MongoDB data.
There is a script included in the repo called "load_data.sh".
This script downloads the appropriate dump files from an AWS S3 bucket location, the url for which will be contained in
environment variables or .env file. If you are not authorised to download a test version of this data, you will need to provide your own. See the [documentation](http://dataportal-documentation.s3-website-ap-southeast-2.amazonaws.com/) above for how to initialise the data. 

#### Testing

cd to the directory containing the test files to manually run tests:
```
python -m unittest
```

#### Built With

* [Flask](https://flask.palletsprojects.com/en/1.1.x/) - The framework used
* [Flask-RESTPlus](https://flask-restplus.readthedocs.io/en/stable/) - API Documentation
* [Mongo](https://www.mongodb.com/cloud/atlas/lp/try2?utm_source=google&utm_campaign=gs_apac_australia_search_brand_atlas_desktop&utm_term=mongodb&utm_medium=cpc_paid_search&utm_ad=e&gclid=Cj0KCQjwy6T1BRDXARIsAIqCTXo10E_rTqydYPjnE4viNcoI14ctwUAH6QsJvCDLS4LyRC6pTYBIAjwaAhlSEALw_wcB) - Metadata Database
* [PostgreSQL](https://www.postgresql.org/) - Used for sample storage and auth


## Versioning

See the [documentation](http://dataportal-documentation.s3-website-ap-southeast-2.amazonaws.com/) for versioning information. 

## Authors

* **Jack Bransfield** - Software Engineer, Stemformatics CSCS
* **Jarny Choi** - Bioinformatician, Stemformatics CSCS

See also the list of [contributors](http://dataportal-documentation.s3-website-ap-southeast-2.amazonaws.com/) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
