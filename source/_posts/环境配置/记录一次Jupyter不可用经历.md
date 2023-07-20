---
title: 记录一次Jupyter不可用经历
tags:
  - 环境配置
categories:
  - 环境配置
date: 2023-07-17 20:17:25
---
#环境配置

全局安装jupyter之后，jupyter会在/usr/share/jupyter下创建data dir。但是这个datadir对所有用户可见，但是又不是所有用户都有权限，详见[Template directories not created with world-readable permissions · Issue #1559 · jupyter/nbconvert · GitHub](https://github.com/jupyter/nbconvert/issues/1559)

colinasmith给了两种fix方法
1. 一旦有子目录创建在/usr/share/jupyter/nbconvert/templates下，就要更改其权限，确保是可读可写的
2. **修改nbconvert的加载逻辑**

根据1167号issue https://github.com/jupyter/nbconvert/issues/1167 的描述，在`envs/ml-env/lib/python3.6/site-packages/nbconvert/exporters/templateexporter.py`的`_get_conf`函数中，nbconvert会尝试从jupyter的所有data path下面读取template，不仅仅是环境自己的data path

``` shell
$ jupyter --path
config:
    /home/czh/.jupyter
    /home/czh/anaconda3/envs/ml-env/etc/jupyter
    /usr/local/etc/jupyter
    /etc/jupyter
data:
    /home/czh/.local/share/jupyter
    /home/czh/anaconda3/envs/ml-env/share/jupyter
    /usr/local/share/jupyter
    /usr/share/jupyter
runtime:
    /home/czh/.local/share/jupyter/runtime
```

`_get_conf`的函数定义如下：
``` python
    def _get_conf(self):
        conf = {}  # the configuration once all conf files are merged
        for path in map(Path, self.template_paths):
            conf_path = path / 'conf.json'
            if conf_path.exists():
                with conf_path.open() as f:
                    conf = recursive_update(conf, json.load(f))
        return conf
```

在读取conf path时，如果遇到没有读写权限的路径，这里是直接抛出错误。[#1167](https://github.com/jupyter/nbconvert/issues/1167) 建议用一个空的try except来忽略这种错误，但是这种fix方案一直没有被jupyter的维护者接受。

## 解决方案
- 使用其他版本的jupyter
在4.6.1版本的jupyter中没有发现这个问题
- 修改`_get_conf`函数的逻辑
手动忽略 /usr/share
``` python
    def _get_conf(self):
        conf = {}  # the configuration once all conf files are merged
        for path in map(Path, self.template_paths):
            if str(path).startswith('/usr'):
                print('ignore path: {}'.format(path))
                continue
            conf_path = path / 'conf.json'
            if conf_path.exists():
                with conf_path.open() as f:
                    conf = recursive_update(conf, json.load(f))
        return conf
```

