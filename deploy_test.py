from qiita_v2.client import QiitaClient

config_file = "config.yaml"
user_name = "<user_name>"
client = QiitaClient(config_file=config_file)
response = client.get_user(user_name)
print(response.to_json())
