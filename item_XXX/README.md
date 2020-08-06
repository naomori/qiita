# はじめに

パンデミックが発生した後、2020/04に[DELL XPS 13(9300)][]を購入しました。
ラップトップPCとして、性能に不満はないです。
画面は広い(1920x1200)し、キーボードも良いですし、言うことないです。

ただ、巨大なデータを処理をする上では、やはり力不足ですし、
自宅の デスクトップPC を使いたいと思うことが出てくるはずです。
(今は仕事で外出することが一切ないので今後を見越してのことです)
そこで、自宅外から自宅内にVPNを張ってログインできる環境を作っておくことにしました。

# VPN に何をつかうか？

最初は、自宅ルータの[Yamaha RTX830][]をVPNサーバとして、でiPhoneをVPNクライアントとして
接続を試したのですが、全然接続できませんでした...

たぶん、IKEv1/v2の違い、ISPのフィルタ、携帯事業者のフィルタ、設定間違い...などが
考えられると思うのですが、もう疲れました。

そう思ってGoogle先生に聞いてみると、[WireGuardでVPNごしに自宅サーバ開発できる環境を作った][]で
[WireGuard][]を使ったVPN構築方法をとても分かりやすく解説してくださっていました。

そこで、[Yamaha RTX830][]の配下に置いたラズパイ(Raspberry Pi 4 Model B)に
[WireGuard][]をインストールして、宅外に持ち出した[DELL XPS 13(9300)][](Ubuntu 20.04-LTS)と
VPNを構築することにします。

# 1. Wireguardのインストール

[WireGuard][]はPeer to Peer接続なので、サーバ/クライアントの概念はありません。
つまり、[WireGuard][] はラズパイにもラップトップPCにもインストールする必要があります。

## 1-1. ラズパイへのWireguardインストール

ラズパイへのインストール方法については、[WireGuard-Raspi][]に説明してくれています。

```bash
$ sudo apt-get update
$ sudo apt-get upgrade 
$ sudo apt-get install raspberrypi-kernel-headers
$ echo "deb http://deb.debian.org/debian/ unstable main" | sudo tee --append /etc/apt/sources.list.d/unstable.list
$ sudo apt-get install dirmngr 
$ wget -O - https://ftp-master.debian.org/keys/archive-key-$(lsb_release -sr).asc | sudo apt-key add -
$ printf 'Package: *\nPin: release a=unstable\nPin-Priority: 150\n' | sudo tee --append /etc/apt/preferences.d/limit-unstable
$ sudo apt-get update
$ sudo apt-get install wireguard 
$ sudo reboot
```

## 1-2. Ubuntu 20.04-LTSへのWireguardインストール

aptでインストールできるので簡単です。

```bash
$ sudo apt update
$ sudo apt install wireguard
```

# 2. Wireguardのためのパケット転送設定

[Wireguard][]のためのパケット転送設定があります。

## 2-1. ラズパイでのWireguard設定

パケット転送できるように設定しておきます。
これは、[Wireguard][]はUDPでP2Pのトンネルを張るのですが、
自宅外のラップトップPCからホームネットワークにアクセスするために、
ラズパイ側はNATボックスとしても動作させるからです。

```bash
$ sudo perl -pi -e 's/#{1,}?net.ipv4.ip_forward ?= ?(0|1)/net.ipv4.ip_forward = 1/g' /etc/sysctl.conf 
$ sudo reboot
```

きちんと設定されたかどうか確認します。

```bash
$ sysctl net.ipv4.ip_forward 
net.ipv4.ip_forward = 1
```

# 3. VPN用鍵生成

VPN用の秘密鍵と公開鍵を生成します。
ラズパイとラップトップPCの両方で鍵を生成します。

プロトコルとしてはP2Pですが、
便宜上、ラズパイ側をserverとし、ラップトップPCをclientとしておきます。

## 3-1. ラズパイ側の鍵生成

```bash
$ mkdir wgkeys
$ cd wgkeys/
$ umask 077
$ wg genkey > server_private.key
$ wg pubkey > server_public.key < server_private.key
```

## 3-2. ラップトップPC側の鍵生成

```bash
$ mkdir wgkeys
$ cd wgkeys/
$ umask 077
$ wg genkey > client_private.key
$ wg pubkey > client_public.key < client_private.key
```

# 4. VPN用鍵設定

## 4-1. ラズパイ側の鍵設定

`/etc/wireguard`ディレクトリを作成し、そこに設定ファイル(`wg0.conf`)を置きます。

```bash
$ sudo mkdir /etc/wireguard/
$ sudo vim /etc/wireguard/wg0.conf
```

```config
[Interface]

# 1. VPNの仮想的なネットワークで使うIPアドレスを設定します。
# 今回はわかりやすいように10.0.0.1/24で設定しました。
Address = 10.0.0.1/24

# 2. WireGuard を listen させるポート。ルータのポート開放に使うので適当に変えます。
# ポート番号は何でも良いです。
ListenPort = 1194

# 3. wgコマンドで生成した秘密鍵(サーバ側)を文字列で記入します。
PrivateKey = <server private key>

# 4. replace eth0 with the interface open to the internet (e.g might be wlan0 if wifi)
# 起動時と終了時に動くコマンドがかけます。ひとまずnatするための呪文だと思っておきましょう。
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]

# 5. wgコマンドで生成した公開鍵(クライアント側)を文字列で記入します。
PublicKey = <client public key>

# 6. わかりやすくするためにクライアントの仮想IPを 10.0.0.2/32 に設定します。
# サーバへの接続許可IPに追加します。
AllowedIPs = 10.0.0.2/32
```

複数の Peer から接続できるようにするためには、
`[Peer]`の項目をそのクライアントの分だけ増やしてあげればOKです。

## 4-2. ラップトップPC側の鍵設定

ラップトップPC側もラズパイと同様に設定します。

```bash
$ sudo mkdir /etc/wireguard/
$ sudo vim /etc/wireguard/wg0.conf
```

ただし、ラップトップ側にはNAT設定は不要です。

```config
[Interface]

# 1. wgコマンドで生成した秘密鍵(クライアント側)を文字列で記入する
PrivateKey = <client private key>

# 2. クライアントの仮想IP
Address = 10.0.0.2/24

[Peer]

# 3. serverの公開鍵を文字列で記入します
PublicKey = <server public key>

# 4. サーバの仮想IP(10.0.0.1/32)を、クライアントへの接続許可IPに追加します。
# あと、ホームネットワークのアドレス空間も追加します。
AllowedIPs = 10.0.0.1/32,192.168.0.0/24

# 5. サーバのグローバルIP(FQDNでも良い)と
# ListenPort(サーバ側で1194と決めたやつ)を設定します。
Endpoint = <server global ip address>.net:1194
```

# 5. Wireguard(ラズパイ)の自動起動

ラズパイ(サーバ)側で以下のようにして WireGuard を起こします。

```bash
$ sudo wg-quick up wg0
[#] ip link add wg0 type wireguard
[#] wg setconf wg0 /dev/fd/63
[#] ip -4 address add 10.0.0.1/24 dev wg0
[#] ip link set mtu 1420 up dev wg0
[#] iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

ラズパイの起動時に[WireGuard][]も自動的に開始するようにします。

```bash
$ sudo wg-quick down wg0
$ sudo systemctl enable wg-quick@wg0
$ sudo systemctl start wg-quick@wg0
```

# 6. ホームルータでのポート転送

[Yamaha RTX830][]でポート転送の設定をしておきます。
外側で受信したポート番号`11194`をラズパイのポート番号`1194`に変換して転送します。

```bash
pp select 1
ip filter 200100 pass * <ラズパイのIPアドレス> udp * 1194
pp1# ip pp secure filter in ... 200100
no pp select
nat descriptor type 1000 masquerade
nat descriptor masquerade static 1000 1 <ラズパイのIPアドレス> udp 11194=1194
```

お使いのホームルータに合わせて設定してください。

# 7. VPN接続・切断

ラップトップPCから[Wireguard][]でVPN接続するときは、
以下のようにコマンドを実行します。

```bash
$ sudo wg-quick up /etc/wireguard/wg0.conf
```

VPN接続を切断するときは以下です。

```bash
$ sudo wg-quick down /etc/wireguard/wg0.conf
```

# まとめ

以上で、自宅外から自宅のホームネットワークに接続できるようになりました。
これで、デスクトップPCにアクセスできるようになり、膨大なデータ処理も快適にできます。

デスクトップPCを常時起動させておくのはちょっと...という場合は、

* [自宅のPCをWake On LANで起こそう](https://qiita.com/naomori/items/d1f3caaf5bec7f8d6987) 

を読んでみてください。

# References

* [WireGuardでVPNごしに自宅サーバ開発できる環境を作った][]
* [WireGuard-Raspi][]


[DELL XPS 13(9300)]: https://www.dell.com/ja-jp/shop/cty/pdp/spd/xps-13-9300-laptop
[WireGuardでVPNごしに自宅サーバ開発できる環境を作った]: https://blog.koh.dev/2020-01-01-vpn/
[Raspberry Pi OS]: https://www.raspberrypi.org/downloads/raspberry-pi-os/
[Yamaha RTX830]: https://network.yamaha.com/products/routers/rtx830/index
[WireGuard]: https://www.wireguard.com/
[WireGuard-Raspi]: https://github.com/adrianmihalko/raspberrypiwireguard
