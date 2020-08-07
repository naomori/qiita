# はじめに

Raspberry Pi だと[Raspberry Pi OS][](以前はRaspbian)をインストールすることを
最初に考えると思いますが、[Ubuntu][]をインストールすることもできます。

使おうと思っているツールやライブラリによっては、[Raspberry Pi OS][]をサポートしていないけど、
[Ubuntu][]はサポートしているということもあります(例えば [kubernetes][] とか)。

そこで、Raspberry Pi 4 Model B に[Ubuntu 20.04 LTS(64-bit) for Raspbeery Pi][]をインストールします。
また、ときにはGUI環境も必要になることもあるかと思いますので、GUI環境も構築します。
(例えば [Google Colab][] のインスタンスを維持させたい場合とか。)

# 1. Ubuntu のインストール

[Install Ubuntu Server on a Raspberry Pi 2,3 or 4][]にRaspberry Piのイメージがあるので、
[Ubuntu 20.04 LTS(64-bit) for Raspbeery Pi][]をダウンロードします。

OSイメージのダウンロードが完了したら、解凍しmicroSDカードに書き込みます。

```bash
~/Downloads ❯❯❯ xz -dv ubuntu-20.04-preinstalled-server-arm64+raspi.img.xz
ubuntu-20.04-preinstalled-server-arm64+raspi.img.xz (1/1)
  100 %     667.0 MiB / 3,054.4 MiB = 0.218    92 MiB/s       0:33
```

OSイメージの書き込みには、[こちら](https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#2-prepare-the-sd-card)にもある通りに、Raspberry Pi imager というツールがあるそうですが、
私のノートPCはUbuntuなので、`dd`コマンドで書き込みます。書き込みツールは何でも構いません。

```bash
~/Downloads ❯❯❯ sudo dd if=ubuntu-20.04-preinstalled-server-arm64+raspi.img of=/dev/mmcblk0 status=progress
3201147392 bytes (3.2 GB, 3.0 GiB) copied, 622 s, 5.1 MB/s
6255474+0 records in
6255474+0 records out
3202802688 bytes (3.2 GB, 3.0 GiB) copied, 627.603 s, 5.1 MB/s
```

# 2. 事前設定

設定は簡便化のため、ヘッドレス(ディスプレイ・キーボード接続なし)で行います。
その方法は[How to install Ubuntu on your Raspberry Pi][]に記載されているので、簡単です。
また、[こちら](https://rabbit-note.com/2020/06/06/raspberry-pi-ubuntu-headless-install/)も参考になります。

OSイメージを書き込んだmicroSDカードを抜き差しすると、以下のパーティションが自動でマウントされます。

```bash
~/Downloads ❯❯❯ df -k
...
/dev/mmcblk0p2   2754000   1813920    780472  70% /media/$USER/writable
/dev/mmcblk0p1    258095     62017    196079  25% /media/$USER/system-boot
```

IPアドレス、DNSサーバの設定をします。

```bash
~/Downloads ❯❯❯ cd /media/$USER/system-boot
/m/n/system-boot ❯❯❯ vim network-config
```

```config
version: 2
ethernets:
  eth0:
    dhcp4: no
    addresses: [<IP-ADDRESS>"/"<PREFIX-LENGTH>]
    gateway4: <GATEWAY-IP-ADDRESS>
    nameservers:
      addresses: [<DNS1-IP-ADDRESS>,<DNS2-IP-ADDRESS>]
    optional: true
```

次にホスト名の設定をします。

```bash
/m/n/system-boot ❯❯❯ vim user-data
```

```config
fqdn: <HOSTNAME>
chpasswd:
  expire: false
  list:
  - ubuntu:ubuntu
```

ちなみにログインするためのアカウントは以下です。

* user: ubuntu
* pass: ubuntu

# 3. ログインしたらすること

作成したmicroSDカードをラズパイに挿入し、ラズパイの電源を入れたら
sshでログイン(user:ubuntu,pass:ubuntu)します。
あと、手元のPCで作成したSSHの秘密鍵のパスフレーズを無しにした公開鍵を
ラズパイにコピーして、ログインしやすくしておきます。

```bash
~/Downloads ❯❯❯ ssh ubuntu@<IP-ADDRESS>
~/Downloads ❯❯❯ scp ~/.ssh/id_rsa.pub ubuntu@<IP-ADDRESS>:
```

```bash
ubuntu@colab:~$ cat id_rsa.pub >> .ssh/authorized_keys
ubuntu@colab:~$ rm -f id_rsa.pub
```

接続したら、まずはパッケージを更新しておきます。

```bash
ubuntu@colab:~$ sudo apt update && sudo apt upgrade -y
```

時間の設定もしておきます。

```bash
ubuntu@colab:~$ sudo timedatectl set-timezone Asia/Tokyo
ubuntu@colab:~$ timedatectl
               Local time: Mon 2020-07-06 22:13:48 JST
           Universal time: Mon 2020-07-06 13:13:48 UTC
                 RTC time: n/a
                Time zone: Asia/Tokyo (JST, +0900)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

# 4. GUI環境の構築

[こちら](https://gihyo.jp/admin/serial/01/ubuntu-recipe/0624?page=1)を参考に[Lubuntu][]をインストールします。
なぜ、[Lubuntu][]かと言うと[こちら](https://pc-freedom.net/basic/heavy-desktop-environment-ranking/)によると、
[Lubuntu][]が最も軽いデスクトップとのことだからです。

```bash
ubuntu@colab:~$ git clone https://github.com/wimpysworld/desktopify.git
ubuntu@colab:~$ cd desktopify/
ubuntu@colab:~/desktopify$ ./desktopify --help

Usage
  ./desktopify --de <desktop environment>

Available desktop environments are
  lubuntu
  kubuntu
  ubuntu
  ubuntu-budgie
  ubuntu-kylin
  ubuntu-mate
  ubuntu-studio
  xubuntu

You can also pass the optional --oem option which will run a setup
wizard on the next boot.
```

```bash
ubuntu@colab:~/desktopify$ sudo ./desktopify --de lubuntu
```

また、ラズパイとデスクトップ共有をするために、
[Lubuntu][]に[Xrdp](http://xrdp.org/)(リモートデスクトップサーバ)をインストールします。

```bash
ubuntu@colab:~$ sudo apt install -y xrdp
```

さらに、Webブラウザもインストールしておきます。

```bash
ubuntu@colab:~$ sudo apt install -y chromium-browser
```

# まとめ

以上で、ラズパイにUbuntuをインストールし、基本的なGUI環境を構築できました。
[Google Colab][]とのセッション維持のためにGUI環境やブラウザをインストールしたラズパイを使えますし、
[kubernetes][]の環境をローカルで試してみたい場合にはGUIなしのラズパイも使えます。
用途に応じて、GUIの有無を自由にできるのも便利です。

# References

* [Raspberry Pi に Ubuntu 20.04 をヘッドレスインストール](https://rabbit-note.com/2020/06/06/raspberry-pi-ubuntu-headless-install/)

[Raspberry Pi OS]: https://www.raspberrypi.org/downloads/raspberry-pi-os/
[Ubuntu]: https://ubuntu.com/
[kubernetes]: https://kubernetes.io/
[Ubuntu 20.04 LTS(64-bit) for Raspbeery Pi]: https://ubuntu.com/download/raspberry-pi/thank-you?version=20.04&architecture=arm64+raspi
[Install Ubuntu Server on a Raspberry Pi 2,3 or 4]: https://ubuntu.com/download/raspberry-pi
[How to install Ubuntu on your Raspberry Pi]: https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#1-overview
[Lubuntu]: https://lubuntu.me/focal-released/
[Google Colab]: https://colab.research.google.com/
