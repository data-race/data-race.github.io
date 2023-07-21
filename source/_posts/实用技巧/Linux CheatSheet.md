---
title: Linux CheatSheet
tags:
  - cheatsheet
  - 实用技巧
categories:
  - 实用技巧
date: 2023-07-17 20:17:25
---
#cheatsheet 
#实用技巧 

## SSH黑科技 端口转发
1. 本地端口映射到远程，场景：内网服务器无法连接外网，使用本机代理;  内网服务器的ssh 22 暴露到云主机，从而绕开VPN访问
```shell
ssh -R ${remote ip}:${remote port}:${local ip}:${local port} user@${remote ip}
# 例：ssh -R n91:21087:localhost:7890 czh@n91
# 然后在n91上 export https_proxy=http://127.0.0.1:21087 就可以使用本机上的7890端口上的代理进行连接外网
```
2. 远程端口映射本地，用于暂时暴露内网某些服务
``` shell
ssh -L ${local ip}:${local port}:${remote ip}:${remote port} user@{remote ip}
```

## 网络测速： 
``` shell
ssh czh@n168 ‘dd if=/dev/zero bs=1GB count=5 2>/dev/null’ | dd of=/dev/null status=progress

sudo ethtool <device> | grep Speed
```

## pypi临时使用校内镜像： 

``` shell
pip3 install some-package -i https://mirrors.nju.edu.cn/pypi/web/simple/
```

## 查看GPU的拓扑结构: 
``` shell
nvidia-smi topo -m
```

## 查看端口是否开放
``` shell
telnet host port
```

## Linux用户加入sudoers
``` shell
# Ubuntu
usermod -aG sudo username
# CentOS
usermod -aG wheel username
```

## 查看上一条指令的返回结果
``` shell
echo $?
```

## Linux 查看管道运行状态
> [shell - Get exit status of process that’s piped to another - Unix & Linux Stack Exchange](https://unix.stackexchange.com/questions/14270/get-exit-status-of-process-thats-piped-to-another)
``` shell
$ false | true
# bash
$ echo ${PIPESTATUS[@]}
# zsh
$ echo ${pipestatus[@]}
```

## 通过cat简化需要文件的操作
```shell
cat <<EOF | <some command>
...
content
...
EOF
```
例如
```shell
cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: my-svc.my-namespace
spec:
  request: $(cat server.csr | base64 | tr -d '\n')
  signerName: kubernetes.io/kubelet-serving
  usages:
  - digital signature
  - key encipherment
  - server auth
EOF
```

## 使用 `tee` 创建文件

``` shell
tee foo.txt << EOF 
bar
EOF
```


## 带JSON request body的CURL
``` shell
curl -i -X POST -H "Content-type: application/json" <url> -d '{"foo":"bar"}' 
```

## 查看CPU内存
``` shell
cat /proc/cpuinfo
grep MemTotal /proc/meminfo
```

## 查看目录大小
``` shell
du -sh <dir>
```

## centos7 网卡配置
[How to Configure CentOS 7 Network Settings - Serverlab](https://www.serverlab.ca/tutorials/linux/administration-linux/how-to-configure-centos-7-network-settings/)
	- 静态IP
``` shell
vim /etc/sysconfig/network-scripts/<interface-config-file>
# write
DEVICE=<device-name>
ONBOOT=yes
IPADDR=192.168.1.10
NETMASK=255.255.255.0
GATEWAY=192.168.1.1

# excute
ifdown <device-name>
ifup <device-name>
```

	- DHCP
``` shell
DEVICE=enp3s0
ONBOOT=yes
DHCP=yes

ifdown <device-name>
ifup <device-name>
```

## 查看系统调用
``` shell
strace -o <path-to-log> <executable-file>
# 例如
# strace -o hello.log ./helloworld
# strace -o hello.log python3 hello.py
# strace -T -o  hello.log ./helloworld (-T采集时间)
```

## 查看系统调用说明
``` shell
man 2 <syscall-name>
# 例如
# man 2 write
# man 2 read
```

## 采集CPU在用户态和内核态分别的用时
``` shell
sar -P <core-id> <period>
# 例如
# sar -P 0 1
# sar -P ALL 1
```

 ## 查看依赖的库
``` shell
ldd <path-to-executable>
``` 

## 获得当前脚本文件所在文件夹
``` shell
dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
```

## NFS 配置

![](img/CentOS7下yum安装和配置NFS-Zhanming'sblog.pdf
)

## 查看网络吞吐

```shell
# iftop
sudo apt-get install iftop
sudo iftop

# nload
sudo yum install -y epel-release && sudo yum install -y nload
sudo nload <DEVICE> #for example, sudo nload eth0
```


## Vscode 查看命令输出
``` shell
# 使用 cmd | code - 经常失败
cmd > t; code t; sleep 1; rm t
```
