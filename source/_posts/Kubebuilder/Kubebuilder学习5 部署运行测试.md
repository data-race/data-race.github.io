---
title: Kubebuilder学习5 部署运行测试
tags:
  - kubebuilder
categories:
  - Kubebuilder
date: 2023-07-17 20:17:27
---
#kubebuilder 

Controller和Kind都已经实现了，虽然还可以增加Webhook，但是这暂时不是我们关注的重点，我们现在可以将CRD安装到集群中进行测试了。

## 安装CRD
``` shell
(base) > $ make install                                                                                                                                                               
/Users/cui/go/bin/controller-gen "crd:trivialVersions=true" rbac:roleName=manager-role webhook paths="./..." output:crd:artifacts:config=config/crd/bases
kustomize build config/crd | kubectl apply -f -
customresourcedefinition.apiextensions.k8s.io/apiexamples.myapp.github.com created
                                                                                                                                                                                                                                                                                                               
(base) > $ k get crd                                                                                                                                                                   
NAME                           CREATED AT
apiexamples.myapp.github.com   2020-05-29T07:09:35Z
helloservices.cuizihan.xyz     2020-03-12T05:37:50Z

```
## 部署Controller

``` shell
(base) > $ make docker-build                                                                                                                                                           
docker build . -t registry.cn-hangzhou.aliyuncs.com/cuizihan/kubebuilder-example:latest
Sending build context to Docker daemon  85.32MB
Step 1/13 : FROM golang:1.13 as builder
 ---> 297e5bf50f50
Step 2/13 : WORKDIR /workspace
 ---> Using cache
 ---> 53f2feee3231
Step 3/13 : COPY go.mod go.mod
 ---> Using cache
 ---> c5d6bfc4122d
Step 4/13 : COPY go.sum go.sum
 ---> Using cache
 ---> 3d51653f300b
Step 5/13 : COPY vendor/ vendor/
 ---> Using cache
 ---> 37df790f1394
Step 6/13 : COPY main.go main.go
 ---> Using cache
 ---> b0c2379890df
Step 7/13 : COPY api/ api/
 ---> 9b49b9c856f4
Step 8/13 : COPY controllers/ controllers/
 ---> a9b84fcdbeaf
Step 9/13 : RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 GO111MODULE=on go build -a -mod=vendor -o manager main.go
 ---> Running in 18b5da680863
Removing intermediate container 18b5da680863
 ---> 020589723037
Step 10/13 : FROM alpine:3.11
3.11: Pulling from library/alpine
cbdbe7a5bc2a: Pull complete 
Digest: sha256:9a839e63dad54c3a6d1834e29692c8492d93f90c59c978c1ed79109ea4fb9a54
Status: Downloaded newer image for alpine:3.11
 ---> f70734b6a266
Step 11/13 : WORKDIR /
 ---> Running in a266895cda73
Removing intermediate container a266895cda73
 ---> c5314d4e6f15
Step 12/13 : COPY --from=builder /workspace/manager .
 ---> ca6d7d8ea86c
Step 13/13 : ENTRYPOINT ["/manager"]
 ---> Running in 1645f00d4dc9
Removing intermediate container 1645f00d4dc9
 ---> 2bf730bb057e
Successfully built 2bf730bb057e
Successfully tagged registry.cn-hangzhou.aliyuncs.com/cuizihan/kubebuilder-example:latest
                                                                                                                                                                                                     

(base) > $ make docker-push                                                                                                                                                            
docker push registry.cn-hangzhou.aliyuncs.com/cuizihan/kubebuilder-example:latest
The push refers to repository [registry.cn-hangzhou.aliyuncs.com/cuizihan/kubebuilder-example]
fd215ef7976c: Pushed 
3e207b409db3: Pushed 
latest: digest: sha256:9a1cc4ac52242dbfbd27733913fd2d3fd6a82cfd3226f79af9d40e5ff6804d40 size: 740


(base) > $ make deploy                                                                                                                                                                 
/Users/cui/go/bin/controller-gen "crd:trivialVersions=true" rbac:roleName=manager-role webhook paths="./..." output:crd:artifacts:config=config/crd/bases
cd config/manager && kustomize edit set image controller=registry.cn-hangzhou.aliyuncs.com/cuizihan/kubebuilder-example:latest
kustomize build config/default | kubectl apply -f -
namespace/kubebuilder-example-system unchanged
customresourcedefinition.apiextensions.k8s.io/apiexamples.myapp.github.com configured
role.rbac.authorization.k8s.io/kubebuilder-example-leader-election-role unchanged
clusterrole.rbac.authorization.k8s.io/kubebuilder-example-manager-role configured
clusterrole.rbac.authorization.k8s.io/kubebuilder-example-proxy-role unchanged
rolebinding.rbac.authorization.k8s.io/kubebuilder-example-leader-election-rolebinding unchanged
clusterrolebinding.rbac.authorization.k8s.io/kubebuilder-example-manager-rolebinding unchanged
clusterrolebinding.rbac.authorization.k8s.io/kubebuilder-example-proxy-rolebinding unchanged
service/kubebuilder-example-controller-manager-metrics-service unchanged
deployment.apps/kubebuilder-example-controller-manager created
                                                                                                                                                                                                     
(base) > $ k get deployment -n kubebuilder-example-system                                                                                                                              
NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
kubebuilder-example-controller-manager   1/1     1            1           19s

(base) > $ k get events -n kubebuilder-example-system                                                                                                                                  
LAST SEEN   TYPE     REASON              OBJECT                                                        MESSAGE
35s         Normal   LeaderElection      configmap/controller-leader-election-helper                   kubebuilder-example-controller-manager-d65d46c49-59vpg_df9b89bb-f0a7-404a-bb89-27f492f65a45 became leader
<unknown>   Normal   Scheduled           pod/kubebuilder-example-controller-manager-d65d46c49-59vpg    Successfully assigned kubebuilder-example-system/kubebuilder-example-controller-manager-d65d46c49-59vpg to minikube
60s         Normal   Pulled              pod/kubebuilder-example-controller-manager-d65d46c49-59vpg    Container image "gcr.io/kubebuilder/kube-rbac-proxy:v0.4.1" already present on machine
60s         Normal   Created             pod/kubebuilder-example-controller-manager-d65d46c49-59vpg    Created container kube-rbac-proxy
60s         Normal   Started             pod/kubebuilder-example-controller-manager-d65d46c49-59vpg    Started container kube-rbac-proxy
60s         Normal   Pulling             pod/kubebuilder-example-controller-manager-d65d46c49-59vpg    Pulling image "registry.cn-hangzhou.aliyuncs.com/cuizihan/kubebuilder-example:latest"
53s         Normal   Pulled              pod/kubebuilder-example-controller-manager-d65d46c49-59vpg    Successfully pulled image "registry.cn-hangzhou.aliyuncs.com/cuizihan/kubebuilder-example:latest"
53s         Normal   Created             pod/kubebuilder-example-controller-manager-d65d46c49-59vpg    Created container manager
53s         Normal   Started             pod/kubebuilder-example-controller-manager-d65d46c49-59vpg    Started container manager
62s         Normal   SuccessfulCreate    replicaset/kubebuilder-example-controller-manager-d65d46c49   Created pod: kubebuilder-example-controller-manager-d65d46c49-59vpg
62s         Normal   ScalingReplicaSet   deployment/kubebuilder-example-controller-manager             Scaled up replica set kubebuilder-example-controller-manager-d65d46c49 to 1
```

## 创建Object
准备如下的yaml
``` yaml
apiVersion: myapp.github.com/v1alpha1
kind: ApiExample
metadata:
  name: apiexample-sample
  namespace: kubebuilder-example-system
spec:
  # Add fields here
  schedule: "*/1 * * * *"
  startingDeadlineSeconds: 60
  concurrencyPolicy: Allow
  jobTemplate:
    spec:
      containers:
        - name: hello
          image: alpine
          args:
            - /bin/sh
            - -c
            - date; echo Hello from the Kubernetes cluster
      restartPolicy: OnFailure


```

使用yaml创建ApiExample之后，在controller的log中可以看到Reconcile的输出
![](img/20D1F4AD-2EB9-47E7-A0B2-1D0550BDF2B1.png
)

同时，可以看到ApiExample创建出的一个个pod。
![](img/96F140D6-1937-41B0-847E-3F452BD4CB65.png
)

需要注意的是，kubebuilder的rbac只提供了对CRD进行操作的权限，而对于Pod这种资源进行操作还需要我们自己进行rbac。


