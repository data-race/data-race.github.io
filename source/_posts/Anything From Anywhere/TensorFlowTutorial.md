---
title: TensorFlow Tutorial
tags:
  - 充电
categories:
  - Anything From Anywhere
date: 2023-07-17 20:17:25
---
#充电 

## 概览

### Tensorflow 介绍

TensorFlow 是 Google 于 2015 年发布的深度学习框架，最初版本只支持符号式编程。得益于发布时间较早，以及 Google 在深度学习领域的影响力，TensorFlow 很快成为最流行的深度学习框架。


![](img/Pastedimage20221108165854.png)


发展历史
- 2016.4: 发布0.8.0，原生支持分布式运行
- 2016.6: 发布0.9.0，原生支持iOS
- 2016.12: 发布0.12.0，支持Windows系统
- 2017.2：发布1.0.0
- 2017.5: 发布专用于Android开发的Tensorflow Lite
- 2019.9: 发布Tensorflow 2.0，进行大量变更

### Tensorflow 和 PyTorch

目前来看，TensorFlow 和 PyTorch 框架是业界使用最为广泛的两个深度学习框架，TensorFlow 在工业界拥有完备的解决方案和用户基础，PyTorch 得益于其精简灵活的接口设计，可以快速设计调试网络模型，在学术界获得好评如潮。TensorFlow 2.x 发布后，弥补了 TensorFlow 在上手难度方面的不足，使得用户可以既能轻松上手TensorFlow 框架，又能无缝部署网络模型至工业系统。

### 深度学习训练任务

```plantuml
dataloader -> model: data batch
dataloader -> criterion: label
model -> criterion: output
criterion -> optimizer: loss
optimizer -> model: update
```



### 静态图 vs 动态图

模型的本质是计算图，图中的节点是算子，边是变量。
![](img/Pastedimage20221108192939.png)

在深度学习框架中，构建计算图的方式有两种
- 一种是命令式(imperative)
	命令式的程序使用编程语句改变程序状态，明确输入变量，并根据程序逻辑逐步运算。Pytorch 便是采用命令式编程的范式。
	- 优点：它易于理解，大部分代码编起来都很直观。程序也容易调试，可以很方便地进行单步跟踪，获取并分析所有中间变量。
	- 缺点：计算图是运行时根据具体执行的命令动态生成的，因此难以在运行前去进行优化，所以不适合对性能特别敏感（比如部署的场景）
- 一种是符号式(symbolic)
	符号式编程一般先定义各种变量，然后建立一个计算图(数据流图)，计算图指定了各个变量之间的计算关系，此时对计算图进行编译，没有任何输出，计算图还是一个空壳，只有把需要运算的输入放入后，才会在模型中形成数据流，形成输出。
	- 更高效，在编译的时候系统容易做更多优化。它也更容易移植。
	- 缺点，不够灵活，难以运行时调试




### Tensorflow 1.x vs Tensorflow 2.x

Tensorflow 1.x 是符号式的，Tensorflow 2.x是命令式的。两者在编程风格和接口设计上有较大的区别。Tensorflow 2.x不兼容Tensorflow 1.x 的代码

1. Tensorflow 2.x 提供动态图优先，可以通过Tensorflow Keras API构建模型
	TensorFlow 与 Keras 之间有着密切的联系。Keras 可以理解为一套高层 API 的设计规范，Keras 本身对这套规范有官方的实现，在 TensorFlow 中也实现了这套规范，称为 tf.keras 模块，并且 tf.keras 将作为 TensorFlow 2.x 版本的唯一高层接口，避免出现接口重复冗余的问题。
2. Tensorflow 2.x 提供了`@tf.function` 装饰器用于将动态图代码转换成静态图，用于提升运行效率。

例子

``` python
# tf 1.x
import tensorflow as tf
a = tf.placeholder(tf.float32, name='var_a')
b = tf.placeholder(tf.float32, name='var_b')
add_op = tf.add(a, b, name='var_c')
sess = tf.InteractiveSession()
init = tf.global_variables_initializer()
sess.run(init)
res = sess.run(add_op, feed_dict={a:2., b:4.,})
print('a+b=', res)
```

```python
# tf 2.x
import tensorflow as tf
a = tf.constant(2.)
b = tf.constant(4.)
print('a+b=', a+b)
```


---

## 任务： 手写数字识别

### 安装anaconda

https://www.anaconda.com

anaconda提供了对于Python/R/Julia等数据科学语言的环境管理方案，通过创建不同的环境可以很好的实现不同环境之间语言版本、依赖的第三方的类库的隔离，也容易实现环境的共享和迁移。

anaconda 并不是IDE

下载方式

1. 官网图形化安装: www.anaconda.com
2. 命令行安装
```shell
wget https://repo.anaconda.com/archive/Anaconda3-2022.10-Linux-x86_64.sh
bash Anaconda3-2022.10-Linux-x86_64.sh
cd ~/anaconda/bin
./conda init
```
![](img/Pastedimage20221108195816.png)

常用命令
``` shell
conda create -n $ENV_NAME python=x.y.z
conda activate $ENV_NAME
conda deactivate
conda install -n $ENV_NAME some-package
```

### Tensorflow 1.x 写法

#### 环境配置

``` shell
conda create -n tf-1x  python=3.8
conda activate tf-1x
pip3 install tensorflow-gpu==1.12.0
pip3 install tensorflow==1.12.0 matplotlib
```

#### 数据集
``` python
from tensorflow.examples.tutorials.mnist import input_data
mnist = input_data.read_data_sets("../dataset/", one_hot=True)
print("train dataset: image shape: {}, label: shape: {}".format(
    mnist.train.images.shape,
    mnist.train.labels.shape,
))

print("test dataset: image shape: {}, label: shape: {}".format(
    mnist.test.images.shape,
    mnist.test.labels.shape,
))

label = np.argmax(mnist.train.labels[32])  
im = np.reshape(mnist.train.images[32], [28,28])
plt.imshow(im, cmap='Greys')
plt.title('label:' + str(label))
plt.show()
```

#### 模型

- 工具函数
``` python
""" Initialize weight """
def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)

""" Initialize bias """ 
def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)

""" Define convolution """
def conv2d(x, W):
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

""" Define pooling """
def max_pool_2x2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')

```

- 模型定义
	两层卷机 + 全连接 + dropout + 全连接
```python
g = tf.Graph()
with g.as_default():
    x = tf.placeholder(tf.float32, [None, 784])
    y_true = tf.placeholder(tf.float32, [None, 10])
    # reshape
    x_image = tf.reshape(x, [-1,28,28,1])
    # 卷积层 1， weight和bias
    W_conv1 = weight_variable([5, 5, 1, 32])  
    b_conv1 = bias_variable([32])
    # 卷积操作 1
    h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)
    # 池化操作 1
    h_pool1 = max_pool_2x2(h_conv1)
    # 卷积层 2， weight和bias
    W_conv2 = weight_variable([5, 5, 32, 64]) 
    b_conv2 = bias_variable([64])
    # 卷积操作 2
    h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
    # 池化操作 2
    h_pool2 = max_pool_2x2(h_conv2)
    # 全连接层， weight和bias
    W_fc1 = weight_variable([7 * 7 * 64, 1024])  
    b_fc1 = bias_variable([1024])
    # 全连接操作
    h_pool2_flat = tf.reshape(h_pool2, [-1, 7*7*64])
    h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)
    # drop out
    keep_prob = tf.placeholder(tf.float32)
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)
    # 全连接 2
    W_fc2 = weight_variable([1024, 10])
    b_fc2 = bias_variable([10])
    y_conv=tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)
```

#### 训练评估
``` python
with g.as_default():
    cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_true * tf.log(y_conv), reduction_indices=[1]))
    optimizer = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
    correct_prediction = tf.equal(tf.argmax(y_conv,1), tf.argmax(y_true,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

with tf.Session(graph=g) as sess:
    sess.run(tf.global_variables_initializer())
    
    # Sample every 100 pieces of data to perform learning 2000 times.
    for i in range(2000):
        batch = mnist.train.next_batch(100)
        if i % 100 == 0:
            train_accuracy = accuracy.eval(feed_dict={
                x: batch[0], y_true: batch[1], keep_prob: 1.0})
            print('step {}, training accuracy {}'.format(i, train_accuracy))
        optimizer.run(feed_dict={x: batch[0], y_true: batch[1], keep_prob: 0.5})

    print('test accuracy {}'.format(accuracy.eval(feed_dict={
        x: mnist.test.images, y_true: mnist.test.labels, keep_prob: 1.0})))
```

### Tensorflow 2.x 写法

#### 环境配置

```shell
conda create -n tf-2x  python=3.8
conda activate tf-2x
pip3 install tensorflow==2.4
```

#### 代码

``` python
import tensorflow as tf
from tensorflow.keras import Model, layers
import numpy as np
# Training parameters.
learning_rate = 0.1
training_steps = 500
batch_size = 256
display_step = 100
# dataset
from tensorflow.keras.datasets import mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train, x_test = np.array(x_train, np.float32), np.array(x_test, np.float32)
x_train = x_train.reshape(x_train.shape+(1,))
x_test = x_test.reshape(x_test.shape + (1,))
x_train, x_test = x_train / 255., x_test / 255.
x_train.shape, x_test.shape
# model
class SimpleConvNet(Model):
    def __init__(self):
        super(SimpleConvNet, self).__init__()
        self.conv1 = layers.Conv2D(4, 3, activation='relu', padding='same') # (batch_size, 28, 28, 1) -> (batch_size, 28, 28, 4)
        self.conv2 = layers.Conv2D(2, 3, activation='relu', padding='same') # (batch_size, 28, 28, 4) -> (batch_size, 28, 28, 2)
        self.flatten = layers.Flatten()
        self.fc = layers.Dense(10)
    
    def call(self, x, is_training=False):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.flatten(x)
        x = self.fc(x)
        if not is_training:
            x = tf.nn.softmax(x)
        return x

neural_net = SimpleConvNet()

# train and eval
# Cross-Entropy Loss.
# Note that this will apply 'softmax' to the logits.
def cross_entropy_loss(x, y):
    # Convert labels to int 64 for tf cross-entropy function.
    y = tf.cast(y, tf.int64)
    # Apply softmax to logits and compute cross-entropy.
    loss = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=y, logits=x)
    # Average loss across the batch.
    return tf.reduce_mean(loss)

# Accuracy metric.
def accuracy(y_pred, y_true):
    # Predicted class is the index of highest score in prediction vector (i.e. argmax).
    correct_prediction = tf.equal(tf.argmax(y_pred, 1), tf.cast(y_true, tf.int64))
    return tf.reduce_mean(tf.cast(correct_prediction, tf.float32), axis=-1)

# Stochastic gradient descent optimizer.
optimizer = tf.keras.optimizers.SGD(learning_rate)

# Optimization process. 
def run_optimization(x, y):
    # Wrap computation inside a GradientTape for automatic differentiation.
    with tf.GradientTape() as g:
        # Forward pass.
        pred = neural_net(x, is_training=True)
        # Compute loss.
        loss = cross_entropy_loss(pred, y)
        
    # Variables to update, i.e. trainable variables.
    trainable_variables = neural_net.trainable_variables

    # Compute gradients.
    gradients = g.gradient(loss, trainable_variables)
    
    # Update W and b following gradients.
    optimizer.apply_gradients(zip(gradients, trainable_variables))

train_data = tf.data.Dataset.from_tensor_slices((x_train, y_train))
train_data = train_data.repeat().shuffle(5000).batch(batch_size).prefetch(1)
# Run training for the given number of steps.
for step, (batch_x, batch_y) in enumerate(train_data.take(training_steps), 1):
    # Run the optimization to update W and b values.
    run_optimization(batch_x, batch_y)
    
    if step % display_step == 0:
        pred = neural_net(batch_x, is_training=True)
        loss = cross_entropy_loss(pred, batch_y)
        acc = accuracy(pred, batch_y)
        print("step: %i, loss: %f, accuracy: %f" % (step, loss, acc))

# Test model on validation set.
pred = neural_net(x_test, is_training=False)
print("Test Accuracy: %f" % accuracy(pred, y_test))
```


----
## 其他

### Tensorboard






