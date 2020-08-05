# はじめに

[Google Colab][]をDeep LearningのTrainingで使いたいです。
なぜかというと、[Google Colab][]では、[Tesla P100][]という90万円近くするGPUをサポートしており、
Deep LearningのTrainingに最適なんじゃないかと思ったからです。
ちなみに、[Google Colab][]だとこのGPUを毎回使えるわけではないのですが、
[Colab Pro][]では、このGPUを毎回使えるとのことです。
お値段は **$9.99/month** で、機材費や電気代を考えるとお得ではないでしょうか。
やめたいときにやめられますので、今月は使わないなと思ったら一時的にやめられます。

一方で、[Google Colab][],[Colab Pro][]の両方とも、Webインターフェイスでインスタンスを生成してから、
ブラウザで90分間、何も操作がないと、インスタンスがリセットされてしまいます。
そこで、ブラウザ(Google Chrome/Chromium)のアドオン([Super Auto Refresh Plus][])を使って、
自動でリロードさせるようにします。こうすることで、インスタンスがリセットされなくなります。

ただし、ラップトップやデスクトップPCを一日中稼働させておかないといけないというのは、
電気代面でも、他の作業がしたくなった場合でも、とても不便です。

そこで、Raspberry Pi 4 Model B に[Ubuntu 20.04 LTS(64-bit) for Raspbeery Pi][]をインストールして、
GUI環境を構築し常時稼働させ、[Google Colab][]に接続する専用ノードにしようと思います。

ただ、ブラウザだけで作業するのは、少し不便です。
スクリプトをいくつか同時に実行したり、CPU/GPUの使用状況を確認したり、
スクリプトを走らせながら、次に動かすスクリプトを編集したりしたいなとか思ってしまいます。
ですので、[Google Colab][]に ssh ログインできれば、そのようなことができるはずです
また、sshアクセス元で[tmux][]などの端末多重化ソフトウェアを利用して、
処理を継続したい場合は detach するなどできるので便利なはずです。

[Google Colab][]にアクセスする方法については、
こちらの[Google Colaboratoryにsshログインをしてお手軽GPU実験環境を作ってみた][]を
参考にしようと思いましたが、ngrok というサービスを使っていて、しかもそれが遅いらしいです。
ということで、[Colabをshellから使う][]を参考にさせていただきまして、
自宅の Raspberry Pi 4 Model B に外部からsshログインできる環境を作って、
[Google Colab][]から自宅の Raspberry Pi 4 Model B にSSHトンネルを通したいと思います。

# 0.事前準備

## 0-1. Ubuntu Server on Raspberry Pi 4 Model B

Raspberry Pi だと[Raspberry Pi OS][](以前はRaspbian)を最初に考えますが、
今回はUbuntu 20.04-LTS(64bit)をインストールすることにします。特に理由はありません。
[Install Ubuntu Server on a Raspberry Pi 2,3 or 4][]にRaspberry Piのイメージがあるので、
これをインストールします。

このインストール方法や設定については、この記事では省略します（別途記事を書きます）。

## 0-2. 自宅ルータに外部からのsshアクセス用に穴を通す

これは、利用しているルータ次第です。
私は、自宅のルータとして[Yamaha RTX830][]を使っているので、以下のようにポート転送を設定します。

```config
ip pp secure filter in ... <設定するフィルタ番号>
ip filter <設定するフィルタ番号> pass * <自宅サーバ-ローカルIPアドレス> tcp * 22
nat descriptor type 1000 masquerade
nat descriptor masquerade static 1000 2 <自宅サーバ-ローカルIPアドレス> tcp <公開するポート番号>=22
```

ちなみに、[Google Domains](https://domains.google/)でドメインを取得し、
[Yamaha RTX830][]上でLuaスクリプトを定期的に実行して、DDNSを更新しています。
こうすることで、登録したドメイン名で、外部から自宅ルータにアクセスできるようになります。
もちろん、他のドメインサービスでも構いません。

**0-image**

# 1. Google Colaboratory のインスタンスを生成します

**1-image**

## 1-1. Raspberry Pi に接続してデスクトップ共有します

手元のLaptop(Ubuntu)の[Remmina][]アプリから、
RDPプロトコルでRaspberry Piに接続して、デスクトップ共有します。

Ubuntuなら[Remmina][]はaptのパッケージに含まれているので、簡単にインストールできます。

```bash
sudo apt install -y remmina
```

ちなみに、どのような方法でデスクトップ共有しても構いません。
Windows や Mac の Remote Desktop や VNC でも出来るはずです。

## 1-2. Raspberry Pi のブラウザで Google Colab にアクセスします

`Internet -> Chromium Web Browser`でブラウザを開き、Google Colab にアクセスします。
(ターミナルで`chromium-browser`コマンドを実行しても良いです)
`Runtime -> Change runtime type` で以下のように設定します。

- Hardware accelerator: **GPU**
- Runtime shape: **High-RAM**

これで、[Tesla P100][]と25.0GBのメモリを持つインスタンスが生成されます。

そして、ブラウザのアドオン[Super Auto Refresh Plus][]を有効化します。
最初のReloadタイミングで、ポップアップが上がってくるのですが、
これは手動でクリックする必要があります。
初回以降のReloadタイミングはクリックする必要がありません。
私の場合は、Reload周期を10minにしています。
それくらいだと、以降の作業が終わるくらいに、初回のReloadタイミングが来るので、
Reloadタイミング待ちの時間がなくて良いと思います。

# 2. Google Colaboratory でSSHサーバを起動します

続けて、ブラウザで以下のスクリプトを実行します。

```Python
#1.import necessary packages
import random, string, urllib.request, json, getpass

#2.Generate root password
password = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(20))

#3.Setup sshd
! apt-get install -qq -o=Dpkg::Use-Pty=0 openssh-server pwgen > /dev/null

#4.Set root password
! echo root:$password | chpasswd
! mkdir -p /var/run/sshd
! echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
! echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
! echo "LD_LIBRARY_PATH=/usr/lib64-nvidia" >> /root/.bashrc
! echo "export LD_LIBRARY_PATH" >> /root/.bashrc

#5.Run sshd
get_ipython().system_raw('/usr/sbin/sshd -D &')

#6.Print root password
print(f'Root password: {password}')
```

このスクリプトで実行していることは以下です。

1. 必要なパッケージを import します。
2. Google Colab で立ち上げるSSHサーバにアクセスするためのrootパスワードを生成します。
    - 英文字と数字からランダムに20文字を選び、それをパスワードとしています。
3. SSHサーバとパスワード生成器をインストールします。
    - `-qq`と[-o=Dpkg::Use-Pty=0で余分な出力を抑制](https://askubuntu.com/questions/258219/how-do-i-make-apt-get-install-less-noisy)します。
4. 2.で生成したパスワードをrootに設定し、SSHサーバ用の設定もします。
    - SSHサーバはrootでのログインOK,パスワード認証OKとします。
    - nvidia用のライブラリパスも通しておきます。
5. SSHサーバを起動します。
    - [get_ipython][]でシェルインスタンスを取得します。
    - [interactiveshell][]の`system_raw`でコマンドを実行します。
6. **rootパスワードを表示します。**
    - **このパスワードは、後で[Google Colab][]にsshログインするために使用するので重要です。**
    - **このパスワードはコピペしておきましょう。**


ちなみに、[github][]に[Google Colab][]で実行するJupyter Notebookを置いておくと、
ブラウザ上からその Notebook を開けば、[Google Colab][]に接続して、
すぐに Notebook 内のスクリプトを実行できるようになるので、便利です。

# 3. 自宅のラズパイからGoogle ColabにSSHトンネルを張ります

**2-image**

ブラウザで以下のスクリプトを実行します。

```python
#1.prepare a script that shows password for raspberry pi
proxy_password = '<ラズパイにSSHログインするためのパスワード>'
!echo "echo $proxy_password" > proxy_password.sh
!chmod +x proxy_password.sh

#2.create ssh tunneling
get_ipython().system_raw(
    'export SSH_ASKPASS=/content/proxy_password.sh; \
     export DISPLAY=dummy:0; \
     setsid ssh -p <自宅ルータで公開しているポート番号> -oStrictHostKeyChecking=no -fNR <トンネル入り口のポート番号>:localhost:22 ubuntu@<公開している自宅のFQDN> &')
```

このスクリプトで実行していることは以下です。

1. パスワード表示スクリプトを作成します。
    - プロンプトからのパスワード入力はできないので、パスワードを出力するスクリプトを用意します。
2. SSHトンネルを作成します。
    - パスワードの受け渡しは`SSH_ASKPASS`を利用します。
    - `-oStrictHostKeyChecking=no`で入力しないといけない状況を回避します。
    - `-R`オプションを使って、ラズパイから[Google Colab][]へトンネルを張ります

最後のsshコマンドは、例えば以下のようになります。

* 自宅ルータで公開しているポート番号: 10022
* トンネル入口のポート番号: 20022
* 公開している自宅のFQDN: hoge.net

```bash
setsid ssh -p 10022 -oStrictHostKeyChecking=no -fNR 20022:localhost:22 ubuntu@hoge.net
```

このスクリプトで行っているSSHの使い方については、以下の記事を参考にさせていただきました。

* [Colabをshellから使う][]
* [SETSID][]
* [SSHトンネルの掘り方][]
* [expectやsshpassを使わずにシェルでSSHパスワード認証を自動化する][]

# 4. SSHでGoogle Colabにログインします

**3-image**

手元のLaptopからラズパイにSSHログインするか、Remmina上で端末エミュレータを起動するかします。
その端末で[tmux][]を起動し、ラズパイのトンネル入り口ポートを通って、[Google Colab][]にアクセスします。

```bash
ubuntu@colab:~$ ssh -p <トンネル入り口のポート番号> root@localhost
```

ユーザ名が`root`なのは、[Google Colab][]には`root`アカウントでログインするからですね。
そして、パスワードを聞かれます。
ここで入力するパスワードは、「**2.Google Colaboratory でSSHサーバを起動します**」の最後で表示されたパスワードです。
これをパスワードとして入力すると、[Google Colab][]にsshでログインできます。

# まとめ

以上で、**自宅サーバ(ラズパイ)を使ってGoogle Colabにsshログインする**ことができました。
ブラウザでポチポチするのが面倒だったり、ブラウザでファイルを編集するのが嫌だという人には、
とても便利な環境が構築できたのではないかと思います。

ちなみに、ラズパイのブラウザですが、初回のReloadボタンを押した後は、手元のLaptopのRemminaは落としても問題ありません。
Remminaを落としても、ラズパイ上のブラウザはReloadし続けてくれるので、[Google Colab][]インスタンスは維持されます。
また、ラズパイ上の端末エミュレータで起動した[tmux][]は`detach`してしまえば、
手元のLaptopからのSSH接続を切っても、ラズパイ上の端末エミュレータを落としても大丈夫です。
再度、ラズパイに接続し直す、あるいは、ラズパイ上の端末エミュレータを起動して、
[tmux][]で`attach`すれば、[Google Colab][]で作業していたセッションに再接続できます。

# References

* [tmux][]
* [Google Colab][]
* [Colab Pro][]
* [Tesla P100][]
* [Ubuntu 20.04 LTS(64-bit) for Raspbeery Pi][]
* [docker-ce][]
* [Raspberry Pi 3 Model B][]
* [Raspberry Pi OS][]
* [Install Ubuntu Server on a Raspberry Pi 2,3 or 4][]
* [How to install Ubuntu on your Raspberry Pi][]
* [Lubuntu][]
* [remmina][]
* [Super Auto Refresh Plus][]
* [Google Colaboratoryにsshログインをしてお手軽GPU実験環境を作ってみた][]
* [Colabをshellから使う][]
* [SSHトンネルの掘り方][]
* [expectやsshpassを使わずにシェルでSSHパスワード認証を自動化する][]
* [SETSID][]
* [Yamaha RTX830][]
* [Remmina][]
* [github][]
* [get_ipython][]
* [interactiveshell][]



[tmux]: https://github.com/tmux/tmux/wiki
[Google Colab]: https://colab.research.google.com/
[Colab Pro]: https://colab.research.google.com/signup
[Tesla P100]: https://www.nvidia.com/en-us/data-center/tesla-p100/
[Ubuntu 20.04 LTS(64-bit) for Raspbeery Pi]: https://ubuntu.com/download/raspberry-pi/thank-you?version=20.04&architecture=arm64+raspi
[docker-ce]: https://docs.docker.com/install/linux/docker-ce/ubuntu/
[Raspberry Pi 3 Model B]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b/
[Raspberry Pi OS]: https://www.raspberrypi.org/downloads/raspberry-pi-os/
[Install Ubuntu Server on a Raspberry Pi 2,3 or 4]: https://ubuntu.com/download/raspberry-pi
[How to install Ubuntu on your Raspberry Pi]: https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#1-overview
[Lubuntu]: https://lubuntu.me/focal-released/
[remmina]: https://remmina.org/
[Super Auto Refresh Plus]: https://chrome.google.com/webstore/detail/super-auto-refresh-plus/globgafddkdlnalejlkcpaefakkhkdoa?hl=en
[Google Colaboratoryにsshログインをしてお手軽GPU実験環境を作ってみた]: https://qiita.com/y-vectorfield/items/7632d24776954e50fbd5
[Colabをshellから使う]: https://www.slideshare.net/stealthinu/colabshell
[SSHトンネルの掘り方]: https://www.kmc.gr.jp/advent-calendar/ssh/2013/12/09/tunnel2.html#:~:text=ssh%20%E3%81%AB%E3%81%AF%2C%20R%E3%82%AA%E3%83%97%E3%82%B7%E3%83%A7%E3%83%B3,%E3%83%9D%E3%83%BC%E3%83%88%E3%81%AB%E6%B5%81%E3%81%97%E8%BE%BC%E3%82%80%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89%E3%81%A7%E3%81%99.
[expectやsshpassを使わずにシェルでSSHパスワード認証を自動化する]: https://qiita.com/wadahiro/items/977e4f820b4451a2e5e0
[SETSID]: https://linuxjm.osdn.jp/html/LDP_man-pages/man2/setsid.2.html
[Yamaha RTX830]: https://network.yamaha.com/products/routers/rtx830/index
[Remmina]: https://remmina.org/
[github]: https://github.com/
[get_ipython]: https://ipython.readthedocs.io/en/stable/api/generated/IPython.core.getipython.html
[interactiveshell]: https://ipython.readthedocs.io/en/stable/api/generated/IPython.core.interactiveshell.html
