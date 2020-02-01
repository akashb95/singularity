# singularity

## Quick Nav
- [Start with "Why?"‍](#why)
- [What's the idea?](#what)
- [How do we do this?](#how)
- [Leggo️](#leggo)
    + [Installing gRPC stuff](#installing-grpc-stuff)
    + [Environment Variables](#environment-variables)
    + [DB](#db)
    + [Running Lighting server](#running-lighting-server)
    + [Running Lighting client](#running-lighting-client)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

<a name="why"></a>
## Start with "Why?" 🤷🏽‍

We'll all be veterans one day of this deadly quagmire of software junk that is PLANet. We all think we can do better, and that had _we_ been in charge, we could have figured it all out.

This project is a chance to show what is possible with a bit of time, a lot of energy, and a group vibrant individuals working as a team. 

Oh and there's gonna be pizza. And coke (BYO credit cards). Maybe a hipflask of Captain Morgan. 👀

<a name="what"></a>
## What's the idea? 💡
In the time afforded to us, we can make a decent attempt at showcasing some of the key functionality within PLANet. After an informal discussion with Jon, it seems that the most important things people do with our hunk of software is check Daily Faults (what's gone wrong?? 🤢) and billing (how much am I shelling out _now_??? 🔥💸). 

As we all know (but I'll provide some brief context anyway), PLANet codebase is totally monolithic. SQL commands are all over the place, the ExtJS is inextricably tied up with the PHP, and every little TALQ CMS has to do requires non-trivial and fiddly changes in the outmoded and obsolete DB.
 
The solution is quite simple: microservices 🎉. It keeps the separate components... well... Separate. In this way, everything that depends on the DB can be kept isolated from each other and doesn't have to interact with any PLANet code at all. It won't just clean up PLANet, but will provide a scalable and modular way to organise the entire business. 

Of course, microservices have been around for years and years. But who wants to always stick with the old? 

And so, this particular project experiments with [gRPC](grpc.io). gRPC is a (relatively new) framework that allows microservices to communicate via well-defined protocols. Each of the services can be in any of 10 different languages, from Java to JavaScript, from PHP to Python. 

The idea is simple enough. We give gRPC certain **protocol definitions**. Using a simple CLI command, we generate **boilerplate code** in whichever of the supported languages we choose. The boilerplate provides functions/class/methods with which we can tell **servers and clients** what to do with the messages they receive and how to respond.

<a name="how"></a>
## How do we do this? 🧐⁉️
We envisage a system where:
* The frontend (i.e. PLANet) is slick and smooth and sexy.
* Frontend communicates to an API Gateway of a kind that validates and forwards requests to the appropriate microservices.
* The microservices can communicate between themselves and do the tasks they're meant to.
* The microservices and ONLY the microservices can directly modify and/or read the DB directly.
* The response feeds back through the chain, and is reflected in the frontend.

Of course, for the _full_ range of functionality that Telensa provides, this would take months to implement, even with an effective team. But to reiterate, we only want to focus on a couple of key functionalities and highlight the attractions of our _design_ rather than flaunt the range of tricks our code can do.

For now, we propose that we come up with a list of tasks (that we'll put in as Github Issues), that can be taken up by anyone who wishes to tackle that particular task. The list of tasks itself should be decided in conference, but we deliberately want to keep these limited owing to the very little time we have on the day ⏰.

<a name="leggo"></a>
## Leggo 🏃🏽‍♂️🏃🏽‍♀️
This repo is mainly a kind of template that everyone else can follow when working with gRPC stuff. It also will, hopefully, convey the structure that I envisage for the project. For now, this only contains implementations of gRPC server and client in Python the language of _my_ expertise. Separate microservices should be stored as separate projects on separate [orphan branches](https://stackoverflow.com/questions/14679614/whats-the-best-practice-for-putting-multiple-projects-in-a-git-repository).

_Disclaimer: This repo is my gRPC Tutorial Island (everyone else is welcome too, it ain't a Desert Island 🏜!), so please bear in mind there will be places where I'm probably not following best practices, and using hotfixes._

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
