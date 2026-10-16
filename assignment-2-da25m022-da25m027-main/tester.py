import requests

url = 'http://10.60.114.94:5290/'

translate_url = url + 'translate'

headers = {'Content-Type': 'application/json'}
data = {}

container_id_count = {}

for _ in range(100):
    response = requests.get(url=url)

    c_id = response.json()['container_id']
    if c_id not in container_id_count.keys():
        container_id_count[c_id] = 1
    else:
        container_id_count[c_id] += 1

    response_trans = requests.post(url=translate_url, json=data, headers=headers)

    print((response.json()))
    print((response_trans.json()))

print(container_id_count)
