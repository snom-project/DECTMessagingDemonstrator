-- Schema for devices logged in 
create table Devices (
    account		text,
    device_type 	text default "None",
    bt_mac 		text default "",
    name		text default "no name",
    rssi		text default "-100",
    uuid		text default "",
    beacon_type		text default "None",
    proximity		text default "0",
    beacon_gateway	text default "FFFFFFFFFF",
    user_image		text default "/images/Heidi_MacMoran_small.jpg",
    device_loggedin	text default "0",
    base_location	text default "None",
    base_connection	text default "('127.0.0.1', 4711)",
    time_stamp		text default "2020-04-01 00:00:01.100000",
    UNIQUE(account)
);

