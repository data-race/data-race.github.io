---
title: Java环境配置
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 

## Mac

MacOS下直接使用Azul提供的OpenJDK，下载dmg文件，直接安装即可。
https://www.azul.com/downloads/?version=java-8-lts&package=jdk
![](img/Pastedimage20221022142156.png
)


## Linux

Linux下也推荐使用OpenJDK

```shell
sudo apt update
sudo apt install openjdk-[VERSION]-jdk
java --version

```



## Maven 初始化项目

```shell
mvn archetype:generate -DgroupId=com.microsoft.dgp.internship.scan_agent -DartifactId=JedisTest -DarchetypeArtifactId=maven-archetype-quickstart -DinteractiveMode=false
```
