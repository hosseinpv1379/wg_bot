import requests 

url = 'http://91.107.130.13:8443/api/get-peers'

# اضافه کردن هدر و API key
headers = {
    "X-API-Key": "default_api_key_for_development"  # کلید API را اینجا قرار دهید
}

name = 'hossein'
param = {'peer_name' : name ,"config_name" : 'wg0' }


response = requests.get(url= url , headers=headers , params=param)

print(response.status_code)
print(response.json())
