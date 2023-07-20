---
title: Chapter 6 Training with PyTorch
tags:
  - ios开发
  - 保存模型
  - 加载模型
categories:
  - iOS开发
date: 2023-07-17 20:17:29
---
#ios开发 

书上说这章会介绍Keras的使用，但是这一章的内容并没有完整介绍，我猜测是将Keras的模型通过coremltool工具包转化成coreml的模型。不过使用Pytorch也大同小异。因此，我们将学习使用coremltools把一个Pytorch的模型转换成coreml模型，并集成到ios app中。


## Step1: 在Pytorch中训练
我们选用常用的Cifar10数据集和AlexNet模型进行训练，在模型训练好后，将其保存下来，在Pytorch中，保存模型有两种方式，一种是只保存模型的参数，在使用时，需要先创建模型的实例，再将模型的参数导入到模型中：
``` python
# 保存
torch.save(model.state_dict(), PATH)
# 加载
model = TheModelClass(*args, *kwargs)
model.load_state_dict(torch.load(PATH))
```

另一种方法是直接将模型序列化：
``` python
#保存模型
torch.save(model, PATH)
#加载模型
model = torch.load(PATH)
model.eval()

```
我们推荐使用第一种方式。
## Step2: Pytorch to onnx
由于苹果提供的coremltools不支持直接将Pytorch的模型直接转换为mlmodel格式，但是可以通过先将Pytorch模型转换为onnx格式，再将其转换为mlmodel格式。
``` python
    dummy_input = torch.rand(1,3,32,32)
    input_names = ['image']
    output_names = ['classLabelProbs']

    torch.onnx.export(model,
        dummy_input,
        'alexnet.onnx',
        verbose=True,
        input_names = input_names,
        output_names = output_names)
```

这里要注意的一些地方有input _names和output_names和下一步转换时用到的参数要一致。在输入是图片时，input_names必须是image，否则会被当作MultiArray处理。
导出之后，我们用Netron打开.onnx文件，就可以看到我们的模型：
![](img/23FBCB5E-8848-4BD5-925B-0E3F65C80C3D.png
)

## Step 3: Onnx to cormel
我们用pip安装onnx_coreml，然后将onnx转化为mlmodel，在实际测试中，这一步如果不在macOS系统上做，会段错误，原因不明。
``` python
from onnx_coreml import convert
class_labels = ['air plane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog','horse','ship','truck']
model = convert(model='alexnet.onnx', minimum_ios_deployment_target='13',image_input_names=['image'], 
                mode='classifier',
               predicted_feature_name='classLabel',
               class_labels=class_labels)
```

Convert函数有很多参数。

然后我们用Xcode打开模型文件，就可以看到相关的信息，就可以在应用中使用模型了。
![](img/EA6BFE2A-9CEC-4EB3-8786-4BE26C5855A5.png
)

我在实际应用中，效果并不是很好。虽然模型在测试数据集上的准确度有80%，但是实际应用中只有60%左右。我猜测是数据集的原因，CIFAR中的图片为了节省空间，都是32x32大小的，而ios摄像头采集的图片质量很高。因此，可以得出的结论有：有些数据集只适合检测算法和模型是否有效，而不适合实际应用。