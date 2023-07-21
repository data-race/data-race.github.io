---
title: Windows开发环境配置
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-19 13:01:34
---
#环境配置 

## 安装工具

- Windows Terminal
- Visual Studio
- Visual Studio Code
- WSL
- Docker，安装Docker会自动安装Kubectl
- Nerd Font + Fira Code Font
- 运维工具: Terraform, Azure-Cli

## WSL配置

WSL选择运用较为广泛的Ubuntu，首先需要开启Windows Features。再TaskBar的搜索框中搜索`Turn On/Off Windows Features`.

![](img/Pastedimage20230718153029.png)

勾选上Windows Subsystem for Linux，然后重启机器后，在微软应用商店中安装Ubuntu即可。安装之后，可以按照[[Zsh 配置]]等在Ubuntu中配置Linux开发环境。

## Windows Terminal 配置

在微软应用商店中安装Windows Terminal，安装后，会自动添加Powershell和Ubuntu的Profile。但是Ubuntu默认使用的是Bash，在Profile中设置使用zsh
![](img/Pastedimage20230718153243.png
)
将`Command Line` 修改为`ubuntu2204.exe -c zsh` 即可。


## VSCode / Visual Studio配置
VSCode配置较为简单，直接登录自己的github账号，就可以同步安装VSCode扩展。
Visual Studio也是类似。

## Powershell配置
可以使用类似`oh-my-zsh`的`oh-my-posh`对Powershell进行配置，为Powershell添加补全等功能。
首先下载`oh-my-posh`

```powershell
winget install JanDeDobbeleer.OhMyPosh -s winget
notepad $PROFILE
```

在PROFILE中写入下面的脚本，类似于`.zshrc`

```powershell
oh-my-posh init pwsh | Invoke-Expression
```

然后添加自动补全插件
```powershell
Install-Module -Name PSReadLine -Scope CurrentUser -Force -SkipPublisherCheck
notepad $PROFILE
# 写入如下内容
# Add auto complete (requires PSReadline 2.2.0-beta1+ prerelease)
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView
Set-PSReadLineOption -EditMode Windows
```

最后设置一些Alias和Function
```powershell
New-Alias -Name tf -Value terraform
New-Alias -Name k -Value kubectl
New-Alias -Name dn -Value dotnet

function kg { kubectl get $args }
```

效果：

![](img/Pastedimage20230718154358.png
)



## 编程环境安装
### C\# 
直接去官网下载安装：[.NET | Build. Test. Deploy. (microsoft.com)](https://dotnet.microsoft.com/en-us/)

### Golang
[The Go Programming Language](https://go.dev/)

### Java
安装Azure Java SDK
[Microsoft Build of OpenJDK](https://www.microsoft.com/openjdk)

### Python
安装Anaconda [Conda :: Anaconda.org](https://anaconda.org/anaconda/conda)
然后在Conda Prompt中执行`conda init`

### 环境变量设置

![](img/Pastedimage20230718154914.png
)

类似于Linux中的环境变量，只是方式不一样。
Linux中通过在`.zshrc`或者`/etc/profile` 中`export KEY=VALUE`来导入环境变量，Windows则是在用户图形界面中创建新的环境变量。
最后都需要将可执行文件所在路径加入到`PATH`中才可以在命令行中执行。