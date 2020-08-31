import sys
import logging

from lxml import etree as ET
import lxml.builder
from copy import deepcopy

import os
import sqlite3


class DECTMessagingDb:

    def __init__(self, logger=logging.getLogger('DECTMessagingDb')):
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        logger.addHandler(ch)
          
        self.logger = logger

        # DB
        self.db_filename = None
        self.schema_filename = None
        self.connection = None
        self.createDB()


    def createDB(self):
        self.db_filename = 'DB/DECTMessaging.db'
        self.schema_filename = 'DB/DECTMessagingSchema.sql'

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
#                conn.executescript("""
#                insert into Devices (account)
#                values ('test_db_account');
#                """)

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
    '''
    def update_db(self, **kwargs):        
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
        table = "Devices"
        keys = ["%s" % k for k in kwargs]
        values = ["'%s'" % v.replace("'","\"") for v in kwargs.values()]
        #print(kwargs.values())
        sql = list()
        sql.append("INSERT OR REPLACE INTO %s (" % table)
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



    def delete_db(self, **kwargs):
        # we take any given when condition
        if len(kwargs):
            # delete selected rows
            #print(kwargs)
            """ DELETE FROM Devices Where ??
             given the key-value pairs in kwargs
            """
            # prepare the SQL statement
            conditions = ["%s='%s'" % (k, v) for k,v in kwargs.items()]
            print(conditions)
            sql = list()
            sql.append("DELETE ")
            sql.append("FROM Devices WHERE ")
            sql.append(" OR ".join(conditions))
            sql.append(";")
            sql = "".join(sql)
        else:
            # delete all rows
            sql = list()
            sql.append("DELETE FROM Devices;")
            sql = "".join(sql)
                 
        print(sql)
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
                #print('Result:%s' % result)
                cur.close()

                return result
        else:
            print('read_db: Connection does not exist, do nothing')
            return []

 
    def read_db(self, **kwargs):
        # account is our key to find the data
        if kwargs.get("account"):
            account_key = kwargs.get("account")
        else:
            return False
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
        sql.append(" FROM Devices WHERE account=")
        sql.append("'%s'" % str(account_key))
        sql.append(";")
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
                cur.close()
                #print('Result:%s' % result)
                return result
        else:
            print('read_db: Connection does not exist, do nothing')
            return []

    def read_devices_db(self):
       
        """ SELECT * from Devices
         given the key-value pairs in kwargs
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
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                # conn.close()
                
                # convert to dict
                result = [dict(row) for row in cur.fetchall()]
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
                            time_stamp = device['time_stamp']
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
      
