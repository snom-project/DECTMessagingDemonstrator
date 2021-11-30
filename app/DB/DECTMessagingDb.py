import logging

import os
import sqlite3
import time
import pyodbc

class DECTMessagingDb:

    def __init__(self, beacon_queue_size=3, alarm_queue_size=5, odbc=False, initdb=True, logger=logging.getLogger('DECTMessagingDb')):
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
        self.alarm_queue_size = alarm_queue_size

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

        self.logger.debug('Trying ODBC Connect')
        #cnxn = pyodbc.connect("DRIVER={SQLite 3};Direct=True;Database=%s" % self.db_filename)

        # only connect or new DB
        if not self.initdb:
            cnxn.execute("""
                            USE DECTmessaging;
                         """)

            return True

        directory = 'DB'

        for _root, _dirs, files in os.walk(directory):
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

        # try WAL modes, multiple read accesses granted
        #conn = sqlite3.connect(self.db_filename)
        conn = sqlite3.connect(self.db_filename, isolation_level=None)
        conn.execute('pragma journal_mode=wal;')

        # remember the connection to reuse
        self.connection = conn

        if db_is_new:
            self.logger.info('Creating schema')
            with open(self.schema_filename, 'rt') as f:
                schema = f.read()
                conn.executescript(schema)

                self.logger.debug('Inserting initial data')
                conn.executescript("""
                insert into Beacons (account)
                values ('test_db_account');
                """)

        else:
            self.logger.info('Database exists, assume schema does, too.')
        # keep the connection
        #conn.close()


    '''
        uses Device table by default. 
        account		VARCHAR(255),
        device_type 	VARCHAR(255) default "None",
        bt_mac 		VARCHAR(255) default "",
        name		VARCHAR(255) default "no name",
        rssi		VARCHAR(255) default "-100",
        uuid		VARCHAR(255) default "",
        beacon_type		VARCHAR(255) default "None",
        proximity		VARCHAR(255) default "0",
        beacon_gateway	VARCHAR(255) default "FFFFFFFFFF",
        beacon_gateway_name    VARCHAR(255) default "",
        user_image		VARCHAR(255) default "/images/Heidi_MacMoran_small.jpg",
        device_loggedin	VARCHAR(255) default "0",
        base_location	VARCHAR(255) default "None",
        base_connection	VARCHAR(255) default "('127.0.0.1', 4711)",
        time_stamp		VARCHAR(255) default "2020-04-01 00:00:01.100000",
        tag_time_stamp	VARCHAR(255) default "2020-04-01 00:00:01.100000",
        UNIQUE(account)
    '''
    def update_db(self, table="Devices", **kwargs):
        # update nullifies all values not given in key kwargs!
        # account is our key to find the data
        if kwargs.get("account"):
            _account_key = kwargs.get("account")
        else:
            return False
        #print(kwargs)

        """ update/insert ALL rows into objects table (update if the row already exists)
            given the key-value pairs in kwargs
            INSERT OR REPLACE INTO Devices (account, name, rssi) VALUES ('depp_acc', 'depp', '-99');
            Note: all other column values will be nullified
        """
        # prepare the SQL statement
        keys = ["%s" % k for k in kwargs]
        # temporary extra test on forgotten fields.
        if len(keys) != 16 and table == "Devices":
            self.logger.error('update_db: not all columns specified, remaining column-values will be nullified! keys=%s', ",".join(keys))

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
            self.logger.error('update_db: Connection does not exist, do nothing')


    def update_with_key_db(self, table="Devices", **kwargs):
        # update nullifies all values not given in key kwargs!
        # account is our key to find the data
        if kwargs.get("account"):
            _account_key = kwargs.get("account")
        else:
            return False
        #print(kwargs)

        # prepare the SQL statement
        keys = ["%s" % k for k in kwargs]
        
        values = ["'%s'" % v.replace("'","\"") for v in kwargs.values()]
        #print(kwargs.values())
        sql = list()

        sql.append("UPDATE %s SET " % table)
        set_list = ["%s = %s" % (a,b) for a, b in zip(keys, values)]
        sql.append(", ".join(set_list))
        sql.append(" WHERE ")
        sql.append("account = '%s'" % _account_key)
        sql.append(";")
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
            self.logger.error('update_with_key_db: Connection does not exist, do nothing')


    '''
        Alarms are stored in a queue - FILO, the queue is limited to
        alarms_queue_size rows.

    account                 VARCHAR(255),
    name		            VARCHAR(255) default "no name",
    externalid              VARCHAR(255) default "0000000000",
    alarm_type              SMALLINT default 0,
    beacon_type             VARCHAR(255) default "None",
    beacon_broadcastdata    VARCHAR(255) default "00000000000000000000000000000000000000000",
    beacon_bdaddr           VARCHAR(12) default "000000000000",
    rfpi_s                  VARCHAR(10) default "FFFFFFFFFF",
    rssi_s                  VARCHAR(255) default "-100",
    rfpi_m                  VARCHAR(10) default "FFFFFFFFFF",
    rssi_m                  VARCHAR(255) default "-100",
    rfpi_w                  VARCHAR(10) default "FFFFFFFFFF",
    rssi_w                  VARCHAR(255) default "-100",
    time_stamp              VARCHAR(255) default "2020-04-01 00:00:01.100000",
    server_time_stamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    '''
    def record_alarm_db(self, **kwargs):
        # account is our alarm key, bt_mac is only exisintg when BTLE is enabled on the device
        if kwargs.get("account"):
            account_key = kwargs.get("account")
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
                self.update_db(table="Alarms", **kwargs)
                '''
                       2. remove oldest rows
                '''
                sql = list()

                if self.sqlite:
                    sql.append("DELETE FROM Alarms WHERE ROWID IN (SELECT ROWID FROM Alarms WHERE account='%s' ORDER BY ROWID DESC LIMIT -1 OFFSET %s)" % (account_key, self.alarm_queue_size))
                    sql = "".join(sql)
                    #print(sql)

                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
                    cur.close()

                else:
                    # get old rows to be deleted
                    sql.append("SELECT * FROM (SELECT * FROM (SELECT server_time_stamp FROM Alarms WHERE account='%s' order by server_time_stamp desc) as tobedeleted  LIMIT 10 offset %s) as b" % (account_key, self.alarm_queue_size))
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
                    sql.append("DELETE FROM Alarms WHERE ")
                    sql.append(" OR ".join(conditions))
                    sql.append(";")
                    sql = "".join(sql)
                    #print(sql)

                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
                    cur.close()
                    # conn.close()

                return True
        else:
            self.logger.error('record_alarm_db: Connection does not exist, do nothing')


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
        beacon_gateway_name    text default "",
        time_stamp        text default "2020-04-01 00:00:01.100000",
        server_time_stamp    DATETIME DEFAULT CURRENT_TIMESTAMP
    '''
    def record_beacon_db(self, **kwargs):
        # bt_mac is our beacon key
        if kwargs.get("bt_mac"):
            bt_mac_key = kwargs.get("bt_mac")
        else:
            return False
        if kwargs.get("beacon_gateway"):
            beacon_gateway_key = kwargs.get("beacon_gateway")
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
                # add beacon_gateway_name when existing
                cur = conn.cursor()
                cur = conn.execute("UPDATE Beacons SET beacon_gateway_name=(SELECT beacon_gateway_name FROM m9bIPEI WHERE beacon_gateway_IPEI=Beacons.beacon_gateway) WHERE EXISTS (SELECT * FROM m9bIPEI WHERE beacon_gateway_IPEI=Beacons.beacon_gateway);")
                conn.commit()
                cur.close()
                '''
                       2. remove oldest rows
                '''
                sql = list()

                if self.sqlite:
                    sql.append("DELETE FROM Beacons WHERE ROWID IN (SELECT ROWID FROM Beacons WHERE bt_mac='%s' AND beacon_gateway='%s' ORDER BY ROWID DESC LIMIT -1 OFFSET %s)" % (bt_mac_key, beacon_gateway_key, self.beacon_queue_size))
                    sql = "".join(sql)
                    #print(sql)

                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
                    cur.close()

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
                    cur.close()
                    # conn.close()

                return True
        else:
            self.logger.error('record_beacon_db: Connection does not exist, do nothing')

    '''
        M9B manages several devices and reports their proximity
        This table records the actual proximity per m9b and device

        bt_mac         text default "",
        rssi        text default "-100",
        uuid        text default "",
        beacon_type        text default "None",
        proximity        text default "0",
        beacon_gateway    text default "FFFFFFFFFF",
        beacon_gateway_name    text default "",
        time_stamp        text default "2020-04-01 00:00:01.100000",
        server_time_stamp    DATETIME DEFAULT CURRENT_TIMESTAMP
    '''
    def record_m9b_device_status_db(self, **kwargs):
        # bt_mac is our beacon key
        if kwargs.get("bt_mac"):
            _bt_mac_key = kwargs.get("bt_mac")
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
                self.update_db(table="m9bdevicestatus", **kwargs)
                # add beacon_gateway_name when existing
                cur = conn.cursor()
                cur.execute("UPDATE m9bdevicestatus SET beacon_gateway_name=(SELECT beacon_gateway_name FROM m9bIPEI WHERE beacon_gateway_IPEI=m9bdevicestatus.beacon_gateway_IPEI) WHERE EXISTS (SELECT * FROM m9bIPEI WHERE beacon_gateway_IPEI=m9bdevicestatus.beacon_gateway_IPEI);")
                conn.commit()
                cur.close()
                return True
        else:
            self.logger.error('record_m9b_device_status_db: Connection does not exist, do nothing')


    def update_m9b_tag_status_db(self, bt_mac, proximity):
        # bt_mac is our beacon key     
        #connection = sqlite3.connect(self.db_filename)
        # reuse old connection
        connection = self.connection
        if connection:
            with connection as conn:
                # update all gateways holding TAG bt_mac
                cur = conn.cursor()
                cur.execute("UPDATE m9bdevicestatus SET proximity='%s' WHERE bt_mac='%s';" % (proximity, bt_mac))
                conn.commit()
                cur.close()
                return True
        else:
            self.logger.error('update_m9b_tag_status_db: Connection does not exist, do nothing')


    def clear_old_m9b_tag_status_db(self, bt_mac, target_timestamp):
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                #conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                '''   mysql
                "DELETE FROM m9bdevicestatus WHERE time_stamp  < STR_TO_DATE({},'%Y-%m-%d %H:%M:%S.%f') ".format(target_timestamp))
                '''
                cur.execute("DELETE FROM m9bdevicestatus where bt_mac = '{}' AND strftime('%s', time_stamp) < strftime('%s', '{}')".format(bt_mac, target_timestamp))
                conn.commit()
                cur.close()
                # conn.close()
                return True
        else:
            self.logger.error('clear_old_m9b_device_status_db: Connection does not exist, do nothing')
            return []


    def clear_old_m9b_device_status_db(self, _timeout, target_timestamp):
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                #conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                '''   mysql
                "DELETE FROM m9bdevicestatus WHERE time_stamp  < STR_TO_DATE({},'%Y-%m-%d %H:%M:%S.%f') ".format(target_timestamp))
                '''
                cur.execute("DELETE FROM m9bdevicestatus where strftime('%s', time_stamp) < strftime('%s', '{}')".format(target_timestamp))
                conn.commit()
                cur.close()
                # conn.close()
                return True
        else:
            self.logger.error('clear_old_m9b_device_status_db: Connection does not exist, do nothing')
            return []


    def read_m9b_device_status_db(self):
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                #conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                '''   mysql

                '''
                cur.execute("SELECT account, bt_mac, rssi, uuid, beacon_type, proximity, beacon_gateway_IPEI, beacon_gateway_name, time_stamp, server_time_stamp, strftime('%s', datetime('now','localtime'))  - strftime('%s', time_stamp) AS timeout FROM m9bdevicestatus ORDER BY bt_mac DESC")

                # convert to dict / compatible without factory Row
                result = [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]

                cur.close()
                # conn.close()
                return result
        else:
            self.logger.error('read_m9b_device_status_db: Connection does not exist, do nothing')
            return []


    def read_m9b_device_status_2_db(self):
        """Function returns Devices.account, Devices.base_connection to re-use to send SMS or alarms to the right base and status information, like
        m9bdevicestatus.bt_mac, m9bdevicestatus.rssi, m9bdevicestatus.proximity,
        m9bdevicestatus.beacon_gateway_IPEI, m9bdevicestatus.beacon_gateway_name.
        Filters only proximity != '0'

        Returns:
            [List of dict]: DB result composed
        """
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                #conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                '''   mysql

                '''
                cur.execute("SELECT m9bIPEI.max_allowed_devices, Devices.account, Devices.base_connection, m9bdevicestatus.bt_mac, m9bdevicestatus.rssi, m9bdevicestatus.proximity, m9bdevicestatus.beacon_gateway_IPEI, m9bdevicestatus.beacon_gateway_name FROM m9bdevicestatus INNER JOIN Devices on Devices.bt_mac = m9bdevicestatus.bt_mac INNER JOIN m9bIPEI on m9bdevicestatus.beacon_gateway_IPEI = m9bIPEI.beacon_gateway_IPEI WHERE m9bdevicestatus.proximity != '0'")
                # convert to dict / compatible without factory Row
                result = [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]

                cur.close()
                # conn.close()
                return result
        else:
            self.logger.error('read_m9b_device_status_db_2: Connection does not exist, do nothing')
            return []


    def read_m9b_device_status_3_db(self):
        """Function returns Devices.account, Devices.base_connection to re-use to send SMS or alarms to the right base and status information, like
        m9bdevicestatus.bt_mac, m9bdevicestatus.rssi, m9bdevicestatus.proximity,
        m9bdevicestatus.beacon_gateway_IPEI, m9bdevicestatus.beacon_gateway_name.

        Returns:
            [List of dict]: DB result composed
        """
        connection = self.connection
        if connection:
            with connection as conn:
                # format needed to convert to dict
                #conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                '''   mysql

                '''
                cur.execute("SELECT m9bIPEI.max_allowed_devices, Devices.account, Devices.base_connection, m9bdevicestatus.bt_mac, m9bdevicestatus.rssi, m9bdevicestatus.proximity, m9bdevicestatus.beacon_gateway_IPEI, m9bdevicestatus.beacon_gateway_name FROM m9bdevicestatus INNER JOIN Devices on Devices.bt_mac = m9bdevicestatus.bt_mac INNER JOIN m9bIPEI on m9bdevicestatus.beacon_gateway_IPEI = m9bIPEI.beacon_gateway_IPEI WHERE m9bdevicestatus.proximity != 'a0'")
                # convert to dict / compatible without factory Row
                result = [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]

                cur.close()
                # conn.close()
                return result
        else:
            self.logger.error('read_m9b_device_status_db_3: Connection does not exist, do nothing')
            return []


    def record_gateway_db(self, table="m9bIPEI", **kwargs):
        if kwargs.get("beacon_gateway_IPEI"):
            _ipei = kwargs.get("beacon_gateway_IPEI")
        else:
            return False

        # prepare the SQL statement
        keys = ["%s" % k for k in kwargs]
        values = ["'%s'" % v.replace("'","\"") for v in kwargs.values()]
        #print(kwargs.values())
        sql = list()
        sql.append("INSERT OR IGNORE INTO %s (" % table)
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
            self.logger.error('record_gateway_db: Connection does not exist, do nothing')


    def read_gateway_db(self, table="m9bIPEI", order_by=None, **kwargs):
        """ SELECT ?? FROM m9bIPEI
         given the key-value pairs in kwargs
        """
        # prepare the SQL statement
        keys = ['%s' % k for k in kwargs]
        #values = ["'%s'" % v for v in kwargs.values()]
        #print(kwargs)
        sql = list()
        sql.append("SELECT ")
        sql.append(", ".join(keys))
        if kwargs.get("beacon_gateway_IPEI"):
            account_key = kwargs.get("beacon_gateway_IPEI")
            sql.append(" FROM %s WHERE beacon_gateway_IPEI=" % table)
            sql.append("'%s'" % str(account_key))
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
            self.logger.error('read_gateway_db: Connection does not exist, do nothing')
            return []


    def delete_db(self, table="Devices", **kwargs):
        # we take any given when condition
        if len(kwargs) > 0:
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
            #print(sql)
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
                cur.close()
                # conn.close()
                return True
        else:
            self.logger.error('delete_db: Connection does not exist, do nothing')
            return []


    def read_db(self, table="Devices", order_by=None, group_by=None, **kwargs):
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
        if group_by:
            sql.append(" group BY %s" % group_by)
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
            self.logger.error('read_db: Connection does not exist, do nothing')
            return []


    # returns max 5 newest locations with proximity > 0
    def read_last_locations_db(self, table="Devices", order_by=None, group_by=None, **kwargs):
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
                #sql.append(" AND proximity<>'0' ")
            else:
                sql.append(" FROM %s " % table)

        if group_by:
            sql.append(" group BY %s" % group_by)
        if order_by:
            sql.append(" ORDER BY %s " % order_by)
        sql.append(" LIMIT 5")
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
            self.logger.error('read_last_locations_db: Connection does not exist, do nothing')
            return []


    def read_devices_db(self):
        """ SELECT * from Devices
        """
        sql = list()
        sql.append("SELECT * FROM Devices WHERE account!='' ORDER BY device_type DESC, account ASC;")
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
            self.logger.error('read_devices_db: Connection does not exist, do nothing')
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
                            beacon_gateway_name = device['beacon_gateway_name'],
                            user_image = device['user_image'],
                            device_loggedin = device['device_loggedin'],
                            base_location = device['base_location'],
                            base_connection = str(device['base_connection']),
                            time_stamp = device['time_stamp'],
                            tag_time_stamp = device['tag_time_stamp']
                            )

        return True


    def update_single_device_db(self, device):
        if device:
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
                            beacon_gateway_name = device['beacon_gateway_name'],
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
            self.logger.error('is_empty_db: Connection does not exist, do nothing')
            return []


if __name__ == "__main__":
    #connect to ODBC datasource DNS
    msgDb = DECTMessagingDb(beacon_queue_size=15, odbc=False, initdb=False)
    # update nullifies all other values not explicitly given!
    msgDb.update_db(table="Beacons", account="test_beacon", beacon_gateway="FFFFF00000")
    # this one updates selected fields in an existing record with account as key 
    msgDb.update_with_key_db(table="Beacons", account="test_beacon", name="Test Beacon", rssi="-44")
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
