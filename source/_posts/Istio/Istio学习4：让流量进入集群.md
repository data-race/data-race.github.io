---
title: Istio学习4：让流量进入集群
tags:
  - Istio
categories:
  - Istio
date: 2023-9-26 16:04:00
---

## 流量入口（Traffic Ingress）

当我们希望将集群中的服务暴露给用户时，需要提供一个Ingress point。
Ingress point就像整个集群的守门人一样，对到来的流量进行分类，并且根据路由规则路由到目标服务上。
一般来说，简单的场景可以直接使用Nginx Ingress Controller，通过创建Kubernetes Ingress v1 资源作为流量的入口。
但是Kubernetes Ingress Controller有些不足之处：
1. Ingress Controller 是专为Http/Https协议服务的，它并不能对TCP的流量进行路由，因此也不能向外暴露TCP服务，例如MongoDB/MySQL等。
2. Ingress Controller 缺少复杂的路由规则的支持，难以进行流量分流等复杂的定制。
3. Ingress Controller 只工作在第七层，而Istio工作在L4/L5/L7，且具有强大的可扩展性，因此可以理解各种Protocol，例如MongoDB等。

因此，在复杂场景下，相比与Ingress Controller，Istio会更受到青睐。

![img](img/istio-4-1.jpg)

从概念上来说，Istio起到的作用就是一个反向代理（Reverse Proxy），接受流量，根据规则，将流量路由到对应的服务。
在这一过程中，主要由Istio Gateway作为流量入口。
当我们部署好Istio后，就可以在`Istio-system`下看到`Ingress gateway服务`
```bash
❯ kubectl get svc -n istio-system
NAME                   TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)                                                                      AGE
istio-egressgateway    ClusterIP      10.108.41.126    <none>        80/TCP,443/TCP                                                               6h21m
istio-ingressgateway   LoadBalancer   10.103.255.65    localhost     15021:32391/TCP,80:30502/TCP,443:32589/TCP,31400:30115/TCP,15443:32151/TCP   6h21m
istiod                 ClusterIP      10.107.211.190   <none>        15010/TCP,15012/TCP,443/TCP,15014/TCP                                        6h21m
```
我们也可以根据需求，部署新的Ingress Gateway。

我们知道，Istio借助Envoy作为每个Pod的Sidecar，由Envoy代理Pod的流量。但是实际上，Ingress Gateway也是借助Envoy
```bash
❯ k exec -n istio-system deploy/istio-ingressgateway -- ps
    PID TTY          TIME CMD
      1 ?        00:00:09 pilot-agent
     24 ?        00:00:52 envoy
     45 ?        00:00:00 ps
```
毕竟Envoy的功能十分强大。

## 配置Ingress Gateway

在Istio中，Ingress Gateway的配置是通过`Gateway`和`VirtualService`来完成的。
其中，`Gateway`定义了Ingress Gateway的端口和协议，`VirtualService`定义了流量的路由规则。
下面通过一些例子来展示如何配置Ingress Gateway，来进行流量的Traffic-In。

### Http流量
以最简单的Http流量为例。
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: coolstore-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
      hosts:
        - "webapp.istioinaction.io"
```
首先我们创建一个`Gateway`，在这个`Gateway`中，暴露了一个端口80，协议为Http，监听的域名为`webapp.istioinaction.io`。
我们也可以通过设置host为`*`，来监听所有的域名。
这个配置的含义是期望在Ingress Gateway上监听80端口的访问到`webapp.istioinaction.io`的Http流量。
在`.spec.selector`中我们可看到，这个`Gateway`的selector为`istio: ingressgateway`，这个selector会匹配到`istio-ingressgateway`的Svc。

接下来，我们需要配置`VirtualService`，来定义流量的路由规则。
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: webapp-vs-from-gw
spec:
  hosts:
    - "webapp.istioinaction.io"
  gateways:
    - coolstore-gateway
  http:
    - route:
        - destination:
            host: webapp
            port:
              number: 80
```
在这个`VirtualService`中，我们定义了流量的路由规则。
具体来说，这个VirtualService会将`webapp.istioinaction.io`的流量路由到`webapp`这个K8s Service的80端口上。

我们创建`Gateway`和`VirtualService`之后，可以查看Istio中生成的路由规则
```shell
istioctl proxy-config route deploy/istio-ingressgateway \
-o json --name http.8080 -n istio-system

[
   {
      "name":"http.8080",
      "virtualHosts":[
         {
            "name":"blackhole:80",
            "domains":[
               "*"
            ]
         }
      ],
      "validateClusters":false
   }
]
```
然后我们启动对应的服务，并且去call这个服务（注意这里使用的是Docker Desktop，会在localhost上自动的暴露Istio Ingress Gateway，如果使用Kind等，我们可能需要手动进行kubectl port-froward将Ingress Gateway Svc的80端口暴露出来）
``` shell
k apply -f services/webapp/kubernetes/webapp.yaml
curl http://localhost/api/catalog -H "Host: webapp.istioinaction.io" # 需要用Host Header来指定域名


[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
```

### Https 流量
出于安全性的考虑，我们一般会使用Https来进行流量的传输。
Https在Http的基础上添加了TLS/SSL层，用来验证服务端的身份，以及对流量进行加密。
这里简单介绍一些Https中的四次握手的过程：
1. 客户端向服务端发送一个随机数，以及客户端支持的加密算法。
2. 服务端向客户端发送一个随机数，以及服务端的证书，证书中会包含服务端的基本信息，证书签发者，服务端的公钥和数字签名等。
3. 客户端验证证书，具体来说，客户端计算证书的hash值，然后使用证书签发者的公钥对hash值进行解密，如果解密后的hash值与数字签名相同，则证明证书是可信的。换句话说，数字签名就是CA使用自己的私钥对hash值进行加密的结果。
4. 验证成功后，客户端使用服务端公钥加密一个pre-master随机数，然后发送给服务端。
5. 最后服务端和客户端都有了三个随机数，客户端和服务端使用这三个随机数，以及之前协商的加密算法，生成一个对称加密的密钥，用来加密后续的流量。

从这个过程中我们可以看到，一个完整的Https通信，需要服务端有自己的密钥和证书，以及客户端有CA的公钥。
在Istio中，我们可以通过`Secret`来配置服务端的Cert和Key

``` shell
k create -n istio-system secret tls webapp-credential --key ch4/certs/3_application/private/webapp.istioinaction.io.key.pem --cert ch4/certs/3_application/certs/webapp.istioinaction.io.cert.pem

kg secret webapp-credential -o yaml -n istio-system | yq
apiVersion: v1
data:
  tls.crt: xxxx
  tls.key: xxxx
kind: Secret
metadata:
  creationTimestamp: "2023-09-26T02:55:52Z"
  name: webapp-credential
  namespace: istio-system
  resourceVersion: "8192"
  uid: 56d15c91-18bb-459a-ae85-9259cf41594a
type: kubernetes.io/tls
```

创建好secret后，我们更新Gateway的配置，使其支持Https
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: coolstore-gateway
  namespace: istioinaction
spec:
  selector:
    istio: ingressgateway
  servers:
    - hosts:
        - webapp.istioinaction.io
      port:
        name: http
        number: 80
        protocol: HTTP
    - hosts:
        - webapp.istioinaction.io
      port:
        name: https
        number: 443
        protocol: HTTPS
      tls:
        credentialName: webapp-credential
        mode: SIMPLE

```

然后使用`curl`来测试Https流量
```shell
curl -H "Host: webapp.istioinaction.io" \
https://webapp.istioinaction.io:443/api/catalog \
--cacert ch4/certs/2_intermediate/certs/ca-chain.cert.pem \  # 需要指定CA的证书
--resolve webapp.istioinaction.io:443:127.0.0.1              # 用resolve来重定向域名到127.0.0.1

[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
```

我们有时希望将Http的流量重定向的Https。可以在Gateway中添加`.tls.httpsRedirect: true`来实现
```diff 
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: coolstore-gateway
  namespace: istioinaction
spec:
  selector:
    istio: ingressgateway
  servers:
    - hosts:
        - webapp.istioinaction.io
      port:
        name: http
        number: 80
        protocol: HTTP
+     tls:
+       httpsRedirect: true
    - hosts:
        - webapp.istioinaction.io
      port:
        name: https
        number: 443
        protocol: HTTPS
      tls:
        credentialName: webapp-credential
        mode: SIMPLE
```

这时我们再用Http去访问，就会返回301 move permanently，重定向到Https
```shell
curl -v http://localhost/api/catalog -H "Host: webapp.istioinaction.io"

*   Trying 127.0.0.1:80...
* Connected to localhost (127.0.0.1) port 80 (#0)
> GET /api/catalog HTTP/1.1
> Host: webapp.istioinaction.io
> User-Agent: curl/7.87.0
> Accept: */*
>
* Mark bundle as not supporting multiuse
< HTTP/1.1 301 Moved Permanently
< location: https://webapp.istioinaction.io/api/catalog
< date: Tue, 26 Sep 2023 09:28:02 GMT
< server: istio-envoy
< content-length: 0
<
* Connection #0 to host localhost left intact
```

### mTLS配置

有时为了更好的安全性，除了客户端要验证服务端的身份，服务端也需要验证客户端的身份。
这时就会用到mTLS(Mutual TLS)，即双向TLS认证。
原理上并不复杂，除了客户端要验证服务端证书，服务端也会验证客户端证书。

![img](img/istio-4-2.jpg)

在Istio中，使用mTLS也比较简单，首先我们需要创建新的secret，在之前Https中，我们创建的secret只包含了tls.key和tls.crt，这里我们需要再添加一个ca.crt，用来验证客户端的证书。
```shell
k create -n istio-system secret generic webapp-credential-mtls \
--from-file=tls.key=ch4/certs/3_application/private/webapp.istioinaction.io.key.pem \
--from-file=tls.crt=ch4/certs/3_application/certs/webapp.istioinaction.io.cert.pem \
--from-file=ca.crt=ch4/certs/2_intermediate/certs/ca-chain.cert.pem
```

然后更新Gateway的配置，使其支持mTLS
```diff
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: coolstore-gateway
  namespace: istioinaction
spec:
  selector:
    istio: ingressgateway
  servers:
    - hosts:
        - webapp.istioinaction.io
      port:
        name: http
        number: 80
        protocol: HTTP
    - hosts:
        - webapp.istioinaction.io
      port:
        name: https
        number: 443
        protocol: HTTPS
      tls:
+       credentialName: webapp-credential-mtls
+       mode: MUTUAL
```

现在我们再次方位webapp时，必须带上客户端证书/密钥，否则会返回403 forbidden
```shell
curl -v -H "Host: webapp.istioinaction.io" https://webapp.istioinaction.io:443/api/catalog \
--cacert ch4/certs/2_intermediate/certs/ca-chain.cert.pem --resolve webapp.istioinaction.io:443:127.0.0.1 \
--key ch4/certs/4_client/private/webapp.istioinaction.io.key.pem \
--cert ch4/certs/4_client/certs/webapp.istioinaction.io.cert.pem

* Added webapp.istioinaction.io:443:127.0.0.1 to DNS cache
* Hostname webapp.istioinaction.io was found in DNS cache
*   Trying 127.0.0.1:443...
* Connected to webapp.istioinaction.io (127.0.0.1) port 443 (#0)
* ALPN: offers h2
* ALPN: offers http/1.1
*  CAfile: ch4/certs/2_intermediate/certs/ca-chain.cert.pem
*  CApath: none
* [CONN-0-0][CF-SSL] TLSv1.3 (OUT), TLS handshake, Client hello (1):
* [CONN-0-0][CF-SSL] TLSv1.3 (IN), TLS handshake, Server hello (2):
* [CONN-0-0][CF-SSL] TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
* [CONN-0-0][CF-SSL] TLSv1.3 (IN), TLS handshake, Request CERT (13):
* [CONN-0-0][CF-SSL] TLSv1.3 (IN), TLS handshake, Certificate (11):
* [CONN-0-0][CF-SSL] TLSv1.3 (IN), TLS handshake, CERT verify (15):
* [CONN-0-0][CF-SSL] TLSv1.3 (IN), TLS handshake, Finished (20):
* [CONN-0-0][CF-SSL] TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
* [CONN-0-0][CF-SSL] TLSv1.3 (OUT), TLS handshake, Certificate (11):
* [CONN-0-0][CF-SSL] TLSv1.3 (OUT), TLS handshake, CERT verify (15):
* [CONN-0-0][CF-SSL] TLSv1.3 (OUT), TLS handshake, Finished (20):
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384
* ALPN: server accepted h2
* Server certificate:
*  subject: C=US; ST=Denial; L=Springfield; O=Dis; CN=webapp.istioinaction.io
*  start date: Jul  4 12:49:32 2021 GMT
*  expire date: Jun 29 12:49:32 2041 GMT
*  common name: webapp.istioinaction.io (matched)
*  issuer: C=US; ST=Denial; O=Dis; CN=webapp.istioinaction.io
*  SSL certificate verify ok.
* Using HTTP2, server supports multiplexing
* Copying HTTP/2 data in stream buffer to connection buffer after upgrade: len=0
* h2h3 [:method: GET]
* h2h3 [:path: /api/catalog]
* h2h3 [:scheme: https]
* h2h3 [:authority: webapp.istioinaction.io]
* h2h3 [user-agent: curl/7.87.0]
* h2h3 [accept: */*]
* Using Stream ID: 1 (easy handle 0x2335e40)
> GET /api/catalog HTTP/2
> Host: webapp.istioinaction.io
> user-agent: curl/7.87.0
> accept: */*
>
* [CONN-0-0][CF-SSL] TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
* [CONN-0-0][CF-SSL] TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
* old SSL session ID is stale, removing
* Connection state changed (MAX_CONCURRENT_STREAMS == 2147483647)!
< HTTP/2 200
< content-length: 357
< content-type: application/json; charset=utf-8
< date: Tue, 26 Sep 2023 10:14:12 GMT
< x-envoy-upstream-service-time: 10
< server: istio-envoy
<
* Connection #0 to host webapp.istioinaction.io left intact
[{"id":1,"color":"amber","department":"Eyewear","name":"Elinor Glasses","price":"282.00"},{"id":2,"color":"cyan","department":"Clothing","name":"Atlas Shirt","price":"127.00"},{"id":3,"color":"teal","department":"Clothing","name":"Small Metal Shoes","price":"232.00"},{"id":4,"color":"red","department":"Watches","name":"Red Dragon Watch","price":"232.00"}]
```

### 多个Virtual Service

目前我们只有一个`Gateway`和一个`VirutalService`，如果我们有多个`VirtualService`，我们可以通过`Gateway`的`.spec.servers.hosts`来指定多个`VirtualService`的域名。
```diff
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: coolstore-gateway
  namespace: istioinaction
spec:
  selector:
    istio: ingressgateway
  servers:
    - hosts:
        - webapp.istioinaction.io
      port:
        name: https-webapp
        number: 443
        protocol: HTTPS
      tls:
        credentialName: webapp-credential
        mode: SIMPLE
+   - hosts:
+       - catalog.istioinaction.io
+     port:
+       name: https-catalog
+       number: 443
+       protocol: HTTPS
+     tls:
+       credentialName: catalog-credential
+       mode: SIMPLE
```


### TCP流量配置

除了Http/Https流量，我们也可以配置TCP流量。
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: echo-tcp-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 31400
      name: tcp-echo
      protocol: TCP
    hosts:
    - "*"
```