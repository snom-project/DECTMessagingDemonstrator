FROM python:3.7.2-slim
RUN pip3 install pandas
RUN pip3 install cython && \
    pip3 install numpy
    
RUN apt-get update
RUN apt-get install -y protobuf-compiler
RUN apt-get install -y rsyslog 


WORKDIR /usr/src/app
COPY requirements.txt ./
COPY start.sh ./start.sh 
RUN chmod +x ./start.sh
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
#CMD bash 
CMD ./start.sh  

