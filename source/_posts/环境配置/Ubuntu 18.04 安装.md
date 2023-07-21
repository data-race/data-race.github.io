---
title: Ubuntu 18
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 

## 环境准备
将准备好的镜像文件和U盘使用UtralISO制作为UEFI启动盘，然后使用DiskGenius清理出一个空闲分区。启动机器时，选择启动方式为从U盘启动，然后选择Install Ubuntu。

## 硬盘分区
这部分时安装过程中比较复杂的一部分：
![](img/20170311194320121.png
)
因为是要和windows并存，所以不能选择清除整个磁盘。我们选择手动创建分区
![](img/20170311194807404.png
)
找到我们划分出的空闲分区，点击➕
+ 首先建立bios启动分区的空间
![](img/20170311194903560.png
)
这部分大小为2GB足够

+ 然后建立虚拟内存交换空间，大小和物理内存一致：
![](img/20170311195145921.png
)

+ 然后是根目录分区空间：这部分存放系统文件和第三方软件，不能太小，我们设置为70GB
![](img/20170311195253549.png
)

+ 最后是/home的空间，这部分存放用户数据，将剩余空间都分配给这里：
![](img/20170311195448990.png
)

分配好之后，选择引导器设备为之前分配的bios内存空间的设备号：
![](img/20170311195633117.png
)
然后安装。

## 静态IP设置
由于我在Wifi环境下使用该机器作为服务器，所以希望机器具有静态的ip地址，而不是DHCP分配的动态地址：
打开WIFI设置/IPV4，将IPV4 method由DHCP更改为手动。
首先我们查看网关：
``` shell
ip route | grep default
```
然后在Wifi设置中正确填写希望使用的ip、掩码、网关。
最后使用阿里云的DNS服务器 223.5.5.5，223.6.6.6

## SSH server配置
由于经常使用SSH来连接机器，所以先进行SSH server的配置
``` shell
sudo apt-get install openssh-server # 如果提示和当前软件版本有冲突，安装推荐的版本
sudo apt-get install vim
vim ~/.ssh/authorize_keys # 写入公钥
```

## 换源
``` shell
cd /etc/apt
sudo mv sources.list sources.list.bak
sudo vim sources.list
sudo apt-get update
```

我使用的是阿里的源，如果是校内环境，推荐使用清华的源：
```
deb http://mirrors.aliyun.com/ubuntu/ trusty main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ trusty-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ trusty-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ trusty-proposed main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ trusty-backports main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ trusty main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ trusty-security main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ trusty-updates main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ trusty-proposed main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ trusty-backports main restricted universe multiverse
```

## 系统代理设置
因为经常需要使用google的仓库来拉取镜像，所以我们需要设置代理
Linux下常用clash作为代理软件：
``` shell
czh@hp:~$ cd clash
czh@hp:~/clash$ wget https://github.com/Dreamacro/clash/releases/download/v0.18.0/clash-linux-amd64-v0.18.0.gz
czh@hp:~/clash$ wget https://github.com/Dreamacro/maxmind-geoip/releases/latest/download/Country.mmdb
czh@hp:~/clash$ gzip clash-linux-amd64-v0.18.0.gz -d .
czh@hp:~/clash$ mv clash-linux-amd64-v0.18.0 clash
czh@hp:~/clash$ chmod a+x clash 
czh@hp:~/clash$ wget -O config.yml config-file-url
czh@hp:~/clash$ ./clash -d .
INFO[0000] Start initial compatible provider Proxy      
INFO[0000] Start initial compatible provider Domestic   
INFO[0000] Start initial compatible provider GlobalTV   
INFO[0000] Start initial compatible provider AsianTV    
INFO[0000] Start initial compatible provider Others     
INFO[0000] SOCKS proxy listening at: :7891              
INFO[0000] RESTful API listening at: 0.0.0.0:9090       
INFO[0000] HTTP proxy listening at: :7890               
INFO[0000] Redir proxy listening at: :7892   
```

之后在网络代理中设置http https socks的代理即可。在本地模式下，所有的终端都拥有代理，在ssh远程登录时，还需要设置环境变量：
``` shell
czh@hp:~$ export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7891
czh@hp:~$ curl www.google.com
<!doctype html>....
```

## Docker安装
这里用一个比较偷懒的方法：
``` sudo
sudo snap install docker 
```
虽然速度较慢，但是比较方便。其他的方法可以参考：
[Ubuntu Docker 安装 | 菜鸟教程](https://www.runoob.com/docker/ubuntu-docker-install.html)

测试
``` shell
czh@hp:~$ sudo docker version 
[sudo] password for czh: 
Client:
 Version:           19.03.11
 API version:       1.40
 Go version:        go1.13.12
 Git commit:        dd360c7
 Built:             Mon Jun  8 20:23:26 2020
 OS/Arch:           linux/amd64
 Experimental:      false

czh@hp:~$ sudo docker pull ubuntu:latest
latest: Pulling from library/ubuntu
a4a2a29f9ba4: Pull complete 
127c9761dcba: Pull complete 
d13bf203e905: Pull complete 
4039240d2e0b: Pull complete 
Digest: sha256:35c4a2c15539c6c1e4e5fa4e554dac323ad0107d8eb5c582d6ff386b383b7dce
Status: Downloaded newer image for ubuntu:latest
docker.io/library/ubuntu:latest
czh@hp:~$ sudo docker run -it --rm ubuntu  /bin/bash
root@8a172b7cea56:/# echo hello
hello
root@8a172b7cea56:/# exit
exit

```


## CodeServer安装
虽然vscode提供了ssh的插件，但是更轻量级的方法是使用code server，这样可以在任何可以运行浏览器的设备中进行开发。

+ 安装：
``` shell
wget https://github.com/codercom/code-server/releases/download/1.939-vsc1.33.1/code-server1.939-vsc1.33.1-linux-x64.tar.gz
```

+ 使用：
``` shell
czh@hp:~/code-server$ cd code-server1.939-vsc1.33.1-linux-x64/
czh@hp:~/code-server/code-server1.939-vsc1.33.1-linux-x64$ ls
code-server  LICENSE  README.md
czh@hp:~/code-server/code-server1.939-vsc1.33.1-linux-x64$ ./code-server --help
Usage: code-server [options]

Run VS Code on a remote server.

Options:
  -V, --version                output the version number
  --cert <value>               
  --cert-key <value>           
  -e, --extensions-dir <dir>   Set the root path for extensions.
  -d --user-data-dir <dir>     	Specifies the directory that user data is kept in, useful when running as root.
  --data-dir <value>           DEPRECATED: Use '--user-data-dir' instead. Customize where user-data is stored.
  -h, --host <value>           Customize the hostname. (default: "0.0.0.0")
  -o, --open                   Open in the browser on startup.
  -p, --port <number>          Port to bind on. (default: 8443)
  -N, --no-auth                Start without requiring authentication.
  -H, --allow-http             Allow http connections.
  -P, --password <value>       DEPRECATED: Use the PASSWORD environment variable instead. Specify a password for authentication.
  --disable-telemetry          Disables ALL telemetry.
  --socket <value>             Listen on a UNIX socket. Host and port will be ignored when set.
  --install-extension <value>  Install an extension by its ID.
  --bootstrap-fork <name>      Used for development. Never set.
  --extra-args <args>          Used for development. Never set.
  -h, --help                   output usage information
```

可以通过-p参数设置端口，通过-P参数设置密码。

``` shell
czh@hp:~/src$ code-server -p 7777 -P 980120
```

这种情况下会提示有证书问题，忽略这个问题进行访问，就可以在浏览器中看到vscode了。

![](img/15497621-5D04-4909-BD85-037A60D76AE9.png
)

尝试了一下，在扩展安装方面，code server有所欠缺，可能还是vscode remote更适合复杂的工作。