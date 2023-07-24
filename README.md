# order_planning_server

This is a server made with FastAPI and run with Uvicorn in development. It can be developed either on localhost, or within a Docker container (my preference).

Requirements:
- SQL Server database
- SQL Server database drivers (set up in the Docker image)
- Python

The username and password for connecting into the db will be what you set up on the SQL Server database; please omit it when committing and pushing code.

Developing on localhost:

1. Set up a virtual environment with the necessary dependencies, e.g. on windows:

`python -m venv order_planning_venv`
`order_planning_venv\Scripts\activate`
`python -m pip install -r requirements/dev.txt`

System-wide installations of Python3.3 and later put the Python launcher on your path, so you can install multiple python versions if needed and run with e.g. `py -3.10`.

2. Run server.

`cd` into `src`, and run:
`python -m order_planning_server.main`

Developing in the Docker container:

1. `cd` into the directory containing the Dockerfile, and run `docker build -t "order_planning_server" .`

2. `docker container run -p 8000:8000 -it order_planning_server`

3. Run server.

`cd` into `src`, and run:
`python3.10 -m order_planning_server.main`

Depending on your OS, you may need to modify the networking e.g. IP on which server runs, IP that database is located at.