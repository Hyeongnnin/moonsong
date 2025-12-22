import requests, sys
url = sys.argv[1]
token = sys.argv[2]
res = requests.get(url, headers={'Authorization': f'Bearer {token}'})
print('STATUS', res.status_code)
print(res.text)
