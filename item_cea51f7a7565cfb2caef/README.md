# はじめに

前回、[Amazon Rekognition Custom Labelsでカスタムモデルをトレーニングする][]によって、
ナンバープレートを検知することができるカスタムモデルを構築できました。

このカスタムモデルのAPIを利用することで、画像ファイル内のオブジェクトを検知できます。

今回の説明の範囲は以下です。

![Face_and_VehicleRegistrationPlates_Detection_Overview-Detection.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/3c83a19f-e416-e90e-8320-7020fdfa7c07.png)

今回は、[Amazon S3][]に動画ファイル(.mov)がアップロードされたことをトリガーに
[AWS Lambda][]を実行し、その中で、動画ファイルを静止画に分解します。
分解した静止画一枚一枚に対して、顔検出、ナンバープレート検出を行います。
検出した顔・ナンバープレートの領域にモザイク処理を施します。
モザイク処理を施したすべての静止画から動画ファイル(.mp4)に再構成します。

# 1. Amazon S3 Put をトリガーに AWS Lambda を実行します

私は、開発エディタとして、[PyCharm][]を使っているのですが、
[AWS Toolkit for PyCharm][]プラグインを追加すると、
[AWS CloudFormation][]を使って、リソースをプロビジョニングできるので便利です。

#### Amazon S3 バケット
[AWS Lambda][]をトリガーする[Amazon S3][]は以下のように定義します。
`SOURCE_BUCKET_NAME`に実際のバケット名を定義します。
これにより、ファイルのsuffixとして`.mov`を持つファイルが
S3バケットに保存されると、Lambda関数`TriggerDetect`がトリガーされます。

<details><summary>S3 Bucket templateファイル</summary><div>

```yaml
Resources:
  SrcS3Bucket:
    Type: AWS::S3::Bucket
    DependsOn: TriggerDetectPermission
    Properties:
      BucketName: SOURCE_BUCKET_NAME
      NotificationConfiguration:
        LambdaConfigurations:
          - Event: s3:ObjectCreated:*
            Filter:
              S3Key:
                Rules:
                  - Name: suffix
                    Value: mov
            Function: !GetAtt
              - TriggerDetect
              - Arn
```
</div></details>


#### AWS Lambda 関数

Lambda関数`TriggerDetect`と関数で利用するリソースを定義します。

特にメモリサイズを`MemorySize: 3008`(MB)としているのは、
Lambda内で静止画をメモリに展開して画像処理をする必要があるので、
最大値(3008MB)にしています。
さらに、時間がかかる処理が多いため、時間を`Timeout: 900`(sec)と最大値にしています。
また、処理時間を短縮するために並列処理をしており、
その並列数分だけ`ReservedConcurrentExecutions: 4`を設定しています。
<details><summary>AWS Lambda templateファイル</summary><div>

```yaml
Resources:
  TriggerDetect:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: faces_and_license_plates_detect/
      FunctionName: trigger_detect
      Handler: app.lambda_handler
      MemorySize: 3008
      ReservedConcurrentExecutions: 4
      Role: !GetAtt TriggerDetectRole.Arn
      Runtime: python3.7
      Timeout: 900
      Environment:
        Variables:
          PROJECT_VERSION_ARN: "AMAZON_RESOURCE_NAME_OF_AMAZON_REKOGNITION_CUSTOM_LABELS_THAT_YOU_BUILT"
          OUTPUT_BUCKET: "OUTPUT_BUCKET_NAME"
          MAX_WORKERS: 4
          FACE_MIN_CONFIDENCE: 10
          LICENSE_PLATE_MIN_CONFIDENCE: 75

  TriggerDetectPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt
        - TriggerDetect
        - Arn
      Principal: s3.amazonaws.com
      SourceArn: !Join
        - ""
        - - "arn:aws:s3:::"
          - "SOURCE_BUCKET_NAME"
```
</div></details>


#### template.yaml

`template.yaml`全体を以下に載せておきます。

<details><summary>template.yaml全体</summary><div>

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: "Test Face Detection and License Plate Detection"

Resources:

  TriggerDetectRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: trigger_detect_role
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Action: sts:AssumeRole
            Principal:
              Service:
                - lambda.amazonaws.com
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonS3FullAccess
        - arn:aws:iam::aws:policy/AmazonRekognitionFullAccess
        - arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

  TriggerDetect:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: faces_and_license_plates_detect/
      FunctionName: trigger_detect
      Handler: app.lambda_handler
      MemorySize: 3008
      ReservedConcurrentExecutions: 4
      Role: !GetAtt TriggerDetectRole.Arn
      Runtime: python3.7
      Timeout: 900
      Environment:
        Variables:
          PROJECT_VERSION_ARN: "AMAZON_RESOURCE_NAME_OF_AMAZON_REKOGNITION_CUSTOM_LABELS_THAT_YOU_BUILT"
          OUTPUT_BUCKET: "OUTPUT_BUCKET_NAME"
          MAX_WORKERS: 4
          FACE_MIN_CONFIDENCE: 10
          LICENSE_PLATE_MIN_CONFIDENCE: 75

  TriggerDetectPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt
        - TriggerDetect
        - Arn
      Principal: s3.amazonaws.com
      SourceArn: !Join
        - ""
        - - "arn:aws:s3:::"
          - "SOURCE_BUCKET_NAME"

  SrcS3Bucket:
    Type: AWS::S3::Bucket
    DependsOn: TriggerDetectPermission
    Properties:
      BucketName: SOURCE_BUCKET_NAME
      NotificationConfiguration:
        LambdaConfigurations:
          - Event: s3:ObjectCreated:*
            Filter:
              S3Key:
                Rules:
                  - Name: suffix
                    Value: mov
            Function: !GetAtt
              - TriggerDetect
              - Arn

  DstS3Bucket:
    Type: AWS::S3::Bucket
    DependsOn: TriggerDetectPermission
    Properties:
      BucketName: OUTPUT_BUCKET_NAME
```
</div></details>

# 2. 動画ファイルを静止画に分解します

まずは、Lambda関数の入りの部分で、
[Amazon S3][]に置いた動画ファイル(.mov)を[AWS Lambda][]にダウンロードします。

```python
        movie_path = u'/tmp/' + os.path.basename(input_key)
        s3_client.download_file(Bucket=input_bucket, Key=input_key,
                                Filename=movie_path)
```

<details><summary>Amazon S3からダウンロードする - Python スクリプト</summary><div>

```python
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    convert_video_to_images(event)
    return {
        'message': 'finish'
    }


def convert_video_to_images(event):
    try:
        input_bucket = event['Records'][0]['s3']['bucket']['name']
        input_key = unquote_plus(event['Records'][0]['s3']['object']['key'],
                                 encoding='utf-8')
        logger.debug(f"input: {input_bucket}/{input_key}")
        # Download the movie file which was uploaded on a triggered s3 bucket
        movie_path = u'/tmp/' + os.path.basename(input_key)
        s3_client.download_file(Bucket=input_bucket, Key=input_key,
                                Filename=movie_path)
        input_filename, input_ext = os.path.splitext(input_key)
        logger.debug(f"movie: {movie_path}")
        multi_upload_images_and_analyze(movie_path, input_filename)
        return
    except Exception as e:
        logger.error(e)
        logger.error('convert_video_to_images error')
        raise e
```
</div></details>


次にダウンロードした動画ファイル(.mov)を読み込みます。
後で必要となる高さ、幅、フレームレートを取得しておきます。

```python
        cap = cv2.VideoCapture(movie_path)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
```

`ret, frame = cap.read()`で動画ファイルから静止画フレームを読み取り、
オブジェクト検知をする`upload_images_and_analyze()`に渡しています。
処理時間を短縮するために、ThreadPoolExecutor()を使い並列処理をしています。

```python
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while cap.isOpened():
                for _ in range(max_workers):
                    ret, frame = cap.read()
                    executor.submit(upload_images_and_analyze,
                                    input_filename, png_num,
                                    frame, height, width, False)
```

<details><summary>動画ファイルを静止画に分解する - Python スクリプト</summary><div>

```python
def multi_upload_images_and_analyze(movie_path, input_filename):
    try:
        cap = cv2.VideoCapture(movie_path)
        if not cap.isOpened():
            return
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        output_mp4 = f"{input_filename}.mp4"
        output_path = f"/tmp/{output_mp4}"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        mp4 = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        logger.info(f"start detecting all objects:{movie_path}")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            finish = False
            futures = []
            png_num = 0
            while cap.isOpened():
                for _ in range(max_workers):
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        finish = True
                        break
                    future = executor.submit(upload_images_and_analyze,
                                             input_filename, png_num,
                                             frame, height, width, False)
                    futures.append(future)
                    png_num += 1
                write_frames(mp4, futures)
                if finish:
                    break

        logger.info(f"finished detecting all objects:{movie_path}")
        mp4.release()
        mosaic_key = f"{input_filename}/mosaic/{output_mp4}"
        s3.Bucket(output_bucket).upload_file(Filename=output_path,
                                             Key=mosaic_key)
        logger.info(f"uploaded mosaic movie:{output_bucket}/{mosaic_key}")
        cap.release()
        os.remove(movie_path)
    except Exception as e:
        logger.error(e)
        logger.error('multi_upload_images_and_analyze error')
        raise e
```
</div></details>

# 3. 静止画に含まれるオブジェクトを検知します

最初に`upload_images_and_analyze()`は、静止画フレームをファイルに保存します。
保存した静止画ファイルを[Amazon S3][]にアップロードし、
オブジェクト検知をする準備をします。
なぜなら、Amazon Rekognition で検知する対象の画像ファイルは
[Amazon S3][]に置く必要があるためです。

```python
def upload_images_and_analyze(name, frame_id, frame, height, width,
                              each_frame_upload=False):
    try:
        tmp_png = f"/tmp/{frame_id:0=6}.png"
        cv2.imwrite(tmp_png, frame)
        image_file = f"{name}/images/{frame_id:0=6}.png"
        s3.Bucket(output_bucket).upload_file(Filename=tmp_png,
                                             Key=image_file)
        os.remove(tmp_png)
```

[Amazon S3][]に静止画ファイルを置いたら、オブジェクト検知のための関数を呼び出します。

* 顔検知(detect_faces_and_mosaic)
* ナンバープレート検知(detect_plates_and_mosaic)

```python
        # detect faces and mosaic
        frame = detect_faces_and_mosaic(output_bucket, image_file, frame,
                                        height, width)
        # detect license plates and mosaic
        frame = detect_plates_and_mosaic(output_bucket, image_file, frame,
                                         height, width)
        return [frame_id, frame]
```

<details><summary>オブジェクト検知をする - Pythonスクリプト</summary><div>

```python
def upload_images_and_analyze(name, frame_id, frame, height, width,
                              each_frame_upload=False):
    try:
        tmp_png = f"/tmp/{frame_id:0=6}.png"
        cv2.imwrite(tmp_png, frame)
        image_file = f"{name}/images/{frame_id:0=6}.png"
        logger.info(f"start uploading orignal:{output_bucket}/{image_file}")
        s3.Bucket(output_bucket).upload_file(Filename=tmp_png,
                                             Key=image_file)
        logger.info(f"finished uploading orignal:{output_bucket}/{image_file}")
        os.remove(tmp_png)

        # detect faces and mosaic
        frame = detect_faces_and_mosaic(output_bucket, image_file, frame,
                                        height, width)
        # detect license plates and mosaic
        frame = detect_plates_and_mosaic(output_bucket, image_file, frame,
                                         height, width)
        # upload
        if each_frame_upload:
            # write image to tmp directory
            mosaic_png = f"/tmp/mosaic_{frame_id:0=6}.png"
            cv2.imwrite(mosaic_png, frame)

            mosaic_file = f"{name}/mosaic/{frame_id:0=6}.png"
            logger.debug(f"upload mosaic:{output_bucket}/{mosaic_file}")
            s3.Bucket(output_bucket).upload_file(Filename=mosaic_png,
                                                 Key=mosaic_file)
            os.remove(mosaic_png)
        logger.info(f"finished detecting objects:{output_bucket}/{image_file}")
        return [frame_id, frame]
    except Exception as e:
        logger.error(e)
        logger.error('upload_images_and_analyze error')
        raise e
```
</div></details>

# 4. 顔検知をする

顔検知には、[Amazon Rekognition Image][]の[DetectFaces][]を使います。

[Amazon S3][]に置いた画像ファイルに対して顔検知を実施することができます。
`MY_BUCKET`,`PATH_TO_MY_IMAGE`は、
オブジェクト検知をしたい画像ファイルの置き場所に合わせて適切な値を使用してください。

```bash
aws rekognition detect-faces \
  --image '{"S3Object":{"Bucket":"MY_BUCKET","Name":"PATH_TO_MY_IMAGE"}}' \
  --attributes "DEFAULT" \
  --region REGION
```

以下の左のオリジナル画像に対して、推論を実行してみます。
すると、以下のような json データを取得できます。

```JSON
{
    "FaceDetails": [
        {
            "BoundingBox": {
                "Width": 0.25266027450561523,
                "Height": 0.22566114366054535,
                "Left": 0.36638733744621277,
                "Top": 0.23561207950115204
            },
            # ... 省略 ...
            "Confidence": 99.99996185302734
        }
    ]
}
```

顔検知した領域を枠で囲ってみると良い感じに顔検知できてそうです。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/4ba59815-78c9-bab2-32c3-dc3a3082e32d.jpeg" width=50% height=50%><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/4d4f800e-a1a2-a5eb-8ddf-2f441a019940.jpeg" width=50% height=50%>

これと同じことを[AWS Lambda][]で実装します。

```python
def detect_faces_and_mosaic(bucket_name, png_key, frame, height, width):
    try:
        return_faces = rekog.detect_faces(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': png_key}},
            Attributes=['DEFAULT'])
        for face_detail in return_faces['FaceDetails']:
            confidence = face_detail['Confidence']
            if confidence < face_min_confidence:
                continue
            bbox = face_detail['BoundingBox']
            bbox_height, bbox_width, bbox_top, bbox_left = \
                bbox_correction(height, width,
                                math.ceil(height * bbox['Height']),
                                math.ceil(width * bbox['Width']),
                                math.floor(height * bbox['Top']),
                                math.floor(width * bbox['Left']))
            frame = mosaic_area(frame,
                                bbox_height, bbox_width, bbox_top, bbox_left)
```

ここで`bbox_correction()`はバウンディングボックスの調整を行います。
後で説明するナンバープレートのときにも同じことが言えますが、
バウンディングボックスが画像サイズから外れる場合があるため、
バウンディングボックスが画像内におさまるように調整する必要があります。

<details><summary>バウンディングボックス補正 - Python スクリプト</summary><div>

```python
def bbox_correction(height, width, bbox_h, bbox_w, bbox_t, bbox_l):
    if bbox_h <= 0:
        logger.info(f"correct bbox_height:{bbox_h} -> 1")
        bbox_h = 1
    if bbox_h > height:
        logger.info(f"correct bbox_height:{bbox_h} -> height:{height}")
        bbox_h = height

    if bbox_w <= 0:
        logger.info(f"correct bbox_width:{bbox_w} -> 1")
        bbox_w = 1
    if bbox_w > width:
        logger.info(f"correct bbox_width:{bbox_w} -> width:{width}")
        bbox_w = width

    if bbox_t < 0:
        logger.info(f"correct bbox_top:{bbox_t} -> 0")
        bbox_t = 0
    if bbox_t >= height:
        logger.info(f"correct bbox_top:{bbox_t} -> top:{height} - 1")
        bbox_t = height - 1

    if bbox_l < 0:
        logger.info(f"correct bbox_left:{bbox_l} -> 0")
        bbox_l = 0
    if bbox_l >= width:
        logger.info(f"correct bbox_left:{bbox_l} -> top:{width} - 1")
        bbox_l = width - 1

    return bbox_h, bbox_w, bbox_t, bbox_l
```
</div></details>

最後に`mosaic_area()`を呼び出して、検知した領域にモザイク処理をかけます。


<details><summary>顔検知 - Python スクリプト</summary><div>

```python
def detect_faces_and_mosaic(bucket_name, png_key, frame, height, width):
    try:
        return_faces = rekog.detect_faces(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': png_key}},
            Attributes=['DEFAULT'])
        logger.debug(f"detect_faces(bucket:{bucket_name},name:{png_key})")
        if return_faces is None or 'FaceDetails' not in return_faces:
            logger.debug(f"not return_faces or FaceDetails")
            return frame
        for face_detail in return_faces['FaceDetails']:
            if 'Confidence' not in face_detail or \
                    'BoundingBox' not in face_detail:
                logger.debug(f"not Confidence or BoundingBox")
                continue
            confidence = face_detail['Confidence']
            if confidence < face_min_confidence:
                continue
            bbox = face_detail['BoundingBox']
            bbox_height, bbox_width, bbox_top, bbox_left = \
                bbox_correction(height, width,
                                math.ceil(height * bbox['Height']),
                                math.ceil(width * bbox['Width']),
                                math.floor(height * bbox['Top']),
                                math.floor(width * bbox['Left']))
            logger.debug(f"detect_faces(bucket:{bucket_name}, name:{png_key}), "
                         f"height:{bbox_height}, width:{bbox_width}, "
                         f"top:{bbox_top}, left:{bbox_left}")
            frame = mosaic_area(frame,
                                bbox_height, bbox_width, bbox_top, bbox_left)
        return frame
    except Exception as e:
        logger.error(e)
        logger.error('detect_faces_and_mosaic error')
        return frame
```
</div></details>

# 5. ナンバープレート検知をする

ナンバープレート検知は、
[Amazon Rekognition Custom Labelsでカスタムモデルをトレーニングする][]でやったのと同じことを
Python API([DetectCustomLabels][])で実現します。

[Amazon S3][]に置いた画像ファイルに対して顔検知を実施することができます。
`MY_BUCKET`,`PATH_TO_MY_IMAGE`は、
オブジェクト検知をしたい画像ファイルの置き場所に合わせて適切な値を使用してください。

ナンバープレート検知した結果(json)が、顔検知の結果と多少異なるより他は、
顔検知の処理とほぼ同じです。

検知した結果の中で、ナンバープレートのクラス("vehicle_registration_plate")だけを
抽出しています。

<details><summary>ナンバープレート検知 - Python スクリプト</summary><div>

```python
def detect_plates_and_mosaic(bucket_name, png_key, frame, height, width):
    try:
        result = rekog.detect_custom_labels(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': png_key}},
            MinConfidence=plate_min_confidence,
            ProjectVersionArn=project_version_arn)
        if result is None or "CustomLabels" not in result:
            logger.debug(f"CustomLabels don't exist in {png_key}:{result}")
            return frame
        custom_labels = result['CustomLabels']
        target_label_names = ["vehicle_registration_plate"]
        plate_labels = [plate for plate in custom_labels
                        if plate["Name"] in target_label_names]
        for plate_label in plate_labels:
            if "Geometry" not in plate_label:
                continue
            bbox = plate_label['Geometry']['BoundingBox']
            bbox_height, bbox_width, bbox_top, bbox_left = \
                bbox_correction(height, width,
                                math.ceil(height * bbox['Height']),
                                math.ceil(width * bbox['Width']),
                                math.floor(height * bbox['Top']),
                                math.floor(width * bbox['Left']))
            logger.debug(f"detect_custom_labels(bucket:{bucket_name}, "
                         f"name:{png_key}), "
                         f"height:{bbox_height}, width:{bbox_width}, "
                         f"top:{bbox_top}, left:{bbox_left}")
            frame = mosaic_area(frame,
                                bbox_height, bbox_width, bbox_top, bbox_left)
        return frame
    except Exception as e:
        logger.error(e)
        logger.error('detect_plates_and_mosaic error')
        return frame
```
</div></details>

# 6. モザイク処理をかける

モザイク処理は、以下の方の記事を参考にさせていただきました。

[Python, OpenCVで画像にモザイク処理（全面、一部、顔など）](https://note.nkmk.me/python-opencv-mosaic/)

モザイクは、画像を一旦縮小してから拡大して元のサイズに戻すことで実現しています。


<details><summary>モザイク処理 - Python スクリプト</summary><div>

```python
def mosaic_area(img, height, width, top, left, ratio=0.1):
    try:
        dst = img.copy()
        dst[top:top+height, left:left+width] = \
            mosaic(dst[top:top+height, left:left+width], ratio)
        del img
        gc.collect()
        return dst
    except Exception as e:
        logger.error(e)
        logger.error('mosaic area error')
        raise e


def mosaic(img, ratio=0.1):
    try:
        small = cv2.resize(img, None, fx=ratio, fy=ratio)
        return cv2.resize(small, img.shape[:2][::-1],
                          interpolation=cv2.INTER_NEAREST)
    except Exception as e:
        logger.error(e)
        logger.error('mosaic error')
        raise e
```
</div></details>

# 7. 静止画から動画を構成する

動画から抽出した静止画フレームに対して、個人情報領域にモザイク処理(`upload_images_and_analyze`)を施した後、
`cv2.VideoWriter()`で作成した動画ファイルに、その静止画フレームを書き込んでいきます(`write_frames()`)。
すべての静止画フレームを書き込んだ後に`mp4.release()`で終了処理をしておきます。

動画ファイルが完成したら、出力用の[Amazon S3][]バケットにアップロードします。

```python
def multi_upload_images_and_analyze(movie_path, input_filename):
    try:
        cap = cv2.VideoCapture(movie_path)
        output_mp4 = f"{input_filename}.mp4"
        output_path = f"/tmp/{output_mp4}"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        mp4 = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while cap.isOpened():
                for _ in range(max_workers):
                    ret, frame = cap.read()
                    future = executor.submit(upload_images_and_analyze,
                                             input_filename, png_num,
                                             frame, height, width, False)
                    futures.append(future)
                write_frames(mp4, futures)

        mp4.release()
        mosaic_key = f"{input_filename}/mosaic/{output_mp4}"
        s3.Bucket(output_bucket).upload_file(Filename=output_path,
                                             Key=mosaic_key)
        cap.release()
        os.remove(movie_path)
```

```python
def write_frames(mp4, futures):
    concurrent.futures.wait(futures, timeout=None)
    frames_list = [future.result() for
                   future in concurrent.futures.as_completed(futures)]
    frames_list.sort()
    [mp4.write(frame[1]) for frame in frames_list]

```

以上により、ソースS3バケットに動画ファイル(.mov)を置いて、しばらく待つと、
宛先S3バケットに顔・ナンバープレートにモザイク処理が施された動画ファイル(*.mp4)が
保存されます。

# 注意事項.1: 並列処理数について

今回並列処理を4としたのは、[DetectCustomLabels][]に一度に多くのリクエストを送ると
`LimitExceededException`エラーが返ってくるためです(5以上にすると時々エラーになる)。
[Limits in Amazon Rekognition Custom Labels][]や[Amazon Rekognition endpoints and quotas][]によると、
[Create case][]を使うと制限を変更できるみたいなのですが、変更対象のAPIとして[DetectCustomLabels][]を
選択できないため、今はまだ制限をへ変更できないみたいです。

# 注意事項.2: 元の動画ファイルとLambdaでの処理時間について

顔・ナンバープレート検知する元の動画ファイルとしては、
1080p@30fps の動画ファイルで録画時間が7-8(sec)くらいが、
[AWS Lambda][]の動作リミットである900(sec)にギリギリ収まると思います。
私は安全目に5(sec)程度の動画ファイル(1080p@30fps)でテストしましたが、440-460(sec)くらいでした。
もちろん解像度によっても処理時間は異なると思いますし、
フレームレートを落とせばその分だけ処理時間は確実に短くなるはずです。

# 注意事項.3: モザイク処理後の動画ファイルについて

あと、注意点としては、元の映像をH.264でエンコードしていた場合でも、
[AWS Lambda][]で静止画フレームから動画ファイルを構成するときに、
H.264でエンコードしていないため、モザイク処理後の動画ファイル(.mp4)が
かなり大きくなります。
例えば、iPhoneXで撮影したH.264エンコードされた5(sec), 2.2MBの動画ファイル(.mov)は、
本モザイク処理をすると、270MBになりました。
[AWS Lambda][]ではなくH.264エンコードが利用できる環境で処理するのが良いように思います。

# 注意事項.4: 料金について

推論のためにモデルを動作させるのに必要な料金は US$4.00/hour です。
また、5(sec)の動画ファイルにモザイク処理を施すのに必要な時間は大体7-8(min)です。
とすると、1時間の動画ファイルにモザイク処理を施すのに必要な時間は約108時間です。
つまり、1時間の動画ファイルにモザイク処理を施すのに必要な料金は、US$432 == 45,000~50,000円 ほどです。
非現実的な料金ですね。ですので、動画の中のオブジェクト検知をする場合は、
[Amazon Rekognition Custom Labels][]以外の方法を考えた方が良さそうです。

# まとめ

以上で、**Amazon Rekognition で動画中の顔・ナンバープレートにモザイクをかける**ことができました。
注意事項でも書きましたが、やってみると動画のオブジェクト検知には、
[AWS Lambda][], [Amazon Rekognition Custom Labels][]はあまり適していないと感じました。

AWSのAIサービスは、とても使いやすくて簡単にやりたいことが実現できると思います。
ただし、少し凝ったことがしたいと思ったときには、MLサービスなどを検討する必要があるのかも。

例えば、GPU付きの[Amazon EC2][]でH.264エンコード、推論処理をして、
[Amazon SageMaker][]でモデルのトレーニングをするということが考えられます。

奥が深いですね。楽しくなってきました。
以上です。ありがとうございました。

最後に実装したLambda関数を載せておきます。


<details><summary>AWS Lambda Function - Python スクリプト</summary><div>

```python
import os
import gc
import math
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import cv2
import boto3
import logging
from urllib.parse import unquote_plus


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
rekog = boto3.client('rekognition')

output_bucket = os.environ['OUTPUT_BUCKET']
project_version_arn = os.environ['PROJECT_VERSION_ARN']
max_workers = int(os.environ['MAX_WORKERS'])
face_min_confidence = int(os.environ['FACE_MIN_CONFIDENCE'])
plate_min_confidence = int(os.environ['LICENSE_PLATE_MIN_CONFIDENCE'])


def lambda_handler(event, context):
    logger.debug("Log group name:", context.log_group_name)
    logger.debug("Request ID:", context.aws_request_id)
    logger.debug("Mem. limits(MB):", context.memory_limit_in_mb)
    logger.info(f"MAX_WORKERS: {max_workers}")
    logger.info(f"FACE_MIN_CONFIDENCE: {face_min_confidence}")
    logger.info(f"LICENSE_PLATE_MIN_CONFIDENCE: {plate_min_confidence}")
    convert_video_to_images(event)
    return {
        'message': 'finish rekognition'
    }


def convert_video_to_images(event):
    try:
        input_bucket = event['Records'][0]['s3']['bucket']['name']
        input_key = unquote_plus(event['Records'][0]['s3']['object']['key'],
                                 encoding='utf-8')
        logger.debug(f"input: {input_bucket}/{input_key}")
        # Download the movie file which was uploaded on a triggered s3 bucket
        movie_path = u'/tmp/' + os.path.basename(input_key)
        s3_client.download_file(Bucket=input_bucket, Key=input_key,
                                Filename=movie_path)
        input_filename, input_ext = os.path.splitext(input_key)
        logger.debug(f"movie: {movie_path}")
        multi_upload_images_and_analyze(movie_path, input_filename)
        return
    except Exception as e:
        logger.error(e)
        logger.error('convert_video_to_images error')
        raise e


def write_frames(mp4, futures):
    concurrent.futures.wait(futures, timeout=None)
    frames_list = [future.result() for
                   future in concurrent.futures.as_completed(futures)]
    frames_list.sort()
    [mp4.write(frame[1]) for frame in frames_list]


def multi_upload_images_and_analyze(movie_path, input_filename):
    try:
        cap = cv2.VideoCapture(movie_path)
        if not cap.isOpened():
            return
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        output_mp4 = f"{input_filename}.mp4"
        output_path = f"/tmp/{output_mp4}"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        mp4 = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        logger.info(f"start detecting all objects:{movie_path}")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            finish = False
            futures = []
            png_num = 0
            while cap.isOpened():
                for _ in range(max_workers):
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        finish = True
                        break
                    future = executor.submit(upload_images_and_analyze,
                                             input_filename, png_num,
                                             frame, height, width, False)
                    futures.append(future)
                    png_num += 1
                write_frames(mp4, futures)
                if finish:
                    break

        logger.info(f"finished detecting all objects:{movie_path}")
        mp4.release()
        mosaic_key = f"{input_filename}/mosaic/{output_mp4}"
        s3.Bucket(output_bucket).upload_file(Filename=output_path,
                                             Key=mosaic_key)
        logger.info(f"uploaded mosaic movie:{output_bucket}/{mosaic_key}")
        cap.release()
        os.remove(movie_path)
    except Exception as e:
        logger.error(e)
        logger.error('multi_upload_images_and_analyze error')
        raise e


def upload_images_and_analyze(name, frame_id, frame, height, width,
                              each_frame_upload=False):
    try:
        tmp_png = f"/tmp/{frame_id:0=6}.png"
        cv2.imwrite(tmp_png, frame)
        image_file = f"{name}/images/{frame_id:0=6}.png"
        logger.info(f"start uploading orignal:{output_bucket}/{image_file}")
        s3.Bucket(output_bucket).upload_file(Filename=tmp_png,
                                             Key=image_file)
        logger.info(f"finished uploading orignal:{output_bucket}/{image_file}")
        os.remove(tmp_png)

        # detect faces and mosaic
        frame = detect_faces_and_mosaic(output_bucket, image_file, frame,
                                        height, width)
        # detect license plates and mosaic
        frame = detect_plates_and_mosaic(output_bucket, image_file, frame,
                                         height, width)
        # upload
        if each_frame_upload:
            # write image to tmp directory
            mosaic_png = f"/tmp/mosaic_{frame_id:0=6}.png"
            cv2.imwrite(mosaic_png, frame)

            mosaic_file = f"{name}/mosaic/{frame_id:0=6}.png"
            logger.debug(f"upload mosaic:{output_bucket}/{mosaic_file}")
            s3.Bucket(output_bucket).upload_file(Filename=mosaic_png,
                                                 Key=mosaic_file)
            os.remove(mosaic_png)
        logger.info(f"finished detecting objects:{output_bucket}/{image_file}")
        return [frame_id, frame]
    except Exception as e:
        logger.error(e)
        logger.error('upload_images_and_analyze error')
        raise e


def detect_faces_and_mosaic(bucket_name, png_key, frame, height, width):
    try:
        return_faces = rekog.detect_faces(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': png_key}},
            Attributes=['DEFAULT'])
        logger.debug(f"detect_faces(bucket:{bucket_name},name:{png_key})")
        if return_faces is None or 'FaceDetails' not in return_faces:
            logger.debug(f"not return_faces or FaceDetails")
            return frame
        for face_detail in return_faces['FaceDetails']:
            if 'Confidence' not in face_detail or \
                    'BoundingBox' not in face_detail:
                logger.debug(f"not Confidence or BoundingBox")
                continue
            confidence = face_detail['Confidence']
            if confidence < face_min_confidence:
                continue
            bbox = face_detail['BoundingBox']
            bbox_height, bbox_width, bbox_top, bbox_left = \
                bbox_correction(height, width,
                                math.ceil(height * bbox['Height']),
                                math.ceil(width * bbox['Width']),
                                math.floor(height * bbox['Top']),
                                math.floor(width * bbox['Left']))
            logger.debug(f"detect_faces(bucket:{bucket_name}, name:{png_key}), "
                         f"height:{bbox_height}, width:{bbox_width}, "
                         f"top:{bbox_top}, left:{bbox_left}")
            frame = mosaic_area(frame,
                                bbox_height, bbox_width, bbox_top, bbox_left)
        return frame
    except Exception as e:
        logger.error(e)
        logger.error('detect_faces_and_mosaic error')
        return frame


def detect_plates_and_mosaic(bucket_name, png_key, frame, height, width):
    try:
        result = rekog.detect_custom_labels(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': png_key}},
            MinConfidence=plate_min_confidence,
            ProjectVersionArn=project_version_arn)
        if result is None or "CustomLabels" not in result:
            logger.debug(f"CustomLabels don't exist in {png_key}:{result}")
            return frame
        custom_labels = result['CustomLabels']
        target_label_names = ["vehicle_registration_plate"]
        plate_labels = [plate for plate in custom_labels
                        if plate["Name"] in target_label_names]
        for plate_label in plate_labels:
            if "Geometry" not in plate_label:
                continue
            bbox = plate_label['Geometry']['BoundingBox']
            bbox_height, bbox_width, bbox_top, bbox_left = \
                bbox_correction(height, width,
                                math.ceil(height * bbox['Height']),
                                math.ceil(width * bbox['Width']),
                                math.floor(height * bbox['Top']),
                                math.floor(width * bbox['Left']))
            logger.debug(f"detect_custom_labels(bucket:{bucket_name}, "
                         f"name:{png_key}), "
                         f"height:{bbox_height}, width:{bbox_width}, "
                         f"top:{bbox_top}, left:{bbox_left}")
            frame = mosaic_area(frame,
                                bbox_height, bbox_width, bbox_top, bbox_left)
        return frame
    except Exception as e:
        logger.error(e)
        logger.error('detect_plates_and_mosaic error')
        return frame


def mosaic_area(img, height, width, top, left, ratio=0.1):
    try:
        dst = img.copy()
        dst[top:top+height, left:left+width] = \
            mosaic(dst[top:top+height, left:left+width], ratio)
        del img
        gc.collect()
        return dst
    except Exception as e:
        logger.error(e)
        logger.error('mosaic area error')
        raise e


def mosaic(img, ratio=0.1):
    try:
        small = cv2.resize(img, None, fx=ratio, fy=ratio)
        return cv2.resize(small, img.shape[:2][::-1],
                          interpolation=cv2.INTER_NEAREST)
    except Exception as e:
        logger.error(e)
        logger.error('mosaic error')
        raise e


def bbox_correction(height, width, bbox_h, bbox_w, bbox_t, bbox_l):
    if bbox_h <= 0:
        logger.info(f"correct bbox_height:{bbox_h} -> 1")
        bbox_h = 1
    if bbox_h > height:
        logger.info(f"correct bbox_height:{bbox_h} -> height:{height}")
        bbox_h = height

    if bbox_w <= 0:
        logger.info(f"correct bbox_width:{bbox_w} -> 1")
        bbox_w = 1
    if bbox_w > width:
        logger.info(f"correct bbox_width:{bbox_w} -> width:{width}")
        bbox_w = width

    if bbox_t < 0:
        logger.info(f"correct bbox_top:{bbox_t} -> 0")
        bbox_t = 0
    if bbox_t >= height:
        logger.info(f"correct bbox_top:{bbox_t} -> top:{height} - 1")
        bbox_t = height - 1

    if bbox_l < 0:
        logger.info(f"correct bbox_left:{bbox_l} -> 0")
        bbox_l = 0
    if bbox_l >= width:
        logger.info(f"correct bbox_left:{bbox_l} -> top:{width} - 1")
        bbox_l = width - 1

    return bbox_h, bbox_w, bbox_t, bbox_l
```
</div></details>


# Amazon Rekognition で動画中の顔・ナンバープレートにモザイクをかける - 全記事

**Overview:** [Amazon Rekognition で動画中の顔・ナンバープレートにモザイクをかける]()

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
