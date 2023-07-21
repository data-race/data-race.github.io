---
title: Deep Learning Tool Box 2
date: 2023-07-17 20:17:25
tags: [MatLab]
---

#MatLab

## 准备
在配置完成MJS集群后，如果节点上有可用GPU(驱动正常，有CUDA)，那么在Matlab中可以使用这些GPU，可以在命令行中输入gpuDevice和gpuDeviceCount来查看可用设备，以及可用设备的个数


![](img/DA17F4D6-73E2-42B9-8F21-D4DB8AA282DE.png
)

实验使用的是4节点的MJS集群，每个节点有2块1080ti的GPU，每个节点有20个worker，所以在实际使用中，每个节点只有两个节点是有worker的，根据matlab文档的描述：

![](img/60970741-AEA0-44F9-9F39-DD5CD3B9CA36.png
)

如果worker是不拥有GPU的，那么worker将不会被用于训练的计算，只会被用于数据的预处理。所以在训练的时候，可以设置工作负载为每个节点2个worker，那么将使用全部的GPU进行训练。修改trainingOptions部分，增大MaxEpoch，修改WorkerLoad为2

``` Matlab
options = trainingOptions('sgdm',...
    'MiniBatchSize', miniBatchSize,...
    'Verbose', true,...
    'InitialLearnRate', initialLearnRate,...
    'L2Regularization', 1e-10,...
    'MaxEpochs', 50,...
    'Shuffle', 'every-epoch',...
    'ValidationData', imdsValidation,...
    'ExecutionEnvironment', 'parallel',...
    'Plots', 'training-progress',...
    'WorkerLoad', 2,...
	  'LearnRateDropFactor', 0.1,...
	  'LearnRateSchedule', 'piecewise',...
    'LearnRateDropPeriod', 25);
```

开启训练后，可以在每个节点上看到使用GPU的进程中出现了Matlab创建的任务进程

![](img/B70D8485-07D1-4A71-AC5B-9A501C7654B8.png
)

可以看到每个卡上都有不止一个进程使用gpu，说明一个worker在使用gpu时也进行了并行的优化，这一点和pytroch，tensorflow的独占式使用是不一样的。

## 结果
使用4个节点8个GPU进行并行训练的速度是非常快的，40个Epoch只用了21分钟：
![](img/34ABA02E-5D20-42A8-871D-AD596FC54E1B.png)
