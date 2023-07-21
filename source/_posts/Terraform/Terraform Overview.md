---
title: Terraform Overview
tags: []
categories:
  - Terraform
date: 2023-07-17 20:17:26
---

## 基础设施即代码 Infrastructure as Code (IaC)

在云计算时代，各种公有云提供商(AWS, Azure, GCE, AliCloud) 提供了完备的产品，可以让小企业或者初创公司通过租用的方式，搭建自己所需的基础设施。比如某个小公司需要一些K8S集群进行测试、开发、生产环境部署，那么相比于高成本的自己搭建维护基础设施，更方便的选择是可以去订阅一些EKS，AKS实例。

相比于自己搭建基础设施，从公有云提供商租用基础设施有一下好处：
1. 基础设施的可靠性有提供商保证，租用者不需要考虑异地多副本这样的安全措施
2. 动态伸缩：如果访问量大，可以根据需求调整实例大小，如果访问量小，可以减少实例大小，因此节省了成本
3. 公有云提供多种服务，涵盖计算、存储、网络等，可以满足各种需求

当我们需要在公有云上创建基础设施时，往往需要登录到控制台，创建资源，配置资源，例如AWS Console，Azure Portal等
![](img/Pastedimage20230118142446.png)

手动使用控制台创建实例非常繁琐，特别是我们需要配置复杂的基础设施时，或者创建大量同一种类型的实例时，不仅容易出错，而且非常麻烦。HashiCorp提出了解决方案TerraForm，可以通过编写HCL脚本来自动化基础设施创建的步骤，同时通过模块化，也可以让基础设施的创建变得可以复用，让创建基础设施变得像写代码一样。(Infrastructure as Code)

## 概念

### 项目结构
一般来说，一个Terraform的项目结构如下
``` less
.
├── README.md
├── main.tf
├── variables.tf
├── outputs.tf
├── ...
├── modules/
│   ├── nestedA/
│   │   ├── README.md
│   │   ├── variables.tf
│   │   ├── main.tf
│   │   ├── outputs.tf
│   ├── nestedB/
│   ├── .../
├── examples/
│   ├── exampleA/
│   │   ├── main.tf
│   ├── exampleB/
│   ├── .../
```

- README.md 包含了对模块的说明，比如目的，执行方法等
- variabels.tf 中定义需要输入的一些变量，比如实例名称，一些配置项等，可以通过`xxx.auto.tfvars` 来配置默认值，也可以在编写变量时提供默认值。
- outputs.tf 中定义模块等输出，一个模块中的输出可以被其他使用这个模块的模块引用
- main.tf：定义所需资源，所需其他模块
- modules：其他用到的模块
- exmaples: 可选使用例

### Provider

![](img/Pastedimage20230118144628.png)

Terraform 支持多种Provider，Provider可以理解为资源提供商。比如使用aws作为provider，就可以创建出很多aws的资源。更强的是，如果使用Kubernetes作为provider，还可以创建K8s的资源，有点点像Helm。
Provider通过插件的形式提供，因此Terraform的可扩展性很强。

### Variable
在`variables.tf` 中一般会定义一些配置项
``` less
variable "env_name" {
  description = "Environment name to make this deployment unique"
  type        = string
}

variable "project_name" {
  description = "Project name to name all resources"
  type        = string
}

variable "network" {
  description = "Network Configuration"
  type        = any
}

variable "worker_groups" {
  description = "Worker groups configuration"
  type        = list(any)
}
```

当我们执行 `terraform plan` 或者 `terraform apply` 时，会要求我们输入Variable的值，我也可以配置默认值或者提供默认值文件 
``` less
variable "name" {
  type    = string
  default = "John Doe"
}
```

默认值文件
``` less
# main.auto.tfvars
env_name     = "dev"
project_name = "project"
region       = "us-west-2"

network = {
  cidr            = "10.0.0.0/16"
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
}
```

同一个模块中，变量可以通过var.name进行引用，例如在声明资源定义时
``` less
resource "some_resource" "a" {
  name    = var.user_information.name
  address = var.user_information.address
}
```

### Output
如果把一个Terraform模块看作一个函数，那么Variabels就是输入，而Output就是输出。Output一般给调用者使用，例如某个模块创建了一个EKS后，将它的Admin Token作为输出，给调用者使用

``` less
output "instance_ip_addr" {
  description = "the private_ip of the instance"
  value = aws_instance.server.private_ip
}
```

output可以给调用者使用，通过module.name.output_name可以引用使用的模块的output
``` less
# main.tf
module "main" {
  source        = "../modules"
  env_name      = var.env_name
  project_name  = var.project_name
  network       = var.network
  worker_groups = local.worker_groups
}

# ../modules/output.tf
output "cluster_id" {
  description = "EKS cluster ID."
  value       = module.eks.cluster_id
}
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane."
  value       = module.eks.cluster_endpoint
}
...

# output.tf
output "cluster_id" {
  description = "EKS cluster ID."
  value       = module.main.cluster_id 
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane."
  value       = module.main.cluster_endpoint
}
```

### Resource
Terraform中，通过Resource Block创建资源
``` less
locals {
  eks_mng_sg          = "${var.remote_workspace}-${var.eks_cluster_name}-mng-sg"
  vpc_cni_irsa_prefix = "${var.eks_cluster_name}-CNI-IRSA"
  ebs_csi_irsa_prefix = "${var.eks_cluster_name}-EBS-CSI-IRSA"
}

resource "aws_kms_key" "eks" {
  description             = "EKS Secret Encryption Key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags                    = var.tags
  xxx                     = local.eks_mng_sg
}
```
创建格式为 `resource "resource_category" "name"`
在配置resource时，就可以使用var来引用变量，或者使用local来引用本地声明的值

不仅可以创建公有云提供商提供的资源，甚至可以创建K8s中的资源
``` less
resource "kubernetes_service_account_v1" "admin" {
  metadata {
    name      = var.admin_name
    namespace = var.admin_namespace
  }
  secret {
    name = local.token_name
  }
}

resource "kubernetes_secret_v1" "admin" {
  metadata {
    name      = local.token_name
    namespace = var.admin_namespace
    annotations = {
      "kubernetes.io/service-account.name" = var.admin_name
    }
  }

  type = "kubernetes.io/service-account-token"
  depends_on = [kubernetes_service_account_v1.admin]
}
```


### Module
除了创建resource外，还可以通过Module block来引用Module，并且创建Module下面的所有资源。Module可以是远程registry上的一个Module，也可以是本地路径
``` less
# 远程Module
resource "helm_release" "cert_manager" {
  name             = var.cert_manager_release_name
  namespace        = var.cert_manager_namespace
  create_namespace = var.cert_manager_create_namespace
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = var.cert_manager_version
  timeout          = 1200

  set {
    name  = "installCRDs"
    value = "true"
  }
  set {
    name  = "serviceAccount.name"
    value = var.cert_manager_service_account
  }
  set {
    name  = "serviceAccount.create"
    value = "true"
  }
  # Reference: https://cert-manager.io/docs/configuration/acme/dns01/route53/#service-annotation
  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = module.cluster_cert_manager_irsa_role.iam_role_arn
  }
  set {
    name  = "securityContext.fsGroup"
    value = "1001"
  }
}

# 本地Module
module "cert_manager" {
  source                        = "../../../shared_modules/k8s/cert_manager"
  cert_manager_namespace        = "cert-manager"
  cert_manager_create_namespace = var.cert_manager_create_namespace
  cert_manager_service_account  = "cert-manager"
  cert_manager_version          = var.cert_manager_version
  cert_manager_role_name        = "${var.workspace_name}-${var.eks_cluster_name}-cm-role"

  route53_zone_id           = var.route53_zone_id
  cluster_oidc_provider_arn = var.cluster_oidc_provider_arn

  tags = var.tags
}

```