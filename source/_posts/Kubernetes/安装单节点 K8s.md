---
title: 安装单节点 K8s
tags:
  - k8s实践
categories:
  - Kubernetes
date: 2023-07-17 20:17:27
---
#k8s实践 

## 准备工作
[How to Set the Proxy for APT on Ubuntu 18.04 - Serverlab](https://www.serverlab.ca/tutorials/linux/administration-linux/how-to-set-the-proxy-for-apt-for-ubuntu-18-04/)

### Docker
- 安装
``` shell
# 删除旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc
# 添加依赖
sudo apt-get update
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
# 添加公钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# 验证
sudo apt-key fingerprint 0EBFCD88
# 添加仓库
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
# 安装
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
# 验证
sudo docker run hello-world
```
- 可选配置
为了加速镜像拉取的速度，我们使用阿里云的镜像加速器：
``` shell
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://sets4hf9.mirror.aliyuncs.com"]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

## 使用kubeadm引导kubernetes
### 让iptables看到网络通信
``` shell
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sudo sysctl --system
```

### 安装运行时
> If both Docker and containerd are detected, Docker takes precedence. This is needed because Docker 18.09 ships with containerd and both are detectable even if you only installed Docker. If any other two or more runtimes are detected, kubeadm exits with an error.

我们已经安装了Docker，在Kubernetes的官方教程上说，Docker相比于containerd具有优先级。这是必要的，因为在Docker18.09的版本，Docker依赖了containerd，所以即使只安装了Docker，也会检测到containerd，如果除了Docker和Containerd，还有其他运行时被检测到，那么kubeadm会报错退出（这种情况需要手动配置指定运行时）

我们已经安装了docker，所以跳过这部分。

### 安装kubeadm，kubelet， kubectl
- kubeadm： 用于引导kubenetes集群的命令行工具
- kubelet： the component that runs on all of the machines in your cluster and does things like starting pods and containers.
- kubectl： 客户端工具

``` shell
sudo apt-get update && sudo apt-get install -y apt-transport-https curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

::在执行完这步之后，代理可以关掉了，之后从谷歌仓库拉取镜像的部分可以用aliyun的镜像::
### 配置cgroup driver
当你使用Docker作为容器运行时时，kubeadm会自动检测cgroup的驱动，并将它设置在/var/lib/kubelet/config.yaml文件中。如果你使用不同的运行时，那么必须手动设置cgroup的驱动，并且通过以下的方法来重启kubelet。
``` shell
systemctl daemon-reload
systemctl restart kubelet
```
docker自带的cgroupdriver是cgroupfs，但是kubernetes不支持cgroupfs，而推荐使用systemd
``` shell
# 编辑文件
vim /usr/lib/systemd/system/docker.service
# 修改，添加启动选项
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock --exec-opt native.cgroupdriver=systemd

# 重启docker服务
systemctl daemon-reload
systemctl restart docker
```

::目前社区已经在着手处理其他容器运行时的cgroup驱动的自动检测::


### FAQ
如果在之前的安装中遇到了问题，可以参考官方的troubleshooting页面
[Troubleshooting kubeadm | Kubernetes](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/)

### 使用kubeadm创建集群
+ 关闭swap
``` shell
 sudo vim /etc/fstab
```
注释掉有swapfile的那一行然后重启。
+ 执行kubeadm init
``` shell
sudo kubeadm init --image-repository registry.aliyuncs.com/google_containers --kubernetes-version v1.19.0 --pod-network-cidr=10.244.0.0/16
```
通常情况下，kubeadmin init足够创建一个可用集群，如果需要加入定制的部分，可以参考kubeadmin的具体参数，这里的网段选择和要使用的网络插件有关
[kubeadm init | Kubernetes](https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm-init/)
运行成功后会给出同一网络中其他节点加入集群的指令。

+ 配置kube config
``` shell
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

+ 配置网络插件
发现Node处于Not Ready的状态，我们查看pod，发现coredns处于pending
[image:F0A4AF32-5F15-4135-8FB3-B10AB7F35E54-1249-00001716E4D40F09/2A6A07FE-1FB2-4A93-B5E6-0258F66273BE.png]

结合官方的说明，需要进行网络插件的配置
[Installing Addons | Kubernetes](https://kubernetes.io/docs/concepts/cluster-administration/addons/)
我们安装[flannel](https://github.com/coreos/flannel)网络插件
``` shell
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```

+ 安装成功
![](img/Pastedimage20221021122018.png
)









