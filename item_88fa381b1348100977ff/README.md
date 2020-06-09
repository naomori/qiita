# Open Images Dataset V6 + Extensions から Amazon SageMaker Ground Truth 形式のデータセットを作成する

## はじめに

顔検出は、[Amazon Rekognition Image][]で実現できますが、
ナンバープレートは、[Amazon Rekognition Image][]では検出できません。
そこで、ナンバープレートを検出するために、[Amazon Rekognition Custom Labels][]を使います。

[Amazon Rekognition Custom Labels][]でナンバープレートを検出するためには、
検知したい内容に合わせてトレーニング画像セットをアップロードする必要があります。

今回の説明の範囲は以下です。

![Face_and_VehicleRegistrationPlates_Detection_Overview-Dataset.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/a05dd355-5def-ea0a-aec8-d27598a22fd6.png)

## 1. 目的

ナンバープレートの画像を集めるのはとても大変です。
しかも、その画像にアノテーション情報をつけるのはもっと大変です。
ですので、オープンなデータを活用することにします。

そこで、画像収集、アノテーション情報作成の手間を避けるために、
[Open Images Dataset V6 + Extensions][]の中から、
ナンバープレートを含む画像とそのアノテーション情報を利用することにします。

## 2. データセット

データセットには様々なものがあり、それぞれ何を目的としているのかにより、
様々な特徴があるようです。

こちらで様々なオープンデータセットを紹介してくれています。

[【保存版】オープンデータ・データセット100選 -膨大なデータを活用しよう！](https://ainow.ai/2020/03/02/183280/)

### Open Images Dataset V6 + Extensions


データセットの中には、画像に含まれるラベルをWebインターフェイスで検索できるものがありますので、
そこから検知したいラベルを含むデータセットを利用すると良いです。

ナンバープレートを含むデータセットはたくさんあると思いますが、
[Open Images Dataset V6 + Extensions][]にナンバープレートの画像があったので、
これを利用することにします。

[Open Images Dataset V6 + Extensions][]は、
Googleが提供している世界最大の画像データセットで、200万枚ほどの画像を持ち、
画像内写っているオブジェクト600種類に対して、バウンディングボックスが付与されています。

### Amazon SageMaker Ground Truth

[DetectCustomLabels][]では、トレーニングに使用するデータセットとして、
[Amazon SageMaker Ground Truth][]形式のデータセットを利用することができます。
したがって、[Open Images Dataset V6 + Extensions][]のデータセットを
[Amazon SageMaker Ground Truth][]形式に変換することにします。

こちらの方の記事を参考にさせていただきました。

[VoTTで作成したデータをCustom Labelsで利用可能なAmazon SageMaker Ground Truth形式に変換してみました](https://itnews.org/news_resources/153740)

## 3. Open Images Dataset V6 + Extensions のダウンロード

まずは、[Open Images Dataset V6 Download][]からダウンロードします。
データセットは、Amazon S3 に置いてあるため、ダウンロードには、AWS CLI を使います。
AWS CLIは、[AWS CLI のインストール][]を参考に事前にインストールしておきます。

まずは画像からダウンロードします(`Images - Download from CVDF`)。
全部で560GBほどの画像をダウンロードします。

* target_dir/train (513GB)
* target_dir/validation (12GB)
* target_dir/test (36GB)

```bash
aws s3 --no-sign-request sync s3://open-images-dataset/train  ./train
aws s3 --no-sign-request sync s3://open-images-dataset/validation ./validation
aws s3 --no-sign-request sync s3://open-images-dataset/test ./test
```

あるいは、分割されたファイルでダウンロードすることもできます。
今回はこちらの方法でダウンロードしました。

* train_0.tar.gz (46G)
* train_1.tar.gz (34G)
* train_2.tar.gz (33G)
* train_3.tar.gz (32G)
* train_4.tar.gz (31G)
* train_5.tar.gz (31G)
* train_6.tar.gz (32G)
* train_7.tar.gz (31G)
* train_8.tar.gz (31G)
* train_9.tar.gz (31G)
* train_a.tar.gz (31G)
* train_b.tar.gz (31G)
* train_c.tar.gz (31G)
* train_d.tar.gz (31G)
* train_e.tar.gz (28G)
* train_f.tar.gz (28G)

```bash
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_0.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_1.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_2.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_3.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_4.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_5.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_6.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_7.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_8.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_9.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_a.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_b.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_c.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_d.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_e.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/train_f.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/validation.tar.gz .
aws s3 --no-sign-request cp s3://open-images-dataset/tar/test.tar.gz .
```

また、アノテーション(バウンディングボックス)もダウンロードします(`Boxes - Train/Validation/Test`)。
* Train: oidv6-train-annotations-bbox.csv (2.2G)
* Validation: validation-annotations-bbox.csv (24M)
* Test: test-annotations-bbox.csv (74M)

あと、クラスIDとクラス名との対応表をダウンロードします(`Metadata - Class Names`)。
* Class Names: class-descriptions-boxable.csv (12K)

かなり大きなデータなので、何回かに分けて夜中にダウンロードしておきます。

## 4. Amazon SageMaker Ground Truth 形式

Amazon SageMaker Ground Truth 形式は、
[Amazon SageMaker 出力データ][]の「境界ボックスジョブの出力」に記載があります。
ですが、実際にAmazon SageMaker Ground Truthを使って出力したものは
以下のようになっており、微妙にドキュメントと違うようです。
今回は実際に出力された形式を利用することにします。

```json
{
  "source-ref":"s3://open-images-ground-truth.us-west-2/00009e5b390986a0.jpg",
  "test-job-open-images-ground-truth":{
    "annotations":[
      {
        "class_id":0,
        "width":48,
        "top":599,
        "height":27,
        "left":466
      },
      {
        "class_id":0,
        "width":19,
        "top":517,
        "height":16,
        "left":1005
      },
      {
        "class_id":1,
        "width":500,
        "top":458,
        "height":218,
        "left":461
      },
      {
        "class_id":1,
        "width":44,
        "top":491,
        "height":104,
        "left":980
      }
    ],
    "image_size":[
      {
        "width":1024,
        "depth":3,
        "height":682
      }
    ]
  },
  "test-job-open-images-ground-truth-metadata":{
    "job-name":"labeling-job/test-job-open-images-ground-truth",
    "class-map":{
      "1":"vehicle",
      "0":"plate"
    },
    "human-annotated":"yes",
    "objects":[
      {
        "confidence":0.09
      },
      {
        "confidence":0.09
      },
      {
        "confidence":0.09
      },
      {
        "confidence":0.09
      }
    ],
    "creation-date":"2020-05-15T08:22:21.134415",
    "type":"groundtruth/object-detection"
  }
}
```

* `source-ref`は、画像ファイルの置き場所で、s3である必要があります。
* `annotations`は、クラスIDとそのバウンディングボックスの情報です。
* `image_size`は、画像ファイルの解像度とチャンネル数です。
* `class-map`は、その画像ファイルに含まれるクラスIDとその名前です。
* `objects`は、先のバウンディングボックスを付与した確信度です。手作業の場合は1です。


この出力形式は1エントリのデータ形式であって、
[Amazon Rekognition Custom Labels][]にデータセットとして入力する
`manifest`ファイルでは、jsonデータは改行されておらず1行になっています。
そして、この1行のjsonデータが画像ファイル行数分だけ書かれているファイルが
[Amazon SageMaker Ground Truth][]のデータセットである`manifest`ファイルです。
画像ファイル自体は、s3に置いておく必要があります。

## 5. アノーテション情報の1次選別

こちらの
[Open Image Dataset V5を使ってみる](https://blog.imind.jp/entry/2019/06/18/210510)
がとても参考になります。

トレーニング用のアノテーション情報`oidv6-train-annotations-bbox.csv`を
そのまま開こうとするとファイルが大き過ぎて、PCのメモリ不足で開けなかったりします。
ですので、まずは、検知したい物体が含まれる行のみを選んで、新しいファイルに保存します。

バウンディングボックスのアノテーションファイルから、検知したい物体が含まれる行のみを選んで、
ファイル拡張子の直前に"_pickup"を付加した新しいファイルに保存することにします。

検知したい物体とクラスIDとの関連は、`class-descriptions-boxable.csv`ファイルで確認できます。
今回は、検知したい物体として、交通関連のものをピックアップしました。

```bash
#!/bin/sh

# /m/01jfm_,Vehicle registration plate
# /m/04_sv,Motorcycle
# /m/0k4j,Car
# /m/07yv9,Vehicle
# /m/015qff,Traffic light
# /m/01mqdt,Traffic sign
# /m/0199g,Bicycle
# /m/01bqk0,Bicycle wheel
# /m/01bjv,Bus
# /m/07r04,Truck
# /m/012n7d,Ambulance
# /m/02pv19,Stop sign
# /m/0h9mv,Tire
# /m/0pg52,Taxi

related_labels="/m/01jfm_|/m/04_sv|/m/0k4j|/m/07yv9|/m/015qff|/m/01mqdt|/m/0199g|/m/01bqk0|/m/01bjv|/m/07r04|/m/012n7d|/m/02pv19|/m/0h9mv|/m/0pg52"

head -1 oidv6-train-annotations-bbox.csv > oidv6-train-annotations-bbox_pickup.csv
grep -E ${related_labels} \
oidv6-train-annotations-bbox.csv >> oidv6-train-annotations-bbox_pickup.csv

head -1 validation-annotations-bbox.csv > validation-annotations-bbox_pickup.csv
grep -E ${related_labels} \
validation-annotations-bbox.csv >> validation-annotations-bbox_pickup.csv

head -1 test-annotations-bbox.csv > test-annotations-bbox_pickup.csv
grep -E ${related_labels} \
test-annotations-bbox.csv >> test-annotations-bbox_pickup.csv
```

それぞれのファイルが小さくなり扱いやすくなりました。
* Train: oidv6-train-annotations-bbox.csv (2.2G)
  - **oidv6-train-annotations-bbox_pickup.csv (87M)**
* Validation: validation-annotations-bbox.csv (24M)
  - **validation-annotations-bbox_pickup.csv (1.8M)**
* Test: test-annotations-bbox.csv (74M)
  - **test-annotations-bbox_pickup.csv (5.4M)**


## 6. アノテーション情報の2次選別

今回必要なのは、ナンバープレート情報です。
1次選別では、交通関連の物体のどれかが含まれている画像が選別されており、
ナンバープレートが写っていない画像も含まれています。
したがって、2次選別では、ナンバープレートが含まれている画像のみに選抜します。

2次選別したアノーテション情報を、ファイル名の末尾に`_pickup-vrp`を付加した
csvファイルに保存することにします。

```python
import pandas as pd

# input

annotation_dir = "./"

boxes_train = "oidv6-train-annotations-bbox_pickup.csv"
boxes_valid = "validation-annotations-bbox_pickup.csv"
boxes_test = "test-annotations-bbox_pickup.csv"

boxes = {
    "train": annotation_dir + "/" + boxes_train,
    "valid": annotation_dir + "/" + boxes_valid,
    "test": annotation_dir + "/" + boxes_test,
}

vehicle_registration_plate_label_name = "/m/01jfm_"

# output

outfile_train = "oidv6-train-annotations-bbox_pickup-vrp.csv"
outfile_valid = "validation-annotations-bbox_pickup-vrp.csv"
outfile_test = "test-annotations-bbox_pickup-vrp.csv"

outfiles = {
    "train": annotation_dir + "/" + outfile_train,
    "valid": annotation_dir + "/" + outfile_valid,
    "test": annotation_dir + "/" + outfile_test,
}

# extract


def extract_label_name(df, extract_label_name):
    df_cond = df.LabelName == extract_label_name
    image_ids = df[df_cond].ImageID.unique()
    return df[df.ImageID.isin(image_ids)]


# Picking up images for validation


df_valid = pd.read_csv(boxes["valid"])
df_valid_extract = extract_label_name(df_valid,
                                      vehicle_registration_plate_label_name)
df_valid_extract.to_csv(outfiles['valid'])


# Picking up images for test


df_test = pd.read_csv(boxes["test"])
df_test_extract = extract_label_name(df_test,
                                     vehicle_registration_plate_label_name)
df_test_extract.to_csv(outfiles['test'])


# Picking up images for train


df_train = pd.read_csv(boxes["train"])
df_train_extract = extract_label_name(df_train,
                                      vehicle_registration_plate_label_name)
df_train_extract.to_csv(outfiles['train'])
```

それぞれのファイルがさらに小さくなり扱いやすくなりました。
* Train: oidv6-train-annotations-bbox.csv (2.2G)
  - oidv6-train-annotations-bbox_pickup.csv (87M)
  - **oidv6-train-annotations-bbox_pickup-vrp.csv (4.3M)**
* Validation: validation-annotations-bbox.csv (24M)
  - validation-annotations-bbox_pickup.csv (1.8M)
  - **validation-annotations-bbox_pickup-vrp.csv (325K)**
* Test: test-annotations-bbox.csv (74M)
  - test-annotations-bbox_pickup.csv (5.4M)
  - **test-annotations-bbox_pickup-vrp.csv (957K)**


## 7. 画像の選別

ナンバープレートのアノテーション情報のある画像IDを取得し、
ダウンロードした画像のtarballから、その画像ファイルだけを展開します。
画像 tarball は `$HOME/Downloads` に置いてある前提になっているので、
違う場所にダウンロードした場合は、変更すれば大丈夫だと思います。

```python
import os
import glob
import tarfile

import pandas as pd
from concurrent.futures import ProcessPoolExecutor


annotation_dir = "./"

boxes_train = "oidv6-train-annotations-bbox_pickup-vrp.csv"
boxes_valid = "validation-annotations-bbox_pickup-vrp.csv"
boxes_test = "test-annotations-bbox_pickup-vrp.csv"

boxes = {
    "train": annotation_dir + "/" + boxes_train,
    "valid": annotation_dir + "/" + boxes_valid,
    "test": annotation_dir + "/" + boxes_test,
}

vehicle_registration_plate_label_name = "/m/01jfm_"

# extract function


def extract_images(df, images_tarball_path, extract_dir="."):
    vrp_cond = df.LabelName == vehicle_registration_plate_label_name
    image_ids = df[vrp_cond].ImageID.unique()
    image_files = [f + ".jpg" for f in image_ids]

    with tarfile.open(images_tarball_path) as tar:
        members = tar.getmembers()

    print(f"tarball: {images_tarball_path}: original: {len(members)}")
    members = [m for m in members if os.path.basename(m.name) in image_files]
    print(f"tarball: {images_tarball_path}: picked-up: {len(members)}")

    os.makedirs(extract_dir, exist_ok=True)
    with tarfile.open(images_tarball_path) as tar:
        tar.extractall(path=extract_dir, members=members)

# Picking up images for validation


df_valid = pd.read_csv(boxes["valid"])
valid_images_tarball = "validation.tar.gz"
download_images_dir = f"{os.environ['HOME']}/Downloads"
valid_images_path = download_images_dir + "/" + valid_images_tarball
extract_images(df_valid, valid_images_path)

# Picking up images for test


df_test = pd.read_csv(boxes["test"])
test_images_tarball = "test.tar.gz"
download_images_dir = f"{os.environ['HOME']}/Downloads"
test_images_path = download_images_dir + "/" + test_images_tarball
extract_images(df_test, test_images_path)


# Picking up images for train


df_train = pd.read_csv(boxes["train"])
download_images_dir = f"{os.environ['HOME']}/Downloads"
glob_train_tarballs = download_images_dir + "/" + "train_*.tar.gz"
with ProcessPoolExecutor(max_workers=8) as executor:
    for train_images_tarball in glob.glob(glob_train_tarballs):
        print(f"train_images_tarball: {train_images_tarball}")
        executor.submit(extract_images, df_train, train_images_tarball)
```

これで、ナンバープレートを含む画像のみをtarballから展開し、
各ディレクトリ以下に保存することができました。

## 8. Amazon SageMaker Ground Truth でデータセット作成

ここまでで、必要な画像を取得でき、アノテーション情報も取得できました。
ここからは、
[VoTTで作成したデータをCustom Labelsで利用可能なAmazon SageMaker Ground Truth形式に変換してみました][]
を参考に、これらのデータセットをAmazon SageMaker Ground Truth形式に変換します。

出力ファイルは２つです。
1. output.manifest
    - Amazon SageMaker Ground Truth 形式のマニフェストファイル
    - Amazon Rekognition Custom Labels のトレーニング用データセット
2. output.image_paths: 
    - マニフェストファイルに含まれる画像のローカルパス
    - Amazon S3 にアップロードするために使用する

マニフェストファイルに含むクラスは以下です。
* "/m/01jfm_": "vehicle_registration_plate"
* "/m/0k4j": "car"
* "/m/07yv9": "vehicle"
* "/m/01bjv": "bus"
* "/m/07r04": "truck"
* "/m/012n7d": "ambulance"
* "/m/0pg52": "taxi"
* "/m/04_sv": "motorcycle"
* "/m/0199g": "bicycle"

今回は、すべての画像ファイル(train/validation/test)を
トレーニング用データセット(validation含む)に含むようにします。

```python
import json
import glob
import datetime

import pickle
import pandas as pd
import cv2

annotation_dir = "./"
boxes_train = "oidv6-train-annotations-bbox_pickup-vrp.csv"
boxes_valid = "validation-annotations-bbox_pickup-vrp.csv"
boxes_test = "test-annotations-bbox_pickup-vrp.csv"

boxes = {
    "train": annotation_dir + "/" + boxes_train,
    "valid": annotation_dir + "/" + boxes_valid,
    "test": annotation_dir + "/" + boxes_test,
}

metadata_class_names = "class-descriptions-boxable.csv"

train_dir = "./train_*"
valid_dir = "./validation"
test_dir = "./test"
train_dirs = [test_dir, valid_dir, train_dir]


output_manifest = "output.manifest"
output_image_paths = "output.image_paths"

images_bucket = "BUCKETNAME.us-west-2"
gt_job_name = "job-open-images-ground-truth"
manifest_type = "groundtruth/object-detection"
target_classes = {
    "/m/01jfm_": "vehicle_registration_plate",
    "/m/0k4j": "car",
    "/m/07yv9": "vehicle",
    "/m/01bjv": "bus",
    "/m/07r04": "truck",
    "/m/012n7d": "ambulance",
    "/m/0pg52": "taxi",
    "/m/04_sv": "motorcycle",
    "/m/0199g": "bicycle",
}
num_of_images = -1 # all: <=0


need_columns = ["ImageID", "LabelName", "Confidence",
                "XMin", "XMax", "YMin", "YMax"]
df_train = pd.read_csv(boxes["train"])
df_train = df_train.loc[:, need_columns]

df_valid = pd.read_csv(boxes["valid"])
df_valid = df_valid.loc[:, need_columns]

df_test = pd.read_csv(boxes["test"])
df_test = df_test.loc[:, need_columns]

df_class_id = pd.DataFrame(
    [(idx, lbl) for idx, lbl in enumerate(target_classes.keys())],
    columns=['ClassID', 'LabelName'])

df_class = pd.read_csv(annotation_dir + "/" + metadata_class_names,
                       names=['LabelName', 'ClassName'])
df_class = df_class[df_class['LabelName'].isin(df_class_id['LabelName'])]
df_class = pd.merge(df_class, df_class_id, on='LabelName')

df_all = df_train.append(df_valid)
df_all = df_all.append(df_test)
df_all = pd.merge(df_all, df_class, how='inner', on='LabelName')

class_map_all = {str(row.ClassID): target_classes[row.LabelName]
                 for row in df_class.itertuples()}


def create_source_ref(bucket, image_id):
    return {"source-ref": f"s3://{bucket}/{image_id}.jpg"}


def create_job(job_name, df_annos, jpg_file):
    img = cv2.imread(jpg_file)
    if len(img.shape) == 3:
        height, width, channels = img.shape[:3]
    else:
        height, width = img.shape[:2]
        channels = 1

    annotations = []
    image_size = []
    for df_anno in df_annos.itertuples():
        annotations.append({
            "class_id": int(df_anno.ClassID),
            "top": int(height * df_anno.YMin),
            "left": int(width * df_anno.XMin),
            "height": int(height * (df_anno.YMax - df_anno.YMin)),
            "width": int(width * (df_anno.XMax - df_anno.XMin))
        })
        image_size.append({
            "height": int(height),
            "width": int(width),
            "depth": channels
        })

    job_json = {job_name: {
        "annotations": annotations,
        "image_size": image_size
    }}
    return job_json


def create_job_metadata(job_name, class_map, df_annos, mani_type):
    objects = []
    for df_anno in df_annos.itertuples():
        objects.append({"confidence": df_anno.Confidence})
    dt_now = datetime.datetime.now().isoformat()
    metadata_json = {f"{gt_job_name}-metadata": {
        "job-name": f"labeling-job/{job_name}",
        "class-map": class_map,
        "human-annotated": "yes",
        "objects": objects,
        "creation-date": str(dt_now),
        "type": mani_type
    }}
    return metadata_json


def create_class_map(class_map_orig, tgt_class_ids):
    return {key: class_map_orig[key]
            for key in class_map_orig.keys() if int(key) in tgt_class_ids}


def create_manifest_all(df, num, images_dirs, s3_bucket,
                        job_name, class_map_orig, mani_type):
    if num_of_images <= 0:
        img_ids = df.ImageID.unique()
    else:
        img_ids = df.ImageID.unique()[:num]
        print(f"number of image IDs: {len(img_ids)}")

    manifests = []
    img_paths = []
    for images_dir in images_dirs:
        for img_id in img_ids:
            jpg_path = glob.glob(f"{images_dir}/{img_id}.jpg")
            if not jpg_path:
                continue
            df_target = df[df.ImageID == img_id]
            class_ids = df_target.ClassID.unique()
            class_map = create_class_map(class_map_orig, class_ids)
            manifest = create_manifest(s3_bucket, img_id, job_name, df_target,
                                       *jpg_path, class_map, mani_type)
            manifests.append(manifest)
            img_paths.append(*jpg_path)
    print(f"create: {len(img_paths)} entries")
    return manifests, img_paths


def create_manifest(s3_bucket, img_id, job_name, df_target, jpg_path,
                    class_map, mani_type):
    ref = create_source_ref(s3_bucket, img_id)
    job = create_job(job_name, df_target, jpg_path)
    metadata = create_job_metadata(job_name, class_map, df_target, mani_type)
    manifest = {}
    manifest.update(ref)
    manifest.update(job)
    manifest.update(metadata)
    return manifest


manifest_all, image_paths = create_manifest_all(
    df_all, num_of_images, train_dirs,
    images_bucket, gt_job_name, class_map_all, manifest_type)

with open(output_manifest, 'w') as out_manifest:
    for mani in manifest_all:
        json.dump(mani, out_manifest)
        out_manifest.write('\n')

with open(output_image_paths, 'wb') as out_paths:
    pickle.dump(image_paths, out_paths)
```

## 9. マニフェストと画像ファイルのアップロード

作成したマニフェストファイルと画像ファイルは
Amazon S3 にアップロードする必要があります。

```python
import os
import pickle

from concurrent.futures import ProcessPoolExecutor
import boto3

manifest_file = "output.manifest"
jpg_paths_file = "output.image_paths"

s3_bucket = "open-images-v6-ground-truth.us-west-2"


def upload_file(bucket, file, force=False):
    jpg_key = os.path.basename(file)
    session = boto3.session.Session(profile_name='moritan')
    client = session.client('s3')
    result = client.list_objects(Bucket=bucket, Prefix=jpg_key)
    if "Contents" in result:
        print(f"exists: {jpg_key}")
        if not force:
            return
        print(f"overwrite: {jpg_key}")
    else:
        print(f"not exists: {jpg_key}")
    resource = session.resource('s3')
    resource.Bucket(bucket).upload_file(Filename=file, Key=jpg_key)


with open(jpg_paths_file, 'rb') as jpg_paths_obj:
    jpg_paths = pickle.load(jpg_paths_obj)
    with ProcessPoolExecutor(max_workers=16) as executor:
        for jpg_path in jpg_paths:
            executor.submit(upload_file, s3_bucket, jpg_path)

upload_file(s3_bucket, manifest_file, True)
```

## まとめ

[Amazon Rekognition Custom Labels][]で自分専用のモデルをトレーニングするためには、
データセットが必要ですが、データセットの作成はとても手間がかかります。
オープンなデータセット[Open Images Dataset V6 + Extensions][]を
[Amazon Rekognition Custom Labels][]で利用可能な
[Amazon SageMaker Ground Truth][]形式に変換することで、
自分専用のモデルをトレーニングするためのデータセットを作成することができます。

## 次回

**Amazon Rekognition Custom Labels でカスタムモデルをトレーニングする**を説明する予定です。

1. [Open Images Dataset V6 + Extensions][]から[Amazon SageMaker Ground Truth][]形式のデータセットを作成する
    - 本記事
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
[Open Images Dataset V6 Download]: https://storage.googleapis.com/openimages/web/download.html
[AWS CLI のインストール]: https://docs.aws.amazon.com/ja_jp/cli/latest/userguide/cli-chap-install.html
[Amazon SageMaker 出力データ]: https://docs.aws.amazon.com/ja_jp/sagemaker/latest/dg/sms-data-output.html
[VoTTで作成したデータをCustom Labelsで利用可能なAmazon SageMaker Ground Truth形式に変換してみました]: https://dev.classmethod.jp/articles/rekognition-custom-labels-convert-vott/
