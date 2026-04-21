---
title: Awesome CoreML
tags:
  - ios开发
categories:
  - iOS开发
date: 2023-07-17 20:17:29
---
#ios开发 


## 概要
笔记中整理了一些关于CoreML，ARKit，MapKit的应用。在运行这些项目时，往往需要编辑这些项目的的Bundle Identifier，以及设置开发者的Account。
![](img/6BEFDA89-DEFA-4002-AD5D-691F46847678.png)

## 1. 文本检测应用
+ 项目地址：https://github.com/tucan9389/TextDetection-CoreML
+ 关键字： Vision，TextDetect
+ 项目效果：
![](img/7DEFFBBA-FB5F-4CF0-89DC-118E81B967D1.png)

+ 功能描述：绘制出当前摄像头捕捉的视频中所存在文本的区域。
+ 技术描述：主要用到了Vision中自带的文本检测模型，没有使用自训练的数据集和模型。通过向
VNImageRequestHandler发起VNDetectTextRectanglesRequest的请求，当请求成功时，会返回一个result，result的类型是VNTextObservation的数组
```
<VNTextObservation: 0x2836edd60> EEB346A3-3658-450A-AEF6-394309643B90 requestRevision=1 confidence=1.000000 boundingBox=[0.0812656, 0.4079, 0.814308, 0.104492], 
<VNTextObservation: 0x2836ed360> 4A47D180-8C4E-48F3-AEE0-2E9EB75BCA49 requestRevision=1 confidence=1.000000 boundingBox=[0.00438134, 0.314129, 0.614648, 0.0842859], <VNTextObservation: 0x2836edea0> 7F74A257-89B1-43AC-B6C9-D185A2066D39 requestRevision=1 confidence=1.000000 boundingBox=[0.647553, 0.37663, 0.23406, 0.0514283],
...
```
每一项都是一个VNTextObservation，给出了出现文本区域的boundingBox，以及推断的置信度confidence等信息。在之前设置request时，设置了当请求结束后的回调函数:
``` swift
// MARK: - Setup Core ML
    func setUpModel() {
        let request = VNDetectTextRectanglesRequest(completionHandler: self.visionRequestDidComplete)
        request.reportCharacterBoxes = true
        self.request = request
    }
```
请求结束时会回调visonRequestDidComplete()，这个函数的代码里用了很多emoji的符号
``` swift
func visionRequestDidComplete(request: VNRequest, error: Error?) {
        self.👨‍🔧.🏷(with: "endInference")
        guard let observations = request.results else {
            // end of measure
            self.👨‍🔧.🎬🤚()
            return
        }
        print(observations)
        DispatchQueue.main.async {
            let regions: [VNTextObservation?] = observations.map({$0 as? VNTextObservation})
            
            self.drawingView.regions = regions
            
            // end of measure
            self.👨‍🔧.🎬🤚()
        }
    }
```
大概的意思是将result中的VNTextObservation数组提取出来，然后赋给drawingView.regions，drawingView是和videoPreview重合的一个UIView，用来绘制文本区域。最后在drawingView中完成对文本区域的绘制。

+ 项目总结：该项目较为简单，用到了基础的文本检测方法。主要的逻辑和之前的零食分类类似，只在请求的类型和模型上有区别。


## 2.  图像分割
+ 项目地址：https://github.com/tucan9389/PoseEstimation-CoreML
+ 关键字： Coreml, Vison, 图像分割
+ 项目效果：
![](img/5A2C4E23-7633-4C55-92A3-5CA694A7C724.png)
+ 功能描述：将图片分割为若干自定义的部分。
+ 技术描述：使用了Apple提供的DeepLabV3图像分割模型([Machine Learning - Models - Apple Developer](https://developer.apple.com/machine-learning/models/))，该模型的输入是一个513 * 513大小的图像，输出是一个513 * 513大小的Int型矩阵，每个Int值代表这个像素属于哪类物体。应用可以对视频进行实时分割，也可以对静态图像进行分割。这个应用和上一个文本检测应用的作者一样，所以代码的逻辑基本一样，只是修改了一些和模型有关的代码。
+ 项目总结： 该项目也比较简单，和上一个项目相比使用了预训练好的模型，可以学习如何在一个xcode项目中导入模型文件。此外该项目使用TabBarController来组织多个页面，需要更多有关UI设计的知识。


## 3. 图像深度检测
+ 项目地址：https://github.com/tucan9389/DepthPrediction-CoreML
+ 关键字： CoreML，Vision，深度检测
+ 项目效果：
![](img/1DB2409B-16DF-4350-9D8B-6333A1A3ED41.png)

+ 功能描述：检测图像的景深信息。
+ 技术描述：使用了Apple提供的景深检测模型FCRN([Machine Learning - Models - Apple Developer](https://developer.apple.com/machine-learning/models/))
，该模型的输入是304 * 228大小的图片，输出是一个double型矩阵，大小大概是原始图片的一半(128 * 160)，值越大意味着在原始图片中物体的景深越深。应用具体的逻辑和之前两个应用类似。

+ 项目总结：该项目较为简单，使用训练好的模型。可以帮助学习在应用中使用机器学习模型的流程。


## 4.  图像风格迁移： 边缘提取
+ 项目地址： https://github.com/s1ddok/HED-CoreML
+ 关键字：CoreML，Vision， 风格迁移
+ 项目效果： ![[68747470733a2f2f63646e2d696d616765732d312e6d656469756d2e636f6d2f6d61782f313630302f312a496d5073484d6836385a4e505979775f7561534239672e706e67.png]]

+ 功能描述：通过几种不同的模型，对原始图片进行边缘提取
+ 技术描述：使用自己训练的模型进行边缘提取。模型的信息如下：
![](img/830C5F03-A4F1-4795-9F0A-D4BACDD3A645.png)
输出有5个Array，对应用户选择的5种不同的模型。每个Array的类型是Double 1 x 1 x 1 x 500 x 500 array，和输入是相同的。
然后对每个输出值用sigmoid进行激活，转换成灰度图：
``` swift
// Normalize result features by applying sigmoid to every pixel and convert to UInt8
        for i in 0..<inputW {
            for j in 0..<inputH {
                let idx = i * inputW + j
                let value = dataPointer[idx]
                
                let sigmoid = { (input: Double) -> Double in
                    return 1 / (1 + exp(-input))
                }
                
                let result = sigmoid(value)
                imgData[idx] = UInt8(result * 255)
            }
        }
```

+ 项目总结：也是比较常规的项目。

## 5.  图像物体检测(YOLO: 一种物体检测神经网络)
+ 项目地址: https://github.com/hollance/YOLO-CoreML-MPSNNGraph
+ 关键词： CoreML, Vision,  Keras, coremltools, 图像物体检测
+ 项目效果：
![](img/780D2A81-397C-4BFE-979B-1F68A0E921A4.png)

+ 功能描述：  实时地从捕捉到的图像中检测出包括人、汽车、猫、狗等在内的多种物体。
+ 技术描述：  该应用复现了一种用于物体检测的神经网络YOLO，这个网络十分复杂。使用Keras进行训练模型，并使用coremltools将Keras的模型转化为所需的mlmodel格式模型。使用的数据集是http://host.robots.ox.ac.uk/pascal/VOC/。最终得到的模型的输入是：416*416大小的图片，输出是125*13*13大小的Array，给出了物体的位置等信息。值得一提的是该应用使用两种发起推断的方法，分别是使用Vision的request和使用plain CoreML
``` swift
 func predict(pixelBuffer: CVPixelBuffer, inflightIndex: Int) {
    // Measure how long it takes to predict a single video frame.
    let startTime = CACurrentMediaTime()

    // This is an alternative way to resize the image (using vImage):
    //if let resizedPixelBuffer = resizePixelBuffer(pixelBuffer,
    //                                              width: YOLO.inputWidth,
    //                                              height: YOLO.inputHeight) {

    // Resize the input with Core Image to 416x416.
    if let resizedPixelBuffer = resizedPixelBuffers[inflightIndex] {
      let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
      let sx = CGFloat(YOLO.inputWidth) / CGFloat(CVPixelBufferGetWidth(pixelBuffer))
      let sy = CGFloat(YOLO.inputHeight) / CGFloat(CVPixelBufferGetHeight(pixelBuffer))
      let scaleTransform = CGAffineTransform(scaleX: sx, y: sy)
      let scaledImage = ciImage.transformed(by: scaleTransform)
      ciContext.render(scaledImage, to: resizedPixelBuffer)

      // Give the resized input to our model.
      if let boundingBoxes = yolo.predict(image: resizedPixelBuffer) {
        let elapsed = CACurrentMediaTime() - startTime
        showOnMainThread(boundingBoxes, elapsed)
      } else {
        print("BOGUS")
      }
    }

    self.semaphore.signal()
  }
```
plain CoreML直接调用模型的predict方法。

``` swift
func predictUsingVision(pixelBuffer: CVPixelBuffer, inflightIndex: Int) {
    // Measure how long it takes to predict a single video frame. Note that
    // predict() can be called on the next frame while the previous one is
    // still being processed. Hence the need to queue up the start times.
    startTimes.append(CACurrentMediaTime())

    // Vision will automatically resize the input image.
    let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer)
    let request = requests[inflightIndex]

    // Because perform() will block until after the request completes, we
    // run it on a concurrent background queue, so that the next frame can
    // be scheduled in parallel with this one.
    DispatchQueue.global().async {
      try? handler.perform([request])
    }
  }

  func visionRequestDidComplete(request: VNRequest, error: Error?) {
    if let observations = request.results as? [VNCoreMLFeatureValueObservation],
       let features = observations.first?.featureValue.multiArrayValue {

      let boundingBoxes = yolo.computeBoundingBoxes(features: features)
      let elapsed = CACurrentMediaTime() - startTimes.remove(at: 0)
      showOnMainThread(boundingBoxes, elapsed)
    } else {
      print("BOGUS!")
    }

    self.semaphore.signal()
  }
```

使用Vision需要初始化request，并为其设置handler，然后在图像到来时进行handler的perform，触发回调函数visionRequestDidComplete。在回调函数中处理返回值。

两种方式都可以。

+ 项目总结：该项目包含了完整的收集数据 ->  训练模型 -> 模型转化 -> 模型部署的过程。但是数据集较大，模型训练难度较高，可以考虑用规模更小的数据集和更简单的模型。


## 6. 文本分类
+ 项目地址：https://github.com/cocoa-ai/SentimentCoreMLDemo
+ 关键词： CoreML,  sklearn, coremltools, 文本分类
+ 项目效果：
![](img/1AD96A82-3E27-4A42-9C2B-CBE46714FC56.png)
+ 功能描述：根据文本的情感将文本分成积极的(postive)和消极的(negative)两类。
+ 技术描述：该文本分类模型使用的数据集是 [Homework:  Sentiment Analysis](http://boston.lti.cs.cmu.edu/classes/95-865-K/HW/HW3/)的HW3中的数据集，有1392段短文本，被标注了Postive或者Negative的标签。使用sklearn中的LinearSVC进行训练，并通过Apple提供的coremltools工具包将模型转化成可以供iOS app使用的mlmodel格式。这个模型的输入是一个Dict(String->Double)，给出了文本的词频表示。输出是Dict(String->Double)，给出了类别和概率。进行推断的过程是比较简单的，直接调用模型类的prediction方法就可以：
``` swift
func predictSentiment(from text: String) -> Sentiment {
    do {
      let inputFeatures = features(from: text)
      // Make prediction only with 2 or more words
      guard inputFeatures.count > 1 else {
        throw Error.featuresMissing
      }

      let output = try model.prediction(input: inputFeatures)

      switch output.classLabel {
      case "Pos":
        return .positive
      case "Neg":
        return .negative
      default:
        return .neutral
      }
    } catch {
      return .neutral
    }
  }
```

+ 项目总结： 比较简单的项目，使用的数据集也很小，但是包含了完整的 训练 -> 应用的过程。可以仿照这个思路，找一些大的文本数据集，用更强大的框架进行训练，然后再用coremltools来转化部署。

## 7. 动作捕捉
+ 项目地址： https://github.com/akimach/GestureAI-CoreML-iOS
+ 关键词： CoreML，CoreMotion
+ 项目效果：
![](img/3F995D9C-2AF3-4810-964D-0DE3B14F2244.png)

+ 功能描述： 按住应用中的按钮，然后拿着手机做动作，应用可以识别出手机的运动轨迹（圆、矩形、三角形）
+ 技术描述： 当用户按下按钮时，会不断从MotionManager初获取运动传感器的数据：
``` swift
 @IBAction func gaBtnTouchDown(_ sender: Any) {
        gaBtn.backgroundColor = GAColor.btnSensing
        self.sequenceTarget = []
        
        timer = Timer.scheduledTimer(timeInterval: 1.0, target: self, selector: #selector(self.updateTimer(tm:)), userInfo: nil, repeats: true)
        timer.fire()
        
        motionManager.startAccelerometerUpdates(to: queue, withHandler: {
            (accelerometerData, error) in
            if let e = error {
                fatalError(e.localizedDescription)
            }
            guard let data = accelerometerData else { return }
            self.sequenceTarget.append(data.acceleration.x)
            self.sequenceTarget.append(data.acceleration.y)
            self.sequenceTarget.append(data.acceleration.z)
        })
    }
```
当按钮松起时，会将采集到的加速传感器序列数据传入模型，进行推断。

+ 项目总结： 展示了如何使用CoreMotion获取运动传感器数据。


## 8. AR画刷
+ 项目地址：https://github.com/laanlabs/ARBrush
+ 关键字： ARKit, metal, SceneKit
+ 项目效果：
![](img/CFF1C9C4-B43B-471F-BDE9-F4D4DC6579AF.png)
+ 功能介绍：  可以通过按钮来增加景深，然后按住屏幕并移动手机，就可以画出想要画的图形。
+ 项目总结： 代码有点复杂，需要学习相关知识后才能理解代码运作的流程。


## 9. AR识物
+ 项目地址： https://github.com/hanleyweng/CoreML-in-ARKit
+ 关键词： CoreML， ARKit，SceneKit
+ 项目效果： 
![](img/E0C522DD-A541-48EA-B0E8-DC8293FE0A82.png)

+ 功能介绍：点击屏幕，将识别到的物体的标签放置在屏幕中心指定的场景位置。
+ 技术介绍：主要是看点击屏幕时的处理函数：
``` swift
@objc func handleTap(gestureRecognize: UITapGestureRecognizer) {
        // HIT TEST : REAL WORLD
        // Get Screen Centre
        let screenCentre : CGPoint = CGPoint(x: self.sceneView.bounds.midX, y: self.sceneView.bounds.midY)
        
        let arHitTestResults : [ARHitTestResult] = sceneView.hitTest(screenCentre, types: [.featurePoint]) // Alternatively, we could use '.existingPlaneUsingExtent' for more grounded hit-test-points.
        
        if let closestResult = arHitTestResults.first {
            // Get Coordinates of HitTest
            let transform : matrix_float4x4 = closestResult.worldTransform
            let worldCoord : SCNVector3 = SCNVector3Make(transform.columns.3.x, transform.columns.3.y, transform.columns.3.z)
            
            // Create 3D Text
            let node : SCNNode = createNewBubbleParentNode(latestPrediction)
            sceneView.scene.rootNode.addChildNode(node)
            node.position = worldCoord
        }
    }
```

这里通过SceneKit获得标签应该被放置的三维坐标，然后将latestPrediction制作成3D Text的SceneNode放置到场景中。

+ 项目总结： 结合了CoreML、ARKit和SceneKit的应用，似乎ARKit经常是和SceneKit放在一起使用。


## 10. AR叠高塔游戏
+ 项目地址： https://github.com/XanderXu/ARStack
+ 关键词： ARKit SceneKit
+ 项目效果：
[ARStack/1605417e98d57f47.gif at master · XanderXu/ARStack · GitHub](https://github.com/XanderXu/ARStack/blob/master/1605417e98d57f47.gif)







