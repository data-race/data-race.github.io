---
title: AR Quick Look
tags:
  - ios开发
categories:
  - iOS开发
date: 2023-07-17 20:17:29
---
#ios开发
增强现实技术是苹果着重发展的一个技术，自从WWDC 2018发布了ARKit和IOS12，AR已经被整合进了苹果的生态中。得益于AR Quick Look(AR 预览)技术，可以方便的在设备上展示AR的内容(例如苹果官网上可以用AR来体验新发布的Ipad等)

预览技术已经应用在苹果生态等很多方面，包括可以预览照片，视频和文档，而AR Quick Look可以让我们预览USDZ和Reality格式的，能够展示AR内容的文件。这个技术的应用场景可以是一些购物APP，可以让用户直观的看到产品。

## AR Quick Look的特性
+ Anchors： Anchor允许用户在真实世界中放置虚拟物体，在IOS13中，支持水平表面和垂直表面。
+ Occusion(堵塞)：允许真实的物体可以遮挡你放置的虚拟物体
+ Physics，Forces，Collisions：虚拟的物体也适用于物理定律，包括重力作用下的下落，碰撞等
+ Triggers，Behaviors：用户可以和虚拟物体交互
+ Realtim Shadows： 实时渲染的阴影效果
+ Physically Based Rendering Clear Coat Materials： 基于物理的材质渲染

## AR Quick Look的Limitation
+ 对用户的设备有高要求：只有最新和最强的高端设备可以获得所有的新特性（应该是说配备雷达测距仪的iPad Pro吧）
+ 只能在苹果生态中使用


## AR Quick Look for Apps
书中提供了几个USDZ格式的文件和一个App的脚手架，我们的工作是让这个App可以展示这些USDZ文件。
### 导入USDZ文件
![](img/87FC37A1-D94E-45E9-BA7C-085FF2E4B95D.png
)
直接将Models文件夹拖拽至Xcode项目中，并选择Create Groups

### 添加Protocols
为ViewController添加QLPreviewContollerDelegate和QLPreviewControllerDataSource两个protocol

``` swift
import QuickLook

extension ViewController: QLPreviewControllerDelegate,QLPreviewControllerDataSource {
  func numberOfPreviewItems(in controller: QLPreviewController) -> Int {
    return 1
  }
  
  func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem {
    let url = Bundle.main.url(forResource: modelNames[modelIndex], withExtension: "usdz")!
    return url as QLPreviewItem
  }
  
}
```

### 进行展示
``` swift
 func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
    modelIndex = indexPath.row
    let previewController = QLPreviewController()
    previewController.dataSource = self
    previewController.delegate = self
    present(previewController, animated: false)
  }
```

实际效果：

![](img/D6DAC27C36DB83F30FC9B54E7AB4AD2C.mp4
)



