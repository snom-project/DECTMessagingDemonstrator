# %%
from DB.DECTMessagingDb import DECTMessagingDb

# DB reuse and type
ODBC=False
INITDB=False
msgDb = DECTMessagingDb(beacon_queue_size=3, odbc=ODBC, initdb=INITDB)


def f2(*args, **kwargs):
    result = msgDb.read_gateway_db(**kwargs)
    #print("executed",*args, **kwargs)
    return result

def f(*args, **kwargs):
    beacon_gateway = '0328D7848C'
    result = f2(beacon_gateway_IPEI=beacon_gateway, beacon_gateway_name='')
    print(result)

f(a=1, b=2)

# %%
