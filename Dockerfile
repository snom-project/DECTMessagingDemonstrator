FROM python:3.7.2-alpine
RUN apk add --no-cache python3-dev libstdc++ && \
    apk add --no-cache g++ && \
    ln -s /usr/include/locale.h /usr/include/xlocale.h && \
    pip3 install cython && \
    pip3 install numpy && \
    pip3 install pandas
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN apk add --update --no-cache g++ gcc libxslt-dev
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
CMD [ "python", "./web.py"]
