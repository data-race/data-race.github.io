---
title: Chapter 2 Getting Started with Image Classification
tags:
  - ios开发
categories:
  - iOS开发
date: 2023-07-17 20:17:29
---
#ios开发 

在本章中，根据实现一个能够判定食物是否健康的应用来学习如何在应用中使用机器学习模型。

## 问题背景
食物是否健康是一个典型的二分类问题，二分类看似简单，但是实际上有广泛的应用。例如在医学检测中，只需要判定是阳性还是阴性，在邮件检测中，只需要判定是否是垃圾邮件。图像分类问题是最基础的计算机视觉任务，更高深的计算机视觉应用包括物体检测， 风格迁移，以及图像生成，都建立在图像分类的基础上。

## UI 设计
我使用的设备是iPad Air3，应用的UI设计比较简陋，因为本身对IOS应用开发不是很熟悉

![](img/B756DF5C-7BA9-4CE0-9128-28E443F335D6.png
)

整个应用包括一个展示分类结果的Label，一个展示置信度的Label，一个UIImageView用来展示待分类的图片，一个Button用来选择图片，选择图片可以是从Photo Library，也可以是拍照。

## 选择图片的实现
选择图片的实现我参考了这片博文[Picking images with UIImagePickerController in Swift 5 - The.Swift.Dev.](https://theswiftdev.com/picking-images-with-uiimagepickercontroller-in-swift-5/)
大体的思路是实现一个ImagePicker类以及一个ImagePickerDelegate协议。ImagePickerDelegate有一个方法didSelect，参数是UIImage，在ImagePicker类的Present方法中，展示选择图片来源的AlertController，然后在这个Alert的Handler中实现选择图片的部分，并调用ImagePickerDelegate实例的didSelect方法，将图片传入。这里将ViewController实现为ImagePickerDelegate，当调用didSelect时，ViewController会将图片显示在ImageView上，并调用模型对图片进行判定，将结果显示在Label上。


## CoreML和Vision
苹果公司在IOS11中加入了CoreML，通过CoreML可以简单的在App中使用机器学习模型。差不多就是把模型文件加入到app中，然后调用一些API。当然，只有有已经训练好的模型时，才可以这样使用CoreML，本章所使用的模型文件可以在网上找到https://github.com/threadLord/ML_CoreML/blob/master/02-image-classification/starter/HealthySnacks.mlmodel

之前说过，CoreML也是一种文件格式，是苹果用来存储和使用机器学习模型的文件格式。这个模型文件下载之后，通过Xcode的添加文件功能添加到项目中，然后可以看到它的基础信息：
![](img/7F0B3B97-F402-4494-83E4-D45228BEB357.png
)
从中我们可以得知：
* 该模型使用的是神经网络分类器，基于SqueezeNet
* 该模型大小只有5MB
* 该模型的输入为227*227分辨率图像，因此在传入图像时，要先缩放
* 该模型的输出格式
当然，仅从这种简短的描述上是无法使用模型的，我们在下一部分尝试发起一个推断请求。

CoreML经常可Vision搭配在一起使用，Vision的作用是让CoreML的模型更容易接受图片的输入。Vision提供了许多功能，例如形状检测，文本提取，人脸检测等。因此Vision经常和CoreML搭配在一起，组成流水线使用。例如首先使用Vision检测人脸，然后使用CoreML对人脸的情绪进行识别。

## 发起推断请求
我将分类功能封装成了一个分类器类，它提供classify方法供ViewController使用。
在这个类中，我们有一个请求的成员变量：
``` swift
    lazy var classificationRequest: VNCoreMLRequest = {
        do {
            // 1
            let healthySnacks = HealthySnacks()
            // 2
            let visionModel = try VNCoreMLModel(for: healthySnacks.model)
            // 3
            let request = VNCoreMLRequest(model: visionModel, completionHandler: {
                [weak self] request, error in
                print("Request is finished", request.results)
            })
            // 4
            request.imageCropAndScaleOption = .centerCrop
            return request
        } catch {
            fatalError("Failed to create VNCoreMLRequest")
        }
    }()
```
这里的lazy是说在使用时才会进行初始化。
这里有几个步骤：
1. 创建HealthySnacks的实例，也就是模型实例
2. 从模型实例创建VNCoreMLModel实例
3. 创建请求
4. 设置缩放的方法

## 展示请求结果
我们在classify方法中加入发送请求对部分
```swift
    func classify(image: UIImage)  {
        // 1
        guard let ciImage = CIImage(image:image) else {
            print("Unable to create CIIMAGE")
            return
        }
        // 2
        DispatchQueue.global(qos: .userInitiated).async {
            // 3
            let handler = VNImageRequestHandler(ciImage: ciImage)
            do {
                try handler.perform([self.classificationRequest])
            } catch {
                print("Failed to perform classification:\(error)")
            }
        }
    }
```

1. 首先将UIImage转化为CIImage
2. 异步的发起请求
3. 由handler去执行classificationRequest

请求发起后，会打印出类似的结果：
```
Request is finished! Optional([<VNClassificationObservation: 0x60c00022b940> B09B3F7D-89CF-405A-ABE3-6F4AF67683BB 0.81705 “healthy” (0.917060), <VNClassificationObservation: 0x60c000223580> BC9198C6-8264-4B3A-AB3A-5AAE84F638A4 0.18295 “unhealthy” (0.082940)])
```

我们加入对结果的处理
``` swift
    func processObservations(for request: VNRequest, error: Error?) {
        DispatchQueue.main.async {
            if let results = request.results as? [VNClassificationObservation] {
                if results.isEmpty {
                    self.resultDisplayer.displayResult(result: "Nothing Found", 0.0)
                } else {
                    self.resultDisplayer.displayResult(result: results[0].identifier, Float(results[0].confidence))
                }
            } else if let error = error {
                self.resultDisplayer.displayResult(result: "error: \(error.localizedDescription)", 0.0)
            } else {
                self.resultDisplayer.displayResult(result: "???", 0.0)
            }
        }
    }
```

这个函数在初始化classificationRequest的时候被调用，会将结果通过label展示。

## 应用效果
![](img/demo.mov
)

## 总结
Swift的语言特性还没有完全搞明白，感觉用到了很多闭包回调，非常灵活。
通过CoreML来使用已有的模型不是很复杂，即使之前没接触过IOS开发，也可以快速上手。