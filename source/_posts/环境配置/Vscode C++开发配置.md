---
title: Vscode C++开发配置
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 
在建立好项目之后，因为项目的结构很复杂，所以必须通过c_cpp_properties.json中的includePath来进行代码嗅探。
比较坑的地方是MAC下，vscode似乎不会自动的从系统变量中，例如CPLUS_INCLUDE_PATH去找头文件，所以对与libclang的头文件，也是需要自己将其加入到includePath的。

![](img/6FDD30C7-1732-4C47-9613-906C12F5BF0B.png
)

但是在构建时，还是需要自己使用makefile来构建
``` makefile
CC = clang++
CPPFLAGS = -g -std=c++11 -lclang
LLVM_INCLUDE = `llvm-config --includedir`
LLVM_LIB = `llvm-config --libdir`
MESSAGE?=update

codesim: clean ast-parser
    $(CC) -o codesim AST.o ASTParser.o src/main.cpp -I ./include -I ./lib/include  -I $(LLVM_INCLUDE) -L $(LLVM_LIB) $(CPPFLAGS)

ast-parser: 
    $(CC) -c src/AST.cpp src/ASTParser.cpp  -I ./include -I ./lib/include -I $(LLVM_INCLUDE) -L $(LLVM_LIB) $(CPPFLAGS)



.PHONY: clean test push

clean:
    rm -f *.o
    rm -f *~
    rm -f codesim

test: codesim
    ./codesim ./testcase/1.cpp  ./testcase/1.format.cpp
    ./codesim ./testcase/1.cpp  ./testcase/2.format.cpp 
    ./codesim ./testcase/1.cpp  ./testcase/3.format.cpp 
    ./codesim ./testcase/1.cpp  ./testcase/4.format.cpp 
    ./codesim ./testcase/2.format.cpp ./testcase/3.format.cpp
    ./codesim ./testcase/2.format.cpp ./testcase/4.format.cpp
    ./codesim ./testcase/3.format.cpp ./testcase/4.format.cpp
    ./codesim ./testcase/5.format.cpp ./testcase/6.format.cpp
    ./codesim ./testcase/5.format.cpp ./testcase/7.format.cpp
    ./codesim ./testcase/6.format.cpp ./testcase/7.format.cpp

    ./codesim ./testcase/1.cpp  ./testcase/5.format.cpp 
    ./codesim ./testcase/1.cpp  ./testcase/6.format.cpp 
    ./codesim ./testcase/1.cpp  ./testcase/7.format.cpp  

push:
    git add .
    git commit -m "$(MESSAGE)"
    git push origin master


```

如果没找到c_cpp_properties.json，在控制面板中输入Edit Configuration

![](img/E4843886-8BB8-44D9-8839-2AAF87F5742F.png
)
会自动创建该文件。

