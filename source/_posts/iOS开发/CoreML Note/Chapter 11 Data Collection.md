---
title: Chapter 11 Data Collection
tags:
  - ios开发
categories:
  - iOS开发
date: 2023-07-17 20:17:29
---
#ios开发 

第7章到第10章主要还是针对图片分类模型的训练，更多的涉及如何使用turicreate和keras等框架来训练更强大的图像分类模型，而没有涉及ios app开发本身，所以我们着重来看第11章，如何为序列分类收集数据。

许多的任务是和序列化的数据相关的，例如从视频中提取信息，语音转文字，自然语言的处理等。在本章我们着重学习如何收集人类动作数据（human activity），并将其用作机器学习模型等训练。现代的硬件设备上拥有大量的传感器，你可以根据你的需求使用加速器传感器、陀螺仪传感器、计步器、磁力传感器、测高仪和GPS等，甚至可以从可穿戴设备获得用户的心率数据。


## Build a Dataset
数据集的建立是一个单调乏味且非常耗时的过程，往往需要收集数据，并且人工进行标注。在对人的行为进行标注时，需要观看视频，并进行标注，这可能导致错误。因此本章我们使用另一种方式来建立数据集，我们使用数据收集应用自动的为数据添加标注。

首先打开书中附带的数据收集应用程序 GestureDataRecorder。

![](img/66DC605E-7882-4F0A-9AAB-76E63378AA1E.png
)

这是一个工具应用，当我们选择了动作类型并输入了User ID后，点击Start session，遵照语音指示，做出相应动作，最后该应用可以将收集到的传感器数据打好标注，并存储。

整个应用的工作流程：当我们点击下Start Session按钮时，触发startRecording函数
``` swift
func startRecording() {
    enableUI(isEnabled: false)
    
    let dateFormatter = ISO8601DateFormatter()
    dateFormatter.formatOptions = .withInternetDateTime
    sessionId = dateFormatter.string(from: Date())
    
    numberOfActionsRecorded = 0
    speechSynth.speak(Utterances.phonePlacement)
  }
```

然后将开始播放语音提示，指导如何防止手机。这段代码都是在ViewController中实现，由于我们将ViewController实现了AVSpeechSynthesizerDelegate代理，然后实现了函数speechSynthesizer

![](img/39132B2A-A741-44BE-B790-6F9CE6B452DF.png
)

这个函数会在播放完一段语音后触发，然后在这个函数中，是一个switch语句，告诉应用播放完一段语音后接着应该干什么：

![](img/54E1C174-543F-4441-B8EC-2A6F1FAB528D.png
)

可以看到在播放完sessionStart语音之后，会调用函数queueNextActivity，来记录用户数据，目前这个函数还未实现，需要我们自己来引入CoreMotion，并实现数据采集的部分。
``` swift
func queueNextActivity() {
    if numberOfActionsRecorded >= numberOfActionsToRecord {
      speechSynth.speak(Utterances.sessionComplete, after: Config.secondsBetweenSetupInstructions)
      return
    }
    
    DispatchQueue.main.async { [weak self] in
      guard let self = self else {
        return
      }
      self.numberOfActionsRecorded += 1
      self.currendActivity = self.selectedActivity
      if self.numberOfActionsRecorded > 1 {
        self.speechSynth.speak(Utterances.again)
      } else {
        self.speechSynth.speak(self.utterance(for: self.currendActivity))
      }
    }
  }
```

## Accessing Device Sensors with Core Motion

首先在ViewController.swift中import CoreMotion
``` swift
import CoreMotion
```
然后在info.plist中添加对动作数据的访问权限需求
![](img/F6B7F9DD-2873-496D-AA31-A4C03BDBB73B.png
)

然后在ViewController中添加以下两个属性
``` swift
  // MARK: - Core Motion properties
  var motionManager = CMMotionManager()
  var queue = OperationQueue()
```

然后在startRecordingSession()中加入对Accessible的判断：
``` swift
guard motionManager.isDeviceMotionAvailable else {
      DispatchQueue.main.async { [weak self] in
        guard let self = self else {
          return
        }
        let alert = UIAlertController(title: "Unable to Record",
                                      message: "Device motion data is unavailable",
                                      preferredStyle: UIAlertController.Style.alert)
        alert.addAction(UIAlertAction(title: "Ok", style: .default))
        self.present(alert, animated: true, completion: nil)
      }
      return
    }
```

设定采样的频率
``` swift
static let samplesPerSecond = 25.0
```
苹果设备虽然可以达到100以上的采样频率，但是如果采样频率设置的太高会导致CPU占用过多，也会导致在模型的训练和推断都需要更长的时间，同时会增加电池的消耗。

添加存储数据的变量
``` swift
var activityData: [String] = []
```

在confirmSavingActivityData函数末尾加上实际进行存储的操作：
``` swift
do { try self.activityData.appendLinesToURL(fileURL: dataURL); print("Data appended to \(dataURL)") } catch {

print("Error appending data: \(error)") }
```

在ViewController中添加process方法，进行数据采集
``` swift
  func process(data motionData: CMDeviceMotion) {
    // 1
    let activity = isRecording ? currendActivity : .none
    // 2
    let sample = """
    \(sessionId!)-\(numberOfActionsRecorded),\
    \(activity.rawValue),\
    \(motionData.attitude.roll),\
    \(motionData.attitude.pitch),\
    \(motionData.attitude.yaw),\
    \(motionData.rotationRate.x),\
    \(motionData.rotationRate.y),\
    \(motionData.rotationRate.z),\
    \(motionData.gravity.x),\
    \(motionData.gravity.y),\
    \(motionData.gravity.z),\
    \(motionData.userAcceleration.x),\
    \(motionData.userAcceleration.y),\
    \(motionData.userAcceleration.z)
    """
    // 3
    activityData.append(sample)
  }
```

添加对process的调用：
``` swift
 func enableMotionUpdates() {
    // 1
    motionManager.deviceMotionUpdateInterval = 1 / Config.samplesPerSecond
    // 2
    activityData = []
    // 3
    motionManager.startDeviceMotionUpdates( using: .xArbitraryZVertical, to: queue, withHandler: { [weak self] motionData, error in
    // 4
      guard let self = self, let motionData = motionData else {
        let errorText = error?.localizedDescription ?? "Unknown"
        print("Device motion update error: \(errorText)")
        return
        
      }
      // 5
      self.process(data: motionData)
  })
  }
```

在speechSynthesizer()的sessionStart分支中添加对motion data的启用
``` swift
case Utterances.sessionStart:
      // TODO: enable Core Motion
      enableMotionUpdates()
      queueNextActivity()
```

添加对motionData的停用：
``` swift
func disableMotionUpdates()  {
    self.motionManager.stopDeviceMotionUpdates()
  }

...

case Utterances.sessionComplete:
      disableMotionUpdates()
```

然后就可以进行数据收集了。


