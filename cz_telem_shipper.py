import sys
from math import ceil

import requests
from requests import HTTPError

def chunk_list(li, n):
    for i in range(0, len(li), n):
        yield li[i:i + n]

def ship_cz_telemetry(cz_api_key, stream_name, telemetry_events):
    print(f"Sending {len(telemetry_events)} events to CZ stream {stream_name} "
          f"via {max(ceil(len(telemetry_events) / 3000), 1)} transaction(s)")
    for chunk in chunk_list(telemetry_events, 3000):
        url = f"https://api.cloudzero.com/unit-cost/v1/telemetry/allocation/{stream_name}/replace"
        payload = {"records": chunk}
        headers = {
            "Authorization": cz_api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            print(".", end="", flush=True)
        except HTTPError as error:
            print(error)
            print(response.text)
            sys.exit(-1)
    print("Done!")