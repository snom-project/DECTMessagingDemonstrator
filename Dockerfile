FROM python:3.7.2-slim
RUN pip3 install --upgrade pip
RUN pip3 install pandas
RUN pip3 install cython && \
    pip3 install numpy
    
RUN apt-get update
RUN apt-get install -y protobuf-compiler
RUN apt-get install -y rsyslog 
RUN apt-get install bash

WORKDIR /usr/src/app
COPY requirements.txt ./
COPY start.sh ./start.sh 
RUN chmod +x ./start.sh
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
CMD ["/bin/bash", "./start.sh"]

