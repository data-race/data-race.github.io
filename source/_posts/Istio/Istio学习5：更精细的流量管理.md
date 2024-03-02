---
title: Istio学习5：更精细的流量管理
tags:
  - Istio
categories:
  - Istio
date: 2023-10-08 10:00:00
---

## 部署(Deployment)与发布(Release)

在实践中，假设有一个稳定运行的服务，当我们需要对服务进行更新时，往往需要经过以下几个步骤：
1. 将新版本的代码部署到测试环境进行测试。
2. 测试通过后，将新版本的代码部署到生产环境。
3. 在合适的时候，将流量切换到新版本的服务中，完成一次发布。

从中我们可以看出，所谓部署，是让程序/镜像运行起来，变成进程/容器；而发布，是将流量切换到新版本的服务中。
通常，我们不会直接用新版本的服务替换旧版本的服务，而是采用蓝绿部署的方式，在生产环境中同时部署新旧两个版本的服务。
旧版本，即蓝色版本，继续提供服务。
新版本，即绿色版本，只是部署在生产环境中，但不接受流量，此时我们可以对新版本进行测试、验证、监控。
然后在合适的时机，将流量切换到新版本的服务中，完成发布(Release)。

![img1](img/istio-5-1.png)

## 使用Istio减少发布风险

当我们已经完成了部署后，需要决定什么时候进行发布，也就是将真实的流量切换到新版本的服务中。
这个过程并不是突变的，我们可以通过一些手段，逐步将流量切换到新版本的服务中，这样可以减少发布风险。
例如，我们可以将内部员工的流量切换到新版本的服务中，然后再将外部用户的流量切换到新版本的服务中。
或者将某些特定的用户的流量切换到新版本的服务中，然后再将所有用户的流量切换到新版本的服务中。

![img2](img/istio-5-2.png)

这种方式通常被称之为Canary release。
总的来说，就是在生产环境中，先部署新版本的服务，然后逐步将流量切换到新版本的服务中，在此过程中，观测新版本服务是否有问题；不断迭代这个过程，最终完成发布。

之前我们介绍了Istio使用Gateway来暴露服务，将流量引入到服务网格中。
使用VirtualService来控制流量的路由，将流量引入到不同的服务中。
接下来将通过一些例子，展示如何使用Istio来进行更精细的流量管理，以减少发布风险。

### 从Gateway到服务的流量管理

#### 准备工作
``` shell
istioctl install --set profile=demo -y
kubectl create namespace istioinaction
kubectl label namespace istioinaction istio-injection=enabled
k config set-context docker-desktop --namespace istioinaction
```

- 部署两个版本的Catalog服务
``` shell
k apply -f services/catalog/kubernetes/catalog-deployment.yaml
k apply -f services/catalog/kubernetes/catalog-deployment-v2.yaml
k apply -f services/catalog/kubernetes/catalog-svc.yaml
```

- 创建Gateway和Virtual Service
``` shell
k apply -f ch5/catalog-gateway.yaml
k apply -f ch5/catalog-vs.yaml
kg vs,gw -o yaml
```
查看创建出的Gateway和Virtual Service:
```yaml
apiVersion: v1
items:
  - apiVersion: networking.istio.io/v1beta1
    kind: VirtualService
    metadata:
      name: catalog-vs-from-gw
      namespace: istioinaction
    spec:
      gateways:
        - catalog-gateway
      hosts:
        - catalog.istioinaction.io
      http:
        - route:
            - destination:
                host: catalog
  - apiVersion: networking.istio.io/v1beta1
    kind: Gateway
    metadata:
      name: catalog-gateway
      namespace: istioinaction
    spec:
      selector:
        istio: ingressgateway
      servers:
        - hosts:
            - catalog.istioinaction.io
          port:
            name: http
            number: 80
            protocol: HTTP
kind: List
metadata:
  resourceVersion: ""
```

可以看到目前的策略是只是将流量引入到catalog服务中，但是并没有指定具体的版本。
因此，我们通过curl去访问catalog服务，会发现返回的结果是两个版本的服务交替出现。
``` shell
curl http://localhost/items -H "Host: catalog.istioinaction.io"

[
  {
    "id": 1,
    "color": "amber",
    "department": "Eyewear",
    "name": "Elinor Glasses",
    "price": "282.00",
    "imageUrl": "http://lorempixel.com/640/480" # V2
  },
  {
    "id": 4,
    "color": "red",
    "department": "Watches",
    "name": "Red Dragon Watch",
    "price": "232.00"
  }
]

```
#### 将所有流量切换到V1
我们可以通过VirtualService来控制流量的路由，将所有流量切换到V1版本的服务中。
首先我们需要创建一个DestinationRule资源，来将两个版本的服务分开。
``` shell
cat ch5/catalog-dest-rule.yaml | yq
# apiVersion: networking.istio.io/v1alpha3
# kind: DestinationRule
# metadata:
#   name: catalog
# spec:
#   host: catalog.istioinaction.svc.cluster.local
#   subsets:
#     - name: version-v1
#       labels:
#         version: v1
#     - name: version-v2
#       labels:
#         version: v2

k apply -f ch5/catalog-dest-rule.yaml
```
在这个DestinationRule中，我们通过labels来将两个版本的服务分开。
然后我们通过VirtualService来控制流量的路由，将所有流量切换到V1版本的服务中。
``` shell
cat ch5/catalog-vs-v1.yaml| yq
# apiVersion: networking.istio.io/v1alpha3
# kind: VirtualService
# metadata:
#   name: catalog-vs-from-gw
# spec:
#   hosts:
#     - "catalog.istioinaction.io"
#   gateways:
#     - catalog-gateway
#   http:
#     - route:
#         - destination:
#             host: catalog
#             subset: version-v1

k apply -f ch5/catalog-vs-v1.yaml
for i in {1..10}; do curl http://localhost/items -H "Host: catalog.istioinaction.io"; printf "\n\n"; done

[
  {
    "id": 1,
    "color": "amber",
    "department": "Eyewear",
    "name": "Elinor Glasses",
    "price": "282.00"
  },
  {
    "id": 2,
    "color": "cyan",
    "department": "Clothing",
    "name": "Atlas Shirt",
    "price": "127.00"
  },
  {
    "id": 3,
    "color": "teal",
    "department": "Clothing",
    "name": "Small Metal Shoes",
    "price": "232.00"
  },
  {
    "id": 4,
    "color": "red",
    "department": "Watches",
    "name": "Red Dragon Watch",
    "price": "232.00"
  }
]
...
```

当创建了DestinationRule和新版本的VirtualService后，可以发现所有的流量都会被路由到V1的服务。


#### 将特定流量切换到V2
我们可以通过Virtual Service来控制流量的路由，将特定流量，例如具有某种特殊的Header的Http请求，路由到V2版本的服务中。
``` shell
cat ch5/catalog-vs-v2-request.yaml| yq
# apiVersion: networking.istio.io/v1alpha3
# kind: VirtualService
# metadata:
#   name: catalog-vs-from-gw
# spec:
#   hosts:
#     - "catalog.istioinaction.io"
#   gateways:
#     - catalog-gateway
#   http:
#     - match:
#         - headers:
#             x-istio-cohort:
#               exact: "internal"
#       route:
#         - destination:
#             host: catalog
#             subset: version-v2
#     - route:
#         - destination:
#             host: catalog
#             subset: version-v1

k apply -f ch5/catalog-vs-v2-request.yaml

```
在这个VirtualService中，我们通过match来匹配具有某种特殊的Header的Http请求，然后将这些请求路由到V2版本的服务中。
``` shell
curl http://localhost/items -H "Host: catalog.istioinaction.io" -H "x-istio-cohort: internal"
[
  {
    "id": 1,
    "color": "amber",
    "department": "Eyewear",
    "name": "Elinor Glasses",
    "price": "282.00",
    "imageUrl": "http://lorempixel.com/640/480"
  },
  {
    "id": 2,
    "color": "cyan",
    "department": "Clothing",
    "name": "Atlas Shirt",
    "price": "127.00",
    "imageUrl": "http://lorempixel.com/640/480"
  },
  {
    "id": 3,
    "color": "teal",
    "department": "Clothing",
    "name": "Small Metal Shoes",
    "price": "232.00",
    "imageUrl": "http://lorempixel.com/640/480"
  },
  ...
]
```


### 在服务网格中路由流量
#### 准备工作
之前的例子中，我们通过设置DestinationRule和VirtualService来控制Gateway到服务的流量。
而在微服务架构中，流量除了会从Gateway到服务，服务和服务之间也会有流量。
我们也可以通过设置DestinationRule和VirtualService来控制服务到服务的流量。

例如在下图的场景中:
![image](img/istio-5-3.png)

首先我们删除之前创建的所有资源，并且创建WebApp服务。
``` shell
k delete gw,vs,dr --all
k apply -f services/webapp/kubernetes/webapp.yaml
k apply -f services/webapp/istio/webapp-catalog-gw-vs.yaml
```

这里我们创建了webapp服务，和它的Gateway和VirtualService。
目前，webapp服务回去调用catalog服务，而由于我们并没有为catalog服务设置DestinationRule和VirtualService，因此catalog服务的流量会被随机路由到V1和V2版本的服务中。
``` shell
for i in {1..10}; do curl http://localhost/api/catalog -H "Host: webapp.istioinaction.io"; printf "\n\n"; done
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00","imageUrl":"http://lorempixel.com/640/480"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00","imageUrl":"http://lorempixel.com/640/480"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00","imageUrl":"http://lorempixel.com/640/480"}]

[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00","imageUrl":"http://lorempixel.com/640/480"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00","imageUrl":"http://lorempixel.com/640/480"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00","imageUrl":"http://lorempixel.com/640/480"}]

[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
```

#### 将流量路由到V1

我们为catalog服务创建新的VirtualService，注意在新的VirtualService中，gateways被设置为了mesh，这意味着这个VirtualServices会对所有在Mesh中的流量都生效。

``` shell
cat ch5/catalog-vs-v1-mesh.yaml
# apiVersion: networking.istio.io/v1alpha3
# kind: VirtualService
# metadata:
#   name: catalog
# spec:
#   hosts:
#   - catalog
#   gateways:
#     - mesh
#   http:
#   - route:
#     - destination:
#         host: catalog
#         subset: version-v1

k apply -f ch5/catalog-vs-v1-mesh.yaml
k apply -f ch5/catalog-dest-rule.yaml
```

然后会发现，所有的流量都会被路由到V1版本的服务中。
``` shell
for i in {1..10}; do curl http://localhost/api/catalog -H "Host: webapp.istioinaction.io"; printf "\n\n"; done
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]

[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]

[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]

[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
```

#### 将特定流量切换到V2

和从Gateway到服务类似，我们更新catalog的VirtualService，将具有特定Header的request路由到V2版本的服务中。
``` shell
cat ch5/catalog-vs-v2-request-mesh.yaml
# apiVersion: networking.istio.io/v1alpha3
# kind: VirtualService
# metadata:
#   name: catalog
# spec:
#   hosts:
#   - catalog
#   gateways:
#     - mesh
#   http:
#   - match:
#     - headers:
#         x-istio-cohort:
#           exact: "internal"
#     route:
#     - destination:
#         host: catalog
#         subset: version-v2
#   - route:
#     - destination:
#         host: catalog
#         subset: version-v1

k apply -f  ch5/catalog-vs-v2-request-mesh.yaml
```
测试:
```shell
for i in {1..10}; do curl http://localhost/api/catalog -H "Host: webapp.istioinaction.io" -H "x-istio-cohort: internal"; printf "\n\n"; done
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00","imageUrl":"http://lorempixel.com/640/480"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00","imageUrl":"http://lorempixel.com/640/480"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00","imageUrl":"http://lorempixel.com/640/480"}]

[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00","imageUrl":"http://lorempixel.com/640/480"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00","imageUrl":"http://lorempixel.com/640/480"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00","imageUrl":"http://lorempixel.com/640/480"}]

[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00","imageUrl":"http://lorempixel.com/640/480"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00","imageUrl":"http://lorempixel.com/640/480"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00","imageUrl":"http://lorempixel.com/640/480"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00","imageUrl":"http://lorempixel.com/640/480"}]

```

#### 根据权重分配流量

除了匹配特定的Header，也可以通过权重来在多个版本之间分配流量。
``` shell
cat ch5/catalog-vs-v2-10-90-mesh.yaml
# apiVersion: networking.istio.io/v1alpha3
# kind: VirtualService
# metadata:
#   name: catalog
# spec:
#   hosts:
#   - catalog
#   gateways:
#   - mesh
#   http:
#   - route:
#     - destination:
#         host: catalog
#         subset: version-v1
#       weight: 90
#     - destination:
#         host: catalog
#         subset: version-v2
#       weight: 10

k apply -f  ch5/catalog-vs-v2-10-90-mesh.yaml
```


### 使用Service Discovery 

默认情况下，Istio允许服务网格中的任何流量出口。例如，如果一个应用程序试图与未由服务网格管理的外部网站或服务通信，则Istio将允许此流量出口。由于所有流量首先通过服务网格旁路代理（即Istio代理），并且我们可以控制流量路由，因此我们可以更改Istio的默认策略，并拒绝尝试离开网格的所有流量。

禁止流量离开服务网格是一种安全措施，可以防止应用程序意外地与未经授权的服务通信。例如，如果应用程序遭到劫持，劫持者希望借助应用程序向外部未知的服务发送流量，则可以通过禁止流量离开服务网格来阻止此类行为。

#### 准备工作

- 启用Istio的出口流量策略
```shell
istioctl install --set profile=demo -y --set meshConfig.outboundTrafficPolicy.mode=REGISTRY_ONLY
```

- 部署使用外部服务的forum服务
```shell
k apply -f services/forum/kubernetes/forum-all.yaml
```

由于我们设置了outboundTrafficPolicy.mode=REGISTRY_ONLY，因此forum服务只能访问服务网格中的服务，而不能访问服务网格之外的服务，如下图所示:
![img4](img/istio-5-4.png)

测试:
```shell
curl http://localhost/api/users -H "Host: webapp.istioinaction.io"
error calling Forum service%
```

#### 使用ServiceEntry来允许流量离开服务网格

为了让这个调用成功，我们可以创建一个Istio ServiceEntry资源。这样做会在Istio的服务注册表中插入一个条目，并使其被服务网格感知到。
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: ServiceEntry
metadata:
  name: jsonplaceholder
spec:
  hosts:
  - jsonplaceholder.typicode.com
  ports:
  - number: 80
    name: http
    protocol: HTTP
  resolution: DNS
  location: MESH_EXTERNAL
```

在这个ServiceEntry中，我们指定了一个外部的服务，jsonplaceholder.typicode.com，这个服务的端口是80，协议是HTTP。

```shell
k apply -f ch5/forum-serviceentry.yaml
curl http://localhost/api/users -H "Host: webapp.istioinaction.io"
# [{"id":1,"name":"Leanne Graham","username":"Bret","email":"Sincere@april.biz","address":{"street":"Kulas Light","suite":"Apt. 556","city":"Gwenborough","zipcode":"92998-3874"},"phone":"1-770-736-8031 x56442","website":"hildegard.org","company":{"name":"Romaguera-Crona","catchPhrase":"Multi-layered client-server neural-net","bs":"harness real-time e-markets"}},{"id":2,"name":"Ervin Howell","username":"Antonette","email":"Shanna@melissa.tv","address":{"street":"Victor Plains","suite":"Suite 879","city":"Wisokyburgh","zipcode":"90566-7771"},"phone":"010-692-6593 x09125","website":"anastasia.net","company":{"name":"Deckow-Crist","catchPhrase":"Proactive didactic contingency","bs":"synergize scalable supply-chains"}},{"id":3,"name":"Clementine Bauch","username":"Samantha","email":"Nathan@yesenia.net","address":{"street":"Douglas Extension","suite":"Suite 847","city":"McKenziehaven","zipcode":"59590-4157"}...
```