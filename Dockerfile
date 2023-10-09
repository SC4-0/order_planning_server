FROM ubuntu:22.04

# apt-get and system utilities
# RUN apt-get clean && apt-get update && apt-get install -y \
#    curl apt-utils apt-transport-https gcc build-essential\
#    && rm -rf /var/lib/apt/lists/*
RUN apt-get clean && apt-get update && apt-get install -y curl apt-utils gnupg apt-transport-https

# adding custom MS repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# install SQL Server drivers - ODBC
# ODBC is a wrapper around freetds, allegedly provides better documentation
RUN apt-get update && ACCEPT_EULA=Y apt-get -y install msodbcsql18
RUN apt-get -y install unixodbc unixodbc-dev

# install SQL Server tools
RUN apt-get update && ACCEPT_EULA=Y apt-get -y install mssql-tools18
RUN echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
RUN /bin/bash -c "source ~/.bashrc"

# python libraries
# note that Ubuntu 22.04 ships with Python3.10 pre-installed
RUN apt-get update && apt-get install -y libpython3.10 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# install python env - no venv needed due to containerization
RUN mkdir /home/order_planning_server
ADD . /home/order_planning_server
WORKDIR /home/order_planning_server/src
RUN python3.10 -m pip install -r ../requirements/dev.txt
CMD python3.10 -m order_planning_server.main
