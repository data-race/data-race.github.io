---
title: MQTT Broker配置
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 

## 直接部署
https://www.arubacloud.com/tutorial/how-to-install-and-secure-mosquitto-on-ubuntu-20-04.aspx

### 安装
``` shell
sudo apt update -y && sudo apt install mosquitto mosquitto-clients -y
```

或者下载二进制安装包进行安装
https://mosquitto.org/files/binary/

### 启动服务
``` shell
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
sudo systemctl status mosquitto
● mosquitto.service - LSB: MQTT message broker
   Loaded: loaded (/etc/init.d/mosquitto; generated)
   Active: active (exited) since Mon 2021-07-05 16:24:38 CST; 3s ago
     Docs: man:systemd-sysv-generator(8)
  Process: 7914 ExecStart=/etc/init.d/mosquitto start (code=exited, status=0/SUC

Jul 05 16:24:38 n33 systemd[1]: Starting LSB: MQTT message broker...
Jul 05 16:24:38 n33 systemd[1]: Started LSB: MQTT message broker.
```

### 配置
目前的MQTT服务所有人都可以访问，为Mosquitto添加用户并设置密码:
``` shell
sudo mosquitto_passwd -c /etc/mosquitto/passwd udo-user
Password: 
Reenter password: 
```

这里添加的用户为 udo-user，密码为123456

接着编辑mosquitto的配置文件
``` shell
sudo vim /etc/mosquitto/conf.d/default.conf
```

添加如下配置:
``` shell
port 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
# this will expect websockets connections
listener 1884
protocol websockets
```

重启服务
``` shell
sudo systemctl restart mosquitto
```


## 使用Docker镜像部署
### 拉取镜像

``` shell
sudo docker pull eclipse-mosquitto:2.0.11
```
### 开启端口
``` shell
czh@xeon:~$ sudo ufw allow 1883
czh@xeon:~$ sudo ufw allow 1884
czh@xeon:~$ sudo ufw allow 9001
```

### 创建配置文件夹
``` shell
mkdir -p mosquitto/config mosquitto/data mosquitto/log mosquitto/passwd
```

### 编辑配置文件
在mosquito/config路径下，创建配置文件，并写入
``` shell
czh@xeon:~/mosquitto/config$ vim mosquitto.conf
persistence true
persistence_location /mosquitto/data
log_dest file /mosquitto/mosquitto.log
listener 1883
allow_anonymous false
password_file /mosquitto/passwd/passwd
# this will expect websockets connections
listener 1884
protocol websockets
```

### 启动容器
启动容器，并按照说明，挂载配置文件夹，持久化存储文件夹，以及log文件夹，并开启相应的端口

``` shell
sudo docker run -d -p 1883:1883 -p 1884:1884 -p 9001:9001 -v /home/czh/mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf -v /home/czh/mosquitto/data:/mosquitto/data -v /home/czh/mosquitto/log:/mosquitto/log -v /home/czh/mosquitto/passwd:/mosquitto/passwd --name udo-mqtt --rm eclipse-mosquitto:2.0.11
```

### 进入容器
进入容器，创建用户，设置密码
``` shell
czh@xeon:~$ sudo docker exec -it udo-mqtt /bin/sh
/ # mosquitto_passwd -c mosquitto/passwd/passwd udo-user
Password: 
Reenter password: 
```

### 退出容器
进行测试








