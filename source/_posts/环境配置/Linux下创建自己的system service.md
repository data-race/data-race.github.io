---
title: Linux下创建自己的system service
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 

有时我们需要创建一些系统级别的守护进程，希望可以随着系统启动自动启动，不需要我们手动启动。比如在一个机器上部署code-server这样的应用。

具体的，我们创建一个服务文件
```shell
sudo vim /etc/systemd/system/coder-web.service
```

然后写入配置
``` less
[Unit]
Description=VSCode on the web pog
After=network.target

[Service]
User=zhutingwei
Group=zhutingwei

WorkingDirectory=/home/zhutingwei
ExecStart=/usr/bin/code-server

[Install]
WantedBy=multi-user.target
```

然后重新加载deamon，并启动服务即可
``` shell
sudo systemctl daemon-reload
sudo systemctl start coder-web.service
sudo systemctl status coder-web.service                                                                                               
● coder-web.service - VSCode on the web pog
   Loaded: loaded (/etc/systemd/system/coder-web.service; disabled; vendor preset: enabled)
   Active: active (running) since Fri 2023-07-07 12:06:31 CST; 6min ago
 Main PID: 20976 (node)
    Tasks: 34 (limit: 4915)
   CGroup: /system.slice/coder-web.service
           ├─20976 /usr/lib/code-server/lib/node /usr/lib/code-server
           ├─21015 /usr/lib/code-server/lib/node /usr/lib/code-
           ...
```
