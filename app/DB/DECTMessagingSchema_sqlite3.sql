create table Devices (
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
);

create table Beacons  (
    account		VARCHAR(255),
    device_type 	VARCHAR(255) default "None",
    bt_mac 		VARCHAR(255) default "",
    name		VARCHAR(255) default "no name",
    rssi		VARCHAR(255) default "-100",
    uuid		VARCHAR(255) default "",
    beacon_type		VARCHAR(255) default "None",
    proximity		VARCHAR(255) default "0",
    beacon_gateway    VARCHAR(255) default "FFFFFFFFFF",
    beacon_gateway_name    VARCHAR(255) default "",
    time_stamp		VARCHAR(255) default "2020-04-01 00:00:01.100000",
    server_time_stamp	TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

create table m9bIPEI (
    beacon_gateway_IPEI    VARCHAR(255) default "FFFFFFFFFF",
    beacon_gateway_name    VARCHAR(255) default "",
    UNIQUE(beacon_gateway_IPEI)
);

create table m9bdevicestatus (
    account        VARCHAR(255),
    bt_mac      VARCHAR(255) default "",
    rssi        VARCHAR(255) default "-100",
    uuid        VARCHAR(255) default "",
    beacon_type      VARCHAR(255) default "None",
    proximity        VARCHAR(255) default "0",
    beacon_gateway_IPEI    VARCHAR(255) default "FFFFFFFFFF",
    beacon_gateway_name    VARCHAR(255) default "",
    time_stamp        VARCHAR(255) default "2020-04-01 00:00:01.100000",
    server_time_stamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(beacon_gateway_IPEI, bt_mac, account)
);

create table Alarms (
    account                 VARCHAR(255),
    name		            VARCHAR(255) default "no name",
    externalid              VARCHAR(255) default "0000000000",
    alarm_type              VARCHAR(255) default "None",
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
);
