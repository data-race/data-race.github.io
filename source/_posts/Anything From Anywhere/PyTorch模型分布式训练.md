---
title: PyTorch 模型分布式训练
tags:
  - 充电
categories:
  - Anything From Anywhere
date: 2023-07-17 20:17:25
---
#充电 

## 为什么需要分布式训练

### 深度学习任务特点
-   计算密集
	-   模型参数量提升
	-   模型结构更加复杂
-   数据密集
	-   复杂的模型需要海量训练数据
	-   训练时间长
-   现状：单个设备无法满足需求
![](img/Pastedimage20221030164843.png)

### 分布式深度学习
- 用多个设备去进行加速
- 分类
	- 数据并行化(Data Parallelism)
		- 将数据分配到多个设备
	- 模型并行化(Model Parallelism)
		- 将模型分配到多个设备
	- 混合并行化(Hybrid Parallelism)
		- 混合两种方式


---
## 数据并行 
### 流程
- 每个设备持有一个完整模型副本
- 将数据分到多个设备
- 将多个设备的模型合起来
	 ![[Pasted image 20221030165121.png|600]]

### 原理

$w = w - lr \frac{\partial \frac{1}{n}\sum_{i=1}^n Loss_i}{\partial w}$ 
$\frac{\partial \frac{1}{n}\sum_{i=1}^n Loss_i}{\partial w}=\frac{1}{n}\frac{\partial\sum_{i\in m_1}Loss_i}{\partial w}+\frac{1}{n}\frac{\partial\sum_{i\in m_2}Loss_i}{\partial w}+...+\frac{1}{n}\frac{\partial\sum_{i\in m_k}Loss_i}{\partial w}$ 
$=\frac{|m_1|}{n}\frac{\partial Loss_{m_1}}{\partial w} + \frac{|m_2|}{n}\frac{\partial Loss_{m_2}}{\partial w} + ... + \frac{|m_k|}{n}\frac{\partial Loss_{m_k}}{\partial w}$  

---
## Parameter Server

![](img/Pastedimage20221030165552.png)


-   参与训练的节点被分为Worker和PS
-   Worker进行计算，PS负责存储和同步模型参数
-   Worker更新本地参数后，推送到对应PS
-   Worker从PS拉取最新的参数

---
## Ring All-Reduce

-   节点被组织成逻辑环
-   通信只在环中定义的前驱到后继中发生
-   Scatter：将更新后的本地参数传给后继
-   Gather： 将得到的全局参数传给后继

---
## 单机多卡：DataParallel

### 模式
DP可以被看作是参数服务器的实现

### 流程
-   Worker-0加载Minibatch
-   Worker-0将sub-minibatch分发给其他worker
-   Worker-0将最新模型参数分发给其他worker
-   所有Worker前向传播
-   Worker-0收集输出，计算Loss，并分发Loss
-   所有Worker反向传播
-   Worker-0收集梯度，更新模型

![](img/Pastedimage20221030165644.png
)

---
## 多机多卡: Distributed Data Parallel

### 模式
是Ring AllReduce

### 流程
- 每个worker独立加载数据进行训练
- 得到梯度后，进行同步的梯度收集(All Reduce)
- 每个worker更新本地的模型


