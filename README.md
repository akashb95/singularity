# singularity

<a name="nav"></a>
## Quick Nav 🗺
- [Leggo️](#leggo)
    + [Installing gRPC stuff](#installing-grpc-stuff)
    + [Environment Variables](#environment-variables)
    + [DB](#db)
    + [Running Lighting server](#running-lighting-server)
    + [Running Lighting client](#running-lighting-client)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

<a name="leggo"></a>
## Leggo 🏃🏽‍♂️🏃🏽‍♀️
This repo is mainly a kind of template that everyone else can follow when working with gRPC stuff. It also will, hopefully, convey the structure that I envisage for the project. For now, this only contains implementations of gRPC server and client in Python the language of _my_ expertise.

_Disclaimer: This repo is my gRPC Tutorial Island (everyone else is welcome too, it ain't a Desert Island 🏜!), so please bear in mind there will be places where I'm probably not following best practices, and using hotfixes._

[🗺 Go back to Navigation &uarr;‍](#nav)

<a name="installing-grpc-stuff"></a>
#### Installing gRPC stuff
Assuming you are in the root project directory:

* Install requirements specified in `setup.py`.

* Run the Python script to create the gRPC generated code.

    ```
    cd lighting && python3 run_codegen.py
    ```
    
Generated files will be located in the `lighting/lib` directory.
  
<a name="environment-variables"></a>
#### Environment Variables
A `.env-template` file is provided in the root of the project directory. This should provide a template for the real `.env` file that is required for this project to run.

<a name="db"></a>
#### DB
For this project, I'm using SQLAlchemy as an ORM to manage the data. All Python files responsible for defining the data structure are in `dbHandler`. `dbHandler/seeder.py` includes some handy functions for creating a DB from the schema and seeding the initial, empty DB. All stored datetimes will be in UTC timezone. They should be converted to the appropriate timezone when the data is called.

Also ensure that all the pertinent env vars are set in your `.env` file. Further, ensure that the DB is set up and ready to accept connections.

A thorough tutorial: [link](https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers).

<a name="running-lighting-server"></a>
#### Running Lighting server
* Run `cd lighting/server && python3 server.py` and leave to run in background.

<a name="running-lighting-client"></a>
#### Running Lighting client
* Make sure server is up and running.
* Run `cd lighting/client && python3 client.py`. This is an example script, that demonstrates the use of RPCs that have been defined so far. It simply fires off some requests to the server specified above and logs the response to console.

[🗺 Go back to Navigation &uarr;‍](#nav)
