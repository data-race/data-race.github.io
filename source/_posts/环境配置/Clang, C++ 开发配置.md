---
title: 'Clang, C++ 开发配置'
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 

## 前言
很久没有使用C++进行开发了，或者说之前也没有使用过C++去写一些大型项目。在软件工程这门课上，要求开发一个代码相似度检测工具。大体思路都是需要用Clang来解析AST的，尽管在Python和Go等语言中都可以通过Cython或者Cgo来使用libclang，但是还是原生的C++更加稳定。因此我使用C++来进行开发。

## Clang 安装
``` shell
sudo apt-get insatll llvm-dev clang libclang-dev
```

之后可以通过`llvm-config` 来查看一些重要信息
``` shell
czh@n33:~$ llvm-config --libdir
/usr/lib/llvm-10/lib
czh@n33:~$ llvm-config --version
10.0.0
```
我们来看一下llvm lib的结构
```  shell
czh@n33:/usr/lib/llvm-10$ tree -L 1
.
├── bin
├── build
├── cmake -> lib/cmake/llvm
├── include
├── lib
└── share
```

这里我们主要关注的是include和lib两个文件夹，include中是使用libclang所需的头文件，lib存储了动态链接库：
``` shell
czh@n33:/usr/lib/llvm-10/include$ tree -L 1
.
├── clang
├── clang-c
├── llvm -> ../../../include/llvm-10/llvm
├── llvm-c -> ../../../include/llvm-c-10/llvm-c
├── openmp
└── polly
```

``` shell
czh@n33:/usr/lib/llvm-10/lib$ tree -L 1
.
├── clang
├── cmake
├── libarcher.so
├── libarcher_static.a
├── libclang-10.0.0.so -> libclang-10.so
├── libclang-10.so -> ../../x86_64-linux-gnu/libclang-10.so.1
├── libclang-10.so.1 -> ../../x86_64-linux-gnu/libclang-10.so.1
├── libclangAnalysis.a
├── libclangApplyReplacements.a
├── libclangARCMigrate.a
├── libclangAST.a
......
```

如果我们想使用这些库，那么应该把include和lib加入到某些路径变量中，也可以在编译的时候动态指定，我是在编译时动态指定的，后面会介绍。

## 环境配置
解析AST主要使用clang-c，为了能让vscode的intellisense可以找到我们所依赖的包，我们在/usr/include 中建立符号链接到 $LLVM/include/clang-c
``` shell
ln -s /usr/include/clang-c /usr/lib/llvm-10/include/clang-c
```

然后当我们#include<clang-c/Index.h>时，vscode就可以解析了
![](img/EE69DB22-2C67-4FD7-9F89-C213B5157A70.png
)

## 项目配置

![](img/AC560F9A-E69E-428C-92D1-5889CC4F9FCC.png
)
我的项目的结构是这样，include包含公用头文件，代码在src中，lib中放一些第三方的包，比如argparser之类的，如果有的话。似乎头文件放到include中，就可以自动找到，不需要额外处理，但是在编译时仍然需要特殊处理一下。

## G++ 编译
我们需要让编译器找到我们使用的库，我们通过 -I(大写i)来指定要include的头文件所在文件夹，通过 -L来指定动态链接库的地址。例如
``` shell
g++  -I /usr/lib/llvm-10/include -L /usr/lib/llvm-10/lib -g -std=c++11 test.cpp -lclang -o test
```

这里还加入了一些flag，因为我们用了clang，所以要加上 -lclang，这里编译的test.cpp来自一个简单的clang例子https://shaharmike.com/cpp/libclang/

此外对于我们自己写在include/下的hpp，我们在编译时也要指定 -I ./include，这样才能生成.o文件
``` shell
g++ -c src/ASTParser.cpp -I ./include ...
```

## Makefile组织
大概知道makefile可以定义一些规则以及他们的依赖关系，比如这样：
```makefile
CC = g++
CFLAGS = -g -std=c++11 -lclang
LLVM_INCLUDE = /usr/lib/llvm-10/include
LLVM_LIB = /usr/lib/llvm-10/lib

codesim: clean
    $(CC) -o codesim src/main.cpp -I $(LLVM_INCLUDE) -L $(LLVM_LIB) $(CFLAGS)

.PHONY: clean
clean:
    rm -f *.o
    rm -f *~
    rm -f codesim
```