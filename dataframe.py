import json
import os
import pandas as pd

from redis_client import redis_client


STREAM_NAME = "market:ticks"


# Read latest 50 records from Redis Stream
messages = redis_client.xrevrange(
    STREAM_NAME,
    count=100
)


rows = []

for message_id, fields in messages:

    payload = json.loads(fields["payload"])

    rows.append({
        "symbol": payload["symbol"],
        "ltt": payload["ltt"],
        "received_at": payload["received_at"],
        "ltp": payload["ltp"],
        "volume": payload["volume"],
        "provider": payload["provider"]
    })


df = pd.DataFrame(rows)
#create a output DataFrame
os.makedirs("output", exist_ok=True) 

#create a separate DataFrame for each symbol and save it to a CSV file
for (symbol,provider), symbol_df in df.groupby(["symbol", "provider"]):
    
    symbol_df = symbol_df.sort_values("ltt")



    symbol_df = symbol_df[["symbol","ltt","received_at","ltp","volume", "provider"]]
    file_path = f"output/{symbol}_{provider}.csv"

    symbol_df.to_csv(
        file_path,
        index=False
    )

    print(f"Created: {file_path}")