# singularity: a PoC

### Installing gRPC stuff
* Install requirements specified in `setup.py`.

* Run the Python script to create the gRPC generated code.

    ```
    cd /path/to/project/lighting && python3 settings.py
    ```
    
  Generated files will be located in the `lighting` directory.
  
### Running Lighting server
* Run `lighting/server/server.py`.

### Running Lighting client
* Make sure server is up and running.
* Run `lighting/client/client.py`. This is an example script, that demonstrates the use of RPCs that has been defined so far.
