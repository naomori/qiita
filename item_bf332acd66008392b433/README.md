# Qiitaの記事をGitHubで管理してTravisCI経由で自動投稿する(Python)

Qiita に記事を投稿したいと思っていましたが、記事を書くのは面倒くさい上に手元に好きなエディタも使えないしなぁと感じていたところ、以下の記事を見つけました。

- [Qiitaの記事をGitHubで管理してTravisCI経由で自動投稿する][]

GitHubへのpushと同時に自動で出来たらこんな素晴らしいことはないなと思ったので、丸パクリしたいと思いました。ただ、丸パクリしても全然自分のためにはならないので、Rubyで実現されていたものをPythonに変更することにしました。

## Qiita個人用アクセストークン取得

[Qiita-設定-アプリケーション][]で個人用アクセストークンを新しく発行します。
以下のスコープにチェックを入れて、発行します。

- read_qiita
- write_qiita

表示されたアクセストークンは二度と表示されないので、コピーします。

## Qiita APIv2 ライブラリ

[Qiita API v2のPythonラッパー実装した][]の通りに、`qiita_v2`をインストールします。

ライブラリの動作確認を行います。
`config.yaml`ファイルに`ACCESS_TOKEN`として、トークンを記述しておきます。

```python:deploy_test.py
from qiita_v2.client import QiitaClient

config_file = "config.yaml"
user_name = "hogehoge"
client = QiitaClient(config_file=config_file)
response = client.get_user(user_name)
print(response.to_json())
```

実行してみます。

```python
$ python deploy_test.py
/home/<user_name>/github/qiita/venv/lib/python3.7/site-packages/qiita_v2/client_base.py:36: YAMLLoadWarning: calling yaml.load() without Loader=... is deprecated, as the default Loader is unsafe. Please read https://msg.pyyaml.org/load for full details.
  config = yaml.load(f)
```

すると、何か Warning が出力されていて煩いので、[ここ](https://github.com/bioconda/bioconda-utils/issues/462)を参考に修正します。

```diff
@@ -33,7 +33,7 @@
         self.team = team
         if config_file:
             with open(config_file, 'r') as f:
-                config = yaml.load(f)
+                config = yaml.safe_load(f)
                 if 'ACCESS_TOKEN' in config:
                     self.access_token = config['ACCESS_TOKEN']
                 if 'TEAM' in config:
```

## Qiita投稿用スクリプトを作成

投稿用のスクリプトを作成します。
`QiitaClient`にアクセストークンを渡す方法でやってみたのですが、`Unauthorized`と言われてしまうので、ヘッダにトークンを追加するようにしてみました。

```python:deploy.py
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
    print(res.to_json())
else:
    res = client.create_item(params, headers)
    print(res.to_json())
```

## タイトル・タグ

タイトルやタグは、`item/params.json`で定義します。

```json
{
  "title": "Qiitaの記事をGitHubで管理してTravisCI経由で自動投稿する(Python)",
  "tags": [
    {
      "name": "Github",
      "versions": []
    },
    {
      "name": "TravisCI",
      "versions": []
    }
  ],
  "coediting": false,
  "gist": false,
  "private": false,
  "tweet": false
}
```

`item/ITEM_ID`に更新したい記事のIDを保存すると、そのIDの記事を更新するようになります。 `item/ITEM_ID`ファイルがなければ、新たに記事を作成します。

## Qiitaアクセストークン

Qiitaのアクセストークンについては、環境変数として`QIITA_TOKEN`に設定します。

```bash
$ export QIITA_TOKEN=<access_token>
```

## お試し投稿

これで投稿できるようになったので、手元から直接Qiitaに投稿してみます。

```bash
$ python deploy.py
```

Qiitaを覗いてみると、きちんと投稿できてました。


## いよいよ、TravisCI経由で自動投稿します

travis CLI が使いたいので、インストールしておきます。

```bash
$ gem install travis
```

## travis login

何回やってみても失敗してたけど、Travis CIにログインして設定周りを見ていたりして、再度試してみたら、ログイン出来た...理由は分かりません...

```zsh
$ travis login
We need your GitHub login to identify you.
This information will not be sent to Travis CI, only to api.github.com.
The password will not be displayed.

Try running with --github-token or --auto if you don't want to enter your password anyway.

Username: <user_name>
Password for <user_name>: ********
Successfully logged in as <user_name>!
```

## travis init

またまた、何回か失敗していたりしていましたが、`travis-ci.org`に行ってみたら、登録したはずのGithubのレポジトリがなかったりしたので、Githubリポジトリを再度登録して、再度`travis init`してみたらOKでした。理由は分かりません...

```bash
(venv) ~$ travis init
Main programming language used: |Ruby| Python
.travis.yml file created!
<user_name>/qiita: enabled :)
```

これで、`.travis.yml`が初期作成されます。

## アクセストークンの暗号化

Qiitaのアクセストークンは暗号化して、`.travis.yml`に追加します。

```bash
$ travis encrypt QIITA_TOEKN=<access_token> --add
Overwrite the config file /home/<user_name>/github/qiita/.travis.yml with the content below?

This reformats the existing file.

---
language: python
python:
- '2.7'
- '3.3'
- pypy
env:
  global:
      secure: <secure-key>
(y/N)
y
```

## デプロイスクリプトの有効化

`.travis.yml`を以下のように描きます。

- masterブランチ以外のコミットでは動かない
- ライブラリのインストールを記述

```yaml
language: python
python:
- '3.7'
branches:
  only:
  - master
install:
- pip install -r requirements_travis.txt
script:
- 'if [ "$TRAVIS_PULL_REQUEST" = "false" ]; then python deploy.py; fi'
env:
  global:
    secure: XXX
```

ライブラリは以下のようにして出力しておきます。

```bash
$ pip freeze > requirements_travis.txt
```

# 運用方法

さて、最後に、このレポジトリの運用方法についてですが、スクリプトはこのリポジトリの`item`ディレクトリに含まれる`README.md`を記事として投稿します。そして、その記事のタイトルなどは、`params.json`に設定します。
つまり、新しい記事は常に`item`ディレクトリに配置しておく必要があります。
そこで、以下のように運用していきたいと思います。

## 注意事項: 記事に画像を入れるとき

Qiitaでは、画像はAmazon S3に格納しているようです。
したがって、QiitaのWeb編集インターフェイスで、
画像だけはドラッグ＆ドロップでその記事上に置いた上で、
そのリンクアドレスを記事にも反映します(面倒ですね...)。

## 新しい記事を作成するとき

1. `item_XXX`(XXXは文字通り'XXX'という文字列)ディレクトリを作成する
2. そのディレクトリの配下に`README.md`,`params.json`を作成する
3. `item`から`item_XXX`にシンボリックリンクを貼る
4. git で commit & push する
5. 記事の作成が成功したら、その記事の`ITEM_ID`(URLに含まれている文字列)をコピーする
6. `item_XXX`を`item_$ITEM_ID`に変更し、そのディレクトリの中に`ITEM_ID`というファイルを作成する
    - `ITEM_ID`ファイル中の改行は削除しないと駄目みたいです(面倒です...)。
    - `tr -d '\n' < ITEM_ID > ITEM_ID.bak`
    - `mv ITEM_ID.bak ITEM_ID`
7. git で commit & push する

## 既存の記事を更新するとき

1. シンボリックリンク`item`から更新したい記事のディレクトリにリンクを貼る
2. 記事を更新する
3. git で commit & push する
4. シンボリックリンク`item`を削除する

[Qiitaの記事をGitHubで管理してTravisCI経由で自動投稿する]: https://qiita.com/rednes/items/2d76435434ac632fc6d4
[Qiita-設定-アプリケーション]: https://qiita.com/settings/applications
[Qiita API v2のPythonラッパー実装した]: https://qiita.com/petitviolet/items/deda7b66852635264508
