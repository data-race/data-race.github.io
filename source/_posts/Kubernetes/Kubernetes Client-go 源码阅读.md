---
title: Kubernetes Client-go 源码阅读
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes 

## Client-go
``` shell
client-go
...
├── discovery         #提供DiscoveryClient客户端
├── dynamic           #提供DynamicClient客户端，相比于ClientSet，可以操作CRD
├── informers         #提供不同资源的Informer的实现
├── kubernetes        #提供ClientSet客户端
├── listers           #提供资源的Lister功能，该功能对Get和List请求提供只读数据
├── plugin			 #提供其他云服务供应商的授权插件
├── rest				 #提供RESTClient客户端，对API Server进行RESTful操作，是其他Client的基础
├── scale				 #提供ScaleClient客户端，用户扩容或缩容Deployment、ReplicaSet等
├── tools				 #提供常用工具，如Reflector, Cache, DeltaFIFO, Indexers
├── transport			 #提供安全的TCP链接
└── util				 #工具
```

从功能上看Client-go提供了Golang和K8s交互的客户端库，不仅提供了对K8s API Server的多种客户端，而且为了方便用户对K8s进行二次开发，还提供了Reflector, Informer等包，帮助用户构建自己的Controller。


## Client

![](img/440E8566-BB52-4759-9FD2-A559FF4408E5.png
)

- RESTfulClient是最基本的Client，实现了RESTful风格的Api，是其他Client的基础。
``` go
// k8s.io/client-go/rest/client.go
type RESTClient struct {
	// base is the root URL for all invocations of the client
	base *url.URL
	// versionedAPIPath is a path segment connecting the base URL to the resource root
	versionedAPIPath string
	// contentConfig is the information used to communicate with the server.
	contentConfig ContentConfig
	// serializers contain all serializers for underlying content type.
	serializers Serializers
	// creates BackoffManager that is passed to requests.
	createBackoffMgr func() BackoffManager
	// TODO extract this into a wrapper interface via the RESTClient interface in kubectl.
	Throttle flowcontrol.RateLimiter
	// Set specific behavior of the client.  If not set http.DefaultClient will be used.
	Client *http.Client
}
```

- ClientSet在RESTfulClient的基础上封装了对Resource和Version的管理方法，每一个Resource可以理解为一个客户端，多个客户端的集合就是ClientSet，Client只能处理K8s内置资源。 ClientSet实现了`kubernetes.Interface`
``` go
// k8s.io/client-go/kubernetes/clientset.go
// Clientset contains the clients for groups. Each group has exactly one
// version included in a Clientset.
type Clientset struct {
	*discovery.DiscoveryClient
	admissionregistrationV1beta1 *admissionregistrationv1beta1.AdmissionregistrationV1beta1Client
	appsV1                       *appsv1.AppsV1Client
	appsV1beta1                  *appsv1beta1.AppsV1beta1Client
	appsV1beta2                  *appsv1beta2.AppsV1beta2Client
	auditregistrationV1alpha1    *auditregistrationv1alpha1.AuditregistrationV1alpha1Client
	authenticationV1             *authenticationv1.AuthenticationV1Client
	authenticationV1beta1        *authenticationv1beta1.AuthenticationV1beta1Client
	authorizationV1              *authorizationv1.AuthorizationV1Client
	authorizationV1beta1         *authorizationv1beta1.AuthorizationV1beta1Client
	autoscalingV1                *autoscalingv1.AutoscalingV1Client
	autoscalingV2beta1           *autoscalingv2beta1.AutoscalingV2beta1Client
	autoscalingV2beta2           *autoscalingv2beta2.AutoscalingV2beta2Client
	batchV1                      *batchv1.BatchV1Client
	batchV1beta1                 *batchv1beta1.BatchV1beta1Client
	batchV2alpha1                *batchv2alpha1.BatchV2alpha1Client
	certificatesV1beta1          *certificatesv1beta1.CertificatesV1beta1Client
	coordinationV1beta1          *coordinationv1beta1.CoordinationV1beta1Client
	coordinationV1               *coordinationv1.CoordinationV1Client
	coreV1                       *corev1.CoreV1Client
	eventsV1beta1                *eventsv1beta1.EventsV1beta1Client
	extensionsV1beta1            *extensionsv1beta1.ExtensionsV1beta1Client
	networkingV1                 *networkingv1.NetworkingV1Client
	networkingV1beta1            *networkingv1beta1.NetworkingV1beta1Client
	nodeV1alpha1                 *nodev1alpha1.NodeV1alpha1Client
	nodeV1beta1                  *nodev1beta1.NodeV1beta1Client
	policyV1beta1                *policyv1beta1.PolicyV1beta1Client
	rbacV1                       *rbacv1.RbacV1Client
	rbacV1beta1                  *rbacv1beta1.RbacV1beta1Client
	rbacV1alpha1                 *rbacv1alpha1.RbacV1alpha1Client
	schedulingV1alpha1           *schedulingv1alpha1.SchedulingV1alpha1Client
	schedulingV1beta1            *schedulingv1beta1.SchedulingV1beta1Client
	schedulingV1                 *schedulingv1.SchedulingV1Client
	settingsV1alpha1             *settingsv1alpha1.SettingsV1alpha1Client
	storageV1beta1               *storagev1beta1.StorageV1beta1Client
	storageV1                    *storagev1.StorageV1Client
	storageV1alpha1              *storagev1alpha1.StorageV1alpha1Client
}
```

- DynamicClient与ClientSet的不同在于添加了对CRD的访问
``` go
// k8s.io/client-go/dynamic/simple.go
func (c *dynamicClient) Resource(resource schema.GroupVersionResource) NamespaceableResourceInterface {
	return &dynamicResourceClient{client: c, resource: resource}
}
```
通过Resource方法传入一个GVR，从而动态生成一个该资源的客户端，用于处理该资源的操作。对该资源的Get和List会得到`unstructured`类型，需要使用runtime进行进一步的转换。

- DiscoveryClient用于发现API Server支持的资源组，资源版本，资源信息等。
``` go
// k8s.io/client-go/discovery/discovery_client.go
// ServerGroups returns the supported groups, with information like supported versions and the
// preferred version.
func (d *DiscoveryClient) ServerGroups() (apiGroupList *metav1.APIGroupList, err error) {...}

// ServerResourcesForGroupVersion returns the supported resources for a group and version.
func (d *DiscoveryClient) ServerResourcesForGroupVersion(groupVersion string) (resources *metav1.APIResourceList, err error)

...
```

## Informer机制
Kubernetes系统中，组件之间通过HTTP进行通信，为了保障消息的实时性，有效性等，Kubernetes采用了Informer机制，Kubernetes的其他组件都是使用Informer机制和API Server进行通信。
![](img/arch.jpeg
)
### Reflector和 DeltaFIFO
- Reflector用于监控(Watch)指定的资源，首先Reflector通过List获取资源的所有数据，并将其放入DeltaFIFO队列中，然后通过Watch操作，和API Server建立HTTP长连接，接受资源变更的事件(ADD, UPDATE, DELETE)，然后将对应的资源对象更新到本地缓存DeltaFIFO中，并更新资源的resourceVersion（和API的Version作区分）。
- DeltaFIFO是一个队列，保存有关资源对象的操作类型
``` go
type DeltaFIFO struct {
	...
	items map[string]Deltas  // 存储Object对应的Delta，也就是变更事件
	queue []string      // 存储Object的Key
}

type Deltas []Delta

type Delta struct {
	type DeltaType // Added, Updated, Deleted, Sync
	Object	interface{}
}
```
当队列中有元素进入后，会将其Pop，并交付对应的消费者，也就是Informer处理

### Informer
Informer负责:
- 接受DeltaFIFO的Pop方法弹出的资源对象变更事件
- 根据变更，更新本地缓存，即Indexer
- 将资源对象的变更事件交付给已经在Informer中注册的Handler来处理，ResourceEventHandler的定义如下
``` go
//k8s.io/client-go/tools/cache/controller.go
type ResourceEventHandler interface {
	OnAdd(obj interface{})
	OnUpdate(oldObj, newObj interface{})
	OnDelete(obj interface{})
}
```
所以我们自己的Controller只需要实现这个接口，就可以通过向Informer注册的方式，来处理特定资源的变更事件。通常，在编写一个Operator时，并不需要手动实现这个接口，只需要实现Reconcile方法就可以。

### Indexer
Indexer是Client-go的本地缓存，其中存储的资源数据和Etcd保持一致，由Informer进行写入。实际上Reconciler的Reconcile中，通过ObjectKey来获得资源数据的操作并没有和API Server进行通信，而是从Indexer中获取，这种操作可以有效降低API Server的压力。

![](img/url.png
)





 