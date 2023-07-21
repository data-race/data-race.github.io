---
title: Kuberentes Controller 机制 源码阅读
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes 

![](img/结构.png
)

在对Client-go的阅读中，初步对informer机制有了了解。Reflector通过ListWatch方法不断获取对象的变化，存入Delta FIFO Queue，Informer消耗Delta FIFO Queue中的Delta对象，由Indexer来更新本地缓存，同时Informer根据Delta对象，来将变动Dispatch到Controller中的Event Handlers。Controller会根据这些变动来采取相应的行为，在一些成熟的Operator开发框架中(Kube-builder， Operator-SDK)中，我们往往只需要在SetUpWithManager中设置好感兴趣的资源类型，然后写一个Reconcile方法即可，但是为了加深对Controller的理解，熟悉Controller底层的工作机制是十分必要的。
这篇笔记将介绍Controller的工作原理。

## Controller结构体
我们以最简单的`ReplicaSet`的controller为例
``` go
type ReplicaSetController struct {
	schema.GroupVersionKind	// ReplicaSet的GVK   
	kubeClient clientset.Interface		// k8s client
	podControl controller.PodControlInterface		// 对Pod进行增删改查的封装
	burstReplicas int		// 副本数
	syncHandler func(rsKey string) error		// 起到Reconcile功能的函数，放在这里是方便进行test
	expectations *controller.UIDTrackingControllerExpectations
	rsLister appslisters.ReplicaSetLister		// 从Indexer中读取rs的接口
	rsListerSynced cache.InformerSynced		// 判断Indexer中数据是否同步过
	podLister corelisters.PodLister			// 从Indexer中读pod的接口
	podListerSynced cache.InformerSynced		// 判断Indexer中的数据是否同步过
	
	queue workqueue.RateLimitingInterface		// Work Queue
}
```
我们先不逐个介绍每个field的功能，首先来看`ReplicaSetController`是如何被初始化的。


## Controller 初始化
`NewReplicaSetController`方法通过调用`NewBaseController`方法可以获得一个初始化好的ReplicasetController对象
``` go
rsc := &ReplicasetController{...}
rsInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
	AddFunc:    rsc.enqueueReplicaSet,
	UpdateFunc: rsc.updateRS,
	DeleteFunc: rsc.enqueueReplicaSet,
})
rsc.rsLister = rsInformer.Lister()
rsc.rsListerSynced = rsInformer.Informer().HasSynced

podInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
	AddFunc: rsc.addPod,
	UpdateFunc: rsc.updatePod,
	DeleteFunc: rsc.deletePod,
})
rsc.podLister = podInformer.Lister()
rsc.podListerSynced = podInformer.Informer().HasSynced
rsc.syncHandler = rsc.syncReplicaSet
return rsc
```

可以看到初始化主要是
- 初始化`ReplicaSetController`对象
- 向ReplicaSet和Pod的两个Informer注册EventHandlers
- 设置`syncHandler`


## Controller Run()
Controller-Manager在初始化各个资源的Controller时，会调用到Controller的Run方法，我们来看`ReplicaSetController`的Run方法做了什么:
``` go
// Run begins watching and syncing.
func (rsc *ReplicaSetController) Run(workers int, stopCh <-chan struct{}) {
	defer utilruntime.HandleCrash()
	defer rsc.queue.ShutDown()
	...
	if !controller.WaitForCacheSync(rsc.Kind, stopCh, rsc.podListerSynced, rsc.rsListerSynced) {
		return
	}

	for i := 0; i < workers; i++ {
		go wait.Until(rsc.worker, time.Second, stopCh)
	}
	<-stopCh
}

func (rsc *ReplicaSetController) worker() {
	for rsc.processNextWorkItem() {
	}
}
```

- 在Run中，Controller首先会等待Indexer中Cache的同步
- 然后会启动若干goroutine来执行worker方法，直到stopCh发出结束信号

`worker`方法就是不断的执行`processNextWorkItem`，尝试从work queue中取出item，并且进行处理。

## Work Queue 
在介绍WorkQueue之前，我们先来看WorkQueue中的Item是从哪里来的，在注册到Informer的EventHandlers中，需要对关注的对象的ADD, DELETE和UPDATE事件进行处理，这里以`ReplicaSetController` 的`addPod`为例:

``` go
// When a pod is created, enqueue the replica set that manages it and update its expectations.
func (rsc *ReplicaSetController) addPod(obj interface{}) {
	pod := obj.(*v1.Pod)
	...
	if controllerRef := metav1.GetControllerOf(pod); controllerRef != nil {
		rs := rsc.resolveControllerRef(pod.Namespace, controllerRef)
		...
		rsc.enqueueReplicaSet(rs)
		return	
	}
	...
}
```

- 首先将传入的obj转换成Pod
- 根据pod的object Reference尝试去获得管理这个Pod的ReplicaSet的引用，如果找到，则将其加入到WorkQueue
- 如果没找到，做其他处理(认为这个Pod是孤儿，会重新enqueue所有的Replicatset，看是否有Replicaset愿意领养它)

那么我们可以发现，这些EventHandlers总是会去尝试获取和这个Event相关的资源对象，然后将它加入到WorkQueue，等待进一步处理。

WorkQueue和普通的队列一样，有入队出队等基本方法。在Controller中，还对普通的队列进行了额外的扩展，加入了延时入队和限速的功能，首先来看WorkQueue最底层的接口
``` go
type Interface interface {
	Add(item interface{})
	Len() int
	Get() (item interface{}, shutdown bool)
	Done(item interface{})
	ShutDown()
	ShuttingDown() bool
}
```
可以看到这个接口和普通的FIFO队列一样，提供了入队出队的方法，还提供了关闭队列的方法。
在FIFO Queue的基础上，还封装了延时队列
``` go
type DelayingInterface interface {
	Interface
	// AddAfter adds an item to the workqueue after the indicated duration has passed
	AddAfter(item interface{}, duration time.Duration)
}
```
添加了AddAfter方法，一般在等待某个条件是，例如等待Pod变为Running，会使用这个方法。
利用DelayingQueue的延迟入队的特性，又封装了限速队列，限制元素进入队列的速率，防止Worker处理的速度不够，导致队列增长过快。 限速队列中使用了多种限速算法，如令牌桶，指数排队算法。
``` go
// RateLimitingInterface is an interface that rate limits items being added to the queue.
type RateLimitingInterface interface {
	DelayingInterface
	// AddRateLimited adds an item to the workqueue after the rate limiter says it's ok
	AddRateLimited(item interface{})
	Forget(item interface{})
	NumRequeues(item interface{}) int
}

```

## Sync Object
在`processNextWorkItem`中，会首先尝试从Work Queue中出队一个key，这个key就是NamespacedName，然后会调用`syncReplicaSet` ，这个sync的函数顾名思义，是同步ReplicaSet对象，让它向期望状态靠拢，其实这就是我们Reconcile的逻辑实际执行的地方，这里不再做更多介绍。

``` go
func (rsc *ReplicaSetController) processNextWorkItem() bool {
	key, quit := rsc.queue.Get()
	if quit {
		return false
	}
	defer rsc.queue.Done(key)

	err := rsc.syncHandler(key.(string))
	if err == nil {
		rsc.queue.Forget(key)
		return true
	}

	utilruntime.HandleError(fmt.Errorf("Sync %q failed with %v", key, err))
	rsc.queue.AddRateLimited(key)

	return true
}

```

值得注意的是，这个key是个形如 “namespace/name” 的string类型，其实就类似于我们在Reconcile中用到的NamespacedName.

