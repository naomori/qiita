import os
import json

from qiita_v2.client import QiitaClient


params_file_path = 'item/params.json'
body_file_path = 'item/README.md'
item_id_file_path = 'item/ITEM_ID'

client = QiitaClient(access_token='dummy')

headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer {}'.format(os.environ['QIITA_TOKEN'])}

with open(params_file_path) as f:
    params = json.load(f)

with open(body_file_path) as f:
    params['body'] = f.read()

if os.path.exists(item_id_file_path):
    with open(item_id_file_path) as f:
        item_id = f.read()
    res = client.update_item(item_id, params, headers)
#    print(res.to_json())
else:
    res = client.create_item(params, headers)
#    print(res.to_json())
