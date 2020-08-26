# はじめに

Ubuntu 20.04 LTS で Magic Trackpad 2 を使っていますが、
以下の方のように、ときどきカーソルが固まってしまいます。

* [UbuntuデスクトップでMagic Trackpad 2を快適に使う](https://blog.hanhans.net/2019/03/03/ubuntu-magictrackpad2/)

Magic Trackpad 2 のバッテリー容量が減少してくると、
電池消費を抑えるために接続を切断するという動作をしていたがために、
カーソルが固まってしまっていたのですね。

そこで、この方の対応のように、Magic Trackpad 2 だけを対象として、
電池消費を抑える機能をOFFにするパッチをカーネルに当てて、対応しようと思います。

# 1.Ubuntu Kernel ビルド用のDockerコンテナを用意する

こちらが参考になります。

* [Ubuntu Weekly Recipe - 第333回 カーネルパッケージをビルドしよう](https://gihyo.jp/admin/serial/01/ubuntu-recipe/0333)

Ubuntuカーネルをビルドする環境は、デスクトップ環境が汚れると嫌なので、
Docker上に構築することにします。

```bash
docker pull ubuntu:focal
docker run -it --name ubuntu ubuntu:focal bash
```

Dockerコンテナ上で、カーネルビルドに必要なパッケージをインストールします。

```bash
apt update && apt upgrade -y
apt install -y git fakeroot build-essential libncurses5 libncurses5-dev libelf-dev binutils-dev devscripts u-boot-tools
sed 's/# deb-src/deb-src/g' -i /etc/apt/sources.list
apt update
apt-get -y build-dep linux
```

# 2.Ubuntu Kernel にパッチを当てます

カーネルソースをダウンロードします。

```bash
cd
git clone git://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/focal
cd focal
```

Ubuntuデスクトップのカーネルバージョンが以下なので、

```bash
uname -a
Linux ryzen 5.4.0-42-generic #46-Ubuntu SMP Fri Jul 10 00:24:02 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

同じバージョンのカーネルソースをcheckoutします。

```bash
git tag -l Ubuntu-5.4.0-42*
```
```
Ubuntu-5.4.0-42.46
```

```bash
git checkout -b focal+mt2patch Ubuntu-5.4.0-42.46
```

パッチを適用します。

```bash
apt install -y vim
vim drivers/hid/hid-input.c
```
```bash
git diff
```
```diff
diff --git a/drivers/hid/hid-input.c b/drivers/hid/hid-input.c
index dea9cc65bf80..194231ffabee 100644
--- a/drivers/hid/hid-input.c
+++ b/drivers/hid/hid-input.c
@@ -310,6 +310,9 @@ static const struct hid_device_id hid_battery_quirks[] = {
        { HID_BLUETOOTH_DEVICE(USB_VENDOR_ID_APPLE,
                USB_DEVICE_ID_APPLE_ALU_WIRELESS_ANSI),
          HID_BATTERY_QUIRK_PERCENT | HID_BATTERY_QUIRK_FEATURE },
+       { HID_BLUETOOTH_DEVICE(USB_VENDOR_ID_APPLE,
+               USB_DEVICE_ID_APPLE_MAGICMOUSE),
+         HID_BATTERY_QUIRK_IGNORE },
        { HID_BLUETOOTH_DEVICE(USB_VENDOR_ID_ELECOM,
                USB_DEVICE_ID_ELECOM_BM084),
          HID_BATTERY_QUIRK_IGNORE },
```

# 3.Ubuntu Kernel をビルドする

こちらの方の記事を参考にビルドします。

* [Ubuntu Weekly Recipe - 第526回　Ubuntuで最新のカーネルをお手軽にビルドする方法](https://gihyo.jp/admin/serial/01/ubuntu-recipe/0526?page=2)

まずはホストのUbuntuからconfigファイルをdockerにコピーします。

```bash
docker cp /boot/config-5.4.0-42-generic ubuntu:/tmp/
```

dockerコンテナ上でコピーした設定ファイルを移動して、設定を反映させます。

```bash
mkdir ../build
cp /tmp/config-5.4.0-42-generic ../build/.config
scripts/config --file ../build/.config --disable DEBUG_INFO
make O=../build/ oldconfig
```

カーネルとモジュールをビルドします。

```bash
time make -j 32 O=../build/ LOCALVERSION=-mt2patch
```
```
real    5m32.215s
user    140m10.856s
sys     16m43.152s
```
```bash
time make modules -j 32 O=../build/ LOCALVERSION=-mt2patch
```
```
real    0m27.762s
user    1m30.672s
sys     1m41.236s
```
```bash
time make bindeb-pkg -j 32 O=../build/ LOCALVERSION=-mt2patch
```
```
real    1m3.661s
user    4m49.134s
sys     2m14.784s
```

Ryzen 9 3950x は爆速ですね...

# 4.Ubuntu Kernel をインストールする

ビルドした結果、１つ上のディレクトリにパッケージが出来ています。

```bash
ls -l ../*.deb
-rw-r--r-- 1 root root 11424784 Aug 26 17:45 ../linux-headers-5.4.44-mt2patch_5.4.44-mt2patch-1_amd64.deb
-rw-r--r-- 1 root root 61014544 Aug 26 17:45 ../linux-image-5.4.44-mt2patch_5.4.44-mt2patch-1_amd64.deb
-rw-r--r-- 1 root root  1071376 Aug 26 17:45 ../linux-libc-dev_5.4.44-mt2patch-1_amd64.deb
```

ここで、ファイル名が`5.4.44-mt2patch`となっているのは、
カーネルコンフィグのバージョンが`CONFIG_VERSION_SIGNATURE="Ubuntu 5.4.0-42.46-generic 5.4.44"`
となっていたからでしょうか。

これらをホスト側にコピーし、インストールします。

```bash
docker cp ubuntu:/root/linux-headers-5.4.44-mt2patch_5.4.44-mt2patch-1_amd64.deb .
docker cp ubuntu:/root/linux-image-5.4.44-mt2patch_5.4.44-mt2patch-1_amd64.deb .
docker cp ubuntu:/root/linux-libc-dev_5.4.44-mt2patch-1_amd64.deb .
```

```bash
sudo apt install ./linux-headers-5.4.44-mt2patch_5.4.44-mt2patch-1_amd64.deb
sudo apt install ./linux-image-5.4.44-mt2patch_5.4.44-mt2patch-1_amd64.deb
sudo apt install ./linux-libc-dev_5.4.44-mt2patch-1_amd64.deb
```

完了です。これから、カーソルが固まらないと良いな。

# 元のカーネルに戻したいとき

自分でビルドしたカーネルが思うように動かなかった時、
元のカーネルでブートしたくなると思います。
そのときは、`/etc/default/grub`を修正します。

```bash
sudo vim /etc/default/grub
```

修正するのは、`GRUB_TIMEOUT_STYLE=menu`にして、タイムアウト時間を伸ばすことです。
これで、ブート時に使用するカーネルを選択できるようになります。

```diff
--- grub.ucf-dist       2020-08-02 19:43:53.512717712 +0900
+++ grub        2020-08-26 17:25:45.283739309 +0900
@@ -4,8 +4,9 @@
 #   info -f grub -n 'Simple configuration'

 GRUB_DEFAULT=0
-GRUB_TIMEOUT_STYLE=hidden
-GRUB_TIMEOUT=0
+#GRUB_TIMEOUT_STYLE=hidden
+GRUB_TIMEOUT_STYLE=menu
+GRUB_TIMEOUT=5
 GRUB_DISTRIBUTOR=`lsb_release -i -s 2> /dev/null || echo Debian`
 GRUB_CMDLINE_LINUX_DEFAULT=""
 GRUB_CMDLINE_LINUX=""
```

修正が完了したら、grub を更新しておきます。

```bash
sudo update-grub
```
