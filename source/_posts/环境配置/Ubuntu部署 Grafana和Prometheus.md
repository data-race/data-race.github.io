---
title: Ubuntu部署 Grafana和Prometheus
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 

## 部署Node Exporter
> The node_exporter is designed to monitor the host system. It’s not recommended to deploy it as a Docker container because it requires access to the host system.

``` shell
wget https://github.com/prometheus/node_exporter/releases/download/v1.2.0/node_exporter-1.2.0.linux-amd64.tar.gz
tar -zxvf node_exporter-1.2.0.linux-amd64.tar.gz
cd node_exporter-*.*-amd64
./node_exporter --collector.systemd --collector.processes
```

测试

``` shell
curl localhost:9100/metrics
```

## 部署Prometheus
``` shell
wget https://github.com/prometheus/prometheus/releases/download/v2.28.1/prometheus-2.28.1.linux-amd64.tar.gz
tar xvf prometheus-*.*-amd64.tar.gz
cd prometheus-*.*
vim prometheus.yml
```

```
# 修改prometheus的job如下
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'node'
    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'
    static_configs:
    - targets: ['localhost:9100']
```

``` shell
# 启动prometheus
./prometheus --config.file=./prometheus.yml
```


## 部署 Grafana
``` shell
sudo apt-get install -y adduser libfontconfig1
wget https://dl.grafana.com/oss/release/grafana_8.0.6_amd64.deb
sudo dpkg -i grafana_8.0.6_amd64.deb
sudo ufw allow 3000
sudo systemctl start grafana-server
sudo systemctl status grafana-server
```
访问ip:3000

![](img/2FB60426-E57A-4EBD-A469-8B35F988FB7C.png
)

初始用户和密码都是admin，login成功后设置新密码，这里新密码和i2ec的登录密码相同
### 创建Datasource
选择创建prometheus的datasource

![](img/6257BF3B-12AF-4E62-B9A6-C061E61FAAA3.png
)

### 创建Dashboard
选择import一个Dashboard
这里使用一个社区提供的dashboard [Node Exporter Full dashboard for Grafana | Grafana Labs](https://grafana.com/grafana/dashboards/1860)，拷贝这个dashboard的ID，导入

![](img/A069EF92-E9B0-410B-B587-7F3FC206CF7C.png
)

这里datasource选择我们创建的prometheus的datasource

![](img/842157EE-CC91-4BB9-B571-B2E45B2C653A.png
)

然后就可以在Dashboard上看到prometheus的数据

![](img/FC4DD511-A4AE-4746-BC6D-29C891E01DF5.png
)

### 可选
```
# 关闭Grafana登录选项
sudo vim grafana.ini 

disable_login_form = true
[auth.anonymous]
# enable anonymous access 
enabled = true
org_name = Main Org.
org_role = Viewer

sudo systemctl restart grafana-server
```

