---
title: Kubernetes Scheduler Extender机制
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes 

## 前言

通过阅读scheduler的机制，我们了解到K8s的调度器大概可以分为三个重要的阶段
- Predicate
- Prioritize
- Bind
![](img/scheduling-framework-extensions.png
)
K8s允许我们在调度的一些关键节点使用插件的方式对调度器进行扩展，在K8s Schedule Framework的设计提案中，认为在调度周期中，可以供扩展的位置有:
- 队列排序： 对调度队列中待调度的Pod进行排序
- 前置过滤： 预先判断Pod和集群是否满足某些必要条件，如果不满足，则终止调度
- 过滤： 就是Predicate，筛选出满足的节点
- 后置过滤:  当Predicate发现没有资源满足Pod时，可以使用后置过滤来进行抢占
- 前置评分
- 评分
- 还有一些更复杂的方法，例如Reserve, Unreserve, PreBind, Bind等
https://github.com/kubernetes/enhancements/blob/master/keps/sig-scheduling/624-scheduling-framework/README.md
在k8s 1.19+之后，插件机制正式被并入主分支，取代了之前的调度框架。

## Extender机制
一般情况下我们有三种方法来扩展调度器:
- 使用插件机制，直接对调度器的源码进行修改，为调度器添加插件
- 保持原有的默认调度器不变，启动一个新的定制的调度器，然后在Pod中指定schedulerName
- **使用Extender机制对原有的调度器进行扩展**
![](img/arch.jpg
)

### Webhook

scheduler extender 表现为一个webhook，无需修改原有的scheduler代码，只需要在运行scheduler时加一个配置即可，extender的配置数据结构如下:
``` go
// HTTPExtender implements the algorithm.SchedulerExtender interface.
type HTTPExtender struct {
	extenderURL      string
	preemptVerb      string
	filterVerb       string
	prioritizeVerb   string
	bindVerb         string
	weight           int
	client           *http.Client
	nodeCacheCapable bool
	managedResources sets.String
	ignorable        bool
}
```

我们需要提供extender提供服务的地址，以及preemptVerb, filterVerb，prioritizeVerb, bindVerb这四个api的名称，这四个操作分别对应抢占、预选、优选、绑定，scheduler通过读取一个json配置文件来初始化Extender，以阿里云的gpu-share-extender为例，一个配置文件具有如下的形式
``` json
{
  "kind": "Policy",
  "apiVersion": "v1",
  "extenders": [
    {
      "urlPrefix": "http://127.0.0.1:32766/gpushare-scheduler",
      "filterVerb": "filter",
      "bindVerb":   "bind",
      "enableHttps": false,
      "nodeCacheCapable": true,
      "managedResources": [
        {
          "name": "aliyun.com/gpu-mem",
          "ignoredByScheduler": false
        }
      ],
      "ignorable": false
    }
  ]
}
```
其中filterVerb和bindVerb指定了相关方法的地址
[image:C94D36BD-EF1C-44DF-8C2D-27F0A33AD094-71786-000001D976A51B81/D8FCEC0A-35E0-4628-8221-ABB2A74209AF.png]


### Extender请求参数
对于Filter和Prioritize方法，请求的参数为一个Pod和一组Node
``` go
// ExtenderArgs represents the arguments needed by the extender to filter/prioritize
// nodes for a pod.
type ExtenderArgs struct {
	// Pod being scheduled
	Pod   api.Pod      `json:"pod"`
	// List of candidate nodes where the pod can be scheduled
	Nodes api.NodeList `json:"nodes"`
}
```

对于Binding方法，请求的参数为
``` go
// ExtenderBindingArgs represents the arguments to an extender for binding a pod to a node.
type ExtenderBindingArgs struct {
	// PodName is the name of the pod being bound
	PodName string
	// PodNamespace is the namespace of the pod being bound
	PodNamespace string
	// PodUID is the UID of the pod being bound
	PodUID types.UID
	// Node selected by the scheduler
	Node string
}
```

### Extender结果返回
请求的结构体会被序列化为HTTP请求的Body，在Extender的处理逻辑中，只需要反序列化它，然后处理逻辑，返回结果即可
- Filter返回结果的结构体 
``` go
// ExtenderFilterResult represents the results of a filter call to an extender
type ExtenderFilterResult struct {
    // Filtered set of nodes where the pod can be scheduled; to be populated
    // only if ExtenderConfig.NodeCacheCapable == false
    Nodes *v1.NodeList
    // Filtered set of nodes where the pod can be scheduled; to be populated
    // only if ExtenderConfig.NodeCacheCapable == true
    NodeNames *[]string
    // Filtered out nodes where the pod can't be scheduled and the failure messages
    FailedNodes FailedNodesMap
    // Error message indicating failure
    Error string
}
```

- Priority返回的结构体
``` go
// HostPriority represents the priority of scheduling to a particular host, higher priority is better.
type HostPriority struct {
    // Name of the host
    Host string
    // Score associated with the host
    Score int64
}

// HostPriorityList declares a []HostPriority type.
type HostPriorityList []HostPriority
```

- Binding不需要返回特别的结果，只需要返回是否存在错误即可






