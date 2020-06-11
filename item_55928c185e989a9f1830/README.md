# はじめに

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
また、ナンバープレートを検出するためには、[Amazon Rekognition Custom Labels][]を使う必要があります。
[Amazon Rekognition Custom Labels][]は、その名前の通り、使う人専用(Custom)のモデルを
専門知識なしに構築することができます。
しないといけないことは、検知したい内容に合わせたトレーニング画像セットを
アップロードすることだけです。

# 全体像

今回の全体像を示します。

![Face_and_VehicleRegistrationPlates_Detection_Overview.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/08d27f95-b123-28f8-c2f3-8a3b64172d6a.png)

次回から以下を１つ１つ説明する予定です。

1. [Open Images Dataset V6 + ExtensionsからAmazon SageMaker Ground Truth形式のデータセットを作成する][]
2. [Amazon Rekognition Custom Labelsでカスタムモデルをトレーニングする][]
3. [Amazon S3にアップロードされた動画内の個人情報にモザイクをかける][]


[Amazon Rekognition で動画中の顔・ナンバープレートにモザイクをかける]: https://qiita.com/naomori/items/55928c185e989a9f1830
[Open Images Dataset V6 + ExtensionsからAmazon SageMaker Ground Truth形式のデータセットを作成する]: https://qiita.com/naomori/items/88fa381b1348100977ff
[Amazon Rekognition Custom Labelsでカスタムモデルをトレーニングする]: https://qiita.com/naomori/items/0f81db1022d15485441c
[Amazon S3にアップロードされた動画内の個人情報にモザイクをかける]: https://qiita.com/drafts/cea51f7a7565cfb2caef/edit

[VoTTで作成したデータをCustom Labelsで利用可能なAmazon SageMaker Ground Truth形式に変換してみました]: https://dev.classmethod.jp/articles/rekognition-custom-labels-convert-vott/

[PyCharm]: https://www.jetbrains.com/pycharm/
[AWS Toolkit for PyCharm]: https://aws.amazon.com/jp/pycharm/

[AWS Lambda]: https://aws.amazon.com/lambda/
[Amazon S3]: https://aws.amazon.com/s3/
[Amazon Rekognition]: https://aws.amazon.com/jp/rekognition/?nc=sn&loc=0
[Amazon Rekognition Image]: https://aws.amazon.com/jp/rekognition/image-features/?nc=sn&loc=3&dn=2
[DetectFaces]: https://docs.aws.amazon.com/ja_jp/rekognition/latest/dg/faces-detect-images.html
[Amazon Rekognition Custom Labels]: https://aws.amazon.com/jp/rekognition/custom-labels-features/
[DetectCustomLabels]: https://docs.aws.amazon.com/ja_jp/rekognition/latest/dg/API_DetectCustomLabels.html
[Open Images Dataset V6 + Extensions]: https://storage.googleapis.com/openimages/web/index.html
[Amazon SageMaker Ground Truth]: https://aws.amazon.com/jp/sagemaker/groundtruth/
[Open Images Dataset V6 Download]: https://storage.googleapis.com/openimages/web/download.html
[AWS CLI のインストール]: https://docs.aws.amazon.com/ja_jp/cli/latest/userguide/cli-chap-install.html
[Amazon SageMaker 出力データ]: https://docs.aws.amazon.com/ja_jp/sagemaker/latest/dg/sms-data-output.html
[AWS CloudFormation]: https://aws.amazon.com/jp/cloudformation/
[Limits in Amazon Rekognition Custom Labels]: https://docs.aws.amazon.com/rekognition/latest/customlabels-dg/limits.html
[Amazon Rekognition endpoints and quotas]:https://docs.aws.amazon.com/general/latest/gr/rekognition_region.html#limits_rekognition
[Create case]: https://console.aws.amazon.com/support/cases#/create?issueType=service-limit-increase

[Amazon EC2]: https://aws.amazon.com/jp/ec2/
[Amazon SageMaker]: https://aws.amazon.com/jp/sagemaker/
