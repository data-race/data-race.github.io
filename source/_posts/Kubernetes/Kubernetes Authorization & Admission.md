---
title: Kubernetes Authorization & Admission
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes 


## Authorization

当客户端的请求到达API-server后，经过认证后，会进入鉴权阶段。和Authentication一样，K8s也支持多种鉴权机制，只要有一个鉴权模块成功，就认为鉴权成功。

### 概念

在API server中，权限由一组动词描述
```go

// plugin/pkg/auth/authorizer/rbac/bootstrappolicy/policy.go
var (
	Write      = []string{"create", "update", "patch", "delete", "deletecollection"}
	ReadWrite  = []string{"get", "list", "watch", "create", "update", "patch", "delete", "deletecollection"}
	Read       = []string{"get", "list", "watch"}
	ReadUpdate = []string{"get", "list", "watch", "update", "patch"}
)
```
- Write: 只写
- Read： 只读
- ReadWrite: 可读可写
- ReadUpdate: 可读可更新，但是不可创建和删除


### 接口

#### Attributes
对于一个到达的Request，API-server会将其封装成一个实现了`Attributes`接口的对象，`Attributes`中提供了对一次Request的描述，包括这次Request的访问者的信息，访问的动作，访问的资源对象。

``` go
// Attributes is an interface used by an Authorizer to get information about a request
// that is used to make an authorization decision.
type Attributes interface {
	// GetUser returns the user.Info object to authorize
	GetUser() user.Info
	// GetVerb returns the kube verb associated with API requests (this includes get, list, watch, create, update, patch, delete, deletecollection, and proxy),
	// or the lowercased HTTP verb associated with non-API requests (this includes get, put, post, patch, and delete)
	GetVerb() string
	// When IsReadOnly() == true, the request has no side effects, other than
	// caching, logging, and other incidentals.
	IsReadOnly() bool
	// The namespace of the object, if a request is for a REST object.
	GetNamespace() string
	// The kind of object, if a request is for a REST object.
	GetResource() string
	// GetSubresource returns the subresource being requested, if present
	GetSubresource() string
	// GetName returns the name of the object as parsed off the request.  This will not be present for all request types, but
	// will be present for: get, update, delete
	GetName() string
	// The group of the resource, if a request is for a REST object.
	GetAPIGroup() string
	// GetAPIVersion returns the version of the group requested, if a request is for a REST object.
	GetAPIVersion() string
	// IsResourceRequest returns true for requests to API resources, like /api/v1/nodes,
	// and false for non-resource endpoints like /api, /healthz
	IsResourceRequest() bool
	// GetPath returns the path of the request
	GetPath() string
}
```

#### Authorizer
`Attributes`对象将经过`Authorizer`接口的鉴权，`Authorizer`的实现比较简单，接受一个`Attributes`，返回鉴权的结果
```go
// Authorizer makes an authorization decision based on information gained by making
// zero or more calls to methods of the Attributes interface.  It returns nil when an action is
// authorized, otherwise it returns an error.
type Authorizer interface {
	Authorize(a Attributes) (authorized Decision, reason string, err error)
}
```

#### RuleResolver
此外，还有一个特殊的接口`RuleResolver`，有一个方法`RelusFor`，接受一个用户信息和一个Namespace，返回该用户在这个Namespace下的所有Rules，这个Rules可以理解为资源+动词(Resources + Verbs)
```go
// RuleResolver provides a mechanism for resolving the list of rules that apply to a given user within a namespace.
type RuleResolver interface {
	// RulesFor get the list of cluster wide rules, the list of rules in the specific namespace, incomplete status and errors.
	RulesFor(user user.Info, namespace string) ([]ResourceRuleInfo, []NonResourceRuleInfo, bool, error)
}
```

其中, `ResourceRuleInfo`的定义为:
```go
type ResourceRuleInfo interface {
	// GetVerbs returns a list of kubernetes resource API verbs.
	GetVerbs() []string
	// GetAPIGroups return the names of the APIGroup that contains the resources.
	GetAPIGroups() []string
	// GetResources return a list of resources the rule applies to.
	GetResources() []string
	// GetResourceNames return a white list of names that the rule applies to.
	GetResourceNames() []string
}

```

### Authorizer

#### AlwaysAllow & AlwaysDeny

首先是AlwayAllowAuthorizer和AlwayDenyAuthorizer，这两个Authorizer主要是做测试用，实现的也非常简单。
```go
// alwaysAllowAuthorizer is an implementation of authorizer.Attributes// which always says yes to an authorization request.  
// It is useful in tests and when using kubernetes in an open manner.  
type alwaysAllowAuthorizer struct{}  
  
func (alwaysAllowAuthorizer) Authorize(a authorizer.Attributes) (authorized authorizer.Decision, reason string, err error) {  
   return authorizer.DecisionAllow, "", nil  
}  
  
func (alwaysAllowAuthorizer) RulesFor(user user.Info, namespace string) ([]authorizer.ResourceRuleInfo, []authorizer.NonResourceRuleInfo, bool, error) {  
   return []authorizer.ResourceRuleInfo{  
         &authorizer.DefaultResourceRuleInfo{  
            Verbs:     []string{"*"},  
            APIGroups: []string{"*"},  
            Resources: []string{"*"},  
         },      }, []authorizer.NonResourceRuleInfo{  
         &authorizer.DefaultNonResourceRuleInfo{  
            Verbs:           []string{"*"},  
            NonResourceURLs: []string{"*"},  
         },      }, false, nil  
}
```
这里可以看到，AlwaysAllow对任意的Request，都允许，对任意的资源都允许任意的动词。

#### ABAC authorizer

ABAC authorizer是基于属性的访问控制，定义了访问控制的规范，通过特定的策略文件，指定某个用户可以对某个资源执行的操作，例如下面的这个规则，制定了用户Deck可以对所有资源做任何操作。
```json
{"apiVersion": "abac.authorization.kubernetes.io/v1beta1", "kind": "Policy", "spec": {"user": "Deck", "namespace": "*", "resource": "*", "apiGroup": "*"}}
```

ABAC authorizer 的实现位于`pkg/auth/authorizer/abac/abac.go` ，首先读取策略文件，生成一组`abac.Policy`对象
```go
// PolicyList is simply a slice of Policy structs.
type PolicyList []*abac.Policy
```

鉴权部分的实现，就是比对Request所涉及的用户对资源的动词是否包含于策略中
```go
func matches(p abac.Policy, a authorizer.Attributes) bool {
	if subjectMatches(p, a.GetUser()) {
		if verbMatches(p, a) {
			// Resource and non-resource requests are mutually exclusive, at most one will match a policy
			if resourceMatches(p, a) {
				return true
			}
			if nonResourceMatches(p, a) {
				return true
			}
		}
	}
	return false
}
```

#### RBAC Authorizer

基于角色的访问控制是一种使用的最广泛的鉴权模型，在RBAC中，将权限用角色进行了封装。每个角色(Role)拥有不同的权限，每个用户可以绑定一个和多个角色，通过角色的绑定就可以为用户添加相应的权限。在K8s中，可以用`UserAccount` 和 `ServiceAccount` 来表示一个用户，可以创建出不同的`Role`和`ClusterRole`，每个`Role` 指定一组资源和可以对资源进行操作的动词，通过创建`RoleBinding` 和`ClusterRoleBinding`对象，就可以进行角色和用户的绑定。这种方式可以有效简化权限的管理。

![](img/Pastedimage20221102203705.png)


RBAC的实现位于`plugin/pkg/auth/authorizer/rbac/rbac.go` 

```go
// plugin/pkg/auth/authorizer/rbac/rbac.go
func (r *RBACAuthorizer) Authorize(ctx context.Context, requestAttributes authorizer.Attributes) (authorizer.Decision, string, error) {
    ruleCheckingVisitor := &authorizingVisitor{requestAttributes: requestAttributes}
    // ruleCheckingVisitor.visit -> RulesAllow -> 各种 match 函数验证
	r.authorizationRuleResolver.VisitRulesFor(requestAttributes.GetUser(), requestAttributes.GetNamespace(), ruleCheckingVisitor.visit)
	if ruleCheckingVisitor.allowed {
		return authorizer.DecisionAllow, ruleCheckingVisitor.reason, nil
    }
    ...
	return authorizer.DecisionNoOpinion, reason, nil
}
```

K8s的默认角色`Cluster-Admin` 拥有所有资源的最高权限
```go
// plugin/pkg/auth/authorizer/rbac/bootstrappolicy/policy.go
{
    // a "root" role which can do absolutely anything
    ObjectMeta: metav1.ObjectMeta{Name: "cluster-admin"},
    Rules: []rbacv1.PolicyRule{
        rbacv1helpers.NewRule("*").Groups("*").Resources("*").RuleOrDie(),
        rbacv1helpers.NewRule("*").URLs("*").RuleOrDie(),
    },
},
```
此外，K8s还内置了一些角色，比如"system:basic-user", "system:public-info-viewer"等。

### 其他

Api Server 针对Kubelet，提供了Node Rules，kubelet使用角色`system:node`，具有如下权限:
读:
- services
- endpoints
- nodes
- pods
- secrets,configmaps,pvc以及绑定到kubelet对应节点的pod所使用的pv
写:
- 节点和节点状态(只有自身所在的节点)
- Pod和Pod状态(只有运行在自己所在节点上的Pod)


## Admission

![](img/k8s-api-request-lifecycle1.png)

当经过验证和鉴权后，还需要经过访问控制。访问控制一般用于
- 更细粒度的鉴权，比如指定kubelet可以修改Node，但是只能修改自己运行的Node；用于禁止用户修改某些敏感字段，比如修改Pod的环境变量，修改allowPrivilege等。
- 修改某些字段，提供默认值，比如提供ImagePullPolicy，提供ServiceAccount等。
