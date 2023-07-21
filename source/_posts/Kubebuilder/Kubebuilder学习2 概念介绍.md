---
title: Kubebuilder学习2 概念介绍
tags:
  - kubebuilder
categories:
  - Kubebuilder
date: 2023-07-17 20:17:27
---
#kubebuilder
我们跟随官方的tutorial，通过实现一个CronJob Operator，来学习如何开发一个Operator。搭建脚手架的部分在第一章已经学习过，我们直接进入开发部分：

## 程序入口
首先来看脚手架中生成的main.go文件：
``` go
package main

import (
	"flag"
	"os"

	myappv1alpha1 "github.com/cuizihan/kubebuilder-example/api/v1alpha1"
	"github.com/cuizihan/kubebuilder-example/controllers"
	"k8s.io/apimachinery/pkg/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	_ "k8s.io/client-go/plugin/pkg/client/auth/gcp"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	// +kubebuilder:scaffold:imports
)

```

Main中import了一些需要的包，包括核心的controller运行时包，以及一些工具包。

每个controller都需要一个Scheme，可以理解为结构、模式，提供从Kind到Go type的映射，之后我们会学习Kind的一些有关概念：
``` go
var (
	scheme   = runtime.NewScheme()
	setupLog = ctrl.Log.WithName("setup")
)

func init() {
	_ = clientgoscheme.AddToScheme(scheme)

	_ = myappv1alpha1.AddToScheme(scheme)
	// +kubebuilder:scaffold:scheme
}
```

最后，在main函数中，也就是程序的入口中，我们设立了一些标志，并制定了manager，用来追踪我们controller的运行，同时设置共享的缓存和客户端：
``` go

func main() {
	var metricsAddr string
	var enableLeaderElection bool
	flag.StringVar(&metricsAddr, "metrics-addr", ":8080", "The address the metric endpoint binds to.")
	flag.BoolVar(&enableLeaderElection, "enable-leader-election", false,
		"Enable leader election for controller manager. Enabling this will ensure there is only one active controller manager.")
	flag.Parse()

	ctrl.SetLogger(zap.New(func(o *zap.Options) {
		o.Development = true
	}))

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme:             scheme,
		MetricsBindAddress: metricsAddr,
		LeaderElection:     enableLeaderElection,
		Port:               9443,
	})
	if err != nil {
		setupLog.Error(err, "unable to start manager")
		os.Exit(1)
	}

	if err = (&controllers.ApiExampleReconciler{
		Client: mgr.GetClient(),
		Log:    ctrl.Log.WithName("controllers").WithName("ApiExample"),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "ApiExample")
		os.Exit(1)
	}
	// +kubebuilder:scaffold:builder

	setupLog.Info("starting manager")
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		setupLog.Error(err, "problem running manager")
		os.Exit(1)
	}
}
```


## Group Version Kind  Scheme
* Group & Version： Group是一组功能的集合，例如Kubeflow是一个Group，它由多种operator构成，Group有不同的版本。
* Kind & Resources：每一个Group都包含了多个API，每个API称为一个Kind，不同版本的Group之间，Kind可能会发生变化。对于Kind的使用就是Resource，或者说Resource是Kind的实例，例如Kind Pod所对应的Resource就是pods。
* Scheme：当我们特指一个在指定版本Group中的Kind时，我们称之为GroupVersionKind（GVK），如果是资源的话就叫GVR。在框架中，每个GVK都对应包中的一个Go类型：
![](img/4E866F72-1B4F-4EC4-A1C6-77F7E4C880CE.png
)
如何将Kind和Go Type对应在一起依赖Scheme，例如将Json/Yaml解析成我们的Go type就是依赖Scheme，在groupversion_info.go中可以看到Scheme是如何被构建的：
![](img/A20427E0-4E79-4EAC-888F-80F2DB6775A1.png
)


AddToScheme在main中被调用，将我们定义的Kind的结构信息告诉集群。从而完成Kind的Register。