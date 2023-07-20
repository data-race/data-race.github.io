---
title: 'Kubernetes GVK, GVR'
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes 
## GVK和GVR

![](img/D0BD589C-746E-43A5-9434-E1C9900DAFA5.png
)

- K8s 中的API Group是相关功能的集合，每个group包含一个或多个version，例如core, batch, apps，core是一个特殊的资源组，他没有组名，也可以称为GroupLess
- Version是资源的版本，例如v1, v1alpha1, v1beta2等，不同的version含义不同
	- Alpha：内部测试版，代码可能存在缺陷与漏洞，版本可能被删除
	- Beta： 社区测试版，经过广泛测试，版本会有较小改变，但是不会被删除
	- 稳定版：正式版本
	
- Kind每个group-version中包含多个API类型， 称之为Kinds
- Resource是Kind在API中的标识，通常和Kind一一对应


## 源码的实现
一个GVK可以标识一个唯一的Kind，一个GVR可以标识一个唯一的Resource
``` go
//k8s.io/apimachinery/pkg/apis/meta/v1/group_version.go
// GroupVersionKind unambiguously identifies a kind.  It doesn't anonymously include GroupVersion
// to avoid automatic coersion.  It doesn't use a GroupVersion to avoid custom marshalling
//
// +protobuf.options.(gogoproto.goproto_stringer)=false
type GroupVersionKind struct {
	Group   string `json:"group" protobuf:"bytes,1,opt,name=group"`
	Version string `json:"version" protobuf:"bytes,2,opt,name=version"`
	Kind    string `json:"kind" protobuf:"bytes,3,opt,name=kind"`
}

// GroupVersionResource unambiguously identifies a resource.  It doesn't anonymously include GroupVersion
// to avoid automatic coersion.  It doesn't use a GroupVersion to avoid custom marshalling
//
// +protobuf.options.(gogoproto.goproto_stringer)=false
type GroupVersionResource struct {
	Group    string `json:"group" protobuf:"bytes,1,opt,name=group"`
	Version  string `json:"version" protobuf:"bytes,2,opt,name=version"`
	Resource string `json:"resource" protobuf:"bytes,3,opt,name=resource"`
}
```


## Scheme
Scheme资源注册表维护GVK和Type的对应关系
``` go
// k8s.io/apimachinery/pkg/runtime/scheme.go
type Scheme struct {
	gvkToType map[schema.GroupVersionKind]reflect.Type
	typeToGVK map[reflect.Type][]schema.GroupVersionKind

	// unversionedTypes are transformed without conversion in ConvertToVersion.
	unversionedTypes map[reflect.Type]schema.GroupVersionKind

	// unversionedKinds are the names of kinds that can be created in the context of any group
	// or version
	// TODO: resolve the status of unversioned types.
	unversionedKinds map[string]reflect.Type
	...
}
```

在每一个k8s的group 目录下，都有一个install.go，其作用就是将资源信息注册到资源表中，以core为例
``` go
//pkg/apis/core/install/install.go
// Install registers the API group and adds types to a scheme
func Install(scheme *runtime.Scheme) {
	utilruntime.Must(core.AddToScheme(scheme))
	utilruntime.Must(v1.AddToScheme(scheme))
	utilruntime.Must(scheme.SetVersionPriority(v1.SchemeGroupVersion))
}

```