import requests
import json

# Your account details
account_id = "101-004-25172303-001"
access_token = "355e3f854bfe5cd14c1ae71e71cb723e-b1bdecc6d4a9ac5023b66104c9f48863"
instruments = 'SPX500_USD'

# Set up the streaming URL
domain = 'stream-fxpractice.oanda.com'
url = f'https://{domain}/v3/accounts/{account_id}/pricing/stream?instruments={instruments}'

def stream_prices():
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    params = {
        'instruments': instruments,
    }
    # Establishing a streaming connection
    with requests.get(f'https://{domain}/v3/accounts/{account_id}/pricing/stream', headers=headers, params=params, stream=True) as response:
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        # Processing each line of the response stream
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                data = json.loads(decoded_line)
                # Here you can process the price data
                print(data)

stream_prices()