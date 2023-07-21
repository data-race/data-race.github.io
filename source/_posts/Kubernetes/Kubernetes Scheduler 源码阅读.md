---
title: Kubernetes Scheduler 源码阅读
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:27
---
#kubernetes 


> k8s 1.19之后，对scheduler部分的源码有较大的修改，将原本面向过程的调度使用插件机制进行了重构，这是为了增强scheduler的可扩展性。但是schedule的总体过程没有变化

## 介绍
kube-scheduler是k8s的核心组件之一，主要负责整个几千年的Pod资源对象的调度，根据内置或者扩展的调度算法(预选与优选调度算法)，将未调度的Pod调度到最优的工作节点上，从而更加合理，更加充分的利用集群的资源。

![](img/图片1.png
)
schduler的实现位于 `kubernetes/pkg/scheduler`目录下
```shell
scheduler
├── algorithm           #定义预选算法(predicate)和优选算法(prority)
├── algorithmprovider   #将算法注册到工厂
├── api                                 #定义和调度相关的资源api，例如PredictPolicy
├── apis                                
├── core                                #scheduler核心，schedule发生位置
├── eventhandlers.go        #事件处理，处理者为scheduler
├── factory                         #工厂定义
├── framework
├── internal
├── metrics
├── nodeinfo
├── scheduler.go        #scheduler定义
├── util
└── volumebinder
```
 
 

## scheduler/algorithm
### 1. 预选(Predicate)
预选算法定义在`scheduler/algorithm/predicates.go`中，预选算法的主要功能是根据Pod声明的资源需求和节点的状态，筛选出可以满足需求的节点，所有的预选算法都需要实现为形如
```go
// FitPredicate is a function that indicates if a pod fits into an existing node.
// The failure information is given by the error.
type FitPredicate func(pod *v1.Pod, meta PredicateMetadata, 
                       nodeInfo *schedulernodeinfo.NodeInfo) (bool, []PredicateFailureReason, error)
```
的函数，这个函数接受一个pod对象、预选元信息以及节点的信息，返回一个bool值，以及可选的失败原因。K8s内置了很多预选调度算法，大部分都是和资源相关的，例如

- CheckVolumeBindingPred
- HostNamePred
- PodFitsResourcesPred
- NoDiskConflictPred
- PodToleratesNodeTainsPred
- CheckNodeLabelPresencePred
- CheckNodeMemoryPressurePred

等等，在`predicates.go`中定义了这些预选算法的名称和实际的函数，这里我们以检查Node是否满足Pod的资源需求的`PodFItsResources`算法为例
```go
// PodFitsResources checks if a node has sufficient resources, such as cpu, memory, gpu, opaque int resources etc to run a pod.
// First return value indicates whether a node has sufficient resources to run a pod while the second return value indicates the
// predicate failure reasons if the node has insufficient resources to run the pod.
func PodFitsResources(pod *v1.Pod, meta PredicateMetadata, nodeInfo *schedulernodeinfo.NodeInfo) (bool, []PredicateFailureReason, error) {
```
 首先检查节点上是否允许创建更多的Pod，如果超过允许创建的Pod的数目就在`predicateFails`中加入新的失败理由
```go
node := nodeInfo.Node()
    if node == nil {
        return false, nil, fmt.Errorf("node not found")
    }

    var predicateFails []PredicateFailureReason
    allowedPodNumber := nodeInfo.AllowedPodNumber()
    if len(nodeInfo.Pods())+1 > allowedPodNumber {
        predicateFails = append(predicateFails, NewInsufficientResourceError(v1.ResourcePods, 1, int64(len(nodeInfo.Pods())), int64(allowedPodNumber)))
    }
```
然后检查是否用户忽略了一些特定的资源限制
```go
// No extended resources should be ignored by default.
    ignoredExtendedResources := sets.NewString()

    var podRequest *schedulernodeinfo.Resource
    if predicateMeta, ok := meta.(*predicateMetadata); ok {
        podRequest = predicateMeta.podRequest
        if predicateMeta.ignoredExtendedResources != nil {
            ignoredExtendedResources = predicateMeta.ignoredExtendedResources
        }
    } else {
        // We couldn't parse metadata - fallback to computing it.
        podRequest = GetResourceRequest(pod)
    }
```
如果Pod没有申请任何资源，那么将默认实用所属的Namespace下的`LimitRange`资源来限制Pod的资源。如果此时Pod申请的资源为0，那么认为可以调度
```go
if podRequest.MilliCPU == 0 &&
        podRequest.Memory == 0 &&
        podRequest.EphemeralStorage == 0 &&
        len(podRequest.ScalarResources) == 0 {
        return len(predicateFails) == 0, predicateFails, nil
    }
```
如果Pod申请的资源不为0，那么判定节点上的可分配资源是否可以满足需求
```go
// CPU, 内存， 存储
allocatable := nodeInfo.AllocatableResource()
    if allocatable.MilliCPU < podRequest.MilliCPU+nodeInfo.RequestedResource().MilliCPU {
        predicateFails = append(predicateFails, NewInsufficientResourceError(v1.ResourceCPU, podRequest.MilliCPU, nodeInfo.RequestedResource().MilliCPU, allocatable.MilliCPU))
    }
    if allocatable.Memory < podRequest.Memory+nodeInfo.RequestedResource().Memory {
        predicateFails = append(predicateFails, NewInsufficientResourceError(v1.ResourceMemory, podRequest.Memory, nodeInfo.RequestedResource().Memory, allocatable.Memory))
    }
    if allocatable.EphemeralStorage < podRequest.EphemeralStorage+nodeInfo.RequestedResource().EphemeralStorage {
        predicateFails = append(predicateFails, NewInsufficientResourceError(v1.ResourceEphemeralStorage, podRequest.EphemeralStorage, nodeInfo.RequestedResource().EphemeralStorage, allocatable.EphemeralStorage))
    }

// 其他资源，例如GPU， InfiniBand
for rName, rQuant := range podRequest.ScalarResources {
        if v1helper.IsExtendedResourceName(rName) {
            // If this resource is one of the extended resources that should be
            // ignored, we will skip checking it.
            if ignoredExtendedResources.Has(string(rName)) {
                continue
            }
        }
        if allocatable.ScalarResources[rName] < rQuant+nodeInfo.RequestedResource().ScalarResources[rName] {
            predicateFails = append(predicateFails, NewInsufficientResourceError(rName, podRequest.ScalarResources[rName], nodeInfo.RequestedResource().ScalarResources[rName], allocatable.ScalarResources[rName]))
        }
    }
...
return len(predicateFails) == 0, predicateFails, nil
```


### 2. 优选(Priority)
优选是根据定义好的规则给所有节点进行打分，分数越高，则节点越适合运行给定的Pod，优选实现为一个形如
```go
// PriorityMapFunction is a function that computes per-node results for a given node.
// TODO: Figure out the exact API of this method.
// TODO: Change interface{} to a specific type.
type PriorityMapFunction func(pod *v1.Pod, meta interface{}, 
                              nodeInfo *schedulernodeinfo.NodeInfo) (schedulerapi.HostPriority, error)

// PriorityFunction is a function that computes scores for all nodes.
// DEPRECATED
// Use Map-Reduce pattern for priority functions.
type PriorityFunction func(pod *v1.Pod, 
                           nodeNameToInfo map[string]*schedulernodeinfo.NodeInfo, 
                           nodes []*v1.Node) (schedulerapi.HostPriorityList, error)

```
的函数。它的返回值包含了`HostPriority`结构体，这个结构体的定义如下:
```go
type HostPriority struct {
    Host  string
    Score int
}

type HostPriorityList []HostPriority
```
其中记载了Host所对应的分数。当使用不同的`PriorityMapFunction`得到每个节点在不同指标上的分数时，再使用Map-Reduce的方法，将它们的分数聚合起来。
以镜像本地优先(ImageLocality)为例
```go
func ImageLocalityPriorityMap(pod *v1.Pod, meta interface{}, nodeInfo *schedulernodeinfo.NodeInfo) (schedulerapi.HostPriority, error) {
    node := nodeInfo.Node()
    if node == nil {
        return schedulerapi.HostPriority{}, fmt.Errorf("node not found")
    }

    var score int
    if priorityMeta, ok := meta.(*priorityMetadata); ok {
        score = calculatePriority(sumImageScores(nodeInfo, pod.Spec.Containers, priorityMeta.totalNumNodes))
    } else {
        // if we are not able to parse priority meta data, skip this priority
        score = 0
    }

    return schedulerapi.HostPriority{
        Host:  node.Name,
        Score: score,
    }, nil
}
```
如果Host上有Pod所需的镜像，那么Host会获得更高的分数。
 

## scheduler/algorithm-provider
algorithm-provider包的作用是提供两个初始化的方法，分别将predicate和priority的方法注册到工厂中
```go
//algorithm-provider/defaulst/defaults.go 
func init() {
    registerAlgorithmProvider(defaultPredicates(), defaultPriorities())
}
```

## scheduler/factory
scheduler启动后的第一件事就是将K8s内置的调度算法(Predicate,Priority)注册到工厂中，调度算法的注册表与Scheme资源的注册表类似，都是通过map数据结构存放的
```go
var (
    schedulerFactoryMutex sync.RWMutex

    // maps that hold registered algorithm types
    fitPredicateMap        = make(map[string]FitPredicateFactory) // 预选
    mandatoryFitPredicates = sets.NewString()
    priorityFunctionMap    = make(map[string]PriorityConfigFactory) // 优选
    algorithmProviderMap   = make(map[string]AlgorithmProviderConfig) //所有类型的算法

    // Registered metadata producers
    priorityMetadataProducer  PriorityMetadataProducerFactory
    predicateMetadataProducer PredicateMetadataProducerFactory
)
```
## scheduler/scheduler.go
在`scheduler.go`中定义了Scheduler结构体，它包含了`kube-scheduler`的所有组件运行过程中的所有依赖的模块对象，`Scheduler`对象的实例化过程分为三部分:

- 实例化所有的Informer，因为`Scheduler`高度依赖对集群中资源变动的监控，所以需要实例化如下的Informer
```go
sched, err := scheduler.New(cc.Client,
        cc.InformerFactory.Core().V1().Nodes(),
        cc.PodInformer,
        cc.InformerFactory.Core().V1().PersistentVolumes(),
        cc.InformerFactory.Core().V1().PersistentVolumeClaims(),
        cc.InformerFactory.Core().V1().ReplicationControllers(),
        cc.InformerFactory.Apps().V1().ReplicaSets(),
        cc.InformerFactory.Apps().V1().StatefulSets(),
        cc.InformerFactory.Core().V1().Services(),
        cc.InformerFactory.Policy().V1beta1().PodDisruptionBudgets(),
        cc.InformerFactory.Storage().V1().StorageClasses(),
                           ...
        )                    
```

- 实例化所有的调度算法：调度算法的实例化
```go
sc, err := configurator.CreateFromProvider(*source.Provider)
```

- 为Informer添加对应的EventHandler，例如为Pod添加Informer
```go
// scheduled pod cache
    podInformer.Informer().AddEventHandler(
        cache.FilteringResourceEventHandler{
            FilterFunc: func(obj interface{}) bool {
                switch t := obj.(type) {
                case *v1.Pod:
                    return assignedPod(t)
                case cache.DeletedFinalStateUnknown:
                    if pod, ok := t.Obj.(*v1.Pod); ok {
                        return assignedPod(pod)
                    }
                    utilruntime.HandleError(fmt.Errorf("unable to convert object %T to *v1.Pod in %T", obj, sched))
                    return false
                default:
                    utilruntime.HandleError(fmt.Errorf("unable to handle object in %T: %T", sched, obj))
                    return false
                }
            },
            Handler: cache.ResourceEventHandlerFuncs{
                AddFunc:    sched.addPodToCache,
                UpdateFunc: sched.updatePodInCache,
                DeleteFunc: sched.deletePodFromCache,
            },
        },
    )
```
 
在为PodInformer添加Handlers时，会通过一个Filtering函数，该函数判定这个新建的Pod是不是需要调度，如果发现Pod的NodeName字段为空且Pod使用的Scheduler的名字为自己的名字，才回去调度这个Pod
``` go
// unscheduled pod queue
podInformer.Informer().AddEventHandler(
	cache.FilteringResourceEventHandler{
		FilterFunc: func(obj interface{}) bool {
			switch t := obj.(type) {
			case *v1.Pod:
				return !assignedPod(t) && responsibleForPod(t, schedulerName)
			case cache.DeletedFinalStateUnknown:
				if pod, ok := t.Obj.(*v1.Pod); ok {
					return !assignedPod(pod) && responsibleForPod(pod, schedulerName)
				}
				utilruntime.HandleError(fmt.Errorf("unable to convert object %T to *v1.Pod in %T", obj, sched))
				return false
			default:
				utilruntime.HandleError(fmt.Errorf("unable to handle object in %T: %T", sched, obj))
				return false
			}
		},
		Handler: cache.ResourceEventHandlerFuncs{
			AddFunc:    sched.addPodToSchedulingQueue,
			UpdateFunc: sched.updatePodInSchedulingQueue,
			DeleteFunc: sched.deletePodFromSchedulingQueue,
		},
	},
)
```
处理函数的逻辑很简单，只是将Pod放入到调度队列中。
当Scheduler初始化完成之后，就会运行Scheduler的Run函数，这个函数执行不断的执行`scheduleOne`，尝试去完成一个Pod的调度
``` go
// Run begins watching and scheduling. It waits for cache to be synced, then starts a goroutine and returns immediately.
func (sched *Scheduler) Run() {
	if !sched.config.WaitForCacheSync() {
		return
	}

	go wait.Until(sched.scheduleOne, 0, sched.config.StopEverything)
}
```

在`scheduleOne` 中，scheduler会首先尝试从队列中获取一个待调度的Pod，然后一次调用Predicate和Priority算法，来进行Pod的调度。
最后调用Assume方法，将Pod放置到指定的节点上。
``` go
func (sched *Scheduler) assume(assumed *v1.Pod, host string) error {
	// Optimistically assume that the binding will succeed and send it to apiserver
	// in the background.
	// If the binding fails, scheduler will release resources allocated to assumed pod
	// immediately.
	assumed.Spec.NodeName = host

	if err := sched.config.SchedulerCache.AssumePod(assumed); err != nil {
		klog.Errorf("scheduler cache AssumePod failed: %v", err)

		// This is most probably result of a BUG in retrying logic.
		// We report an error here so that pod scheduling can be retried.
		// This relies on the fact that Error will check if the pod has been bound
		// to a node and if so will not add it back to the unscheduled pods queue
		// (otherwise this would cause an infinite loop).
		sched.recordSchedulingFailure(assumed, err, SchedulerError,
			fmt.Sprintf("AssumePod failed: %v", err))
		return err
	}
	// if "assumed" is a nominated pod, we should remove it from internal cache
	if sched.config.SchedulingQueue != nil {
		sched.config.SchedulingQueue.DeleteNominatedPodIfExists(assumed)
	}

	return nil
}

```




