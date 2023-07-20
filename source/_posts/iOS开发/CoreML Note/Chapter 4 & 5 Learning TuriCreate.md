---
title: Chapter 4 & 5 Learning TuriCreate
tags:
  - ios开发
categories:
  - iOS开发
date: 2023-07-17 20:17:29
---
#ios开发 

第四章和第五章介绍了苹果提供的机器学习工具包TuriCreate，它是一个Python工具包，主要功能是进行迁移学习，然后将模型导出为coreml的格式，以供ios应用使用。

## 使用Anaconda管理Python环境
第四章介绍了Conda的使用，conda是一个为Python使用者开发的软件，兼具包管理和环境管理的功能。用户可以选用较为精简的miniconda，也可以选用集成了多种机器学习包和GUI界面的Anaconda。

我们安装好Anaconda后，可以创建Python环境，并在环境中安装包。可以使用Anaconda Navigator提供的GUI界面安装包，也可以在终端中切换到指定环境再使用Pip来进行安装。

![](img/36C0189B-46C6-4E89-9B4C-82F00ED05BD6.png
)

在Navigator中，可以选择环境，并在指定环境中安装Python工具包。
对环境本身也可以进行创建删除等操作。

## 在环境中使用Jupyter notebook
![](img/6EAFCBAB-6808-4BD7-AB2F-09752D08CA65.png
)
在Home页面下，可以在指定环境中启动应用，我们启动Jupyter notebook应用。这是一个在浏览器中使用的开发环境，可以开发运行代码，使用交互式的方法可以实时的展示出某一段代码的输出。

我们在mlenv环境下启动Jupyter notebook，并在自己的工作目录下创建笔记本文件，用浏览器打开，就可以使用Jupyter notebook进行开发。在Jupyter notebook中，代码被组织成一个个cell，编写好一段代码后就可以单独运行这个cell。常见的操作：
* Shift + enter：运行这个cell，如果是最后一个cell，则创建新cell
* Ctrl + enter：只运行cell
* Tab：自动补全
* Shift Tab tab：弹出浮动式文档
* ？：在函数前加上？并运行可以查看函数的文档说明

![](img/85DFB5E6-8F2B-489D-BB25-B3AACA366F1A.png
)

在Jupyer Notebook中，每运行一个cell，就会有与之匹配的输出。

## 使用TuriCreate进行迁移学习
第四章通过一个例子给出了TuriCreate如何使用的一个简单教学。我们仍然使用之前的零食数据集
* 首先，import所需要的包：
``` python
import turicreate as tc
import matplotlib.pyplot as plt
```
* 然后，加载数据集：
``` python
train_data = tc.image_analysis.load_images("/Users/cui/WorkSpace/project/ios-playground/snacks/train", with_path=True)
```

在Jupyter中，我们可以以可视化的方式看到数据集：

![](img/815B56C2-9A33-4E0A-882B-CC70B3D7FD2F.png
)

* 为数据集加上标签：

![](img/4CEC6F58-14AF-4046-AF48-C51146EA2BC8.png
)

* 可以进行一个类别统计：
![](img/4443844A-CAB0-4BD7-B2F9-9B8C69420ACD.png
)

* 进行迁移学习，使用的基学习器是VisionFeaturePrint_Screen，在第三章中介绍过，改模型将图片提取成2048维的特征向量，再进行对数回归。

![](img/361D5776-D185-4C63-882F-B037623D8696.png
)

* 保存/加载模型，进行测试
![](img/13C33A84-D5EC-4408-904F-631CCA48A8EE.png
)


* 将模型导出为coreml的格式
![](img/D89BED4F-99DB-4E63-9E75-E024693A9195.png
)


## 第四章总结
第四章通过一个简单单例子教学了TuriCreate的基础使用

## 进阶使用
在第五章，我们基于SqueezeNet训练零食分类器，同时，我们也将学到Python中一些可视化工具包的使用技巧。
和之前的训练流程一致，只是把训练分类器时使用的基分类器改为SqueezeNet
![](img/DE893E3C-363D-408A-AA86-4DB293C209E1.png
)
在实际操作的过程中，需要从苹果的服务器将squeezenet这个模型完全下载下来，由于网络原因，下载一段时间就会抛出异常。需要多试几次：
下载成功后，就会开启训练流程：
![](img/2D06E310-2E53-4E2D-AB17-A895722DF949.png
)
在训练过程中，TuriCreate会贴心的提示你的迭代次数太少，还没有到达最优的情况，因此可以根据这个提示来增加迭代次数。实际测试，135次是一个较好的数字，再大会过拟合。测试的方法也和之前一样
![](img/F97C843C-CC43-4717-88F0-77E81F25235D.png
)
不过实测这个模型效果不如之前的。

## 可视化
在测试结束后，我们会得到测试结果的混淆矩阵，通过对混淆矩阵进行可视化，可以直观的看到测试的结果,首先，我们定义两个函数：
``` python
import numpy as np
import seaborn as sns

def compute_confusion_matrix(metrics, labels):
    num_labels = len(labels)
    label_to_index = {l: i for i,l in enumerate(labels)}
    
    conf = np.zeros((num_labels, num_labels), dtype = np.int)
    for row in metrics["confusion_matrix"]:
        true_label = label_to_index[row["target_label"]]
        pred_label = label_to_index[row['predicted_label']]
        conf[true_label, pred_label] = row['count']
    return conf

def plot_confusion_matrix(conf, labels, figsize=(8,8)):
    fig = plt.figure(figsize=figsize)
    heatmap=sns.heatmap(conf, annot=True, fmt='d')
    heatmap.xaxis.set_ticklabels(labels, rotation=45,ha='right', fontsize=12)
    heatmap.yaxis.set_ticklabels(labels, rotation=0, ha='right', fontsize=12)
    plt.xlabel('Predicted label', fontsize=12)
    plt.ylabel('True label', fontsize=12)
    plt.show()
```

这两个函数分别从混淆矩阵中提取信息，并进行可视化。
![](img/86805104-898F-4E2E-920B-EED6C3D916BE.png
)


## 总结
个人感觉，实际应用场景中，很少会使用TuriCreate进行模型的训练，更多的是用其他的，更受欢迎的框架训练出模型，然后将其转换为coreml格式来使用，因此，接下来学习如何将常用的Pytorch模型转换为coreml模型来使用。
