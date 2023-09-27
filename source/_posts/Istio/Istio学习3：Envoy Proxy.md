---
title: 'Istio学习3: Envoy Proxy'
tags:
  - Istio
categories:
  - Istio
date: 2023-09-09 15:39:00
---
## Envoy Proxy 简介

### 什么是代理
Envoy (直译为使节) 是由Lyft公司使用C++开发的一种高性能代理。在Istio中，Envoy和每一个应用实例部署在一起，以构建服务网格。Envoy的设计遵循以下两种重要的原则：
- 网络应该对应用透明。
- 如果网络/应用出了问题，应该很容易判定问题的所在。

这里首先需要解释什么是代理（Proxy），概念上，代理是一种处于客户端和服务器之间的通信中间件。

![image](img/Pastedimage20230909214338.png)

由于代理处在客户端和服务器之间，所以可以为客户端和服务器之间的通信提供一些新的特性，例如通信安全、通信隐私、流量分发等。代理有两种类型：

- **正向代理**：正向代理是代表客户端进行网络请求，向服务器请求数据。代理服务器接收客户端的请求，然后将其转发到目标服务器，再将响应返回给客户端。正向代理能够掩盖客户端的身份，保护客户端的隐私，隐藏客户端的真实IP地址等。
- **反向代理**：反向代理是代表服务器接收客户端的网络请求，并将其转发给后端服务器，然后将响应返回到客户端。反向代理能够负载均衡，服务发现，路由配置，安全策略实现等。

Envoy是一种反向代理。

在OSI七层协议栈中，将网络从底向上分为：物理层、链路层、网络层、传输层、会话层、表示层、和应用层。代理有可能工作在其中的某些层，这也决定了他们的能力，例如：
- Kube-proxy是工作在第四层，也就是网络层的代理，它能做的就是维护IP Tables，IPVS等，将发往Service的流量路由到对应的Pod，但是它并不能理解流量内部具体信息，因为他看到的只是传输层的段(segment)
- Envoy工作在第七层和第四层，因此Envoy可以看到应用层报文，可以理解HTTP/HTTPs/gRPC/MongoDB等各种应用层协议。可以根据返回的报文判断请求是否成功，实现故障恢复、请求重试、限流、安全性等功能，同时提供丰富的观察性支持。

### Envoy中的概念
下图中展示了一些概念
![image](img/Pastedimage20230909215315.png)

- Listeners: 在Envoy中，Listener是负责侦听网络流量的组件。它定义一个IP地址和端口号（或Unix套接字路径）。当流量从客户端到达Listeners时，Listeners根据Routes对流量进行路由。
- Routes：一旦代理服务器收到Downstream发来的流量，路由表会告诉代理服务器该将流量发送到哪个Upstream中，这就是Route的作用。Route通常由规则和条件组成，例如HTTP头或者匹配的URL路径等。
- Clusters：Cluster定义了一组Upstream实例，它们可以处理和响应客户端请求。每个Upstream实例代表一个后端服务器或一个服务器集群。Cluster实现了连接池、负载均衡、故障恢复等功能。
- Downstream：Downstream服务器是向代理发送网络流量的客户端，也就是接收来自客户端的请求并向代理服务器发送请求，Downstream流量是代理服务接收的流量。
- Upstream：Upstream服务器是处理客户端请求的服务器，这些服务器通常是集群中的一部分。Upstream流量是代理服务器发送到处理网络流量请求的服务器的流量。

## Envoy In Action

### 环境准备

```shell
docker pull envoyproxy/envoy:v1.19.0
docker pull nicolaka/netshoot
docker pull citizenstig/httpbin
```

启动httpbin测试服务器
```shell
docker run -d --name httpbin citizenstig/httpbin
# 测试
docker run -it --rm --link httpbin nicolaka/netshoot  curl -X GET http://httpbin:8000/headers
{
  "headers": {
    "Accept": "*/*",
    "Host": "httpbin:8000",
    "User-Agent": "curl/7.80.0"
  }
}
```

> 这里使用--link，这个参数将当前要启动的容器连接到指定的容器，并使用容器名称作为容器的地址。

使用如下的配置文件启动Envoy代理容器，并在端口15001上监听

```yaml
# ch3/simple.yaml
admin:
  address:
    socket_address: { address: 0.0.0.0, port_value: 15000 }

static_resources:
  listeners:
  - name: httpbin-demo
    address:
      socket_address: { address: 0.0.0.0, port_value: 15001 }
    filter_chains:
    - filters:
      - name:  envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          http_filters:
          - name: envoy.filters.http.router
          route_config:
            name: httpbin_local_route
            virtual_hosts:
            - name: httpbin_local_service
              domains: ["*"]
              routes:
              - match: { prefix: "/" }
                route:
                  auto_host_rewrite: true
                  cluster: httpbin_service
  clusters:
    - name: httpbin_service
      connect_timeout: 5s
      type: LOGICAL_DNS
      dns_lookup_family: V4_ONLY
      lb_policy: ROUND_ROBIN
      load_assignment:
        cluster_name: httpbin
        endpoints:
        - lb_endpoints:
          - endpoint:
              address:
                socket_address:
                  address: httpbin
                  port_value: 8000
```

``` shell
docker run -d --name proxy --link httpbin envoyproxy/envoy:v1.19.0 \
--config-yaml "$(cat ch3/simple.yaml)"
```

### 测试

然后我们用测试容器，连接到proxy，并且访问15001端口，测试能否访问到httpbin服务：
``` shell
docker run -it --rm --link proxy nicolaka/netshoot  sh
$ curl -X GET http://proxy:15001/headers
{
  "headers": {
    "Accept": "*/*",
    "Host": "httpbin",
    "User-Agent": "curl/7.80.0",
    "X-Envoy-Expected-Rq-Timeout-Ms": "15000",
    "X-Request-Id": "19f3f675-21e0-462c-bf0c-57d7db29871e"
  }
}
```
在实际到达Httpbin的hedaer中，我们可以看到Envoy为我们的Header添加了两个item，分别是:
- `X-Envoy-Expected-Rq-Timeout-Ms`: 对上游服务的提示，表明该请求预计在15,000毫秒后超时。上游系统和任何其他跳点都可以使用此提示来实现截止日期。
- `X-Request-Id`: 可以用于在集群和潜在地跨服务的多个跳点之间关联请求以完成请求。


### 设置超时时间

然后我们使用新的配置文件启动Envoy Proxy:
``` shell
docker rm -f proxy
docker run --name proxy -d --link httpbin envoyproxy/envoy:v1.19.0 \
--config-yaml "$(cat ch3/simple_change_timeout.yaml)"
```

再次访问Httpbin/headers，查看proxy修改后的Hedaer
``` shell
 curl -X GET http://proxy:15001/headers
{
  "headers": {
    "Accept": "*/*",
    "Host": "httpbin",
    "User-Agent": "curl/7.80.0",
    "X-Envoy-Expected-Rq-Timeout-Ms": "1000",
    "X-Request-Id": "f28d686c-ea48-4553-a655-871a6dad6467"
  }
}
```

可以看到超时时间被修改成了1000ms
### Envoy Admin API

我们设置了在Envoy容器的15000端口上暴露Admin API，我们可以通过该API查看Envoy的状态、所有的Clusters等信息
``` shell
curl -X GET http://proxy:15000/stats | grep retry

cluster.httpbin_service.circuit_breakers.default.rq_retry_open: 0
cluster.httpbin_service.circuit_breakers.high.rq_retry_open: 0
cluster.httpbin_service.retry_or_shadow_abandoned: 0
cluster.httpbin_service.upstream_rq_retry: 0
cluster.httpbin_service.upstream_rq_retry_backoff_exponential: 0
cluster.httpbin_service.upstream_rq_retry_backoff_ratelimited: 0
...

curl -X GET http://proxy:15000/clusters
httpbin_service::observability_name::httpbin_service
httpbin_service::default_priority::max_connections::1024
httpbin_service::default_priority::max_pending_requests::1024
httpbin_service::default_priority::max_requests::1024
httpbin_service::default_priority::max_retries::3
httpbin_service::high_priority::max_connections::1024
httpbin_service::high_priority::max_pending_requests::1024
httpbin_service::high_priority::max_requests::1024
httpbin_service::high_priority::max_retries::3
httpbin_service::added_via_api::false
httpbin_service::172.17.0.2:8000::cx_active::0
httpbin_service::172.17.0.2:8000::cx_connect_fail::0
httpbin_service::172.17.0.2:8000::cx_total::1
httpbin_service::172.17.0.2:8000::rq_active::0
httpbin_service::172.17.0.2:8000::rq_error::0
httpbin_service::172.17.0.2:8000::rq_success::1
httpbin_service::172.17.0.2:8000::rq_timeout::0
httpbin_service::172.17.0.2:8000::rq_total::1
httpbin_service::172.17.0.2:8000::hostname::httpbin
httpbin_service::172.17.0.2:8000::health_flags::healthy
httpbin_service::172.17.0.2:8000::weight::1
httpbin_service::172.17.0.2:8000::region::
httpbin_service::172.17.0.2:8000::zone::
httpbin_service::172.17.0.2:8000::sub_zone::
httpbin_service::172.17.0.2:8000::canary::false
httpbin_service::172.17.0.2:8000::priority::0
httpbin_service::172.17.0.2:8000::success_rate::-1.0
httpbin_service::172.17.0.2:8000::local_origin_success_rate::-1.0

```



