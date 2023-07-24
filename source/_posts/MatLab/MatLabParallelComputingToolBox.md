---
title: MatLab Parallel Computing Tool Box
tags:
  - MatLab
categories:
  - MatLab
date: 2023-07-17 20:17:25
---
#MatLab

## 介绍
Matlab的Parallel Computing ToolBox可以让使用者使用多核处理器、GPU解决计算上数据敏感的问题。通过使用高层的代码（并行的For循环、特殊的Array类型等）可以让使用者将应用并行化，而不需要使用CUDA、MPI。并且适用于Parallel Computing ToolBox的应用不需要进行任何修改就可以在Parallel server上使用。

## Get Started
并行计算可以让使用者同步的执行许多计算。大问题通常可以被分割为可以同时解决的多个小问题，并行计算的优势在于：
+ 将任务分解为多个可以同时执行的小任务可以节省时间
+ 可以处理更大规模的问题
+ 可以提高资源的利用效率

通过使用MatLab Parallel Computing ToolBox，可以
+ 可以使用交互式的并行计算工具，例如parfor、parfeval来进行代码的加速
+ 可以使用大数据处理工具，例如distributed， tall， datastore， mapreduce
+ 可以通过特殊的类型例如gpuArray来使用gpu进行计算
+ 可以使用batch将计算分配到多个机器上进行

并行计算的基础概念：
+ Node： 独立的计算机，可以包含一个或者多个CPU，GPU。多个Node被组织成集群或者超级计算机
+ Thread：被调度执行的最小单位，在一个GPU或者多处理器/多核的系统中，多个线程可以被同时执行
+ Batch：后台的函数脚本执行
+ Scalability：在有更多资源下能够加速的能力

MatLab Parallel ToolBox提供什么
+ MatLab Workers：在后台运行的MatLab计算引擎。可以使用Parallel ToolBox中的函数来自动的将任务分割，并且将子任务提交给Matlab计算引擎来并行的进行。
+ Parallel pool： 类似于线程池的概念，通常，toolbox提供的函数会进行自动创建，也可以通过parpool来进行手动创建。通常情况，Matlab默认的worker数目等于CPU的物理核个数，尽管CPU可以划分出多个虚拟核，但是虚拟核之间共享一些必要的资源，例如FPU。所以这样做可以确保每一个worker都有自己独立的FPU，如果应用不是计算敏感的，而是IO敏感的，那么可以使用更多的worker，例如每个物理核对应两个worker。
+ Speed Up： 通过使用parfor， parfeval， gpuArray等来加速应用
+ 数据划分：可以将大数据划分给多个worker进行处理，例如mapreduce
+ 在集群或者云上进行计算：如果数据太大，不能放在单机上进行，那么可以在多个机器上进行。


## Example 1: 使用parfor进行并行加速
``` matlab
gridSize = 8;
 
nu = linspace(100, 150, gridSize);
mu = linspace(0.5, 2, gridSize);
 
[N, M] = meshgrid(nu, mu);
 
Z = nan(size(N));
c = surf(N, M, Z);
xlabel("\mu Values", "Interpreter", "Tex");
ylabel("\nu Values", "Interpreter", "Tex");
zlabel("Mean Period of y");
view(137, 30);
axis([100 150 0.5 2 0 500])
 
D = parallel.pool.DataQueue;
D.afterEach(@(x)  updateSurface(c, x));
parfor ii = 1:numel(N)
    [t,y] = solveVdp(N(ii), M(ii));
    l = islocalmax(y(:, 2));
    send(D, [ii mean(diff(t(l)))])
end

```

![](img/xxIntermediateResultsCluster.gif
)
D.afterEach接受一个匿名函数，在parfor中，将参数发送给D，D会并行的调用afterEach传入的匿名函数，实现并行的加速训练。


## Example 2 simple parfor benchmark
这个例子通过反复进行21点纸牌游戏的模拟来进行测试。例子的主要逻辑是选定一个worker的数目，对于每个worker，并行的进行模拟。
首先检测是否开启了parallel pool
``` matlab
p = gcp;
if isempty(p)
    error('pctexample:backslashbench:poolClosed', ...
        ['This example requires a parallel pool. ' ...
         'Manually start a pool using the parpool command or set ' ...
         'your parallel preferences to automatically start a pool.']);
end
poolSize = p.NumWorkers;
```

poolSize设置为实际的worker数目。

然后根据实际使用的worker数目对问题的规模进行缩放，并统计每个配置下所用的时间

``` matlab
numHands = 2000;
numPlayers = 6;
fprintf('Simulating each player playing %d hands.\n', numHands);
t1 = zeros(1, poolSize);
for n = 1:poolSize
    tic;
        pctdemo_aux_parforbench(numHands, n*numPlayers, n);
    t1(n) = toc;
    fprintf('%d workers simulated %d players in %3.2f seconds.\n', ...
            n, n*numPlayers, t1(n));
end
```

运行的环境有4个物理核，

结果如下
Simulating each player playing 2000 hands.
1 workers simulated 6 players in 0.34 seconds.
2 workers simulated 12 players in 0.29 seconds.
3 workers simulated 18 players in 0.34 seconds.
4 workers simulated 24 players in 0.35 seconds.
Ran in 0.28 seconds using a sequential for-loop.

最后绘制出加速比

![](img/9D09D203-D14C-481F-91B0-87C10A1120CE.png
)

