---
title: 'HTTPS, X.509，以及实践'
tags:
  - 充电
categories:
  - Anything From Anywhere
date: 2023-07-17 20:17:25
---
#充电 

https://juejin.cn/post/6844903870078910471
https://medium.com/avmconsulting-blog/how-to-secure-applications-on-kubernetes-ssl-tls-certificates-8f7f5751d788

## TLS 和 HTTPS

![](img/Pastedimage20221028164844.png)

在HTTP协议中，通信内容以明文形式发送，因此可能有安全问题
- 窃听风险：通信链路上可以通过抓包获得通信内容
- 篡改风险：修改通信内容
- 冒充/中间人： 冒充通信实体，欺骗用户

HTTPS在HTTP和TCP之间加入了SSL/TLS层，用于提供安全的点对点通信。在进行通信之前，客户端和服务器先通过TLS握手，建立TLS连接，后续的通信内容使用握手期间生成的对称密钥进行加密，实用摘要算法进行摘要，实用证书，进行验证，可以应对上述的问题。

所谓证书，就是由权威机构（CA, Certificate Authority）颁发签署的，可以验证通信实体身份信息的一种文件。其中包含了如下的关键信息
> [!summary] Content
> - 持有者的公钥
>- 持有者的信息
>- CA的信息
>- CA对证书的签名
>- CA对证书进行数字签名使用的算法
>- 证书有效期

在进行TLS握手时，双方要经过4次握手，
1. 客户端 -> 服务器：发送客户端随机数C，支持的TLS版本号，支持的密码套件算法列表
2. 服务器 -> 客户端：发送服务器随机数S，选定的TLS版本号，选定的密码套件，服务器证书
	1. 客户端收到证书后进行证书验证
	2. 首先根据证书中CA的信息，用CA的公钥来解密CA对该证书的签名
	3. 实用签名算法计算证书的数字签名
	4. 将2和3得到的两个签名进行比较，相同则验证成功
3. 客户端 -> 服务器(服务器公钥加密)：发送pre-master
	1. 客户端和服务器都持有C,S, pre-master三个随机数，这三个随机数可以生存会话密钥
	2. 客户端 -> 服务器(会话密钥)： 使用会话密钥加密发送之前通信的摘要
4. 服务器 -> 客户端(会话密钥)： 使用会话密钥加密发送之前通信的摘要

握手结束

## X.509格式
可以看到，证书在进行安全通信时至关重要，目前使用最广泛的一种证书格式就是x.509格式。
![](img/Pastedimage20221028170402.png)
当我们在公网上部署https服务时，就需要从CA处获取证书。一般，可以使用各种公有云厂商提供的证书服务。

## 实践

在非生产环境，或者内网通信时，如果要使用https协议，也需要使用证书，这个时候可以使用自签名的证书，也就是这个证书并不是由CA签发，而是我们自己签发的。最常用的创建自签名证书的软件就是`openssl`。此外，各大公有云服务商的Kubernetes Service提供了证书管理的配套方案，比如Azure Cert Manager等，用来简化手动管理证书的繁琐。

下面是一个在K8s Ingress中，使用自签名证书的一个实践。

#### 创建Service
首先，用如下的代码创建一个最简单的Golang Http server
```go
package main
import (
	"fmt"
	"net/http"
)

func hello(w http.ResponseWriter, req *http.Request) {
	fmt.Fprintf(w, "hello world!\n")
}

  
func main() {
	http.HandleFunc("/hello", hello)
	_ = http.ListenAndServe(":9999", nil)
}
```

然后用这个镜像创建一个service + deployment + ingress

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name:  simple-server
  namespace: test-ssl
  labels:
    app:  simple-server
spec:
  selector:
    matchLabels:
      app: simple-server
  replicas: 1
  template:
    metadata:
      labels:
        app:  simple-server
    spec:
      containers:
      - name:  simple-server
        image:  czh1998/simple-server:latest
        command: ["./server"]
        resources:
          requests:
            cpu: 100m
            memory: 100Mi
          limits:
            cpu: 100m
            memory: 100Mi
      restartPolicy: Always
---
apiVersion: v1
kind: Service
metadata:
  name: simple-server
  namespace: test-ssl
spec:
  selector:
    app: simple-server
  type: ClusterIP
  ports:
  - name: simple-server
    protocol: TCP
    port: 9999
    targetPort: 9999 
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ssl-ingress
  namespace: test-ssl
spec:
  rules:
  - host: n167.njuics.cn
    http:
      paths:
      - path: /hello
        pathType: Prefix
        backend:
          service:
            name: simple-server
            port:
              number: 9999
```

测试, 可以正常访问。但是由于未使用tls，所以并不安全，接下来进行自签证书
![](img/Pastedimage20221028210840.png
)


### 自签证书
```shell
openssl genrsa -out ca.key 2048
openssl req -x509 \
   -new -nodes  \
   -days 365 \
   -key ca.key \
   -out ca.crt \
   -subj "/CN=n167.njuics.cn"   
```

### 创建Secret
```shell
kubectl create secret -n test-ssl tls my-tls-secret \
--key ca.key \
--cert ca.crt 
```

### 修改Ingress

```yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ssl-ingress
  namespace: test-ssl
spec:
  rules:
  - host: n167.njuics.cn
    http:
      paths:
      - path: /hello
        pathType: Prefix
        backend:
          service:
            name: simple-server
            port:
              number: 9999
```

![](img/Pastedimage20221028235141.png
)
