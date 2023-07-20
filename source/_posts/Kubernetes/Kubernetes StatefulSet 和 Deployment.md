---
title: Kubernetes StatefulSet 和 Deployment
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes 

![](img/1*A_3DbP7Ee3ZbSyQ3x6pbNQ.png
)

阿里云二面时，面试官问到了Deployment和StatefulSet的区别，Deployment通过ReplicaSet来管理Pod的多个副本，同时Deployment提供了对历史版本的存储，用户可以通过指令来回滚Deployment。但是StatefulSet因为没有使用过，所以不太理解。

“Deployment用于部署无状态服务，StatefulSet用来部署有状态服务”，尽管可以通过为Deployment中的Pod挂载持久化卷的方式，但是如果发生Pod Reschedule，Deployment中的Pod仍然可能丢失持久化，而StatefulSet提供:
- 稳定的，唯一的网络标识
- 稳定的，持久的存储
- 有序的，优雅的部署和伸缩
- 有序的，优雅的删除和停止
- 有序的，自动的滚动更新

> 这里所说的稳定是针对Pod发生Reschedule之后，仍然保持之前的网络标识(hostName，在集群中的DNS Record，不包括PodIP)， 保持之前的持久化存储。比较适合采用StatefulSet部署的服务例如：MySQL等数据库服务

## StatefulSet的Spec
相比于Deployment，StatefulSet的Spec中，有如下值得关注的字段
``` go
type StatefulSetSpec {
	VolumeClaimTemplates []api.PersistentVolumeClaim
	ServiceName string
	PodManagementPolicy PodManagementPolicyType
}
```

- VolumeClainTemplates： 由StatefulSet创建的Pod将自动申领该templates对应的PVC，PVC的名称为`${volumeClaimTemplates.name}-${podHostName}`，和Pod一一对应。因此当Pod被Reschedule之后，它将仍然挂载该PVC Bound到的PV。当删除StatefulSet时，不会级联删除对应的PVC，所以要手动删除。
- ServiceName:  和这个StatefulSet所对应的Headless Service，必须在StatefulSet创建之前创建，用于为StatefulSet提供网络标识，Pod将从该Service处获得hostName和DNS Record，形式为: `${statefulset.name-ordinal}.serviceName.default.svc.cluster.local`。
	- 持久的网络标识的意义在于，即使Pod IP发生变化，其他使用这个Pod提供的服务的Pod时，仍然可以通过DNS找到这个Pod。

- PodManagementPolicy： 可取值为“OrderedReady” 和 “Parallel”。
	- OrderedReady: 
		- 当部署/扩容有N个副本的StatefulSet应用时，严格按照index从0到N-1的递增顺序创建，下一个Pod创建必须是前一个Pod Ready为前提。
		- 当删除/缩容有N个副本的StatefulSet应用时，严格按照index从N-1到0的递减顺序删除，下一个Pod删除必须是前一个Pod shutdown并完全删除为前提。
	- Parallel:
		- 和Deployment一样，当count发生变化时，立即创建\删除 Pod


## 最佳实践 Headless Service + StatefulSet
- Headless service 就是 clusterIP为None的service，也就是不需要clusterIP的service
- 一般来说，Headless Service和StatefulSet配合使用，为StatefulSet提供servicename
- Headless Service也可以和一组Pod一起使用，为Pod提供DNS Record
- Headless Service + StatefulSet = 一组具有固定网络标识，有固定存储的Pods
- https://segmentfault.com/a/1190000022993205
	