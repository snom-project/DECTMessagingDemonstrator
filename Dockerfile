FROM python:3.9-slim
RUN apt-get update
RUN apt-get install -y libxml2-dev libxslt1-dev
RUN apt-get install -y bash
RUN apt-get install -y unixodbc-dev

RUN apt-get install gcc libpq-dev -y
RUN apt-get install python3-dev python3-pip python3-venv python3-wheel -y

RUN apt-get install unixodbc-dev -y
RUN apt-get install sqlite3 -y

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade setuptools
RUN python3 -m pip install wheel
#RUN python3 setup.py bdist_wheel

RUN python3 -m pip install pandas
RUN python3 -m pip install cython && \
    python3 -m pip install numpy
RUN python3 -m pip install pygame

WORKDIR /usr/src/app
COPY requirements.txt ./
COPY start.sh ./start.sh
RUN chmod +x ./start.sh
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install sqlite-web
COPY app/ .
CMD ["/bin/bash", "./start.sh"]

