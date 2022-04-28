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


#### Credits and Acknowledgments
Kevin Worthington, Colorado State University

Kara Handren, University of Toronto

Jack Reed, Stanford Libraries

Karen Majewicz, University of Minnesota, BTAA;
Yijing (Zoey) Zhou, University of Minnesota, BTAA
https://github.com/BTAA-Geospatial-Data-Project/dcat-metadata
https://github.com/BTAA-Geospatial-Data-Project/workflow