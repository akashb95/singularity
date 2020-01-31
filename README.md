# singularity: a PoC

### Installing gRPC stuff
* Install requirements specified in `setup.py`.

* Run the Python script to create the gRPC generated code.

    ```
    cd /path/to/project/lighting && python3 settings.py
    ```
    
  Generated files will be located in the `lighting` directory. In each of these files, fix the import paths to explicitly specify where to import them from:
  e.g. `import location_pb2 as location__pb2` &rarr; `from lighting import location_pb2 as location__pb2`.
  
  
### Environment Variables
A `.env-template` file is provided in the root of the project directory. This should provide a template for the real `.env` file that is required for this project to run.

### Running Lighting server
* Run `lighting/server/server.py`.

### Running Lighting client
* Make sure server is up and running.
* Run `lighting/client/client.py`. This is an example script, that demonstrates the use of RPCs that has been defined so far.

### DB
For this project, I'm using SQLAlchemy as an ORM to manage the data. All Python files responsible for defining the data structure are in `dbHandler`. `dbHandler/seeder.py` includes some handy functions for creating a DB from the schema and seeding the initial, empty DB. All stored datetimes will be in UTC timezone. They should be converted to the appropriate timezone when the data is called.

Also ensure that all the pertinent env vars are set in your `.env` file. Further, ensure that the DB is set up and ready to accept connections.

A thorough tutorial: [link](https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers).