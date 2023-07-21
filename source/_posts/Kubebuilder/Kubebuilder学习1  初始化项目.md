---
title: Kubebuilder学习1  初始化项目
tags:
  - kubebuilder
categories:
  - Kubebuilder
date: 2023-07-17 20:17:27
---
#kubebuilder
## 前言

在对Kubernetes进行二次开发时，经常遇到基础资源类型无法满足需求的情况，这时需要我们自己设计资源类型，扩展Kubernetes的api。常用的方法是开发Kubernetes Operator，所谓Operator就是CRD + Controller，通过这种方式，可以让我们自定义的资源类型和K8s原生的资源类型一样，被系统编排调度。

之前学过operator-sdk的一些基本使用，这次，我们来学习另一种operator开发框架Kubebuilder的使用。我们会通过一个例子来学习一个Operator的开发流程。我们参考官方的教学：https://book.kubebuilder.io/introduction.html。

## 安装

macOS上安装比较简单
``` shell
# kubebuilder
brew install kubebuilder
# kustomize
brew install kustomize
```

## 创建Operator项目并初始化

* 如果在GOPATH/src下创建，那么可以略过这步：
首先我们创建一个go module：
``` shell
$ mkdir kubebuilder-example 
$ cd kubebuilder-example  
$ go mod init github.com/cuizihan/kubebuilder-example                                             
```

* 然后，在项目文件夹下执行kubebuilder的初始化指令：
``` shell
# 注意， domain不能带子路径
$ kubebuilder init --domain github.com
```

执行完之后，就可以看到项目中多出很多生成的代码文件，Makefile，等构件文件：
``` shell
$ tree                                                                                                                                                               
.
├── Dockerfile
├── Makefile
├── PROJECT
├── bin
│   └── manager
├── config
│   ├── certmanager
│   │   ├── certificate.yaml
│   │   ├── kustomization.yaml
│   │   └── kustomizeconfig.yaml
│   ├── default
│   │   ├── kustomization.yaml
│   │   ├── manager_auth_proxy_patch.yaml
│   │   ├── manager_webhook_patch.yaml
│   │   └── webhookcainjection_patch.yaml
│   ├── manager
│   │   ├── kustomization.yaml
│   │   └── manager.yaml
│   ├── prometheus
│   │   ├── kustomization.yaml
│   │   └── monitor.yaml
│   ├── rbac
│   │   ├── auth_proxy_role.yaml
│   │   ├── auth_proxy_role_binding.yaml
│   │   ├── auth_proxy_service.yaml
│   │   ├── kustomization.yaml
│   │   ├── leader_election_role.yaml
│   │   ├── leader_election_role_binding.yaml
│   │   └── role_binding.yaml
│   └── webhook
│       ├── kustomization.yaml
│       ├── kustomizeconfig.yaml
│       └── service.yaml
├── go.mod
├── go.sum
├── hack
│   └── boilerplate.go.txt
└── main.go

9 directories, 29 files
```

## 新增API
新增API：假定我们想要开发一个简单的资源类型叫ApiExample，那么我们需要执行
``` shell
$ kubebuilder create api --group myapp --version v1alpha1 --kind ApiExample
Create Resource [y/n]
y
Create Controller [y/n]
y
Writing scaffold for you to edit...
api/v1alpha1/apiexample_types.go
```
然后就可以发现controllers和apis文件夹下多了一些go文件，分别是控制器和资源类型的定义，这也是我们需要实现的部分。为了方便依赖管理，我们使用vendor。用Goland导入项目，就可以看到项目的完整结构了：
![](img/4275CC82-F406-44C6-8820-CD4B5C5625F4.png
)
其中，config文件夹下有一组配置文件：
	* config/default: 包括用来启动controller的标准配置
	* config/manager: 将controller做为pod启动在集群中
	* config/rbac: 创建服务账号以及角色绑定的配置文件

* 测试：我们使用的是本地的minikube环境来测试，所以只要在命令行中输入几条指令就可以，如果需要在远程的集群上进行测试，那么需要使用镜像仓库来部署，参考：https://www.chenshaowen.com/blog/how-to-develop-a-operator-using-kubebuilder.html
我们首先开启minikube，并将docker环境切换到minikube下：
``` shell
$ minikube start --image-mirror-country='cn' --image-repository='registry.cn-hangzhou.aliyuncs.com/google_containers'
$ eval $(minikube docker-env) 
```
	* 安装CRD到集群
``` shell
$ make install                                                                                                                                                                             
/Users/cui/go/bin/controller-gen "crd:trivialVersions=true" rbac:roleName=manager-role webhook paths="./..." output:crd:artifacts:config=config/crd/bases
kustomize build config/crd | kubectl apply -f -
customresourcedefinition.apiextensions.k8s.io/apiexamples.myapp.github.com created
# 查看crd
$ k get crd                                                                                                                                                                                
NAME                           CREATED AT
apiexamples.myapp.github.com   2020-05-28T03:22:30Z
```
	* 部署Controller
``` makefile
# Image URL to use all building/pushing image targets
IMG ?= registry.cn-hangzhou.aliyuncs.com/cuizihan/kubebuilder-example:latest
```
因为在下一步部署Controller时，需要构建镜像并上传拉取，如果使用默认的镜像仓库，会很慢，导致拉取失败。接着，我们构建并推送镜像：
``` shell
$ make docker-build
$ make docker-push
```
这一步会遇到一些问题，首先是构建阶段的test会失败，原因不知道，暂时是把test给跳过了。还有就是对Dockerfile中的一些基镜像进行了修改。
构建好之后，再执行部署controller的命令
``` shell
$ make deploy                                                                                                                                                                              
/Users/cui/go/bin/controller-gen "crd:trivialVersions=true" rbac:roleName=manager-role webhook paths="./..." output:crd:artifacts:config=config/crd/bases
cd config/manager && kustomize edit set image controller=controller:latest
kustomize build config/default | kubectl apply -f -
namespace/kubebuilder-example-system created
customresourcedefinition.apiextensions.k8s.io/apiexamples.myapp.github.com configured
role.rbac.authorization.k8s.io/kubebuilder-example-leader-election-role created
clusterrole.rbac.authorization.k8s.io/kubebuilder-example-manager-role created
clusterrole.rbac.authorization.k8s.io/kubebuilder-example-proxy-role created
rolebinding.rbac.authorization.k8s.io/kubebuilder-example-leader-election-rolebinding created
clusterrolebinding.rbac.authorization.k8s.io/kubebuilder-example-manager-rolebinding created
clusterrolebinding.rbac.authorization.k8s.io/kubebuilder-example-proxy-rolebinding created
service/kubebuilder-example-controller-manager-metrics-service created
deployment.apps/kubebuilder-example-controller-manager created
# 查看controller
$ kubectl get deployment -n kubebuilder-example-system                                                                                                                                
NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
kubebuilder-example-controller-manager   1/1     1            1           9m56s
```
注意，这一步也有一些问题，会遇到镜像拉不下来的情况

![](img/25EB2659-F351-432C-982E-7F0067EDDB65.png
)

由于minikube的docker是不走代理的，解决方案是用docker通过代理拉取gcr.io的镜像，然后推送到自己的阿里云仓库，再切换到minikube的docker，从阿里云拉取镜像。
	* 创建CRD对象
``` shell
$ k apply -f config/samples/myapp_v1alpha1_apiexample.yaml                                                                                                                      
apiexample.myapp.github.com/apiexample-sample created

$ k get apiexamples.myapp.github.com -o yaml                                                                                                                                   
apiVersion: v1
items:
- apiVersion: myapp.github.com/v1alpha1
  kind: ApiExample
  metadata:
    annotations:
      kubectl.kubernetes.io/last-applied-configuration: |
        {"apiVersion":"myapp.github.com/v1alpha1","kind":"ApiExample","metadata":{"annotations":{},"name":"apiexample-sample","namespace":"default"},"spec":{"foo":"bar"}}
    creationTimestamp: "2020-05-28T04:56:30Z"
    generation: 1
    name: apiexample-sample
    namespace: default
    resourceVersion: "1686224"
    selfLink: /apis/myapp.github.com/v1alpha1/namespaces/default/apiexamples/apiexample-sample
    uid: fb7bdb5a-b80f-4318-8b76-0b7b028c2a28
  spec:
    foo: bar
kind: List
metadata:
  resourceVersion: ""
  selfLink: ""
```

	* 可以通过make uninstall 和 k delete deployment将crd和controller从集群中删除。
