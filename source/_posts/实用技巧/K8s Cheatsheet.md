---
title: K8s Cheatsheet
tags:
  - k8s实践
  - cheatsheet
  - 实用技巧
categories:
  - 实用技巧
date: 2023-07-20 21:14:34
---
#k8s实践 
#cheatsheet
#实用技巧 

### 国内拉镜像
[国内拉取google kubernetes镜像 · GitHub](https://gist.github.com/qwfys/aec4d2ab79281aeafebdb40b22d0b748)

### 为kubectl 添加自动补全功能(zsh)
``` shell
$ vim .zshrc
...
alias k='kubectl'
source <(kubectl completion zsh)
complete -F __start_kubectl k
```

### 查看K8s底层的容器运行时
``` shell
kubelet --help | grep "\-\-container-runtime string"     
```

### K8s删除Terminating的Namespace以及其他资源
``` shell
k get namespace dlpipe-operator-system -o json \
| tr -d "\n" | sed "s/\"finalizers\": \[[^]]\+\]/\"finalizers\": []/" \
| k replace --raw /api/v1/namespaces/dlpipe-operator-system/finalize -f -
```

### K8s查看join指令
``` shell
kubeadm token create --print-join-command  
```

### K8s指定某个容器什么都不做，保持running的状态
``` yaml
 containers:
  - name: myapp
    image: registry.cn-hangzhou.aliyuncs.com/cuizihan/torch-imagent:latest
    command: [ "/bin/bash", "-c", "--" ]
    args: [ "while true; do sleep 30; done;" ]

```

### K8s使用emptyDir增加共享内存
``` yaml
		volumeMounts:
      - name: dshm
        mountPath: /dev/shm

  volumes:
    - name: dshm
      emptyDir:
        medium: Memory

```

### K8s 进入指定pod容器的shell
``` shell
kubectl exec {podname} -c {container-name} -n {namespace--stdin} --tty -- /bin/bash
```

### Kubectl配置自动补全
``` shell
source <(kubectl completion zsh)
echo 'alias k=kubectl' >>~/.zshrc
echo 'compdef __start_kubectl k' >>~/.zshrc
```

如果报错，请将下面内容添加到.zshrc开头
``` shell
autoload -Uz compinit
compinit
```

### K8s网络troubleshoot
``` shell
kubectl run temp-netshoot-shell --rm -i --tty  --image nicolaka/netshoot:v0.1 -- /bin/bash
```

### K8s黑科技 端口转发
端口转发适用于将pod或者service的服务通过转发到本地
```shell
# 转发pod的端口到本地
k port-forward pod/<pod-name> <local-port>:<pod-port> -n <namespace>
# 例如需要将pod的ssh 22号端口转发到本地
# k port-forward pod/<pod-name> 22:32121 -n namespace
# 本地就可以通过 ssh -p 32121登录
# 转发service的端口到本地
k port-forward service/<service-name>  <local-port>:<svc-port> -n <namespace>
```

### 使用curl玩转k8s api
例如下面，可以查看集群的api的入口
``` shell
# 这里的cluster addr和token都是rancher .kube/config文件中的user token
# 如果是在pod内部，没有.kube/config，那么可以用如下的方法获取server和token
# 指向引用该集群名称的 API 服务器
# APISERVER=$(kubectl config view -o jsonpath="{.clusters[?(@.name==\"$CLUSTER_NAME\")].cluster.server}")
# 获得令牌
# TOKEN=$(kubectl get secrets -o jsonpath="{.items[?(@.metadata.annotations['kubernetes\.io/service-account\.name']=='default')].data.token}"|base64 -d)

curl -X GET https://<cluster-addr>/api --header "Authorization: Bearer <TOKEN>" --insecure
```
可以得到类似的输出
``` json
{
  "kind": "APIVersions",
  "versions": [
    "v1"
  ],
  "serverAddressByClientCIDRs": [
    {
      "clientCIDR": "0.0.0.0/0",
      "serverAddress": "xxxxxxx"
    }
  ]
}
```

curl还有一个妙用是通过api server提供的proxy子资源，将request直接转发到对应的service或者pod
``` shell
curl -X [POST|GET] -i --insecure ${APISERVER}/services/<namespace>/<service-name>/proxy/<suffix> --header  "Authorization: Bearer ${TOKEN}" -d '{"foo":"bar"}'
```
参考：https://kubernetes.io/zh/docs/tasks/administer-cluster/access-cluster-api/

- 打污点和取消污点
``` shell
k taint nodes <node> key=val:NoSchedule
k taint nodes <node> key=val:NoSchedule-
```

### 让deployment更新镜像
``` shell
kubectl patch deployment <deployment-name> -p \
  "{\"spec\":{\"template\":{\"metadata\":{\"annotations\":{\"date\":\"`date +'%s'`\"}}}}}"
```

### 怎么使用configmap挂载文件
![](img/wecom-temp-8da02404eb88503993e1ae68a32bdf5b.png
)

### 为Secret生成base64
``` shell
echo -n "your-pass-word" | base64
```

### 创建TLS Secret

```shell
openssl genrsa -out ca.key 2048
openssl req -x509 \
   -new -nodes  \
   -days 365 \
   -key ca.key \
   -out ca.crt \
   -subj "/CN=n167.njuics.cn"  

kubectl create secret -n test-ssl tls my-tls-secret \
--key ca.key \
--cert ca.crt 
```

### 查看当前的admission webhook
``` shell
kubectl get --raw /apis/admissionregistration.k8s.io/v1/mutatingwebhookconfigurations | jq
# mutating, validating
```

### 启动一个In-memory的Postgresql 服务

``` yaml
# service
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: psql
  labels:
    app: postgres
spec:
  type: ClusterIP
  ports:
  - port: 5432
    targetPort: 5432
    protocol: TCP
  selector:
   app: postgres
---
# Config
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: psql
  labels:
    app: postgres
data:
  POSTGRES_DB: postgres
  POSTGRES_USER: postgresadmin
  POSTGRES_PASSWORD: password
---
# deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-deployment
  namespace: psql
spec:
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: postgres
  replicas: 1
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:11.7
          imagePullPolicy: "IfNotPresent"
          ports:
            - containerPort: 5432
          envFrom:
            - configMapRef:
                name: postgres-config
```

psql --host postgres-service.psql.svc.cluster.local -p 5432 -U postgresadmin -d postgres