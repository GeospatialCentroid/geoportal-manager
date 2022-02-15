# Geoportal Manager

#### Project Overview
This project extends the functionality of [geoblacklight](https://github.com/geoblacklight/geoblacklight) 
with a frontend geoportal interface 
and a backend administration/management system.

The purpose of this project is to create a unified system for accessing geospatial data 
stored across various platforms. 
Only a dataset's metadata is stored by this system, which is used for discovery provided by the Solr search engine.
Exploration of the data is enabled by a shared web map allowing multiple layers to be overlaid together.
The web services and image servers supporting this map layer capability, are handled by external systems where the data resides.

Supported map layers include:
* Feature Layers 
* Tiled Map Layer
* Dynamic Map Layer
* Image Map Layer
* Web Map Tile Service
* IIIF
* And static images via the Distortable Image plugin https://github.com/publiclab/Leaflet.DistortableImage

Map layers are either harvesting via API calls or manually creating within the management system.
To keep records current, harvesters should be run periodically. 
Often times, harvested metadata needs to be supplemented with additional information. 
To support this, a change management system has been developed to prevent manual changes from being overwritten. 

When metadata is ready to be viewed from the web map interface, it must be ingested into the Solr search engine.

Online demo coming soon.

##### The Frontend Geoportal Interface
The Features of the Geoportal interface include
- Multi-layer map viewer
- Layer customization
- Map annotation
- Map sharing
- Tabular data view with sorting and filtering
- Layer size sort
- Dataset support
- Sub-setting for supported layers
- Multilingual supported public interface
- Child record searching - coming soon
- Map behavioral statistics - coming soon


##### The Backend Management tool
Behind the scenes, a management tool allows data to be harvested, curated and ingested into the Solr search engine.
Built using the Django Python framework, the management tool layers curation features include:
- Searching 
- Sorting
- Filtering 
- And CRUD - Create, Retrieve, Update and Delete

### Installation instructions
This program uses Postgres with PostGIS, Solr, and Python.
To install each of them in OSX use the instructions below.
Note that this is all done via the Terminal using the commands below

##### Installing Solr
```brew install solr```
And remember your solr password.

###### Start Solr
If not already started
```solr start```

##### Create the Solr core and enable the Solr schema
1. Go to http://localhost:8983/ and click the "No cores available button" on the bottom left.
2. Enter 'solr-blackligh-core' for both the name and instanceDir fields.
3. Navigate to the home directory for solr. Note this can be found from the solr Dashboard under the variable "-Dsolr.solr.home"
4. Using the contents of 'solr-blackligh-core.zip' place the scheme in the solr core directory
5. Execute ```solr restart``` in the Terminal

##### Installing postgres with PostGIS
Follow the instructions at https://morphocode.com/how-to-install-postgis-on-mac-os-x/

Create a database called 'geoportal' and a user called 'geoportal_admin' with a password of your choosing

#### Store your passwords as environment variables
To keep your password safe, this program uses environment variables.
from the Terminal enter
```touch ~/.bash_profile; open ~/.bash_profile```
Add the following lines to the open text document,
changing the text between the single quotes as appropriate.

```export GEOPORTAL_DB_PASS='YOUR DATABASE PASSWORD'```

```export SOLR_PASSWORD='YOUR SORL PASSWORD'```

```export SECRET_KEY='YOUR SECRET Key for Django'``` 

```export GOOGLE_ANALYTICS_ID='YOUR Google Analytics Measurement ID'``` 

see https://humberto.io/blog/tldr-generate-django-secret-key/ to generate Django Secret Key

Then in the terminal again enter
```source ~/.bash_profile```

###### Start postgres
If not already started
```pg_ctl -D /usr/local/var/postgres start```

##### Install Python
You'll need python version >3.
The following instructions explain how https://docs.python-guide.org/starting/install3/osx/

##### Setup the Python Virtual Environment
```virtualenv -p python3 venv```

##### Activate Virtual Environment
```source venv/bin/activate```

##### Install the dependencies in the Virtual Environment
In the Terminal with the virtual environment activated,
navigate to the directory of the program code and run
```pip install -r requirements.txt```

##### Create the database tables
```python manage.py migrate```

#### Create an Admin user
```python manage.py createsuperuser```

### Start the Geoportal application
```python manage.py runserver```
Your site can now be seen at http://localhost:8000/
but there aren't any records yet

## Add map layers
Out of the box there aren't any data layers in the database. To add some, follow the steps below:

1. From your web browser navigate to http://localhost:8000/admin
2. Click the End_point link to be taken to the end points page
3. Click the button "Add END_POINT +" button on the top right of the screen
4. Enter a:
   * name
   * Org_name, used as the prefix for harvested data.
   * Url, the json feed to access the data. E.g for ArcGIS hub pages use simply append "/data.json".
     E.g https://geospatialcentroid-csurams.hub.arcgis.com/data.json
   * Use the '+' button to create a default publisher for the end_point
   * Choose your end_point type
        Supported end points include
        * DCAT (ArcGIS Hub)
        * ArcGIS Online. This uses organizational id.
            Note, in an academic setting this is often not a curated collection
        * CONTENTdm
        * dSPACE (not yet integrated with change management)
        * more end_point types can be created, see instructions below
    * a thumnaile url is optional
5. Click the "SAVE" button

###### Harvesting
The Command-line is used to harvest data.
With terminal path set to the code location and with the virtual environment activated
Enter the following
```python manage.py harvest -e 1```

Harvested records will download from the end_point and be saved to the in the /resources/harvester/data/ folder
using the 'Org_name'

-e is the endpoint id from the management system

Other Arguments
-d is for date, and is set to '' to use no date when using Git tracking
omit this to have today's date appended to loaded data when using local matadata tracking

-r for reference ids to target from endpoint

-o for overwriting existing loaded data
without this, subsequent harvests will not refresh existing data

###### Curation
1. Navigate to http://localhost:8000/admin/, use the Django admin username and password created earlier to log-in
   and click the resources link
2. Choose the resource you would like to end
3. Makes changed
4. Click SAVE



###### Ingestion
When ingesting resources into the Solr search engine,
the status value for a resource can help determine what gets ingested.
The status options are as follows with their two character code in brackets:
* Needs Review (nr)- default setting for harvested records
* Approved for Staging (as)
* In Staging (is)
* Approved for Production (ap)
* In Production (ip)
* Remove from Staging (rs)
* Remove from Production (rp)

A typical ingest command looks like this:

`python manage.py ingest -s 'as' -e 1`

-e is the endpoint id from the management system
-s is the two character status code, typically 'as' or 'ap', though any of the two character status codes can be used

Other Arguments
-n is for preventing a status promotion from
* Approved for Staging to In Staging
* Or Approved for Production to In Production

-r is for reference ids to target for ingestion
Note: Be sure to include a status value so child records can be retrieved too ;)

###### Deletion from Solr
With the 'remove staging' (or 'ns') flag set in the django admin,
calling the following will remove all these flagged records from solr
and update their status to 'Needs Review' (or 'nr')
`python manage.py delete -s 'rs'`

--TODO - Add ability to specify which environment to remove a resource from

Other Arguments
-r for reference ids to target for deletion

Passing an "-s 'all'" instead will remove all records from solr
You will be prompted to confirm acceptance before all the records are deleted.

Note: From the Resource Management page,
you can also select specific resources to be removed from Staging (Production coming soon).

#### deleting resources from postgres
As parent and child records are linked, removing a parent causes the system to hang and requires temporarily removing database triggers
To do this the database user requires privileges, giving them SUPERUSER status.
The following script called when logged into the database works for now, though lesser privilege should be considered
```ALTER USER geoportal_admin WITH SUPERUSER;```





#### Adding translation text
Copy the existing translation file /static/i18n/en.json
Give it a new name, e.g fr.json
Replace all the text values for the language you are translating to.
Save the file and in the terminal run the command below to have the file placing in the mirror
'static' folder so that it's accessible from the browser
```python manage.py collectstatic```


### debug mode
Add "?d=1&" as a url parameter to activate an admin link in the details page
Note: this only works for dynamically loaded results

#### Copyright and licensing information

#### Credits and acknowledgments
Kevin Worthington, Colorado State University

Kara Handren, University of Toronto

Jack Reed, Stanford Libraries

Karen Majewicz, University of Minnesota, BTAA
Yijing (Zoey) Zhou, University of Minnesota, BTAA
https://github.com/BTAA-Geospatial-Data-Project/dcat-metadata
https://github.com/BTAA-Geospatial-Data-Project/workflow