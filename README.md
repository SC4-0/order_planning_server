# order_planning_server

This is a server made with FastAPI and run with Uvicorn in development. Since this has not been Dockerized yet, for now:

1. Set up a virtual environment with the necessary dependencies, e.g. on windows:

`python -m venv order_planning_venv`
`order_planning_venv\Scripts\activate`
`python -m pip install -r requirements/dev.txt`

2. Run server.

`cd` into `src`, and run:
`>python -m order_planning_server.main`