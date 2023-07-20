---
title: Git CheatSheet
tags:
  - cheatsheet
  - 实用技巧
  - 修改之前某次
  - 将pick改为edit
categories:
  - 实用技巧
date: 2023-07-17 20:17:25
---
#cheatsheet 
#实用技巧 

###  修改commit message
```shell
git commit --amend -m "new commit message" # 修改上一条

#修改之前某次
git rebase -i commit_id

# pick 56b2308 feat(pages): home DONE
# pick 82f65eb fix(pages movie): slides bug fixed
# pick 08b2087 feat(pages home & movie): add FABs animation 
#将pick改为edit
# edit 56b2308 feat(pages): home DONE
# pick 82f65eb fix(pages movie): slides bug fixed
# pick 08b2087 feat(pages home & movie): add FABs animation 
# 修改完成后

git commit --amend
git rebase --continue
```
[修改 commit message - 简书](https://www.jianshu.com/p/5361e373537c)

### 查看/修改远程地址

```shell
git remote -v
git remote remove origin 
git remote add origin ${NEW ORIGIN}

```

### 暂存/恢复
``` shell
git stash -u # 暂存修改，包括untracked file
git stash list # 查看暂存
git stash pop # 恢复修改
```

## 回滚文件夹
https://stackoverflow.com/questions/6119036/how-to-revert-a-folder-to-a-particular-commit-by-creating-a-patch

``` shell
git reset <commit-id> -- somefolder
git checkout -- somefolder
git clean -fd somefolder
```

## Rebase来合并/同步

如果我的分支上有了一些修改，但是这时main分支上有了别人提交的commit，可以通过
```shell
git switch main
git pull origin main
git switch <BranchName>
git rebase main
```
来变更当前分支的基分支，和merge类似，但是是线性的
![](img/Pastedimage20230215163755.png
)
