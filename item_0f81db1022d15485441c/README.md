# Amazon Rekognition Custom Labelsでカスタムモデルをトレーニングする

## はじめに

前回、[Open Images Dataset V6 + ExtensionsからAmazon SageMaker Ground Truth形式のデータセットを作成する][]の結果、
[Amazon S3][]に画像データとマニフェストファイルがアップロードされました。
アップロードされたマニフェストファイルに書かれた画像ファイルの場所は、
アップロードされた画像ファイルの位置を指しています。
これを使えば、[Amazon Rekognition Custom Labels][]をトレーニングすることができます。

今回の説明の範囲は以下です。

![Face_and_VehicleRegistrationPlates_Detection_Overview-Training.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/b03eddd5-c6e6-fe28-aa61-bac417497316.png)


## 1. 目的

アップロードしたデータセットを元に、[Amazon Rekognition Custom Labels][]をトレーニングし、
画像ファイルに含まれるナンバープレートを検知するためのモデルを構築します。
また、構築したモデルを使ってAWS CLIでテストをしてみます。

## 2. Amazon Rekognition Custom Labels の料金

現在の料金は以下のようになっています。

[Amazon Rekognition の料金](https://aws.amazon.com/jp/rekognition/pricing/?nc=sn&loc=4)

![Amazon_Rekognition_Custom_Labels_pricing.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/bfc964bd-f9fa-f18b-8736-5633c740049b.png)


トレーニングは頻繁にするものではないと思いますので大丈夫だとは思いますが、
推論は、リソースのプロビジョニングを手動で停止しない限り課金されますので、注意が必要です。

## 3. 具体的な手順

具体的な手順は、こちらの方がとても丁寧に説明してくださっていますので、割愛します。

[Amazon Rekognition Custom Labels を使って自分ちの猫を見分ける！](https://qiita.com/clockpulse/items/fe1f7ce6a130e9abe1c6)

ただし、異なる点が1点あります。
それは、データセットの登録作業です。
前回の作業で、データセットの準備は完了しています。
そしてデータセットの登録時に、**Import images labeled by SageMaker GroundTruth** を選択し、
Amazon S3上のマニフェストファイルを選択します。
以上でデータセットの登録が完了し、モデルをトレーニングできます。

## 4. モデルのトレーニング

今回は、車関連の画像ファイル 8157枚 でトレーニングしています。
数百枚で良いとのことなのですが、とりあえず全部入れてみました。

トレーニング結果は以下のようになりました。
画像ファイル数が多いため、トレーニング時間は8時間45分かかりました。

![evaluation_results_8157.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/fba358a8-dc91-44de-797e-467b671863c7.png)

![per_label_performance_8157.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/eb55dd9c-6424-527e-19ba-32e06def09fd.png)

画像ファイル 500枚でもトレーニングしてみましたが、
トレーニング時間は7時間12分かかりました。

![evaluation_results_500.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/a651a9d0-ec7a-1507-4f49-a5813aca2d7f.png)

![per_label_performance_500.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/dee9b6ee-bd15-615f-a5b2-cc731f32750f.png)

トレーニング時間は、画像ファイル数に比例するのではなく、
もともとこれくらいかかるのかもしれません。
検知ラベル数にもよるのかな？

## 5. 推論のテスト

推論を実行するためには、モデルを開始する必要があります。
また、推論処理が必要なければ、課金を回避するためにモデルを停止しておきましょう。

`AMAZON_RESOURCE_NAME`,`REGION`は、トレーニングしたモデルに合わせて適切な値を使用してください。

#### モデル開始スクリプト
```bash
aws rekognition start-project-version \
  --project-version-arn "AMAZON_RESOURCE_NAME" \
  --min-inference-units 1 \
  --region REGION
```

このスクリプトでモデルが開始されます。
モデルが開始されるまでに10分弱ほど待つ必要があります。

モデルが開始されたら、[Amazon S3][]に置いた画像ファイルに対して
オブジェクト検知を実施することができます。

`MY_BUCKET`,`PATH_TO_MY_IMAGE`は、
オブジェクト検知をしたい画像ファイルの置き場所に合わせて適切な値を使用してください。

#### オブジェクト検知スクリプト
```bash
aws rekognition detect-custom-labels \
  --project-version-arn "AMAZON_RESOURCE_NAME" \
  --image '{"S3Object": {"Bucket": "MY_BUCKET","Name": "PATH_TO_MY_IMAGE"}}' \
  --region REGION
```

以下の画像に対して、推論を実行してみます。

![9c5f2a31335627a0.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/addb2ff7-6e67-3ed9-4986-a7f9be8ad2ae.jpeg)

すると、以下のような json データを取得できます。

```JSON
{
    "CustomLabels": [
        {
            "Name": "vehicle_registration_plate",
            "Confidence": 97.59200286865234,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.09474000334739685,
                    "Height": 0.05618999898433685,
                    "Left": 0.43296000361442566,
                    "Top": 0.6481099724769592
                }
            }
        },
        {
            "Name": "car",
            "Confidence": 88.64099884033203,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.5945600271224976,
                    "Height": 0.5289499759674072,
                    "Left": 0.37042999267578125,
                    "Top": 0.29366999864578247
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 39.222999572753906,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.12643000483512878,
                    "Height": 0.21445000171661377,
                    "Left": 0.47453001141548157,
                    "Top": 0.13256999850273132
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 34.805999755859375,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.047129999846220016,
                    "Height": 0.11795999854803085,
                    "Left": 0.5580800175666809,
                    "Top": 0.199070006608963
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 32.172000885009766,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.08023999631404877,
                    "Height": 0.09521999955177307,
                    "Left": 0.04089999943971634,
                    "Top": 0.03644999861717224
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 30.748998641967773,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.02628999948501587,
                    "Height": 0.07625000178813934,
                    "Left": 0.28075000643730164,
                    "Top": 0.34577998518943787
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 26.173999786376953,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.05203000083565712,
                    "Height": 0.2440599948167801,
                    "Left": 0.2878899872303009,
                    "Top": 0.26269999146461487
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 25.97100067138672,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.28141000866889954,
                    "Height": 0.035829998552799225,
                    "Left": 0.545799970626831,
                    "Top": 0.2807599902153015
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 25.216001510620117,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.012500000186264515,
                    "Height": 0.03903000056743622,
                    "Left": 0.926069974899292,
                    "Top": 0.2845500111579895
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 24.47100067138672,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.029810000211000443,
                    "Height": 0.07336000353097916,
                    "Left": 0.028710000216960907,
                    "Top": 0.23675000667572021
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 24.354000091552734,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.06646999716758728,
                    "Height": 0.1822499930858612,
                    "Left": 0.6726800203323364,
                    "Top": 0.6480500102043152
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 23.09200096130371,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.017000000923871994,
                    "Height": 0.0764399990439415,
                    "Left": 0.7660599946975708,
                    "Top": 0.15618999302387238
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 22.642000198364258,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.07248000055551529,
                    "Height": 0.2407200038433075,
                    "Left": 0.03410999849438667,
                    "Top": 0.27195999026298523
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 22.347999572753906,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.049229998141527176,
                    "Height": 0.2868900001049042,
                    "Left": 0.21337999403476715,
                    "Top": 0.22753000259399414
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 22.3439998626709,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.026830000802874565,
                    "Height": 0.11977999657392502,
                    "Left": 0.8071500062942505,
                    "Top": 0.026149999350309372
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 22.155000686645508,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.05996000021696091,
                    "Height": 0.2612200081348419,
                    "Left": 0.3352999985218048,
                    "Top": 0.2620899975299835
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 21.231000900268555,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.062150001525878906,
                    "Height": 0.17190000414848328,
                    "Left": 0.8816800117492676,
                    "Top": 0.5912100076675415
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 20.970001220703125,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.051020000129938126,
                    "Height": 0.27884000539779663,
                    "Left": 0.24369999766349792,
                    "Top": 0.23983000218868256
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 20.922000885009766,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.03767000138759613,
                    "Height": 0.17587000131607056,
                    "Left": 0.41192999482154846,
                    "Top": 0.2854900062084198
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 20.472000122070312,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.023019999265670776,
                    "Height": 0.08722999691963196,
                    "Left": 0.07423000037670135,
                    "Top": 0.4138199985027313
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 17.325000762939453,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.04673999920487404,
                    "Height": 0.1810699999332428,
                    "Left": 0.07997000217437744,
                    "Top": 0.3072099983692169
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 17.16900062561035,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.019700000062584877,
                    "Height": 0.09153000265359879,
                    "Left": 0.8987399935722351,
                    "Top": 0.13268999755382538
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 16.65999984741211,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.017669999971985817,
                    "Height": 0.02525000087916851,
                    "Left": 0.03654000163078308,
                    "Top": 0.4818100035190582
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 16.49100112915039,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.0189800001680851,
                    "Height": 0.08352000266313553,
                    "Left": 0.7942699790000916,
                    "Top": 0.1342500001192093
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 16.051000595092773,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.018530000001192093,
                    "Height": 0.07240000367164612,
                    "Left": 0.7831799983978271,
                    "Top": 0.13763000071048737
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 13.706000328063965,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.009139999747276306,
                    "Height": 0.03830000013113022,
                    "Left": 0.4589900076389313,
                    "Top": 0.28248998522758484
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 13.169999122619629,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.01689000055193901,
                    "Height": 0.09138999879360199,
                    "Left": 0.9336900115013123,
                    "Top": 0.10761000216007233
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 11.838000297546387,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.02474999986588955,
                    "Height": 0.07043000310659409,
                    "Left": 0.9698399901390076,
                    "Top": 0.32592999935150146
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 10.781000137329102,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.016780000180006027,
                    "Height": 0.029360000044107437,
                    "Left": 0.721750020980835,
                    "Top": 0.2597399950027466
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 9.977999687194824,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.02370999939739704,
                    "Height": 0.01979999989271164,
                    "Left": 0.2701199948787689,
                    "Top": 0.49445000290870667
                }
            }
        },
        {
            "Name": "vehicle",
            "Confidence": 3.3259999752044678,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.5945600271224976,
                    "Height": 0.5289499759674072,
                    "Left": 0.37042999267578125,
                    "Top": 0.29366999864578247
                }
            }
        }
    ]
}
```

たくさんのオブジェクトを検知していますが、
`Confidence`の値を**75**以上とすると、以下の２つに絞られます。

```JSON
{
    "CustomLabels": [
        {
            "Name": "vehicle_registration_plate",
            "Confidence": 97.59200286865234,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.09474000334739685,
                    "Height": 0.05618999898433685,
                    "Left": 0.43296000361442566,
                    "Top": 0.6481099724769592
                }
            }
        },
        {
            "Name": "car",
            "Confidence": 88.64099884033203,
            "Geometry": {
                "BoundingBox": {
                    "Width": 0.5945600271224976,
                    "Height": 0.5289499759674072,
                    "Left": 0.37042999267578125,
                    "Top": 0.29366999864578247
                }
            }
        }
    ]
}
```

検知したナンバープレートと車を四角で囲み表示します。
Jupyter Notebook で確認すると楽です。
また、検知したナンバープレートと車を四角で囲んだ画像を
画像ファイルとして保存します。

```Python
#%%

import json
import cv2

%matplotlib inline
import matplotlib.pyplot as plt

#%%

target_dir = "./test-qiita/"
input_image_path = target_dir + "9c5f2a31335627a0.jpg"
custom_labels_result_json_path = target_dir + "9c5f2a31335627a0.json"
output_image_path = target_dir + "9c5f2a31335627a0-detect.jpg"

min_confidence = 75

#%%

image = cv2.imread(input_image_path)
original = image.copy()

with open(custom_labels_result_json_path) as f:
    custom_labels_result = json.load(f)
custom_labels = custom_labels_result['CustomLabels']

#%%

y, x = image.shape[:2]

for obj in custom_labels:
    if obj['Confidence'] < min_confidence:
        continue
    class_name = obj['Name']
    bbox = obj['Geometry']['BoundingBox']
    x_min = int(x * bbox['Left'])
    x_max = x_min + int(x * bbox['Width'])
    y_min = int(y * bbox['Top'])
    y_max = y_min + int(y * bbox['Height'])

    image = cv2.rectangle(image, (x_min, y_min), (x_max, y_max),
                          color=(0, 255), thickness=2)
    cv2.putText(image, class_name, (x_min, y_min),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

#%%

fig, ax = plt.subplots(1, 2, figsize=(24, 16))
ax[0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
ax[1].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.show()
cv2.imwrite(output_image_path, image)
```

![9c5f2a31335627a0-detect.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/f9ae1f6d-b9e9-b8f2-cb5a-b661193975bc.jpeg)

良い感じに検知していそうです。

最後にモデルを停止しておきます。

#### モデル停止スクリプト
```bash:stop_model.sh
aws rekognition stop-project-version \
  --project-version-arn "AMAZON_RESOURCE_NAME" \
  --region REGION
```

## まとめ

[Open Images Dataset V6 + ExtensionsからAmazon SageMaker Ground Truth形式のデータセットを作成する][]で
作成した自前のデータセットを用いて、自分専用のモデルを構築することができました。
また、テスト画像を用いて、ナンバープレートを検知することができました。

気をつけることとしては、
モデルのトレーニングは7-8時間ほどかかりますし、
モデルの開始には10分弱かかりますので、気長に待ちましょう。

また、トレーニングにも推論にも料金がかかります。
特に推論をするためには、モデルを開始する必要がありますが、
最後にモデルを停止するのを忘れないようにしましょう。

## 次回

**AWS LambdaでAmazon S3にアップロードされた動画を静止画にする** を説明する予定です。

1. [Open Images Dataset V6 + ExtensionsからAmazon SageMaker Ground Truth形式のデータセットを作成する](https://qiita.com/naomori/items/88fa381b1348100977ff)
2. [Amazon Rekognition Custom Labels][]でカスタムモデルをトレーニングする
    - 本記事
3. [AWS Lambda][]で[Amazon S3][]にアップロードされた動画を静止画にする
    - T.B.D.
4. [AWS Lambda][]で[DetectFaces][]オペレーションを使って顔を検出します
    - T.B.D.
5. [AWS Lambda][]で[DetectCustomLabels][]オペレーションを使ってナンバープレートを検出します
    - T.B.D.
6. [AWS Lambda][]で検出した領域のモザイク処理を施し、静止画を動画に変換する
    - T.B.D.


[Open Images Dataset V6 + ExtensionsからAmazon SageMaker Ground Truth形式のデータセットを作成する]: https://qiita.com/naomori/items/88fa381b1348100977ff
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
[VoTTで作成したデータをCustom Labelsで利用可能なAmazon SageMaker Ground Truth形式に変換してみました]: https://dev.classmethod.jp/articles/rekognition-custom-labels-convert-vott/
