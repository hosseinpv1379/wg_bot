import requests 

url = 'http://91.107.130.13:10086/api/addPeers/wg0'

# اضافه کردن هدر و API key
headers = {
    'Content-Type': 'application/json',
    'wg-dashboard-apikey': 'gsikmktr5LoeQD3KLgF1fkRHYIiQvEWGobuFS3tYuCI',  # API key خود را اینجا قرار دهید
    'Accept': 'application/json'
}

data = {
    "name": "Donald's Macbook Pro 123",
    "allowed_ips": [
        "10.0.0.100/32"
    ],
    "private_key": "IHYNm6VWb1kV/h4M6xthkgJYOpvGOKbpI24QC1Qt9mU=",
    "public_key": "fzjbAZOtJAQc8uyRBTjvPBTYuaW96bYEHC5TeFResRE=",
    "preshared_key": "Fwgw5H8xenVgyqOVr/rVEIy+vBi2nNiybjXiP45S5Rw=",
    "DNS": "1.1.1.1",
    "endpoint_allowed_ip": "0.0.0.0/0",
    "keepalive": 21,
    "mtu": 1420
}

# response = requests.post(url=url, headers=headers, json=data)

# print(response.status_code)
# print(response.text)


back = requests.get('http://91.107.130.13:10086/api/getWireguardConfigurationBackup?configurationName=wg0' , headers=headers)
print(back.status_code)
print(back.text)
