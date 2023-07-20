---
title: Golang CheatSheet
tags:
  - cheatsheet
  - 实用技巧
categories:
  - 实用技巧
date: 2023-07-17 20:17:25
---
#cheatsheet 
#实用技巧 

### 一行代码duplicate slice
```go
b := append([]T(nil), a...)
```

### 执行有超时检测的shell
```go
// 使用commandContext
ctx, cancel := context.WithTimeout(context.Backgroud(), time.Second * 10)
defer cancel()
cmd := exec.CommandContext(ctx, "/bin/bash", "-c", command)
if err := cmd.Run(); err != nil {
...
}

```

### 排序
- 如果排序的对象不是slice，那么需要让其实现sort.Interface
```go
type Interface interface {
        Len() int
        Less(i, j int) bool
        Swap(i, j int)
}
```
- 如果排序的对象是slice，那么直接用Slice
``` go
func Slice(slice interface{}, less func(i, j int) bool)  //排序
func SliceStable(slice interface{}, less func(i, j int) bool)  //稳定排序
func SliceIsSorted(slice interface{}, less func(i, j int) bool) bool // 判定是否有序
func Search(n int, f func(int) bool) int //判定是否存在制定元素，传入下标
```

## go 常用
[go mod使用 - 简书](https://www.jianshu.com/p/760c97ff644c)
```shell
go mod init <domain>/<group>/<project> #初始化
go mod download #下载依赖到GOPATH
go mod vendor #生成vendor(构建镜像的时候用)
go get package@version #更新package到指定版本
go get -u package	#更新package到最新版本
go mod tidy # 整理依赖
go build -mod=vendor #By default, if a vendor directory is present and the go version 
						#in go.modis 1.14 or higher, the go command acts as if -mod=vendor were set.
						# 如果缺失依赖，go build会将依赖自动拉取到go path
```

## golang 大礼包
``` sh
go install -v github.com/ramya-rao-a/go-outline@latest
go install -v github.com/cweill/gotests/gotests@latest
go install -v github.com/fatih/gomodifytags@latest
go install -v github.com/josharian/impl@latest
go install -v github.com/haya14busa/goplay/cmd/goplay@latest
go install -v github.com/go-delve/delve/cmd/dlv@latest
go install -v github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install -v golang.org/x/tools/gopls@latest
```

## 怎么写一个好的golang makefile
```makefile
REPO=<domain>/<org>/<repo> # 例如 github.com/cuizihan/AwesomeGoProject
VERSION_PKG_PATH=${REPO}/version
VERSION=$(shell sed -nr 's/^version:\s+v?(\S+)/v\1/p' ./chart/Chart.yaml)
GIT_COMMIT=$(shell git show -s --format=%h)
IMAGE_TAG="${VERSION}-${GIT_COMMIT}"

init:
    mkdir -p _bin

main: init
    go build -ldflags "-X '${VERSION_PKG_PATH}.goVersion=`go version`' -X '${VERSION_PKG_PATH}.version=${VERSION}' -X '${VERSION_PKG_PATH}.gitHash=`git show -s --format=%H`' -X '${VERSION_PKG_PATH}.buildTime=`git show -s --format=%cd`'" -o _bin/main xxx/main.go

image: main
    docker build -t <ImageName>:${IMAGE_TAG} . -f <Path-to-Dockerfile>
    docker push <ImageName>:${IMAGE_TAG}

deploy:
    kubectl apply -f manifests/xxx.yaml

undeploy:
    kubectl delete -f manifests/xxx/yaml

clean:
    rm -f _bin/*
```

## 交叉编译
``` shell 
# 交叉编译必须禁用CGO
# GOARCH: amd64, 386, arm64
CGO_ENABLED=0 GOOS=linux  GOARCH=amd64  go build main.go
CGO_ENABLED=0 GOOS=windows  GOARCH=amd64  go build main.go
CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build main.go
```

## 范型
``` go
// 范型结构体
type Foo[T int | int32 | string | float32] struct {
	bar T
	...
}

// 范型方法
func (receiver Foo[T]) Bar(parameter T) T

// 范型函数
func foo[T int | float | string](parameter T) T {
	...
}

// 范型套娃 （| 和 ～）
type UnsignedInteger interface {
	uint | ～uint32 | uint64 | uint16 | ~uint8 // byte 和 rune也被包括了
}
type SignedInteger interface {
	int | int32 | int64 | int16 | int8
}

type Integer interface {
	UnsignedInteger | SingnedInteger
}

// 新alias (comparable, any)
// comparable 可比较类型，注意可比较并非可排序
// any 是 interface{}的别名
type MyMap[K comparable, V any] map[K]V
```


## Golang Simplest Server
```go
package main


import (
	"fmt"
	"net/http"
)

  

func hello(w http.ResponseWriter, req *http.Request) {
	fmt.Fprintf(w, "hello world!\n")
}

  

func main() {
	http.HandleFunc("/hello", hello)
	_ = http.ListenAndServe(":9999", nil)
}
```
