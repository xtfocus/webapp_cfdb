FROM python:3.9-slim

WORKDIR /code

RUN apt-get update && apt-get -y install unixodbc curl debian-keyring

# installing ODBC 17 for mssql
RUN curl https://packages.microsoft.com/keys/microsoft.asc |  tee /etc/apt/trusted.gpg.d/microsoft.asc

RUN apt-get update

RUN curl https://packages.microsoft.com/config/debian/10/prod.list |  tee /etc/apt/sources.list.d/mssql-release.list

RUN  apt-get update
RUN  ACCEPT_EULA=Y apt-get install -y msodbcsql17


# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./backend/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./backend /code/backend



