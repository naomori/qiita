# はじめに

[Kubernetes][]ってなんか面白そう。よく分からんけど。

と、ふと思ったので調べてみることにしました。
ですが、雑誌やWebの記事などを読んでも、よく分かりませんでした。
というわけで実際に手を動かして学んでみることにしました。

実際に手を動かそうと思ったのですが、自宅にPCが何台も持っていません。
ただ、なぜか放置された[Raspberry Pi 3 Model B][]が4台も転がっていたので、
これを使って[Kubernetes][]の環境を構築しようと思い立ちました。

# 参考記事

多くの方々がすでに取り組まれている話題のようで、
以下の記事がとても参考になり、ほぼパクリしました。

* [3日間クッキング【Kubernetes のラズペリーパイ包み　“サイバーエージェント風”】][]
* [Raspberry PiでおうちKubernetes構築【物理編】][]
* [Raspberry Pi 3 Model B][]

ただ、[Raspberry Pi 3 Model B][] x 4 で環境構築しようとしているので、
そこが少しだけ違う点です。

# 材料

参考記事の方々は[Raspberry Pi 3 Model B][] x 3 で構築していて、
スタッカブルケースは1台でコンパクトに仕上げています。

ですが、私は、[Raspberry Pi 3 Model B][] x 4 で構築しようとしているので、
[Raspberry Pi 3 Model B][]用とネットワーク+USB用の2台のスタッカブルケースで構築します。

![k8s-ingredients.jpeg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/59651651-863b-2236-c377-d4567bccacb2.jpeg)

* [エレコム LANケーブル 0.15m 爪折れ防止コネクタ やわらか CAT6準拠 ブルー LD-GPY/BU015](https://www.amazon.co.jp/gp/product/B00G2PY0NU/ref=ppx_yo_dt_b_asin_title_o07_s00?ie=UTF8&psc=1) x 1
* [エレコム LANケーブル 0.3m 爪折れ防止コネクタ やわらか CAT6準拠 ブルー LD-GPY/BU03](https://www.amazon.co.jp/gp/product/B00G2PY0VW/ref=ppx_yo_dt_b_asin_title_o07_s00?ie=UTF8&psc=1) x 4
* [BUFFALO 無線LAN親機 11ac/n/a/g/b 433/150Mbps トラベルルーター ブラック WMR-433W2-BK](https://www.amazon.co.jp/gp/product/B07R2CKQXC/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) x 1
* [ロジテック スイッチングハブ 5ポート 10/100Mbps AC電源 小型 LAN-SW05PSBE](https://www.amazon.co.jp/gp/product/B00D5Q7URW/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) x 1
* [Micro USBケーブル 短い CABEPOW【30cm3本 / 2.4A急速充電 / 高速データ転送】Android 充電 高耐久ナイロン編組み マイクロusbケーブル Huawei/Galaxy/Sony/Xperia/Nexus/Moto/Kindle / PS4などアンドロイド 充電対応（30cm3本 赤）](https://www.amazon.co.jp/gp/product/B07K3WGLV7/ref=ppx_yo_dt_b_asin_title_o00_s01?ie=UTF8&psc=1) x 2
* [両面テープ(透明 超強力 粘着テープ 3cm*2mm*5m)](https://www.amazon.co.jp/gp/product/B07WNZWFK3/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1) x 1
* [GeeekPi Raspberry Piクラスタケーススタッカブルケース冷却ファン付きRaspberry Pi 4ケースRaspberry Pi 4モデルBおよび3B + 3B 2B用ヒートシンク（4レベル）（茶色）](https://www.amazon.co.jp/gp/product/B07TJZ2HDG/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1) x 1
* [積層式ケース for Raspberry Pi 4 / Pi 3 Model B+ 専用 保護用クリア・アクリルケース カバー アルミヒートシンク二個付き 高硬度 耐用性あり Clear/透明 (4段)](https://www.amazon.co.jp/gp/product/B01F8AHNBA/ref=ppx_yo_dt_b_asin_title_o00_s03?ie=UTF8&psc=1) x 1
* [Anker PowerPort 6 (60W 6ポート USB急速充電器) iPhone / iPad / iPod / Xperia / Galaxy / Nexus / 3DS / PS Vita / ウォークマン他対応 【PowerIQ搭載】 (ブラック)](https://www.amazon.co.jp/gp/product/B00PK1QBO8/ref=ppx_yo_dt_b_asin_title_o00_s02?ie=UTF8&psc=1) x 1
* [TRUSCO(トラスコ) マジックバンド結束テープ 両面 黒 10mm×1.5m MKT1015BK](https://www.amazon.co.jp/gp/product/B004OCOY84/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) x 1
* [サンワサプライ マジックバンド CA-MF6W](https://www.amazon.co.jp/gp/product/B000SXOBGI/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) x 1

# 完成形

参考記事の方々の手順とほとんど全く同じですので、構築手順の詳細は省略します。
購入したUSBケーブルは思ったより丈夫で固くて取り回しはあまり自由にはできません。
ただ、ケーブルの断線の心配がないので安心です。
スタッカブルケース2台で組むと持ち歩くのには辛いですが、
自宅に置いておく分には、1台に詰め込まなくても良いので、簡単だと思います。

![k8s-front.jpeg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/b57e8b3d-f3e2-0661-d283-70fd3abd6410.jpeg)
![k8s-back.jpeg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/c1624556-6ffe-1ca8-2e3c-a5520ef2d2d0.jpeg)
![k8s-up.jpeg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/0531546d-df56-d687-e493-2c8ccd039d52.jpeg)

# まとめ

先駆者の方々の取り組みを参考にさせて頂いたので、何も迷うことなく構築できました。
次は、この環境に[Kubernetes][]をインストールして動作確認までをやっていきたいと思います。


[Kubernetes]: https://kubernetes.io/
[3日間クッキング【Kubernetes のラズペリーパイ包み　“サイバーエージェント風”】]: https://developers.cyberagent.co.jp/blog/archives/14721/
[Raspberry PiでおうちKubernetes構築【物理編】]: https://qiita.com/go_vargo/items/d1271ab60f2bba375dcc
[Raspberry Pi 3 Model B]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b/
