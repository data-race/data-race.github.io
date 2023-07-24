---
title: Deep Learning ToolBox
tags:
  - MatLab
categories:
  - MatLab
date: 2023-07-17 20:17:25
---
#MatLab 

## 介绍
深度学习工具包提供了设计和实现深度神经网络的框架，以及已经实现的算法，预训练好的模型和应用。用户可以使用卷积神经网络或者是长短时记忆神经网络来对图片、序列、文本信息等输入进行分类和回归。同时，深度学习工具包提供了Designer App，使用Designer可以快速的，可视化的设计分析训练一个神经网络。
同时，深度学习工具包和其他的框架，例如Pytorch、Tensorflow都可以进行模型的相互转化。深度学习工具包提供了许多预训练的模型用于迁移学习，例如ResNet50，SequeezeNet等。

## 训练流程
在进行模型训练之前，需要先准备用于训练的数据集
``` Matlab
imds = imageDatastore('/Users/cui/parforTrain/cifar10/train', ...
    'IncludeSubfolders', true,...
    'LabelSource', 'foldernames');
 
imdsTest = imageDatastore('/Users/cui/parforTrain/cifar10/test',...
    'IncludeSubfolders', true,...
    'LabelSource', 'foldernames');
 
[imdsTrain, imdsValidation] = splitEachLabel(imds, 0.9);
```

Matlab的数据集一般是文件夹-子文件夹的结构，每个子文件夹是一类样本，样本的label就是子文件夹的名称。
然后需要定义模型的结构，类似于Pytorch等框架中对于模型等分层定义，Matlab中的模型也是组织成若干层：
``` Matlab
layers = [
    imageInputLayer(imageSize)
    convolutionalBlock(netWidth, netDepth)
    maxPooling2dLayer(2, 'Stride', 2)
    convolutionalBlock(2 * netWidth, netDepth)
    maxPooling2dLayer(2, 'Stride', 2)
    convolutionalBlock(4 * netWidth, netDepth)
    averagePooling2dLayer(8)
    fullyConnectedLayer(10)
    softmaxLayer
    classificationLayer
];

```

定义好模型的结构之后，就可以调用trainNetwork函数进行训练，函数返回训练好的模型。
``` Matlab
net = trainNetwork(imdsTrain, layers, options);
```

训练时的配置全部包含在trainNetwork函数的第三个参数options中，这是trainingOptions函数创建的类型，用于指定训练时所采用的batchsize，学习率，正则化参数，以及最重要的所采用的计算资源等配置，trainingOptions的一个例子是：
``` Matlab
options = trainingOptions('sgdm',...
        'MiniBatchSize', miniBatchSize,...
        'Verbose', true,...
        'InitialLearnRate', initialLearnRate,...
        'L2Regularization', 1e-10,...
        'MaxEpochs', 3,...
        'Shuffle', 'every-epoch',...
        'ValidationData', imdsValidation,...
        'OutputFcn', @(state) sendTrainingProgress(D, idx, state));
```

完整的说明如下

+ ::SolverName:::  用于梯度下降优化的算法，可选项包括 sigma, Adam, rmsprop
+ Plots: 是否绘制训练的过程，默认为none，如果开启，需要将其设置为 training-progress
+ Verbose: 是否需要输出训练的日志信息，默认为true
+ VerboseFrequency: 输出日志的间隔，默认是50，每次循环到50的倍数时，就会输出信息
+ ::MaxEpochs::: 最大的训练轮数，默认是30.
+ ::MiniBatchSize::: 在一次循环时被送入网络的数据批的大小
+ Shuffle：是否对数据集进行置乱，可选项有 never, once(default), every-epoch
+ ValidationData: 用于验证的数据
+ ValidationFrequency: 验证的间隔，默认是50
+ ValidationPatience: 正整数类型，用于判断是否需要提前停止训练，如果进行验证时得到的loss不低于之前最小的loss超过该数目，就会提前停止训练，用于防止过拟合。
+ ::InitialLearnRate::: 初始学习率
+ ::LearnRateSchedule::： 调整学习率的策略，默认是none，可以设置为piecewise，那么会每训练一定数目的epoch之后，就将学习率乘上一个固定的系数。
+ ::LearnRateDropFactor::: 学习率调整系数，默认为0.1，可选0到1之间到实数
+ L2Regularization: 默认0.0001，L2正则化的系数，可选非负实数。
+ Momentum： 动量系数，默认0.9，可选0到1指尖的实数。
+ GradientDecayFactor： 用于admaSolver
+ SquaredGradientDecayFactor: 用于adamSolver和rmspropSolver
+ Epsilon: 用于adamSolver和rmspropSolver
+ ResetInputNormalization: 是否需要对输入进行正则化处理，默认为true
+ GradientThreshold: 梯度阈值，默认是Inf，如果梯度超过这个值，那么会按照GradientThresholdMethod设定的方法进行梯度折叠
+ GradientThresholdMethod: 梯度折叠的方法，包括l2normal, global-l2normal, absolute-value
+ SequenceLength: 用于对序列数据的处理，对于长短不一的序列，默认是按最长的对齐，可以选择按照最短的进行截断。
+ ::ExecutionEnvironment::： 训练采用的计算资源，可以是 cpu, gpu, multi-gpu, parallel，默认是auto，即如果gpu可用，就使用gpu，否则使用cpu
	+ cpu：使用cpu进行训练
	+ gpu:  使用gpu进行训练
	+ multi-gpu：使用local parallel pool的多个GPU训练
	+ parallel: 使用任一可用的parallel pool进行并行训练，如果current parallel pool有GPU，则使用GPU，否则使用CPU。
+ ::WorkerLoad:: ：在并行的情况下用于任务在多个woker之间的分配
	+ 可以是0-1之间的实数，例如0.5，代表每个机器上用于训练的Worker占该机器的Worker总数的一半
	+ 可以是一个正整数，例如4，代表用于计算的worker的数目
	+ 可以是一个数组，数组长度等于parallel pool中的worker数目，每个元素代表该worker分得的工作负载
+ DispatchInBackground：默认false，是否允许空闲的worker在后台提前进行数据预处理
+ ::CheckpointPath:: : 默认不进行Checkpoint，如果设置了该路径，那么在每个epoch都会在路径下保存网络
+ ::OutputFcn:: : 每一次循环结束后的回调，会传入的参数有：

![](img/1913A467-8C5E-42BE-8C12-1685EFF41072.png
)

在不使用自带的plot时，可以通过这个函数来记录数据，绘制图形等。
一个OutputFcn的例子
``` MatLab
'OutputFcn', @(state) sendTrainingProgress(D, idx, state));

function sendTrainingProgress(D,idx,info) %info储存了训练过程中的信息
if info.State == "iteration"
    send(D,{idx,info.Iteration,info.TrainingAccuracy});
end
end
```

## 例子1: 并行训练CNN
``` Matlab
delete(gcp);
parpool('local',4);
imds = imageDatastore('/Users/cui/parforTrain/cifar10/train', ...
    'IncludeSubfolders', true,...
    'LabelSource', 'foldernames');
 
imdsTest = imageDatastore('/Users/cui/parforTrain/cifar10/test',...
    'IncludeSubfolders', true,...
    'LabelSource', 'foldernames');
 
[imdsTrain, imdsValidation] = splitEachLabel(imds, 0.9);
 
imageSize = [32, 32, 3];
netDepth = 2;
netWidth = 16;
 
layers = [
    imageInputLayer(imageSize)
    convolutionalBlock(netWidth, netDepth)
    maxPooling2dLayer(2, 'Stride', 2)
    convolutionalBlock(2 * netWidth, netDepth)
    maxPooling2dLayer(2, 'Stride', 2)
    convolutionalBlock(4 * netWidth, netDepth)
    averagePooling2dLayer(8)
    fullyConnectedLayer(10)
    softmaxLayer
    classificationLayer
];
 
miniBatchSizes = [64, 128, 256, 512];
numMiniBatchSizes = numel(miniBatchSizes);
trainNetworks = cell(numMiniBatchSizes, 1);
accuracies = zeros(numMiniBatchSizes, 1);
 
f = figure;
f.Visible = true;
for i = 1:4
    subplot(2,2,i);
    xlabel('Iteration');
    ylabel('Accuracy');
    lines(i) = animatedline;
end
 
D = parallel.pool.DataQueue;
afterEach(D, @(opts) updatePlot(lines, opts{:}));
 
parfor idx = 1:numMiniBatchSizes
    miniBatchSize = miniBatchSizes(idx);
    initialLearnRate = 1e-1 * miniBatchSize / 256;
    options = trainingOptions('sgdm',...
        'MiniBatchSize', miniBatchSize,...
        'Verbose', true,...
        'InitialLearnRate', initialLearnRate,...
        'L2Regularization', 1e-10,...
        'MaxEpochs', 3,...
        'Shuffle', 'every-epoch',...
        'ValidationData', imdsValidation,...
        'OutputFcn', @(state) sendTrainingProgress(D, idx, state));
    
    net = trainNetwork(imdsTrain, layers, options);
    
    YPredicted = classify(net, imdsValidation);
    accuracies(idx) = sum(YPredicted == imdsValidation.Labels) / numel(imdsValidation.Labels);
    
    trainedNetworks{idx} = net;
end
```

![](img/46D8EF1A-1B72-41CD-88E2-18B105F8AAE9.png
)

## 例子2: 使用多个CPU训练
``` MatLab
delete(gcp);
parpool('local',4);
imds = imageDatastore('/Users/cui/parforTrain/cifar10/train', ...
    'IncludeSubfolders', true,...
    'LabelSource', 'foldernames');
 
imdsTest = imageDatastore('/Users/cui/parforTrain/cifar10/test',...
    'IncludeSubfolders', true,...
    'LabelSource', 'foldernames');
 
[imdsTrain, imdsValidation] = splitEachLabel(imds, 0.9);
 
imageSize = [32, 32, 3];
netDepth = 2;
netWidth = 16;
 
layers = [
    imageInputLayer(imageSize)
    convolutionalBlock(netWidth, netDepth)
    maxPooling2dLayer(2, 'Stride', 2)
    convolutionalBlock(2 * netWidth, netDepth)
    maxPooling2dLayer(2, 'Stride', 2)
    convolutionalBlock(4 * netWidth, netDepth)
    averagePooling2dLayer(8)
    fullyConnectedLayer(10)
    softmaxLayer
    classificationLayer
];
 
miniBatchSize = 128;
initialLearnRate = 1e-1 * miniBatchSize / 256;
options = trainingOptions('sgdm',...
    'MiniBatchSize', miniBatchSize,...
    'Verbose', true,...
    'InitialLearnRate', initialLearnRate,...
    'L2Regularization', 1e-10,...
    'MaxEpochs', 4,...
    'Shuffle', 'every-epoch',...
    'ValidationData', imdsValidation,...
    'ExecutionEnvironment', 'parallel',...
    'Plots', 'training-progress',...
    'WorkerLoad', 4);
    
net = trainNetwork(imdsTrain, layers, options);    
YPredicted = classify(net, imdsValidation);
accuracy = sum(YPredicted == imdsValidation.Labels) / numel(imdsValidation.Labels);
```

![](img/473BE9C7-4870-4680-A513-1D6283A352E0.png
)


