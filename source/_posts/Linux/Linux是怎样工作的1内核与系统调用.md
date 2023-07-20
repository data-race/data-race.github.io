---
title: Linux 是怎样工作的1 内核与系统调用
date: 2023-07-17 20:17:25
tags: [linux, 例如]
---
#linux

## 内核是什么
**内核**的直观定义就是：在内核模式下运行的OS的核心程序，包括各种设备驱动程序、进程管理系统、进程调度器、内存管理系统。
## 为什么需要内核
我们可以考虑一个没有内核的系统上，如果我们的进程需要操作底层的硬件，例如通过网卡接收数据、读写磁盘等，是需要自己去实现设备处理程序，这样会带来很多不便：
- 开发者需要自己实现设备处理程序，开发成本高
- 多个进程如果同时去操作一个设备，会出现预料之外的问题
因此为了解决上述问题，Linux提供了::设备驱动程序::，使进程通过设备驱动程序访问设备。此外，为了避免程序绕过设备驱动程序，将CPU分为了::用户模式::和::内核模式::两种状态，只有处于内核模式时，才可以访问设备。除此之外，还有一些特殊的OS程序，不应该运行在用户模式，例如：
- 进程管理程序
- 进程调度程序
- 内存管理系统
这些程序也全部在内核态下运行。
##  应用怎么使用内核
用户态进程和内核的关系就像是Client-Server架构中，客户端和服务器的关系，要使用内核提供的功能，用户进程需要发起系统调用
```x86asm
mov $xxx, %eax # 系统调用号放入%eax寄存器
syscall		  # 系统调用
```
![](img/095BB9E8-A2FE-4CEA-B455-0BBEE7DDD73B1.png
)

## 技巧
- 查看系统调用
``` shell
strace -o <path-to-log> <executable-file>
#例如
# strace -o hello.log ./helloworld
# strace -o hello.log python3 hello.py
# strace -T -o  hello.log ./helloworld (-T采集时间)
```

- 查看系统调用说明
``` shell
man 2 <syscall-name>
# 例如
# man 2 write
# man 2 read
```

- 采集CPU在用户态和内核态分别的用时
``` shell
sar -P <core-id> <period>
# 例如
# sar -P 0 1
# sar -P ALL 1
```

 - 查看依赖的库
``` shell
ldd <path-to-executable>
``` 