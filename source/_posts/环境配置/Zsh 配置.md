---
title: Zsh 配置
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置 

- 安装zsh软件包
``` shell
CentOS： yum -y install zsh git
Ubuntu:  sudo apt -y install zsh git
```

- 克隆zsh
``` shell
git clone https://github.com/robbyrussell/oh-my-zsh.git ~/.oh-my-zsh
```

- 复制配置文件
``` shell
cp ~/.oh-my-zsh/templates/zshrc.zsh-template ~/.zshrc
```

- 修改Shell类型
``` shell
chsh -s /bin/zsh
```

- 下载补全插件/高亮插件
``` shell
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

```

``` shell
vim .zshrc


......
plugins=(
	git
	zsh-syntax-highlighting
	zsh-autosuggestions
)

```

- 安装powerlevel10k
```sh
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/powerlevel10k
echo 'source ~/powerlevel10k/powerlevel10k.zsh-theme' >>~/.zshrc
```

- p10配置
```sh
p10k configure
```
