apt-get update
apt-get install -y libxml2-dev libxslt1-dev python-dev
apt-get install -y protobuf-compiler
apt-get install -y rsyslog
apt-get install -y bash
apt-get install -y unixodbc-dev

apt-get install gcc libpq-dev -y
apt-get install python-dev  python-pip -y
apt-get install python3-dev python3-pip python3-venv python3-wheel -y

apt-get install unixodbc-dev -y
apt-get install sqlite3 -y
apt-get install python-gevent -y

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade setuptools
python3 -m pip install wheel
#python3 setup.py bdist_wheel

python3 -m pip install pandas
python3 -m pip install cython 
python3 -m pip install numpy

pip install --no-cache-dir -r requirements.txt

