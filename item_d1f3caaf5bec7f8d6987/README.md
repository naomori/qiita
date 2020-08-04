# 自宅のPCを Wake On LAN で起こそう

自宅に以下の仕様の自作PCを置いています。

* CPU: AMD Ryzen 9 3950X
* GPU: NVIDIA GeForce RTX2080 SUPER
* RAM: 32.0GB (G.Skill Trident Z Neo F4-3600C16D-32GTZNC (DDR4-3600 16GB×2))
* SSD: 2.0TB  (addlink SSD 2TB S90シリーズ M.2 2280 PCIe Gen 4.0×4 NVMe)
* MOTHER: ASUS AMD AM4対応 マザーボード ROG STRIX X570-E GAMING 
* COOLER: Corsair iCUE H150i RGB PRO XT 簡易水冷CPUクーラー 360mm
* POWER: Thermaltake TOUGHPOWER DIGITAL iRGB PLUS 1000W -GOLD- PC電源ユニット

自宅を離れたときに、この贅沢で潤沢な計算力を持つPCを寝かせておくのは、とてももったいないです。
宅外から自宅内にVPNを張れるようにはしていますが、このPCを常時起動させておくのは電気代がもったいないです。
この"もったいない"x2の状況を乗り越えるために、Wake On LANを活用します。

具体的には、自宅で常時起動しているRaspberry Piに対して、宅外からVPNを通ってログインします。
そのRaspberry PiからWake On LANで自宅のDesktop PCを起こしてあげます。

# Wake On LAN のお勉強

まずは、Wake On LAN とは何かから理解するために、以下を読みます。

[Tech TIPS： Wake On LANでコンピュータを起動する][]

とても分かりやすいですし、どのようなパケットを送信すれば良いのかを理解できます。

# Mother board & Network Interface Card の確認

使っているマザーボード、NICがWake On LANに対応しているかを確認します。
今回は、マザーボードのNICを使用しますので、以下のようにBIOSの設定を変更しておきます。

[Wake On LAN - ROG - Asus][]

# Wake On LAN ツールのインストール

幸運なことに、Wake On LAN の Magic Packet を送信するためのツールは、
Ubuntu, RaspiOS ともにaptを使ってインストールすることができます。

```bash
pi@raspi4:~ $ apt info wakeonlan
Package: wakeonlan
Version: 0.41-12
Priority: optional
Section: net
Maintainer: Thijs Kinkhorst <thijs@debian.org>
Installed-Size: 29.7 kB
Depends: perl
Homepage: https://github.com/jpoliv/wakeonlan
Tag: admin::boot, implemented-in::perl, interface::commandline,
 network::configuration, protocol::ethernet, protocol::udp,
 role::program, scope::utility, use::transmission
Download-Size: 10.5 kB
APT-Manual-Installed: yes
APT-Sources: http://raspbian.raspberrypi.org/raspbian buster/main armhf Packages
Description: Sends 'magic packets' to wake-on-LAN enabled ethernet adapters
 With this package you can remotely wake up and power on machines which have
 motherboards or network cards that support 'Wake-on-Lan' packets.
 .
 The tool allows you to wake up a single machine, or a group of machines.
 .
 You need the MAC addresses of machines to construct the WOL packets, but,
 in contrast to 'etherwake', you do not need root privileges to use the
 program itself as UDP packets are used.
```

```bash
pi@raspi4:~ $ apt install wakeonlan
```

# Wake On LAN の使用

対象の Desktop PC の Mac Address を事前に調べておき、コマンドの引数に渡すだけです。

```bash
pi@raspi4:~ $ wakeonlan <対象のPCのMACアドレス>
```

# まとめ

以上で、宅外から自宅PCを Wake On LAN で起こすことができるようになりました。
残念ながら現時点(2020/08/04)では、COVID-19の影響で外出するのが難しい環境下にありますが、
きっと近い将来、外出を自由に楽しめるときが来ると信じて、そのときのために準備して
今を楽しみたいと思います。

# References

* [Tech TIPS： Wake On LANでコンピュータを起動する][]
* [Wake On LAN - ROG - Asus][]

[Tech TIPS： Wake On LANでコンピュータを起動する]: https://www.atmarkit.co.jp/ait/articles/0602/25/news014.html
[Wake On LAN - ROG - Asus]: https://rog.asus.com/forum/showthread.php?93081-HERO-Wake-on-LAN
