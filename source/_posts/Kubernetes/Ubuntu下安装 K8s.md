---
title: Ubuntu下安装 K8s
tags:
  - k8s实践
categories:
  - Kubernetes
date: 2023-07-17 20:17:27
---

#k8s实践 

## 驱动安装

![](img/截屏2021-07-26下午4.10.56.png
)


``` shell
./NVIDIA-Linux-x86_64-450.102.04.run 
nvidia-smi #输出正常
```


## 安装必要工具
``` shell
# Step 1: K8s 1.17必要工具
apt-get update
apt-get -y install apt-transport-https ca-certificates curl software-properties-common

# Step 2: GPG 证书
wget http://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg
cat gpg | apt-key add -

# Step 3: 写入软件源
add-apt-repository "deb [arch=amd64] http://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"

# Step 4: 安装Docker-CE，版本指定
apt-get -y update
apt install -y docker-ce=5:19.03.15~3-0~ubuntu-bionic docker-ce-cli=5:19.03.15~3-0~ubuntu-bionic
apt-mark hold docker-ce-cli docker-ce

# Step 5: 使用Nvidia-Docker作为运行时
# Step 5.1: 添加源
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
  apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update
# Step 5.2: 安装设置
apt-get install -y nvidia-docker2
pkill -SIGHUP dockerd
cat << EOF > /etc/docker/daemon.json
{
    "exec-opts": ["native.cgroupdriver=systemd"],
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
EOF

systemctl daemon-reload
systemctl restart docker
# 完成后用 docker info | grep Runtime 验证

# Step 6: 模块加载
/sbin/modprobe -- ip_vs
/sbin/modprobe -- ip_vs_rr
/sbin/modprobe -- ip_vs_wrr
/sbin/modprobe -- ip_vs_sh
/sbin/modprobe -- nf_conntrack
/sbin/modprobe -- nf_conntrack_ipv4
/sbin/modprobe -- nf_conntrack_ipv6
lsmod | grep -e ip_vs -e nf_conntrack

cat <<EOF >> /etc/modules
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack
nf_conntrack_ipv4
nf_conntrack_ipv6
br_netfilter
EOF

apt install  -y ipvsadm ipset

# Step 7: 准备安装K8s
curl https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | apt-key add - 
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main
EOF
apt update
apt install -y kubeadm=1.17.17-00 kubelet=1.17.17-00 kubectl=1.17.17-00
apt-mark hold kubelet kubeadm kubectl

# Step 8: 安装K8s
swapoff -a
sed -i 's/.*swap.*/#&/' /etc/fstab
cat <<EOF >  /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sysctl --system

cat <<EOF >> /etc/sysctl.conf 
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
vm.swappiness = 0
EOF
sysctl -p

systemctl enable --now kubelet
```

## 配置与启动K8s
``` shell
kubeadm config print init-defaults > kubeadm-config.yaml

# Step 1: 网络插件配置
# 推荐使用flannel，如果用calico需要把podSubnet修改成192.168.0.0/16
cat > kubeadm-config.yaml << EOF
apiVersion: kubeadm.k8s.io/v1beta2
kind: ClusterConfiguration
kubernetesVersion: v1.17.17
controlPlaneEndpoint: {机器ip}:6443
imageRepository: registry.cn-hangzhou.aliyuncs.com/google_containers
networking:
  podSubnet: 10.244.0.0/16
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: ipvs
EOF

# Step 2: 镜像拉取
# Optional: docker 代理配置
mkdir -p /lib/systemd/system/docker.service.d # n167-n170上在/etc/systemd
cd /lib/systemd/system/docker.service.d
vim http-proxy.conf
# 写入
[Service]
Environment="HTTP_PROXY=http://114.212.80.19:21087" " HTTPS_PROXY=http://114.212.80.19:21087"
# 重启Docker
systemctl daemon-reload
systemctl restart docker
docker info | grep Proxy
# 拉取镜像
kubeadm config images pull --config kubeadm-config.yaml

# Step 3： K8s启动
# ！暂时断开代理
unset http_proxy https_proxy
kubeadm init --config kubeadm-config.yaml --upload-certs
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
# Optional: 节点加入到集群
kubeadm join 114.212.84.206:6443 --token v80clg.a2cllsx8dyy9xx0s     --discovery-token-ca-cert-hash sha256:621136843cf27798ef98152bdcf55aa12da02c4847e38fa1a731b75f1a372303
# 使Master参与调度
kubectl taint nodes --all node-role.kubernetes.io/master-

# Step 4： 启动flannel网络插件
# 如果需要手动指定每个机器使用的网卡，需要修改yaml文件
# containers:
#  - args:
#    - --ip-masq
#    - --kube-subnet-mgr
#    - --iface={网卡名称}
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
# k8s 1.17
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/2140ac876ef134e0ed5af15c65e414cf26827915/Documentation/kube-flannel.yml
# k8s 1.16
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/2140ac876ef134e0ed5af15c65e414cf26827915/Documentation/kube-flannel.yml

# 采用calico网络插件
kubectl create -f https://docs.projectcalico.org/manifests/tigera-operator.yaml
kubectl create -f https://docs.projectcalico.org/manifests/custom-resources.yaml
# 1.16
kubectl apply -f https://docs.projectcalico.org/v3.8/manifests/calico.yaml
# 1.17
kubectl apply -f https://docs.projectcalico.org/v3.11/manifests/calico.yaml
```

## 安装K8s的包管理器 Helm
``` shell
curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

## Nginx-Ingress
``` shell
k create ns ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx  
helm install ingress-nginx ingress-nginx/ingress-nginx \
--namespace ingress-nginx --version 3.34.0 --set rbac.create=true,\
controller.kind=DaemonSet,controller.hostNetwork=true,\
controller.admissionWebhooks.enabled=false \
--set-string controller.nodeSelector."controller\.ingress\.io/enabled"="true",\
controller.config."proxy-body-size"="10240m",\
controller.config."proxy-send-timeout"="60",\
controller.config."proxy-read-timeout"="1800",\

# 注意，如果环境中谷歌镜像被墙，那么不能通过helm，要手动拉镜像创建deamonset
k label node [node的name,也就是暴露服务的node] controller.ingress.io/enabled=true
```

### Ingress示例
``` shell
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: 10240m
    nginx.ingress.kubernetes.io/proxy-send-timeout: 60s
    nginx.ingress.kubernetes.io/proxy-read-timeout: 1800s
    
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  namespace: ics
  name: ics
spec:
  rules:
  - host: ics.nju.edu.cn
    http:
      paths:
      - path: /
        backend:
          serviceName: ics
          servicePort: 38080
---->
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ics
  namespace: ics
spec:
  rules:
  - host: ics.nju.edu.cn
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ics
            port:
              number: 80
```


## NFS Server部署 + Storage Class
``` shell
apt-get install nfs-kernel-server
mkdir /share
vim /etc/exports
# 写入
/share/	114.212.84.0/24(rw,sync,no_root_squash,no_subtree_check)

# 启动
/etc/init.d/rpcbind restart
/etc/init.d/nfs-kernel-server restart

# 创建provisioner和storage class
k create namespace storage
helm repo add stable https://charts.helm.sh/stable
helm install nfs-client-provisioner stable/nfs-client-provisioner \
--namespace storage --set nfs.server={nfs server ip} \
--set nfs.path=/share/

# Optional: 设置NFS为默认的storage class
k patch storageclass nfs-client -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

k get storageclass
```


## Nvidia Device Plugin
``` shell
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.7.2/nvidia-device-plugin.yml
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm repo update
helm install \
    --namespace "kube-system" \
    --version=0.7.1 \
    --generate-name \
    --set compatWithCPUManager=true \
    --set migStrategy=mixed \
    --set resources.requests.cpu=100m \
    --set resources.limits.memory=512Mi \
    nvdp/nvidia-device-plugin
```

## Node-exporter(TODO)
[k8s-deploy/gpu-node-exporter-daemonset.yaml at master · CodeMonk123/k8s-deploy · GitHub](https://github.com/CodeMonk123/k8s-deploy/blob/master/gpu-node-exporter-daemonset.yaml)

``` shell
kubectl label node --all hardware-type=NVIDIAGPU
kubectl apply -f gpu-node-exporter-daemonset.yaml
```

## KubeFlow 安装配置
[Overview of Deployment on Existing Clusters | Kubeflow](https://v1-1-branch.kubeflow.org/docs/started/k8s/overview/)
[Unable to attach or mount volumes: unmounted volumes=istio-token · Issue #406 · kubeflow/kfctl · GitHub](https://github.com/kubeflow/kfctl/issues/406)
``` shell
# 安装kfctl
wget https://github.com/kubeflow/kfctl/releases/download/v1.2.0/kfctl_v1.2.0-0-gbc038f9_linux.tar.gz
tar xvf kfctl_v1.2.0-0-gbc038f9_linux.tar.gz

# 创建一些环境变量
export PATH=$PATH:`pwd` 
export KF_NAME=dlkit-kubeflow 
export BASE_DIR=/opt  
export KF_DIR=${BASE_DIR}/${KF_NAME}  
export CONFIG_URI="https://raw.githubusercontent.com/kubeflow/manifests/v1.2-branch/kfdef/kfctl_k8s_istio.v1.2.0.yaml"
mkdir -p ${KF_DIR} 
cd ${KF_DIR}

# 部署kubeflow
## 可能会因为api server还没完成而失败，等待一段时间，多试几次 
kfctl apply -V -f ${CONFIG_URI}
# 验证
k -n kubeflow get all

# Optional: 可以删除katib等不需要的服务和部署
```

## Prometheus
``` shell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
k create ns prometheus
helm install prometheus prometheus-community/prometheus --namespace \
prometheus --set nodeExporter.enabled=false,server.persistentVolume.storageClass=nfs-client,alertmanager.persistentVolume.storageClass=nfs-client,\
server.ingress.enabled=true,server.ingress.hosts={prometheus.njuics.cn},\
server.securityContext.runAsNonRoot=false,server.securityContext.runAsUser=0,\
server.securityContext.runAsGroup=0,server.securityContext.fsGroup=0
```

## 部署DLKit 三合一版
``` shell
# 镜像制作
DOCKER_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/dlkit:n409
CODER_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/code-server:n409
UI_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/dlkit-ui:n409
NOTEBOOK_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/dlkit-notebook:n409
BASENOTEBOOK_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/base-notebook:n409

make
make ui-image
make image
make coder
make notebook
make push

# 部署
cd cluster
cp ./dlkit/values.yaml.tmpl ./dlkit/values.yaml
k create ns dlkit
k create ns dlkit-resources
helm install --namespace dlkit dlkit ./dlkit -f ./dlkit/values.yaml

# 删除
helm uninstall --namespace dlkit dlkit
```

## 部署DLKit完全版
- dlkit-api
先修改`Makefile`中的 BACKEND_IMAGE
``` shell
BACKEND_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/dlkit-backend:latest
```

然后构建镜像并推送
``` shell
make image
make push
```

- dlkit-ui
升级nodejs，安装依赖
``` shell
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install
```
修改`Makefile`中的UI_IMAGE
``` shell
UI_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/dlkit-ui:latest
```
构建镜像，并推送
``` shell
make image
make push
```

- dlkit-operator
``` shell
DOCKER_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/dlkit-operator:latest
CODER_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/code-server:latest
THEIA_IMAGE=registry.cn-hangzhou.aliyuncs.com/cuizihan/theia:latest

make image
make coder
make push
```

- 鉴权
``` shell
k creant ns openldap
k apply -f docker-openldap/example/kubernetes/simple # 注意把dep中的node name修改正确, 该服务应该部署在n168上
k apply -f docker-phpLDAPadmin/example/kubernetes
# 访问clusterIP:31111，导入ldapbackup.ldif
# login dn 就是binddn
# password可以看ldap pod里的环境变量
k create -f dex/dex.yaml
```


- 部署
``` shell
cd cluster
cp ./dlkit/values.yaml.tmpl ./dlkit/values.yaml
k create ns dlkit
k create ns dlkit-resources
```
修改values.yaml中的镜像为对应的image name
然后部署
``` shell
# 部署
helm install --namespace dlkit dlkit ./dlkit -f ./dlkit/values.yaml
# 删除
helm uninstall --namespace dlkit dlkit
```

::TODO::
::后端启动失败的原因应该是oauth server（ics.nju.edu.cn/oauth）挂了; 此外，前端中的报错信息显示，tune launcher找不到，这是因为该调参服务是单独部署的，后期考虑将其写为一个单独的opearator，目前先把它注释掉::

## 技巧
因为更新了某个镜像，比方后端代码改动，强制更新某个deployment
``` shell
kubectl patch deployment dlkit-backend  -p \
  “{\”spec\”:{\”template\”:{\”metadata\”:{\”annotations\”:{\”date\”:\”`date +'%s'`\”}}}}}”

kubectl patch deployment dlkit-operator  -p \
  “{\”spec\”:{\”template\”:{\”metadata\”:{\”annotations\”:{\”date\”:\”`date +'%s'`\”}}}}}”
```




## 删除节点
``` shell
kubeadm reset -f
iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X
ipvsadm -C
systemctl stop kubelet
systemctl stop docker
rm -rf /var/lib/cni/
rm -rf /var/lib/kubelet/*
rm -rf /etc/cni/
rm -rf /var/lib/calico
rm -rf /var/run/nodeagent
rm -rf /usr/libexec/kubernetes/kubelet-plugins/volume/exec/nodeagent~uds
ifconfig cni0 down
ifconfig flannel.1 down
ifconfig vxlan.calico down
ifconfig docker0 down
ip link delete cni0
ip link delete flannel.1
ip link delete vxlan.calico
rm -rf /var/lib/etcd/
rm -rf /etc/kubernetes/
systemctl start docker
systemctl start kubelet

kubectl drain [nodeName] --delete-local-data --force --ignore-daemonsets
kubectl delete node [nodeName]
```


