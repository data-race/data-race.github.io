---
title: K8s 的包管理器—— Helm
tags:
  - k8s实践
categories:
  - Kubernetes
date: 2023-07-17 20:17:27
---
#k8s实践 

## 背景
使用Yaml清单可以帮我们轻松声明一个资源对象，但是在创建一个具体服务的过程中，使用YAML文件仍然有一些不足之处。这些文件中有许多重复，例如在创建Deployment和Service时，在两个对象对应的Yaml清单中，都有相同的label selector，相同的端口号等。
![](img/截屏2020-09-15下午6.55.39.png
)
我们希望有一种方法，可以定义类似于container.name或者container.port之类的变量。我们在Yaml文件中直接使用这些变量，而这些变量的值在一处定义，如果要修改，那么只需要在一处进行修改，而使用到这个变量的地方会自动的更新。

## Helm
Helm是CNCF的一个项目，提供对于K8s的应用管理功能。Helm中一个应用包叫做Helm Charts，它包含了需要让应用运行所需的所有资源，所有以来，以及其他配置信息。

Helm Chart和其他包管理器（apt， homebrew）不同，它并不包含应用完整的二进制软件， helm chart只是一个包含元信息，告诉kubernetes可以去那里找到应用的所使用的镜像。

## Helm 安装
https://docs.helm.sh/using_helm/#installing-helm 我们参照官方文档可以找到helm被托管的github仓库，在[Releases · helm/helm · GitHub](https://github.com/helm/helm/releases)可以找到helm的release，下载对应的release，解压后，将二进制文件放到bin中就可以。

*现在helm是v3版本，我们学习过程中使用的是v2*

+ 先为helm创建serviceAccount
``` yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
```

``` shell
k apply -f helm-auth.yaml
```

+ 初始化Helm
``` shell
helm init --service-account tiller 
```

在初始化过程中遇到tiller镜像无法拉取的问题：
![](img/207E0F0B-4562-4B4D-903C-6A8BD04EFE8E.png
)

有两种解决方案，1是使用阿里云镜像仓库拉取镜像，修改tag。
``` shell
sudo docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/tiller:v2.16.9
sudo docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/tiller:v2.16.9 gcr.io/kubernetes-helm/tiller:v2.16.9
```

2是在初始化helm时直接用阿里云的仓库
``` shell
helm init --upgrade -i registry.cn-hangzhou.aliyuncs.com/google_containers/tiller:v2.16.9 --stable-repo-url https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts
```

+ 初始化成功
![](img/22691D48-6D1C-4D78-B988-70C9AFBADA10.png
)

## Helm Demo
我们尝试用helm安装一个应用
![](img/60542AE9-E81A-471E-A49D-EA0B7E30FB40.png
)
这个简单的helm chart有一个Chart.yaml记录整个应用的版本信息。有一个values.yaml定义若干变量
![](img/472C0499-1FE5-4D7E-9B98-1EA21AC1237B.png
)
那么在template下的deployment和service中，可以直接使用这些变量：
![](img/AC1D648E-8856-4BCC-89FA-D84763521AFA1.png
)
启动应用：
![](img/11C1B802-D8B7-495A-B71D-985D624BBD27.png
)
打开localhost:32229就可以看到
![](img/362156F9-2E01-476E-AA0B-A1B2B185EEF1.png
)



