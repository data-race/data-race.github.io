---
title: Istio学习2：Istio的安装和简单使用
tags:
  - Istio
categories:
  - Istio
date: 2023-8-8 10:04:00
---

## Istio的安装

> 使用例来自 《Istio In Action》

### Kind安装
Istio的安装可以借助`istioctl`进行，首先我们需要一个Kubernetes集群。比较方便的方法可以通过Docker Desktop, MiniKube，kind等工具来进行本地集群的创建。
这里我们使用`kind`(k8s in docker)，一种在Docker容器内部署Kubernetes集群的工具，对于本地的Kubernetes开发非常友好。

首先安装`kind`:
```shell
go install sigs.k8s.io/kind@v0.20.0
```

然后创建`kind`集群，注意集群的名字会被默认加上`kind-`前缀：
```shell
kind create cluster --name playground
```

使用如下指令就可以查看我们使用的集群：
```shell
k cluster-info --context kind-playground

Kubernetes control plane is running at https://127.0.0.1:35359
CoreDNS is running at https://127.0.0.1:35359/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

### Istio安装
然后安装`istioctl`：
``` shell
curl -L https://istio.io/downloadIstio | sh - 
```


最后安装`istio`，并且验证安装：
```shell
istioctl install --set profile=demo -y
istioctl verify-install
```

查看istio的资源:
```shell
kg all -n istio-system
NAME                                        READY   STATUS    RESTARTS   AGE
pod/istio-egressgateway-75db994b58-56cfq    1/1     Running   0          7m32s
pod/istio-ingressgateway-79bb75ddbb-tgb6r   1/1     Running   0          7m32s
pod/istiod-68cb9f5cb6-hwh9b                 1/1     Running   0          7m46s

NAME                           TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
                                                  AGE
service/istio-egressgateway    ClusterIP      10.96.54.145    <none>        80/TCP,443/TCP
                                                  7m32s
service/istio-ingressgateway   LoadBalancer   10.96.115.102   <pending>     15021:31345/TCP,80:32305/TCP,443:32165/TCP,31400:31776/TCP,15443:30234/TCP   7m32s
service/istiod                 ClusterIP      10.96.83.82     <none>        15010/TCP,15012/TCP,443/TCP,15014/TCP                                        7m46s

NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/istio-egressgateway    1/1     1            1           7m32s
deployment.apps/istio-ingressgateway   1/1     1            1           7m32s
deployment.apps/istiod                 1/1     1            1           7m46s

NAME                                              DESIRED   CURRENT   READY   AGE
replicaset.apps/istio-egressgateway-75db994b58    1         1         1       7m32s
replicaset.apps/istio-ingressgateway-79bb75ddbb   1         1         1       7m32s
replicaset.apps/istiod-68cb9f5cb6                 1         1         1       7m46s

```

可以看到安装istio后，集群中主要多了3个服务，包括`egressgateway`, `ingressgateway` 和 `istiod`，他们的作用分别是:

- Egress Gateway: 也就是负责流量出口的网关，它为离开服务网格的流量提供出口点。它通常用于处理外部请求，例如当服务需要向外部 API 或数据库发送请求时。出口网关保护、路由和管理流量，并为来自服务网格的出口流量提供集中控制点。出口网关可以配置为在流量从服务网格发送出去时执行自定义操作，例如负载平衡或速率限制。
- Ingress Gateway: 也就是入口网关，它为进入服务网格的流量提供入口点。这允许将传入请求路由到服务网格内的适当服务。 Ingress Gateway 可用于通过对入站流量实施严格的安全策略来提高 Kubernetes 服务的安全性。它还可用于负载平衡和路由各种类型的流量，例如 HTTP、TCP 和 UDP。
- Istiod: 是 Istio 的一个组件，充当控制平面，并为服务网格提供中央管理和编排中心。也是Webhook工作的地方。

我们可以看到一些和istio相关的Webhooks:
```shell
kg validatingwebhookconfigurations.admissionregistration.k8s.io -n istio-system

NAME                           WEBHOOKS   AGE
istio-validator-istio-system   1          19m
istiod-default-validator       1          18m

kg mutatingwebhookconfigurations.admissionregistration.k8s.io -n istio-system

NAME                         WEBHOOKS   AGE
istio-revision-tag-default   4          18m
istio-sidecar-injector       4          19m

```
这些webhook应该是用来向容器中注入Envoy Sidecar Container。

![image](img/learnistio2.png)



### 其他组件安装

安装完Istio后，我们可以安装其他的附加组件，例如Grafana等，在我们下载Istio的目录下，执行
``` shell
k apply -f ./istio-1.18.2/samples/addons
kg svc -n istio-system

NAME                   TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
                                          AGE
grafana                ClusterIP      10.96.187.238   <none>        3000/TCP
                                          116s
istio-egressgateway    ClusterIP      10.96.54.145    <none>        80/TCP,443/TCP
                                          31m
istio-ingressgateway   LoadBalancer   10.96.115.102   <pending>     15021:31345/TCP,80:32305/TCP,443:32165/TCP,31400:31776/TCP,15443:30234/TCP   31m
istiod                 ClusterIP      10.96.83.82     <none>        15010/TCP,15012/TCP,443/TCP,15014/TCP                                        32m
jaeger-collector       ClusterIP      10.96.38.245    <none>        14268/TCP,14250/TCP,9411/TCP                                                 116s
kiali                  ClusterIP      10.96.35.242    <none>        20001/TCP,9090/TCP
                                          116s
loki-headless          ClusterIP      None            <none>        3100/TCP
                                          116s
prometheus             ClusterIP      10.96.110.74    <none>        9090/TCP
                                          116s
tracing                ClusterIP      10.96.160.216   <none>        80/TCP,16685/TCP
                                          116s
zipkin                 ClusterIP      10.96.7.12      <none>        9411/TCP
```

可以发现，创建了Metrics收集存储服务Prometheus，日志收集服务Loki以及监控仪表盘服务Grafana。
这个Grafana是部署在Kind里，而且并没有提供External IP，所以我们采用Kubernetes黑科技端口转发来访问该服务：
``` shell
k port-forward svc/grafana 32323:3000 -n istio-system

```
现在在浏览器中打开`localhost:32323`，就可以访问Grafana:

![image1](img/learnistio1.png)

## Istio简单使用

在 https://github.com/istioinaction/book-source-code 上，我们可以找到《Istio In Action》这本书的随书代码。
我们将代码克隆下来之后，就可以开始简单实践。

对于一个资源清单文件来说，我们可以通过`istioctl`手动为其注入Envoy Proxy Sidecar：
``` shell
istioctl kube-inject -f services/catalog/kubernetes/catalog.yaml 
```
该命令会打印被注入后的资源清单。

我们也可以通过为namespace打上Label的方式，允许自动对该namespace内的pod进行注入。
``` shell
k create ns istioinaction
k config set-context $(k config current-context) --namespace istioinaction
k label namespace istioinaction istio-injection=enabled
```

### 部署Catalog服务
然后我们创建`catalog`服务：

```shell
k apply -f services/catalog/kubernetes/catalog.yaml
```

查看pod
```shell
kg po catalog-66b8469f99-k2bgf -o yaml | yq '.spec.containers[] | [{"name": .name, "image":.image, "command":.command}] ' 

- name: catalog
  image: istioinaction/catalog:latest
  command: null
- name: istio-proxy
  image: docker.io/istio/proxyv2:1.18.2
  command: null
```

可以看到，pod确实被注入了istio-proxy。

测试：
``` shell
kubectl run -i -n default --rm --restart=Never dummy --image=curlimages/curl --command -- \
sh -c 'curl -s http://catalog.istioinaction/items/1'

{
  "id": 1,
  "color": "amber",
  "department": "Eyewear",
  "name": "Elinor Glasses",
  "price": "282.00"
}pod "dummy" deleted
```

### 部署WebApp
```shell
k apply -f services/webapp/kubernetes/webapp.yaml

```
查看Pod
```shell
kg po

NAME                       READY   STATUS    RESTARTS   AGE
catalog-66b8469f99-k2bgf   2/2     Running   0          144m
webapp-5d67cbcd7-54mvx     2/2     Running   0          4m7s
```

测试：
```shell
kubectl run -i -n default --rm --restart=Never dummy \
--image=curlimages/curl --command -- \
sh -c 'curl -s http://webapp.istioinaction/api/catalog/items/1'

{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}pod "dummy" deleted
```

使用端口转发访问webapp

``` shell
k port-forward svc/webapp 80:12123

```

![](img/learnistio3.png)


目前我们都是直接使用portforward的方式去访问集群内部的服务，通常来说，将外部流量引入集群内，我们可以使用`Nginx Ingress Controller`，通过创建`Ingress`资源的方式进行。
但是`Ingress`无法满足更复杂的需求，Istio提供了`Gateway`和`VirtualService`，可以代替`Ingress`。
这里我们为`WebApp`创建`Gateway`和 `VirtualService`:

```shell
cat << EOF | k apply -f -
# Manifests
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: outfitters-gateway
  namespace: istioinaction
spec:
  selector:
    istio: ingressgateway # use istio default controller
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: webapp-virtualservice
  namespace: istioinaction
spec:
  hosts:
  - "*"
  gateways:
  - outfitters-gateway
  http:
  - route:
    - destination:
        host: webapp.istioinaction.svc.cluster.local #service fqdn
        port:
          number: 80
EOF
```

> Gateway：网关描述了在网格边缘运行的负载均衡器，接收传入或传出的 HTTP/TCP 连接。该规范描述了一组应公开的端口、要使用的协议类型、负载均衡器的TKS配置等。 
> Virtual Service: 影响流量路由的配置，例如这里配置了将网关`outfitter-gateway`的流量路由到webapp。我们可以通过设置Virtual Service，将流量按照不同的匹配规则分发到不同的服务。

然后我们可以通过Istio的`IngressGateway`服务访问到我们的WebApp
```shell
k port-forward svc/istio-ingressgateway -n istio-system 12123:80
curl http://localhost:12123/api/catalog/items/1

{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}%
```
这里还是使用了端口转发的方式，如果我们在公有云集群上，那么可以使用LoadBalancer暴露`IngressGateway`，就可以将集群外部流量引入内部。

可以使用`istioctl`进一步查看当前集群内的路由情况：

```shell
istioctl proxy-config routes svc/istio-ingressgateway.istio-system

NAME          VHOST NAME     DOMAINS     MATCH                  VIRTUAL SERVICE
http.8080     *:80           *           /*                     webapp-virtualservice.istioinaction
              backend        *           /healthz/ready*
              backend        *           /stats/prometheus*
```

可以看到访问8080的http请求会被路由到webapp的virtual service。


## 探索Istio的能力
### Istio的可观测性

在Grafana中，我们可以观测到各个服务的健康情况
![](img/learnistio4.png)


除了使用Grafana之外，我们也可以用`istioctl`自带的Dashboard Jaeger进行服务流量的观测
``` shell
istioctl dashboard jaeger

http://localhost:16686
```
![](img/learnistio5.png)

注意到我们并没有对应用层面的代码进行任何的修改，网络基础设施自动帮我们完成了应用之间网络流量的检测。

接着我们可以使用提供的脚本，让catalog以100%的概率表现出500 internal error：
``` shell
bash bin/chaos.sh 500 100
```

可以看到成功率急剧下降：

![](img/learnistio6.png)

### Istio的重试机制

然后我们设置让catalog以50%的概率表现出500 internal error

那么可以发现，我们的curl脚本出错的概率大概就是50%：
```
while true; do curl "http://localhost:12123/api/catalog"; echo " "; sleep 5; done
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
error calling Catalog service
error calling Catalog service
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
error calling Catalog service
error calling Catalog service
error calling Catalog service
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
```


接着我们为catalog创建`VirtualService`，并加入重试机制，那么当webapp去访问catalog时，如果出错，Istio会帮我们自动进行重试

```shell
cat << EOF | k apply -f -
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: catalog
spec:
  hosts:
  - catalog
  http:
  - route:
    - destination:
        host: catalog
    retries:
      attempts: 3
      retryOn: 5xx
      perTryTimeout: 2s
EOF
```

可以发现出错的概率大大降低：
``` shell
 while true; do curl "http://localhost:12123/api/catalog"; echo " "; sleep 5; done
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
```

### Istio的流量路由

首先创建V2版本的catalog服务：

```shell
k apply -f services/catalog/kubernetes/catalog-deployment-v2.yaml
```

然后调用webapp发现，有大概一半的流量流向了v2的catalog （带有ImageURL）
```shell
 while true; do curl "http://localhost:12123/api/catalog/items/1"; echo " "; sleep 2; done
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"}
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"}
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"}
```

我们创建`DestinationRule`，将`catalog`的`VirtualService`分成两个子网：
```shell
cat << EOF | k apply -f -
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: catalog
spec:
  host: catalog
  subsets:
  - name: version-v1
    labels:
      version: v1
  - name: version-v2
    labels:
      version: v2
EOF 
```


然后更新catalog的`VirtualService`，让所有流量只流向v1:
```shell
cat << EOF | k apply -f - 
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: catalog
spec:
  hosts:
  - catalog
  http:
  - route:
    - destination:
        host: catalog
        subset: version-v1
EOF
```
现在进行测试，会发现流量均流向了v1版本的catalog:
```shell
while true; do curl "http://localhost:12123/api/catalog/items/1"; echo " "; sleep 2; done
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"}
```

最后我们为`VirtualService`添加匹配规则，根据header来判定，让header中包含了`x-dark-launch=v2`的流量流向v2:


```shell
cat << EOF | k apply -f - 
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: catalog
spec:
  hosts:
  - catalog
  http:
  - match:
    - headers:
        x-dark-launch:
          exact: "v2"
    route:
    - destination:
        host: catalog
        subset: version-v2
  - route:
    - destination:
        host: catalog
        subset: version-v1  
EOF 
```

进行测试，发现流量被路由到了v2的catalog服务:
```shell
 curl http://localhost:12123/api/catalog/items/1 -H "x-dark-launch: v2"
{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"}
```