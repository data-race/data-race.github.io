---
title: 配置Anaconda和Jupyter
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 
## Anaconda
``` shell
wget -P /tmp https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh
bash /tmp/Anaconda3-2020.02-Linux-x86_64.sh # 根据提示操作
source ~/.bashrc
```
## Jupyter
1. 生成默认配置文件
```shell
jupyter notebook --generate-config
```

2. 生成访问密码
终端输入ipython，设置你自己的jupyter访问密码，注意复制输出的tokens
``` shell
ipython
In [1]: from notebook.auth import passwd
In [2]: passwd()
Enter password:
Verify password:
Out[2]: 'sha1:xxxxxxxxxxxxxxxxx'

```

3.  修改 ~/.jupyter/jupyter_notebook_config.py## 中对应行如下
``` shell
c.NotebookApp.ip='*'
c.NotebookApp.password = u'sha:ce...刚才复制的那个密文'
c.NotebookApp.open_browser = False
c.NotebookApp.port =8888 #可自行指定一个端口, 访问时使用该端口
```
  
4. 启动jupyter 

``` shell
jupyter notebook 
```
