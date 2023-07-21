---
title: Kubernetes Device Plugin机制
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes 
# K8s Device Plugin 

## Kubelet 与 Device Plugin
Device Plugin将被作为DaemonSet部署，每个节点上都会运行一个Device Plugin的实例。Device Plugin通过将向Kubelet注册一个gRPC服务，提供ListAndWatch和Allocate等方法，Kubelet调用这些方法可以进行资源的状态查询和分配。

![](img/device_plugin.png
)


## Device Plugin
### 初始化NVML
```go
if err := nvml.Init(); err != nil {
        log.SetOutput(os.Stderr)
        log.Printf("Failed to initialize NVML: %v.", err)
        log.Printf("If this is a GPU node, did you set the docker default runtime to `nvidia`?")
        log.Printf("You can check the prerequisites at: https://github.com/NVIDIA/k8s-device-plugin#prerequisites")
        log.Printf("You can learn how to set the runtime at: https://github.com/NVIDIA/k8s-device-plugin#quick-start")
        log.Printf("If this is not a GPU node, you should set up a toleration or nodeSelector to only deploy this plugin on GPU nodes")
        if failOnInitErrorFlag {
            return fmt.Errorf("failed to initialize NVML: %v", err)
        }
        select {}
    }
```

### FileWatcher和SignalWatcher
启动FileWatcher和SignalWatcher，FileWatcher监听kubelet的socket是否被创建，如果创建，则尝试重启device plugin，SignalWatcher处理系统信号。
``` go
...
restart:
    for {
        select {
            case event := <-watcher.Events:
                if event.Name == pluginapi.KubeletSocket && event.Op&fsnotify.Create == fsnotify.Create {
                    log.Printf("inotify: %s created, restarting.", pluginapi.KubeletSocket)
                goto restart
                }
            
            case s:= <-sigs:
            // handle signal 
            ...
        }
    }
```

### 启动Device Plugin
启动device plugin包括如下过程
- 初始化设备信息，从nvml获得node上所有的gpu，然后根据索引来读取gpu的信息，包括uuid等。
- 初始化gRPC，启动gRPC服务
- 向Kubelet注册gRPC，先尝试和kubelet进行socket连接，然后从这个连接上构建一个client。然后构建一个RegisterRequest，最后使用client远程调用Register方法，传入RegisterRequest，完成device plugin的注册。

``` go
// Start starts the gRPC server, registers the device plugin with the Kubelet,
// and starts the device healthchecks.
func (m *NvidiaDevicePlugin) Start() error {
    m.initialize()

    err := m.Serve()
    if err != nil {
        log.Printf("Could not start device plugin for '%s': %s", m.resourceName, err)
        m.cleanup()
        return err
    }
    log.Printf("Starting to serve '%s' on %s", m.resourceName, m.socket)

    err = m.Register()
    if err != nil {
        log.Printf("Could not register device plugin: %s", err)
        m.Stop()
        return err
    }
    log.Printf("Registered device plugin for '%s' with Kubelet", m.resourceName)

    go m.CheckHealth(m.stop, m.cachedDevices, m.health)

    return nil
}
```


### gRPC 服务
提供服务: Device Plugin向kubelet提供以下的服务
#### GetDevicePluginOptions 
告知kubelet是否支持PreStartContainer和GetPreferredAllocation方法。
#### ListAndWatch
告知kubelet所有的设备信息以及设备的更新。
``` go
// ListAndWatch lists devices and update that list according to the health status
func (m *NvidiaDevicePlugin) ListAndWatch(e *pluginapi.Empty, s pluginapi.DevicePlugin_ListAndWatchServer) error {
    s.Send(&pluginapi.ListAndWatchResponse{Devices: m.apiDevices()})

    for {
        select {
        case <-m.stop:
            return nil
        case d := <-m.health:
            // FIXME: there is no way to recover from the Unhealthy state.
            d.Health = pluginapi.Unhealthy
            log.Printf("'%s' device marked unhealthy: %s", m.resourceName, d.ID)
            s.Send(&pluginapi.ListAndWatchResponse{Devices: m.apiDevices()})
        }
    }
}
```

#### GetPreferredAllocation 
为一组ContainerRequests生成prefered的Allocation，具体来说，一个ContainerRequest包含了`AllocationSize`,`MustIncludeDeviceIDs`和`AvailableDeviceIDs`，device plugin的职责是根据一些策略，生成从`AvailableDeviceIDs`中选择`AllocationSize`个设备，且必须包含`MustIncludeDeviceIDs`。
``` go
// GetPreferredAllocation returns the preferred allocation from the set of devices specified in the request
func (m *NvidiaDevicePlugin) GetPreferredAllocation(ctx context.Context, r *pluginapi.PreferredAllocationRequest) (*pluginapi.PreferredAllocationResponse, error) {
	response := &pluginapi.PreferredAllocationResponse{}
	// 对于每个container request，为其找到合适的设备id
	for _, req := range r.ContainerRequests {
		available, err := gpuallocator.NewDevicesFrom(req.AvailableDeviceIDs)
		if err != nil {
			return nil, fmt.Errorf("Unable to retrieve list of available devices: %v", err)
		}

		required, err := gpuallocator.NewDevicesFrom(req.MustIncludeDeviceIDs)
		if err != nil {
			return nil, fmt.Errorf("Unable to retrieve list of required devices: %v", err)
		}
		// 根据策略进行实际的分配
		allocated := m.allocatePolicy.Allocate(available, required, int(req.AllocationSize))

		var deviceIds []string
		for _, device := range allocated {
			deviceIds = append(deviceIds, device.UUID)
		}
		// 返回结果，形式为一组deviceIDs
		resp := &pluginapi.ContainerPreferredAllocationResponse{
			DeviceIDs: deviceIds,
		}

		response.ContainerResponses = append(response.ContainerResponses, resp)
	}
	return response, nil
}

```
#### Allocate 
传入一组ContainerRequests，完成实际的分配步骤。在Nvidia device plugin中，根据uuid得到device ID。
会根据实际的策略选择将device ID挂载到容器的环境变量或者容器的volume中。

nvidia-docker的容器运行时会在启动容器之前调用prestart hook，读取这些注入的device ID，这个hook会调用nvidia-container-cli，分析出需要映射的GPU设备、库文件、可执行文件，在容器启动后挂载带容器内部(例如会将设备挂载到/dev下)，以达到配置好GPU环境的目的。

![](img/1014716-20191015192117663-341668066.png
)

```go
// Allocate which return list of devices.
func (m *NvidiaDevicePlugin) Allocate(ctx context.Context, reqs *pluginapi.AllocateRequest) (*pluginapi.AllocateResponse, error) {
	responses := pluginapi.AllocateResponse{}
	for _, req := range reqs.ContainerRequests {
		response := pluginapi.ContainerAllocateResponse{}
		uuids := req.DevicesIDs
		deviceIDs := m.deviceIDsFromUUIDs(uuids)
		// 以环境变量的方式挂载入容器，由容器运行时完成实际的工作
		if deviceListStrategyFlag == DeviceListStrategyEnvvar {
			response.Envs = m.apiEnvs(m.deviceListEnvvar, deviceIDs)
		}
		// 以volume的方式挂载到容器内
		if deviceListStrategyFlag == DeviceListStrategyVolumeMounts {
			response.Envs = m.apiEnvs(m.deviceListEnvvar, []string{deviceListAsVolumeMountsContainerPathRoot})
			response.Mounts = m.apiMounts(deviceIDs)
		}
		if passDeviceSpecsFlag {
			response.Devices = m.apiDeviceSpecs(nvidiaDriverRootFlag, uuids)
		}

		responses.ContainerResponses = append(responses.ContainerResponses, &response)
	}

	return &responses, nil
}

```

#### PreStartContainer
容器启动之前的钩子

## Nvidia Docker Runtime
![](img/cuda_gpu_dirver.png
)




