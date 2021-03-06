FROM python:3.7.2-slim
RUN apt-get update
RUN apt-get install -y libxml2-dev libxslt1-dev python-dev
RUN apt-get install -y protobuf-compiler
RUN apt-get install -y rsyslog
RUN apt-get install -y bash
RUN apt-get install -y unixodbc-dev

RUN apt-get install gcc libpq-dev -y
RUN apt-get install python-dev  python-pip -y
RUN apt-get install python3-dev python3-pip python3-venv python3-wheel -y

RUN apt-get install unixodbc-dev -y
RUN apt-get install sqlite3 -y
RUN apt-get install python-gevent -y

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools
RUN pip3 install wheel
#RUN python3 setup.py bdist_wheel

RUN pip3 install pandas
RUN pip3 install cython && \
    pip3 install numpy

WORKDIR /usr/src/app
COPY requirements.txt ./
COPY start.sh ./start.sh 
RUN chmod +x ./start.sh
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
CMD ["/bin/bash", "./start.sh"]

