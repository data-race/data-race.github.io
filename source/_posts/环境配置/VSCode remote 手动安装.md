---
title: VSCode remote 手动安装
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 

在出现一些问题时，比如宿主机网络状况不好，无法自动在宿主机上安装vscode-server，这时可以手动进行安装。

- 查看commit id

![](img/Pastedimage20221110211509.png)

- 创建vscode-server文件夹

``` shell
rm -rf ~/.vscode-server
mkdir -p ~/.vscode-server/bin
```

- 下载对应版本的vscode server
``` shell
wget https://update.code.visualstudio.com/commit:${COMMIT_ID}/server-linux-x64/stable
```

- 解压 复制
``` shell
tar -zxvf stable # 得到一个文件夹 vscode-server-linux-x64
mv vscode-server-linux-x64 ~/.vscode-server/bin/${COMMIT_ID}
```

