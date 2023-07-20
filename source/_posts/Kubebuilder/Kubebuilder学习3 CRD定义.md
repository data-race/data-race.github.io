---
title: Kubebuilder学习3 CRD定义
tags:
  - kubebuilder
categories:
  - Kubebuilder
date: 2023-07-17 20:17:27
---
#kubebuilder 

我们通过开发一个定时任务类型来学习如何使用kubebuilder。在第一部分，我们创建了API
``` shell
kubebuilder create api --group myapp --version v1alpha1 --kind ApiExample
```

之后，在框架代码的api文件夹和controllers文件夹分别生成了类型定义和控制器实现的代码文件。本节首先来看类型定义

## API设计
``` go
package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!
// NOTE: json tags are required.  Any new fields you add must have json tags for the fields to be serialized.

// ApiExampleSpec defines the desired state of ApiExample
type ApiExampleSpec struct {
	// INSERT ADDITIONAL SPEC FIELDS - desired state of cluster
	// Important: Run "make" to regenerate code after modifying this file

	// Foo is an example field of ApiExample. Edit ApiExample_types.go to remove/update
	Foo string `json:"foo,omitempty"`
}

// ApiExampleStatus defines the observed state of ApiExample
type ApiExampleStatus struct {
	// INSERT ADDITIONAL STATUS FIELD - define observed state of cluster
	// Important: Run "make" to regenerate code after modifying this file
}

// +kubebuilder:object:root=true

// ApiExample is the Schema for the apiexamples API
type ApiExample struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   ApiExampleSpec   `json:"spec,omitempty"`
	Status ApiExampleStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// ApiExampleList contains a list of ApiExample
type ApiExampleList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []ApiExample `json:"items"`
}

func init() {
	SchemeBuilder.Register(&ApiExample{}, &ApiExampleList{})
}
```
在类型定义的文件夹下，有一些我们需要完成的结构体定义，包括：
* ApiExampleSpec：Spec描述期望状态，K8s会根据真实状态Status来进行reconcile。
* ApiExampleStatus：Status记录集群观测到的资源对象所处的状态
* ApiExample：这个是我们的资源类型的定义，就像K8s的原生类型一样，包括Metadata(描述API版本和Kind)以及ObjectData（描述namespace，name，labels等）以及期望状态Sepc和观测到的状态Status
* ApiExampleList：是一个简单的包含我们自定义资源对象的容器的类型定义，用于LIST等批量操作。

在该文件最后，我们调用SchemeBuilder.Register将我们的GO type添加到API group中。

## 类型设计
* ApiExampleSpec：描述一个定时任务的期望状态，我们需要以下的部分：
	* Schedule：（the cron in CronJob)
	* A template for the Job to run: 这个我们用PodTemplateSpec来代替
	* A deadline for starting jobs: 如果我们错过了deadline，那么就等待下一次schedule time
	* 是否允许并发
	* 对于Job历史信息的记录
* ApiExampleStatus：
	* 对于正在运行的任务的记录
	* 上一次调度时间的记录

ApiExample和ApiExampleList不需要进行修改。

添加了实现后的ApiExampleSpec和ApiExampleStatus为：
``` go
type ApiExampleSpec struct {
	// INSERT ADDITIONAL SPEC FIELDS - desired state of cluster
	// Important: Run "make" to regenerate code after modifying this file

	// Foo is an example field of ApiExample. Edit ApiExample_types.go to remove/update
	Schedule                  string                 `json:"schedule"`
	StartingDeadlineSeconds   *int64                 `json:"startingDeadlineSeconds,omitempty"`
	ConcurrencyPolicy         ConcurrencyPolicy      `json:"concurrencyPolicy,omitempty"`
	Suspend                   *bool                  `json:"suspend,omitempty"`
	JobTemplate               corev1.PodTemplateSpec `json:"jobTemplate"`
	SuccessfulJobHistoryLimit *int32                 `json:"successfulJobHistoryLimit,omitempty"`
	FailedJobHistoryLimit     *int32                 `json:"failedJobHistoryLimit,omitempty"`
}

// ApiExampleStatus defines the observed state of ApiExample
type ApiExampleStatus struct {
	// INSERT ADDITIONAL STATUS FIELD - define observed state of cluster
	// Important: Run "make" to regenerate code after modifying this file
	Active []corev1.ObjectReference `json:"active,omitempty"`

	LastScheduleTime *metav1.Time `json:"lastScheduleTime,omitempty"`
}

```



