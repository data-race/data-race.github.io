---
title: Terraform CheatSheet
tags:
  - cheatsheet
  - 实用技巧
categories:
  - 实用技巧
date: 2023-07-17 20:17:25
---
#cheatsheet 
#实用技巧 

### 获取创建的IAM User的secret

``` shell
tf state pull | jq '.resources[] | select(.type == "aws_iam_access_key") | .instances[0].attributes.secret'
```
