import sys
import logging

from lxml import etree as ET
import lxml.builder
from copy import deepcopy

import os
import sqlite3
import pyodbc
import time

class DECTMessagingDb:

    def __init__(self, beacon_queue_size=3, odbc=True, initdb=True, logger=logging.getLogger('DECTMessagingDb')):
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        logger.addHandler(ch)
          
        self.logger = logger

        # DB
        self.initdb = initdb
        self.sqlite = not odbc
        self.odbc = odbc
        self.db_filename = None
        self.schema_filename = None
        self.connection = None
        self.beacon_queue_size = beacon_queue_size
        
        if odbc:
            self.connectODBCDB()
        else:
            self.createDB()
        

    def connectODBCDB(self):
        self.schema_filename = 'DB/DECTMessagingSchema_mySQL.sql'
        
        cnxn = pyodbc.connect('DSN=mysqlansi')
        cnxn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
        cnxn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
        cnxn.setencoding(encoding='utf-8')

        
        self.connection = cnxn

        print('Trying ODBC Connect')
        #cnxn = pyodbc.connect("DRIVER={SQLite 3};Direct=True;Database=%s" % self.db_filename)
        
        # only connect or new DB
        if not self.initdb:
            cnxn.execute("""
                            USE DECTmessaging;
                         """)
                  
            return True
        
        directory = 'DB'
        cursor = cnxn.cursor()

        for root, dirs, files in os.walk(directory):
            #print(files)
            for file in files:
                if file.endswith('mySQL.sql'):
                    script = file
                    with open(directory+'/' + script,'rt') as inserts:
                        #print(directory+'/' + script)
                        sqlScript = inserts.read()
                        #print('full', sqlScript)
                        # split into individual SQL commands
                        for statement in sqlScript.split(';'):
                            with cnxn.cursor() as cur:
                                #print('statement:', statement)
                                if " ".join(statement.split()):
                                    cur.execute(" ".join(statement.split()))

        
        cnxn.execute("""
                       insert into Beacons (account)
                       values ('test_db_account');
                       """)
        


    def createDB(self):
        self.sqlite = True
        self.db_filename = 'DB/DECTMessaging.db'
        self.schema_filename = 'DB/DECTMessagingSchema_sqlite3.sql'

        db_is_new = not os.path.exists(self.db_filename)

        conn = sqlite3.connect(self.db_filename)
        # remember the connection to reuse
        self.connection = conn
        
        if db_is_new:
            print('Creating schema')
            with open(self.schema_filename, 'rt') as f:
                schema = f.read()
                conn.executescript(schema)
    
                print('Inserting initial data')
                conn.executescript("""
                insert into Beacons (account)
                values ('test_db_account');
                """)

        else:
            print('Database exists, assume schema does, too.')
        # keep the connection
        #conn.close()

    '''
        account        text,
        device_type     text default "None",
        bt_mac         text default "",
        name        text default "no name",
        ssid        text default "-100",
        uuid        text default "",
        beacon_type        text default "None",
        proximity        text default "0",
        beacon_gateway    text default "FFFFFFFFFF",
        user_image        text default "/images/Heidi_MacMoran_small.jpg",
        device_loggedin    text default "0",
        base_location    text default "None",
        base_connection    text default "('127.0.0.1', 4711)",
        time_stamp        text default "2020-04-01 00:00:01.100000"
        tag_time_stamp       text default "2020-04-01 00:00:01.100000"
    '''
    def update_db(self, table="Devices", **kwargs):
        # account is our key to find the data
        if kwargs.get("account"):
            account_key = kwargs.get("account")
        else:
            return False
        #print(kwargs)
        
        """ update/insert rows into objects table (update if the row already exists)
            given the key-value pairs in kwargs
            INSERT OR REPLACE INTO Devices (account, name, rssi) VALUES ('depp_acc', 'depp', '-99');
            """
        # prepare the SQL statement
        keys = ["%s" % k for k in kwargs]
        values = ["'%s'" % v.replace("'","\"") for v in kwargs.values()]
        #print(kwargs.values())
        sql = list()
        sql.append("REPLACE INTO %s (" % table)
        sql.append(", ".join(keys))
        sql.append(") VALUES (")
        sql.append(", ".join(values))
        sql.append(");")
        sql = "".join(sql)
        #print(sql)

        #connection = sqlite3.connect(self.db_filename)
        # reuse old connection
        connection = self.connection
        if connection:
            with connection as conn:
                cur = conn.cursor()
                # sqlite in python is below 3.24 version which supports UPSERT
                # instead use INSERT OR REPLACE INTO
                cur.execute(sql)
                conn.commit()
                cur.close()
                # conn.close()
        else:
            print('update_db: Connection does not exist, do nothing')


    '''
        Beacons are stored in a queue - FILO, the queue is limited to
        queue_size rows.
        
        account        text,
        device_type     text default "None",
        bt_mac         text default "",
        name        text default "no name",
        rssi        text default "-100",
        uuid        text default "",
        beacon_type        text default "None",
        proximity        text default "0",
        beacon_gateway    text default "FFFFFFFFFF",
        time_stamp        text default "2020-04-01 00:00:01.100000",
        server_time_stamp    DATETIME DEFAULT CURRENT_TIMESTAMP
    '''
    def record_beacon_db(self, **kwargs):
        # bt_mac is our beacon key
        if kwargs.get("bt_mac"):
            bt_mac_key = kwargs.get("bt_mac")
        else:
            return False
        #print(kwargs)
        
        #connection = sqlite3.connect(self.db_filename)
        # reuse old connection
        connection = self.connection
        if connection:
            with connection as conn:
                '''
                       1. insert new row
                '''
                self.update_db(table="Beacons", **kwargs)
                '''
                       2. remove oldest rows
                '''
                sql = list()
               
                if self.sqlite:
                    sql.append("DELETE FROM Beacons WHERE ROWID IN (SELECT ROWID FROM Beacons WHERE bt_mac='%s' ORDER BY ROWID DESC LIMIT -1 OFFSET %s)" % (bt_mac_key, self.beacon_queue_size))
                    #sql.append("DELETE FROM Beacons WHERE server_time_stamp IN (SELECT server_time_stamp FROM Beacons GROUP BY `bt_mac` HAVING COUNT(`bt_mac`) > %s);" % self.beacon_queue_size)
                    sql = "".join(sql)
                    #print(sql)
                    
                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
                                   
                else:
                    # get old rows to be deleted
                    sql.append("SELECT * FROM (SELECT * FROM (SELECT server_time_stamp FROM beacons WHERE bt_mac='%s' order by server_time_stamp desc) as tobedeleted  LIMIT 10 offset %s) as b" % (bt_mac_key, self.beacon_queue_size))
                    sql = "".join(sql)
                    #print(sql)
                                        
                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
                                 
                    conditions = []
                    # convert to dict / compatible without factory Row
                    results = [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]
                    cur.close()
                    if results == []:
                        # nothing to delete, not enough old beacons yet
                        return True
                    
                    # we have too many beacons, delete old beacons
                    for result in results:
                        conditions += ["%s='%s'" % (k, v) for k,v in result.items()]
                    
                    # delete old rows
                    sql = list()
                    sql.append("DELETE FROM Beacons WHERE ")
                    sql.append(" OR ".join(conditions))
                    sql.append(";")
                    sql = "".join(sql)
                    #print(sql)
                    
                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
                    # conn.close()
        else:
            print('update_db: Connection does not exist, do nothing')
    

    def delete_db(self, table="Devices", **kwargs):
        # we take any given when condition
        if len(kwargs):
            # delete selected rows
            #print(kwargs)
            """ DELETE FROM Devices Where ??
             given the key-value pairs in kwargs
            """
            # prepare the SQL statement
            conditions = ["%s='%s'" % (k, v) for k,v in kwargs.items()]
            #print(conditions)
            sql = list()
            sql.append("DELETE ")
            sql.append("FROM %s WHERE " % table)
            sql.append(" OR ".join(conditions))
            sql.append(";")
            sql = "".join(sql)
        else:
            # delete all rows
            sql = list()
            sql.append("DELETE FROM Devices;")
            sql = "".join(sql)
                 
        #print(sql)
        #connection = sqlite3.connect(self.db_filename)
        # reuse old connection
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                #conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                # conn.close()
                return True
        else:
            print('delete_db: Connection does not exist, do nothing')
            return []

 
    def read_db(self, table="Devices", order_by=None, **kwargs):
        # account or bt_mac is our where key, or no where
        #print(kwargs)
        """ SELECT ?? FROM Devices
         given the key-value pairs in kwargs
        """
        # prepare the SQL statement
        keys = ['%s' % k for k in kwargs]
        #values = ["'%s'" % v for v in kwargs.values()]
        #print(kwargs)
        sql = list()
        sql.append("SELECT ")
        sql.append(", ".join(keys))
        if kwargs.get("account"):
            account_key = kwargs.get("account")
            sql.append(" FROM %s WHERE account=" % table)
            sql.append("'%s'" % str(account_key))
        else:
            if kwargs.get("bt_mac"):
                bt_mac_key = kwargs.get("bt_mac")
                sql.append(" FROM %s WHERE bt_mac=" % table)
                sql.append("'%s'" % str(bt_mac_key))
            else:
                sql.append(" FROM %s " % table)
        if order_by:
            sql.append(" ORDER BY %s" % order_by)
        sql.append(";")
        sql = "".join(sql)
        #print(sql)

        #connection = sqlite3.connect(self.db_filename)
        # reuse old connection
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                #conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                
                # convert to dict / compatible without factory Row
                result = [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]
                            
                cur.close()
                #print('Result:%s' % result)
                return result
        else:
            print('read_db: Connection does not exist, do nothing')
            return []

    def read_devices_db(self):
        """ SELECT * from Devices
        """
        sql = list()
        sql.append("SELECT * FROM Devices WHERE account!='';")
        sql = "".join(sql)
        #print(sql)

        #connection = sqlite3.connect(self.db_filename)
        # reuse old connection
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                #conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                
                # convert to dict / compatible without factory Row
                result = [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]
                #result = [dict(row) for row in cur.fetchall()]
                #print('Result:%s' % result)
                cur.close()

                return result
        else:
            print('read_db: Connection does not exist, do nothing')
            return []
              

    def update_devices_db(self, devices):
        for device in devices:
            self.update_db(
                            account     = device['account'],
                            device_type = device['device_type'],
                            bt_mac = device['bt_mac'],
                            name = device['name'],
                            rssi = device['rssi'],
                            uuid = device['uuid'],
                            beacon_type = device['beacon_type'],
                            proximity = device['proximity'],
                            beacon_gateway = device['beacon_gateway'],
                            user_image = device['user_image'],
                            device_loggedin = device['device_loggedin'],
                            base_location = device['base_location'],
                            base_connection = str(device['base_connection']),
                            time_stamp = device['time_stamp'],
                            tag_time_stamp = device['tag_time_stamp']
                            )
                            
        return True
            
    
    def is_empty_db(self):
        sql = list()
        sql.append("SELECT count(*) FROM (select 0 FROM Devices limit 1);")
        sql = "".join(sql)
        #print(sql)

        #connection = sqlite3.connect(self.db_filename)
        # reuse old connection
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                # conn.close()
            
                # convert to dict
                result = [dict(row) for row in cur.fetchall()]
                #print('Result is_empty_db:%s' % result)
                cur.close()

                return result[0]['count(*)'] == "1"
        else:
            print('is_empty_db: Connection does not exist, do nothing')
            return []


if __name__ == "__main__":
    #connect to ODBC datasource DNS
    msgDb = DECTMessagingDb(beacon_queue_size=3, odbc=True, initdb=False)

    msgDb.update_db(table="Beacons", account="test_beacon", beacon_gateway="FFFFF00000")
    result_dict = msgDb.read_devices_db()
    print("Exising devices:", result_dict )
    # fill up queue_size=3
    print("Adding Test devices, please wait approx 10s to exit")

    time.sleep(1.2)
    msgDb.record_beacon_db(account="test_beacon", bt_mac="123456789A", beacon_gateway="FFFFF00000")
    time.sleep(1.2)
    msgDb.record_beacon_db(account="test_beacon", bt_mac="123456789A", beacon_gateway="FFFFF00001")
    time.sleep(1.2)
    msgDb.record_beacon_db(account="test_beacon", bt_mac="123456789A", beacon_gateway="FFFFF00002")
    # add and reduce from 4 to 3 entries
    time.sleep(1.2)
    msgDb.record_beacon_db(account="test_beacon", bt_mac="123456789A", beacon_gateway="FFFFF00003")

    
    
