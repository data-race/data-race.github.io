---
title: Docker CheatSheet
tags:
  - cheatsheet
  - 实用技巧
categories:
  - 实用技巧
date: 2023-07-17 20:17:25
---
#cheatsheet 
#实用技巧

### docker 构建镜像使用代理
``` shell
docker build --build-arg http_proxy=http://114.212.80.19:21087 --build-arg https_proxy=http://114.212.80.19:21087 -t xxx
```

### docker 拉取指定架构的镜像
``` shell
docker pull --platform linux/amd64 xxx
```

### docker 验证代理

``` shell
docker search redis
```

![[FCB24354-03B3-4536-AA20-D5E95DA85807.png]]

### docker 代理配置
``` shell
sudo vim /etc/systemd/system/docker.service.d/http-proxy.conf

[Service]
Environment="HTTP_PROXY=http://114.212.87.33:21087/"
Environment="HTTPS_PROXY=http://114.212.87.33:21087/"
Environment="NO_PROXY=localhost,127.0.0.1,.example.com"
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### Docker 分阶段构建
```dockerfile
FROM maven:3.8.6-openjdk-11 AS BUILDER
WORKDIR /build
COPY . /build
RUN mvn build

FROM openjdk:11.0.15-jre
WORKDIR /appilication
COPY --from=BUILDER /build/scan_config /application/scan_config
COPY --from=BUILDER /build/target/ScanAgentInJava-1.0-SNAPSHOT.jar /application/app.jar
CMD ["java", "-jar", "app.jar"]
```


### Docker 构建时指定镜像的架构
``` shell
docker buildx build --platform linux/arm64 -t ${IMAGE_TAG}  .
```