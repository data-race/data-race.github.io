---
title: Kubernetes Client-go 源码阅读2 Reflector 和 Indexer
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes 
## Introduction
在之前的源码阅读中，我们了解了Controller机制的工作流程。Controller依赖于Client-go的Informer来获取对象的变动事件。而Informer依赖Reflector监听资源的变化，依赖Indexer对资源进行持久化存储。本文通过阅读相关部分的源码，探索`Reflector`和`Indexer`的工作原理

## Reflector
`Reflector`的定义位于`k8s.io/client-go/tools/cache/reflector.go`，它是一个结构体，具体的定义如下
``` go
// Reflector watches a specified resource and causes all changes to be reflected in the given store.
type Reflector struct {
	// name identifies this reflector. By default it will be a file:line if possible.
	name string

	// The name of the type we expect to place in the store. The name
	// will be the stringification of expectedGVK if provided, and the
	// stringification of expectedType otherwise. It is for display
	// only, and should not be used for parsing or comparison.
	expectedTypeName string
	// An example object of the type we expect to place in the store.
	// Only the type needs to be right, except that when that is
	// `unstructured.Unstructured` the object's `"apiVersion"` and
	// `"kind"` must also be right.
	expectedType reflect.Type
	// The GVK of the object we expect to place in the store if unstructured.
	expectedGVK *schema.GroupVersionKind
	// The destination to sync up with the watch source
	store Store
	// listerWatcher is used to perform lists and watches.
	listerWatcher ListerWatcher

	// backoff manages backoff of ListWatch
	backoffManager wait.BackoffManager
	// initConnBackoffManager manages backoff the initial connection with the Watch call of ListAndWatch.
	initConnBackoffManager wait.BackoffManager

	resyncPeriod time.Duration
	// ShouldResync is invoked periodically and whenever it returns `true` the Store's Resync operation is invoked
	ShouldResync func() bool
	// clock allows tests to manipulate time
	clock clock.Clock
	// paginatedResult defines whether pagination should be forced for list calls.
	// It is set based on the result of the initial list call.
	paginatedResult bool
	// lastSyncResourceVersion is the resource version token last
	// observed when doing a sync with the underlying store
	// it is thread safe, but not synchronized with the underlying store
	lastSyncResourceVersion string
	// isLastSyncResourceVersionUnavailable is true if the previous list or watch request with
	// lastSyncResourceVersion failed with an "expired" or "too large resource version" error.
	isLastSyncResourceVersionUnavailable bool
	// lastSyncResourceVersionMutex guards read/write access to lastSyncResourceVersion
	lastSyncResourceVersionMutex sync.RWMutex
	// WatchListPageSize is the requested chunk size of initial and resync watch lists.
	// If unset, for consistent reads (RV="") or reads that opt-into arbitrarily old data
	// (RV="0") it will default to pager.PageSize, for the rest (RV != "" && RV != "0")
	// it will turn off pagination to allow serving them from watch cache.
	// NOTE: It should be used carefully as paginated lists are always served directly from
	// etcd, which is significantly less efficient and may lead to serious performance and
	// scalability problems.
	WatchListPageSize int64
	// Called whenever the ListAndWatch drops the connection with an error.
	watchErrorHandler WatchErrorHandler
}

```

其中比较重要的成员是用于执行listAndWatch的`listerWatcher`以及用于存储结果的`store`，此外还有一些和listAndWatch相关的属性，例如`WatchListPageSize`用于定义请求的page的大小，pagesize存在的意义是如果一个资源有太多的对象，会导致一个请求去传递太多的数据，因此pagesize限制一个请求中的返回对象的数目，缓解服务器压力。以及用于指明需要去listAndWatch的资源类型的成员，如`expectedType`，`expectedGVK`，注意这个`expectedType`是一个`reflect.Type`类型，或许这就是`Reflector`名称的来历。

### Reflector的初始化
当初始化一个Reflector时，需要传入name，用于log，还有一个`ListerWatcher`，执行实际的`ListAndWatch`操作，还有`expectedType`，用于从ListWatch的结果中反射解析出对应的对象，还有一个store，做结果的存储，store实现了`Store`接口，提供了常用的增删改查方法，Reflector会根据ListWatch的结果来更新Store。
``` go
// NewNamedReflector same as NewReflector, but with a specified name for logging
func NewNamedReflector(name string, lw ListerWatcher, expectedType interface{}, store Store, resyncPeriod time.Duration) *Reflector {
	realClock := &clock.RealClock{}
	r := &Reflector{
		name:          name,
		listerWatcher: lw,
		store:         store,
		// We used to make the call every 1sec (1 QPS), the goal here is to achieve ~98% traffic reduction when
		// API server is not healthy. With these parameters, backoff will stop at [30,60) sec interval which is
		// 0.22 QPS. If we don't backoff for 2min, assume API server is healthy and we reset the backoff.
		backoffManager:         wait.NewExponentialBackoffManager(800*time.Millisecond, 30*time.Second, 2*time.Minute, 2.0, 1.0, realClock),
		initConnBackoffManager: wait.NewExponentialBackoffManager(800*time.Millisecond, 30*time.Second, 2*time.Minute, 2.0, 1.0, realClock),
		resyncPeriod:           resyncPeriod,
		clock:                  realClock,
		watchErrorHandler:      WatchErrorHandler(DefaultWatchErrorHandler),
	}
	r.setExpectedType(expectedType)
	return r
}
```

### Reflector的启动
Informer会启动一个底层的Controller来对资源对象进行ListWatch，从而获取相关变动事件，然后将这些事件dispatch到对应的handler，在`k8s.io/client-go/tools/cache/controller.go`中，我们可以看到一个`Reflector`时如何被创建和启动的。
``` go
func (c *controller) Run(stopCh <-chan struct{}) {
	defer utilruntime.HandleCrash()
	go func() {
		<-stopCh
		c.config.Queue.Close()
	}()
	r := NewReflector(
		c.config.ListerWatcher,
		c.config.ObjectType,
		c.config.Queue,
		c.config.FullResyncPeriod,
	)
	...
	var wg wait.Group
	wg.StartWithChannel(stopCh, r.Run)
	wait.Until(c.processLoop, time.Second, stopCh)
	wg.Wait()
}
```
这里可以看到，传给Reflector的是一个`DeltaFIFO`的队列，这个队列会暂存资源变动的事件。
Reflector的启动就是执行`ListAndWatch`这个方法，这个方法的具体实现非常长，我们将其分解来看。
- 首先`ListAndWatch`去List所有的资源，获取资源版本等信息
这里新开了一个goroutine，创建了一个pager来进行list，如果list成功，则close(listCh)，通知`ListAndWatch`的goroutine，已经成功完成了List。这里的pager
```go
klog.V(3).Infof("Listing and watching %v from %s", r.expectedTypeName, r.name)
var resourceVersion string
options := metav1.ListOptions{ResourceVersion: r.relistResourceVersion()}
...
var list runtime.Object
var paginatedResult bool
var err error
listCh := make(chan struct{}, 1)
panicCh := make(chan interface{}, 1)
go func() {
	defer func() {
		if r := recover(); r != nil {
			panicCh <- r
		}
	}()
	// Attempt to gather list in chunks, if supported by listerWatcher, if not, the first
	// list request will return the full response.
	pager := pager.New(pager.SimplePageFunc(func(opts metav1.ListOptions) (runtime.Object, error) {
		return r.listerWatcher.List(opts)
	}))
	switch {
	case r.WatchListPageSize != 0:
		pager.PageSize = r.WatchListPageSize
	case r.paginatedResult:
	case options.ResourceVersion != "" && options.ResourceVersion != "0":
		pager.PageSize = 0
	}

	list, paginatedResult, err = pager.List(context.Background(), options)
	if isExpiredError(err) || isTooLargeResourceVersionError(err) {
		r.setIsLastSyncResourceVersionUnavailable(true)
		list, paginatedResult, err = pager.List(context.Background(), metav1.ListOptions{ResourceVersion: r.relistResourceVersion()})
	}
	close(listCh)
}()
```
这里，pager就会按照事先定义的pagesize，不断的发起List，每次请求不超过pagesize个对象，直到list完成。 pager大概的逻辑是
``` go
for {
    switch {
        case <- ctx.Done():
            return res
        default:
    }
	 // do new list
    ...
}
```

当`ListAndWatch`的goroutine收到了list已经完成的信号之后，会进行校验，并且将结果和`Store`中进行同步。
``` go

resourceVersion = listMetaInterface.GetResourceVersion()
items, err := meta.ExtractList(list)
if err := r.syncWith(items, resourceVersion); err != nil {
	return fmt.Errorf("unable to sync list result: %v", err)
}
r.setLastSyncResourceVersion(resourceVersion)
return nil

// syncWith replaces the store's items with the given list.
func (r *Reflector) syncWith(items []runtime.Object, resourceVersion string) error {
	found := make([]interface{}, 0, len(items))
	for _, item := range items {
		found = append(found, item)
	}
	return r.store.Replace(found, resourceVersion)
}

```
这里关键的步骤就是从List的结果中extract出items，然后和存储进行sync，sync的具体实现取决于store的`Replace` 具体实现。当sync完成后，可以认为store中存储了最新的结果，一般来说，reflector后面会接一个`DeltaFIFO`。 Replace atomically does two things: 
1.  it adds the given objects using the Sync or Replace DeltaType and then 
2.  it does some deletions.

- Watch
当List完成之后，Reflector启动Watch，通过维持一个http长连接，不断的获取资源的最新变动，这部分逻辑比较简单，不列举代码，总之watch获得的结果也会根据Event的类型存入DeltaFIFO中，例如获取了某个资源的Update，就会调用DeltaFIFO的Update方法，存入(“Updated”，Obj)这样的Delta对象
``` go
// Update is just like Add, but makes an Updated Delta.
func (f *DeltaFIFO) Update(obj interface{}) error {
	f.lock.Lock()
	defer f.lock.Unlock()
	f.populated = true
	return f.queueActionLocked(Updated, obj)
}
```

## Indexer
在controller.Run中，启动Reflector之后，controller会开启一个不终止的循环不断的调用`ProcessFunc`，来处理从`DeltaFIFO`中Pop出来的Delta对象。最终还是会根据Delta的类型，将请求dispatch到对应的handler，在handler中，再去将其加入到workqueue，进入调谐，当然这是题外话。
```go
switch d.Type {
case Sync, Replaced, Added, Updated:
	if old, exists, err := clientState.Get(obj); err == nil && exists {
		if err := clientState.Update(obj); err != nil {
			return err
		}
		handler.OnUpdate(old, obj)
	} else {
		if err := clientState.Add(obj); err != nil {
			return err
		}
		handler.OnAdd(obj)
	}
case Deleted:
	if err := clientState.Delete(obj); err != nil {
		return err
	}
	handler.OnDelete(obj)
}
```
我们看到这里除了调用handler的Update，Add等方法， 还调用了clientState的Update，Add等方法，这个clientState就是Indexer，也就是一个本地的缓存，在调谐时，如果需要去查找相关的资源，可以直接从indexer中查找，而不需要再从apiserver请求，从而可以缓解服务器的压力。

### Indexer是什么
顾名思义，Indexer的直接翻译是索引器，它的功能就是缓存资源对象。它的定义是
```go
type Indexer interface {
	Store
	// Index returns the stored objects whose set of indexed values
	// intersects the set of indexed values of the given object, for
	// the named index
	Index(indexName string, obj interface{}) ([]interface{}, error)
	// IndexKeys returns the storage keys of the stored objects whose
	// set of indexed values for the named index includes the given
	// indexed value
	IndexKeys(indexName, indexedValue string) ([]string, error)
	// ListIndexFuncValues returns all the indexed values of the given index
	ListIndexFuncValues(indexName string) []string
	// ByIndex returns the stored objects whose set of indexed values
	// for the named index includes the given indexed value
	ByIndex(indexName, indexedValue string) ([]interface{}, error)
	// GetIndexer return the indexers
	GetIndexers() Indexers

	// AddIndexers adds more indexers to this store.  If you call this after you already have data
	// in the store, the results are undefined.
	AddIndexers(newIndexers Indexers) error
}
type IndexFunc func(obj interface{}) ([]string, error)
type Indexers 	map[string]IndexFunc

type Index map[string]sets.String
type Indices map[string]Index
```

对于一组资源对象，我们可以从很多的维度构建索引，
- Indexers其实是一组索引生成函数，每个键值对都代表不同的索引维度，最常见的自然是基于Namespace进行索引，此时Indexers的Key就是字符串namespace，而Value则为函数MetaNamespaceIndexFunc，它的参数是任意的资源对象，返回的则是该资源对象所处的Namespace。
- 而Indices则是一个存储索引的结构。类似地，它的Key也是构建索引的维度，例如此处的namespace，值是索引Index，
- 而Index则是真正存储索引的结构，Key为某个索引值，Value则是与该索引值匹配的资源对象实例的Key。 

K8s提供了Indexer的一个默认实现`k8s.io/client-go/tools/cache/store.go`的cache，它底层使用theadSafeMap实现存储功能。
在初始化一个cache时，要提供一个keyFunc，这个函数从对象提取key，这个keyFunc提取出的key类似于主键，keyFunc是唯一的。
如果要建立新的索引，可以通过`AddIndexers`来添加一组索引生成器，然后调用`UpdateIndices`来真正的建立索引。

通过`IndexKeys`方法，可以查看某个索引值的所有资源对象的key
``` go
// IndexKeys returns a list of the Store keys of the objects whose indexed values in the given index include the given indexed value.
// IndexKeys is thread-safe so long as you treat all items as immutable.
func (c *threadSafeMap) IndexKeys(indexName, indexedValue string) ([]string, error) 
```

总而言之，Indexer的作用是缓存资源对象，而且它通过构建多维索引的方式，可以大大加快查找的速度。

![](img/233474baffdc2e36733d95cee393b8fb.webp
)
关于Indexer讲解比较详细的博客[client-go 之 Indexer 的理解-技术圈](https://jishuin.proginn.com/p/763bfbd2c2bb)