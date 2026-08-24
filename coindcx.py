import socketio
import json
import sys

from redis_client import redis_client
from datetime import datetime
from zoneinfo import ZoneInfo
sio = socketio.Client()

SOCKET_URL = "wss://stream-spot.coindcx.com"
# CHANNEL = "B-BTC_USDT@trades"
symbols = sys.argv[1:]
print("Selected symbols: ", symbols)

channels = [
    f"B-{symbol}_USDT@trades"
    for symbol in symbols
]
@sio.event
def connect(): #when socket io connect automatic run the function so connect is event handler
    print("Connected to CoinDCX")

    for channel in channels:
        sio.emit(
                "join",
                {
                    "channelName": channel
                }
            ) #sent the event message
        print("Subscribed: " , channel) #"CoinDCX,  want to join/subscribe to this channel."   
    
    
    
    

@sio.event
def disconnect():
    print("Disconnected from CoinDCX")

@sio.on("new-trade") #whenever coindcx sends me and event name new trade , run on-trade
def on_trade(response): #response contains the data that CoinDCX sends you.
    data = json.loads(response["data"]) #convert string to json object
    ist_time = datetime.fromtimestamp(
        data["T"]/1000,
        tz= ZoneInfo("Asia/Kolkata")
    )
    payload = {
        "symbol": data["s"],
        "ltt": ist_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " IST",
        "ltp": float(data["p"]),
        "volume": float(data["q"]),
        "provider": "CoinDCX"
    }
    # print(payload)

    #send payload to Redis
    redis_client.publish(
        "market_data", #redis channel name
        json.dumps(payload) #conver pyton into json string
    )
    print("Published: ", payload)

sio.connect( #actually connection make python connects to socket io server
    SOCKET_URL,
    transports = ["websocket"] #use websocket as trasports
)

sio.wait()#wait for incoming event