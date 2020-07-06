# はじめに

それでは、[前回]()構築した Raspberry Pi 3 Model B にOS、[Kubernetes][]をインストールします。ただ、はじめに一言謝らないといけないことがあります。

Raspberry Pi 3 Model B で[Kubernetes][]のコントロールプレーンノードを動かしてみたのですが、性能不足のためかうまく動きませんでした。
ですので、Raspberry Pi 3 Model B x 4台をワーカーノードにして、Raspberry Pi 4 Model B(4GB) x 1台をコントロールプレーンノードにしました。

こんな感じで1台追加しました。
このRaspberry Pi 4 Model Bをコントロールプレーンノードにすることにします。

![raspi4-master.jpeg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/244489/c0386c67-bd8c-879d-ea9e-c04e80f3100a.jpeg)

# OSのインストール

Raspberry Pi だと[Raspberry Pi OS][](以前はRaspbian)を最初に考えますが、[kubeadmのインストール][]を見てみると、[Raspberry Pi OS][]はサポートされていません。したがって、今回はUbuntu 20.04-LTS(64bit)をインストールすることにします。

実は、[Raspberry Pi OS][]でも[Kubernetes][]をインストールできますし、[Kubernetes][]も動作するのですが、トラブルに遭遇したときに同じような経験をした人が少なくて、面倒なことになりそうなので、Ubuntuにします。

[Install Ubuntu Server on a Raspberry Pi 2,3 or 4][]にRaspberry Piのイメージがあるので、
[Ubuntu 20.04 LTS(64-bit) for Raspbeery Pi 3](https://ubuntu.com/download/raspberry-pi/thank-you?version=20.04&architecture=arm64+raspi)
をダウンロードします。

## SDカードの準備

OSイメージのダウンロードが完了したら、解凍しmicroSDカードに書き込みます。

```bash
~/Downloads ❯❯❯ xz -dv ubuntu-20.04-preinstalled-server-arm64+raspi.img.xz
ubuntu-20.04-preinstalled-server-arm64+raspi.img.xz (1/1)
  100 %     667.0 MiB / 3,054.4 MiB = 0.218    92 MiB/s       0:33
```

OSイメージの書き込みには、[こちら](https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#2-prepare-the-sd-card)にもある通りに、Raspberry Pi imager というツールがあるそうですが、私のノートPCはUbuntuなので、`dd`コマンドでも書き込めます。

```bash
~/Downloads ❯❯❯ sudo dd if=ubuntu-20.04-preinstalled-server-arm64+raspi.img of=/dev/mmcblk0 status=progress
3201147392 bytes (3.2 GB, 3.0 GiB) copied, 622 s, 5.1 MB/s
6255474+0 records in
6255474+0 records out
3202802688 bytes (3.2 GB, 3.0 GiB) copied, 627.603 s, 5.1 MB/s
```

この作業をmicroSDカード5枚分(ControlPlane x 1, Node x 4)行います。

## 設定

ここから設定を行っていくわけですが、ディスプレイ+キーボード+マウスを5台のRaspberry Piに接続して作業するのは、少々面倒です。したがって、それら周辺機器を接続せずに設定していきます。
実は、その方法は[How to install Ubuntu on your Raspberry Pi][]に記載されているので、簡単です。また、[こちら](https://rabbit-note.com/2020/06/06/raspberry-pi-ubuntu-headless-install/)も参考になります。

OSイメージを書き込んだmicroSDカードを抜き差しすると、以下のパーティションが自動でマウントされます。

```bash
~/Downloads ❯❯❯ df -k
...
/dev/mmcblk0p2   2754000   1813920    780472  70% /media/$USER/writable
/dev/mmcblk0p1    258095     62017    196079  25% /media/$USER/system-boot
```

IPアドレスの設定をします。K8sクラスタのIPアドレスは以下のように設定します。

* hostname: k8s-master,ip address: 192.168.0.19/24
* hostname: k8s-node0, ip address: 192.168.0.10/24
* hostname: k8s-node1, ip address: 192.168.0.11/24
* hostname: k8s-node2, ip address: 192.168.0.12/24
* hostname: k8s-node3, ip address: 192.168.0.13/24

```bash
~/Downloads ❯❯❯ cd /media/$USER/system-boot
/m/n/system-boot ❯❯❯ vim network-config
```

```config
version: 2
ethernets:
  eth0:
    dhcp4: no
    addresses: [192.168.0.10/24]
    gateway4: 192.168.0.1
    nameservers:
      addresses: [192.168.0.1,8.8.8.8]
    optional: true
```

次にホスト名とユーザ・パスワードの設定をします。

```bash
/m/n/system-boot ❯❯❯ vim user-data
```

```config
fqdn: k8s-node0
chpasswd:
  expire: false
  list:
  - ubuntu:ubuntu
```

次に[Raspberry Pi 4 Ubuntu 19.10 cannot enable cgroup memory at boostrap](https://askubuntu.com/questions/1189480/raspberry-pi-4-ubuntu-19-10-cannot-enable-cgroup-memory-at-boostrap)
にあるようにDocker/K8sに必要なcgroup memoryを有効化します。

```bash
~ ❯❯❯ vim /media/$USER/system-boot/cmdline.txt
```
```diff
-net.ifnames=0 dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=LABEL=writable rootfstype=ext4 elevator=deadline rootwait fixrtc
+net.ifnames=0 dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=LABEL=writable rootfstype=ext4 elevator=deadline cgroup_enable=cpuset cgroup_enable=memory cgroup_memory=1 rootwait fixrtc
```

以上の設定ができたら、microSDカードをアンマウントして、Raspberry Pi に挿入します。

```bash
~ ❯❯❯ umount /media/naomori/system-boot
~ ❯❯❯ umount /media/naomori/writable
```

同様に、K8s Cluster の 5台分(ControlPlane x 1, Node x 4)の設定をします。

## ssh でログイン

Raspberry Piの電源を入れたらsshでログイン(user:ubuntu,pass:ubuntu)します。あと、SSHの秘密鍵のパスフレーズを無しにした公開鍵をK8s Cluster すべてにscpして、ログインしやすくしておきます。

```bash
~/Downloads ❯❯❯ ssh ubuntu@192.168.0.10
~/Downloads ❯❯❯ scp ~/.ssh/id_rsa.pub ubuntu@192.168.0.10:
```

```bash
ubuntu@k8s-node0:~$ cat id_rsa.pub >> .ssh/authorized_keys
ubuntu@k8s-node0:~$ rm -f id_rsa.pub
```

## 最初にすること

```bash
ubuntu@k8s-node0:~$ sudo apt update && sudo apt upgrade -y
```

あと、簡単にそれぞれのノードにアクセスできるように、`/etc/hosts`にエントリを追加します。


```bash
ubuntu@k8s-node0:~$ sudo vim /etc/hosts
```
```config
# K8s
192.168.0.19 k8s-master
192.168.0.10 k8s-node0
192.168.0.11 k8s-node1
192.168.0.12 k8s-node2
192.168.0.13 k8s-node3
```

# Dockerのインストール

[Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)を参考にDockerをインストールします。

```bash
ubuntu@k8s-node0:~$ sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
```

```bash
ubuntu@k8s-node0:~$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
OK
ubuntu@k8s-node0:~$ sudo apt-key fingerprint 0EBFCD88
pub   rsa4096 2017-02-22 [SCEA]
      9DC8 5822 9FC7 DD38 854A  E2D8 8D81 803C 0EBF CD88
uid           [ unknown] Docker Release (CE deb) <docker@docker.com>
sub   rsa4096 2017-02-22 [S]
```

```bash
ubuntu@k8s-node0:~$ sudo add-apt-repository \
	"deb [arch=arm64] https://download.docker.com/linux/ubuntu \
	$(lsb_release -cs) \
	stable"
```

```bash
ubuntu@k8s-node0:~$ sudo apt update
```

[ここ](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)にしたがって、Dockerのバージョンを指定してインストールします。

```bash
ubuntu@k8s-node0:~$ sudo apt install -y \
  containerd.io=1.2.13-2 \
  docker-ce=5:19.03.11~3-0~ubuntu-$(lsb_release -cs) \
  docker-ce-cli=5:19.03.11~3-0~ubuntu-$(lsb_release -cs)
```

[kubernetes][]とのバージョン依存の問題があるため、[docker-ce][]のバージョンを現在のバージョンで固定化します。

```bash
ubuntu@k8s-node0:~$ sudo apt-mark hold containerd.io docker-ce docker-ce-cli
containerd.io set on hold.
docker-ce set on hold.
docker-ce-cli set on hold.
```

Dockerの設定を変更します。

```bash
ubuntu@k8s-node0:~$ sudo vim /etc/docker/daemon.json
```
```json
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
```

```bash
ubuntu@k8s-node0:~$ sudo mkdir -p /etc/systemd/system/docker.service.d
```

```
ubuntu@k8s-node0:~$ sudo systemctl daemon-reload
ubuntu@k8s-node0:~$ sudo systemctl restart docker
```

```bash
ubuntu@k8s-node0:~$ sudo usermod -aG docker ubuntu
```

```bash
ubuntu@k8s-node0:~$ sudo systemctl enable docker
```

以上の作業を5台分(ControlPlane x 1, Node x 4)します。

# Kubernetesのインストール

[kubeadmのインストール][]を参考にインストールします。

## iptablesがnftablesバックエンドを使用しないようにする

```bash
ubuntu@k8s-node0:~$ sudo apt-get install -y iptables arptables ebtables
```

```bash
ubuntu@k8s-node0:~$ sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
ubuntu@k8s-node0:~$ sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
ubuntu@k8s-node0:~$ sudo update-alternatives --set arptables /usr/sbin/arptables-legacy
ubuntu@k8s-node0:~$ sudo update-alternatives --set ebtables /usr/sbin/ebtables-legacy
```

## kubeadm のインストール

```bash
ubuntu@k8s-node0:~$ sudo apt-get update && sudo apt-get install -y apt-transport-https curl
ubuntu@k8s-node0:~$ curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
```

```bash
ubuntu@k8s-node0:~$ cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
```

```bash
ubuntu@k8s-node0:~$ sudo apt update
ubuntu@k8s-node0:~$ sudo apt install -y kubelet kubeadm kubectl
ubuntu@k8s-node0:~$ sudo apt-mark hold kubelet kubeadm kubectl
kubelet set on hold.
kubeadm set on hold.
kubectl set on hold.
```

## swap 無効化

`kubelet`が正常に動作するためには、**swap**は必ずオフである必要があるとのことなので、**swap**を無効化しておきます。

```bash
ubuntu@k8s-node0:~$ sudo swapoff -a
```

以上の作業を5台分(ControlPlane x 1, Node x 4)します。

# kubeadmを使用したシングルコントロールプレーンクラスターの作成

[kubeadmを使用したシングルコントロールプレーンクラスターの作成][]を参考に、Kubernetesクラスタを作成していきます。ネットワークには、[kube-router][]を使います。

## コントロールプレーンノードの初期化

Masterノードで以下を実行します。

```bash
ubuntu@k8s-master:~$ sudo kubeadm init --pod-network-cidr=10.1.0.0/16
```

```
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join 192.168.0.19:6443 --token n1o5q2.coajyablijtdj1qb \
    --discovery-token-ca-cert-hash sha256:5e0856b519d1f97db37fa1742c4613f99ef3f9eafd4a7bbbf5a5d270145c81bb
```

完了すると、以下を実行しろと言われるので、その通りにします。

```bash
ubuntu@k8s-master:~$ mkdir -p $HOME/.kube
ubuntu@k8s-master:~$ sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
ubuntu@k8s-master:~$ sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

## Podネットワークアドオンのインストール

Podネットワークとして、[kube-router][]を使うことにします。[Deploying kube-router with kubeadm](https://github.com/cloudnativelabs/kube-router/blob/master/docs/kubeadm.md)を参考にします。

```bash
ubuntu@k8s-master:~$ KUBECONFIG=$HOME/.kube/config kubectl apply -f https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kubeadm-kuberouter.yaml
```

```bash
ubuntu@k8s-master:~$ kubectl get pod -n kube-system
NAME                                 READY   STATUS    RESTARTS   AGE
coredns-66bff467f8-j8snh             1/1     Running   0          19m
coredns-66bff467f8-ntsxk             1/1     Running   0          19m
etcd-k8s-master                      1/1     Running   0          19m
kube-apiserver-k8s-master            1/1     Running   0          19m
kube-controller-manager-k8s-master   1/1     Running   0          19m
kube-proxy-87dh9                     1/1     Running   0          19m
kube-router-xlw62                    1/1     Running   0          17m
kube-scheduler-k8s-master            1/1     Running   0          19m
```

## NodeのJoin

以下を`k8s-node[0-3]`で実行して、K8sクラスタに参加させます。

```bash
ubuntu@k8s-node0:~$ sudo kubeadm join 192.168.0.19:6443 --token n1o5q2.coajyablijtdj1qb --discovery-token-ca-cert-hash sha256:5e0856b519d1f97db37fa1742c4613f99ef3f9eafd4a7bbbf5a5d270145c81bb
...
This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.

Run 'kubectl get nodes' on the control-plane to see this node join the cluster.
```

全部が`Running`になっていることを確認します。

```bash
ubuntu@k8s-master:~$ kubectl get pod -n kube-system
NAME                                 READY   STATUS    RESTARTS   AGE
coredns-66bff467f8-j8snh             1/1     Running   0          45m
coredns-66bff467f8-ntsxk             1/1     Running   0          45m
etcd-k8s-master                      1/1     Running   0          45m
kube-apiserver-k8s-master            1/1     Running   0          45m
kube-controller-manager-k8s-master   1/1     Running   0          45m
kube-proxy-4skhr                     1/1     Running   0          19m
kube-proxy-5b7k9                     1/1     Running   0          20m
kube-proxy-87dh9                     1/1     Running   0          45m
kube-proxy-n6w99                     1/1     Running   0          19m
kube-proxy-tw7cr                     1/1     Running   0          20m
kube-router-65lkl                    1/1     Running   0          20m
kube-router-np5z5                    1/1     Running   0          20m
kube-router-ntzkv                    1/1     Running   0          19m
kube-router-xlw62                    1/1     Running   0          43m
kube-router-zjhd6                    1/1     Running   0          19m
kube-scheduler-k8s-master            1/1     Running   0          45m
```

ノードの稼働状況を確認します。

```bash
ubuntu@k8s-master:~$ kubectl get nodes
NAME         STATUS   ROLES    AGE     VERSION
k8s-master   Ready    master   33m     v1.18.5
k8s-node0    Ready    <none>   8m10s   v1.18.5
k8s-node1    Ready    <none>   7m34s   v1.18.5
k8s-node2    Ready    <none>   7m37s   v1.18.5
k8s-node3    Ready    <none>   7m32s   v1.18.5
```

Rolesを設定します。

```bash
ubuntu@k8s-master:~$ kubectl label nodes k8s-node0 kubernetes.io/role=node
ubuntu@k8s-master:~$ kubectl label nodes k8s-node1 kubernetes.io/role=node
ubuntu@k8s-master:~$ kubectl label nodes k8s-node2 kubernetes.io/role=node
ubuntu@k8s-master:~$ kubectl label nodes k8s-node3 kubernetes.io/role=node
```

```bash
ubuntu@k8s-master:~$ kubectl get node
NAME         STATUS   ROLES    AGE   VERSION
k8s-master   Ready    master   85m   v1.18.5
k8s-node0    Ready    node     60m   v1.18.5
k8s-node1    Ready    node     60m   v1.18.5
k8s-node2    Ready    node     60m   v1.18.5
k8s-node3    Ready    node     60m   v1.18.5
```

```bash
ubuntu@k8s-master:~$ kubectl cluster-info
Kubernetes master is running at https://192.168.0.19:6443
KubeDNS is running at https://192.168.0.19:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

# 別ノード(Ubuntu 20.04 LTS)から kubectl で制御します

別のノード(Ubuntu 20.04 LTS)から`kubectl`を実行することもできます。[Install and Set Up kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)を参考に`kubectl`をインストールします。

```zsh
~ ❯❯❯  sudo snap install kubectl --classic
```

masterノードで出力をコピーします。

```bash
ubuntu@k8s-master:~$ kubectl config view --raw
```

別ノードの`~/.kube/config`にペーストします。

```bash
~ ❯❯❯  vim ~/.kube/config
```

これで別ノードからでも`kubectl`を実行できます。また kubectl completion でコマンドの補完ができます。

# まとめ

以上で、
Raspberry Pi 4 Model B x 1 をコントロールプレーンノードに、
Raspberry Pi 3 Model B x 4 をノードにした Kubernetes クラスタを構築できました。 

次回からは、[15Stepで習得 Dockerから入るKubernetes コンテナ開発からK8s本番運用まで](http://www.ric.co.jp/book/contents/book_1161.html)で[Kubernetes][]の勉強をしていきたいと思います。まだ全てを読んだわけではないですが、アーキテクチャやコンポーネントの説明が理解しやすくて、とても良い本だと思います。

[Kubernetes]: https://kubernetes.io/
[docker-ce]: https://docs.docker.com/install/linux/docker-ce/ubuntu/
[kube-router]: https://www.kube-router.io/
[Raspberry Pi 3 Model B]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b/
[Raspberry Pi OS]: https://www.raspberrypi.org/downloads/raspberry-pi-os/
[kubeadmのインストール]: https://kubernetes.io/ja/docs/setup/production-environment/tools/kubeadm/install-kubeadm/
[kubeadmを使用したシングルコントロールプレーンクラスターの作成]: https://kubernetes.io/ja/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/
[Install Ubuntu Server on a Raspberry Pi 2,3 or 4]: https://ubuntu.com/download/raspberry-pi
[How to install Ubuntu on your Raspberry Pi]: https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#1-overview
