# Amazon Rekognition で動画中の顔・ナンバープレートにモザイクをかける

## はじめに

Machine Learning, Deep Learning でいろんなことができそう！と思っても、
初めから自分のやりたいことが実現できるようなネットワークモデルや
アプリケーションを開発するというのは難しそうです。
実際、何から手を付けてよいのかよくわかりません。

そこで、[Amazon Rekognition][]を使って、その難しそうなハードルを
少しでも下げて、自分のやりたいことを実現してみます。

## 目的

今回のやりたいことは、「動画中の顔・ナンバープレートにモザイクをかける」です。  
ドライブレコーダーで撮影した動画を使って、交通状況把握・運転支援・自動運転などに
役立てようと思ったときに、個人情報となる人の顔やナンバープレートは除去する必要があるからです。

動画中の顔・ナンバープレートにモザイクをかけるには、以下の処理が必要です。

1. 動画を静止画に分解する
2. 静止画中に含まれる人間の顔・ナンバープレートを検出する
3. 静止画中に含まれる人間の顔・ナンバープレートにモザイクをかける
4. 静止画を動画に戻す

上記処理において、顔検出は、[Amazon Rekognition Image][]で実現できます。
[Amazon S3][]に静止画を置いて、[Amazon Rekognition Image][]に
[DetectFaces][]オペレーションをリクエストすることで、静止画内の顔を検出できます。

ただし、ナンバープレートは、[Amazon Rekognition Image][]では検出できません。
そのようなオペレーションは用意されていないからです。
ナンバープレートを検出するためには、[Amazon Rekognition Custom Labels][]を使う必要があります。
[Amazon Rekognition Custom Labels][]は、その名前の通り、使う人専用(Custom)のモデルを
専門知識なしに構築することができます。
しないといけないことは、検知したい内容に合わせたトレーニング画像セットを
アップロードすることだけです。

## 全体像

今回の全体像を示します。

![Face and Vehicle registration plates detection Overview](https://github.com/naomori/qiita/tree/master/item_XXX/images/Face_and_VehicleRegistrationPlates_Detection_Overview.png "Face and Vehicle registration plates detection Overview")

次回から以下を１つ１つ説明する予定です。

1. [Open Images Dataset V6 + Extensions][]から[Amazon SageMaker Ground Truth][]形式のデータセットを作成する
    - T.B.D.
2. [Amazon Rekognition Custom Labels][]でカスタムモデルをトレーニングする
    - T.B.D.
3. [AWS Lambda][]で[Amazon S3][]にアップロードされた動画を静止画にする
    - T.B.D.
4. [AWS Lambda][]で[DetectFaces][]オペレーションを使って顔を検出します
    - T.B.D.
5. [AWS Lambda][]で[DetectCustomLabels][]オペレーションを使ってナンバープレートを検出します
    - T.B.D.
6. [AWS Lambda][]で検出した領域のモザイク処理を施し、静止画を動画に変換する
    - T.B.D.


[AWS Lambda]: https://aws.amazon.com/lambda/
[Amazon S3]: https://aws.amazon.com/s3/
[Amazon Rekognition]: https://aws.amazon.com/jp/rekognition/?nc=sn&loc=0
[Amazon Rekognition Image]: https://aws.amazon.com/jp/rekognition/image-features/?nc=sn&loc=3&dn=2
[DetectFaces]: https://docs.aws.amazon.com/ja_jp/rekognition/latest/dg/faces-detect-images.html
[Amazon Rekognition Custom Labels]: https://aws.amazon.com/jp/rekognition/custom-labels-features/
[DetectCustomLabels]: https://docs.aws.amazon.com/ja_jp/rekognition/latest/dg/API_DetectCustomLabels.html
[Open Images Dataset V6 + Extensions]: https://storage.googleapis.com/openimages/web/index.html
[Amazon SageMaker Ground Truth]: https://aws.amazon.com/jp/sagemaker/groundtruth/
