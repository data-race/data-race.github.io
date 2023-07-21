---
title: Kubernetes OwnerReference
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:27
---


#kubernetes 

![](img/2361530B-606D-475A-9D68-09DE284E1FD1.png
)
## OwnerReference解析
在Kubernetes中，有些情况下需要描述一个对象和另一个对象之间的从属关系。在一般的GC系统中，一个对象会知道它拥有哪些对象，这也是符合直觉的，但是在K8s中，则是反过来的，通过设定某个对象的OwnerReference，我们可以知道它的所属者是谁。
![](img/3b60b602-picture2mh.png
)
在OwnerReference中有一些字段：
+ APIVersion Kind Name UID都描述了Owner的基本信息，包括Owner具体的类型，Owner的ID。
+ Controller：这是一个*bool类型的字段，如果是true的话，说明不仅仅是Owner，而且是Controller。
+ BlockOwnerDeletion也是*bool，如果是true的话且使用foregroud的删除策略，那么除非owner被删除，owned的对象是无法被删除的。


## OwnerReference功能
ownerReference描述了对象之间的从属关系，这种从属关系主要的作用是在垃圾收集以及触发Owner的Reconcile方面。

### 垃圾收集
某些Kubernetes对象是其他一些对象的所有者，例如一个ReplicaSet是一组Pod的所有者。那么这组Pod的ownerReference就指向了Replicaset。在删除对象时，可以指定对象的附属者是否被连带删除掉。在Kubernetes中，有几种级联删除模式
+ background：The object itself deleted, after which the GC deletes the objects that it owned.
+ foreground: The object itself can not be deleted before all the objects that it owns are deleted.
+ orphan: The object itself is deleted. The owned objects are “orphaned” by removing the reference to the owner.

直观来说就是在foregroud模式下，如果我尝试去删除一个Replicaset，那么首先会删除它拥有的所有“blocking的”Pod（也就是BlockOwnerDeletion=true的pod），然后再删除Replicaset对象。
而在background的模式下，kubernetes会立刻删除Replicaset，然后垃圾收集器会去删除它拥有的那些pod。而orphan模式，pod会被保留下来。

通过设置Owner的DeletionPropagation：
![](img/94FACDA2-8676-4382-B10E-DA77C9CC35A6.png
)
可以分别使用这些策略。


### 触发Reconcile
在ownerReference中有controller字段，这个字段用来描述owner是否是owned的controller。因为作为controller，会经常需要使用reconcile来比较当前状态是否和预期状态一致，一般当owned的对象变化时，就会触发controller的reconcile。

在sigs.k8s.io/controller-runtime 中，有函数
![](img/2C621947-4C23-4764-AD3B-948EB430B5D0.png
)
可以帮助我们设置对象的ControllerReference，行为就是设置owner为controlled的ownerReference并且将controller字段设置为true，此外我们注意注释中提到，This is for reconciling the owner object on changes to controlled(with a Watch + EnqueueRequestForOwner)，也就是说仅仅设置controllerReference是不够的，还需要手动的设置watch。

在kubebuilder里，我们可以在SetupWithManger中进行Watch
![](img/D4686A46-9917-4F0A-AA39-BAEE02F29C63.png
)

或者在某些情况下，手动创建controller并watch

![](img/F5F4F254-E439-4A52-B132-E2562489D8B1.png
)

上述的Watch写法等价:
![](img/A2713286-4907-4B5F-964B-713D60C27AE3.png
)

