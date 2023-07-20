---
title: Kubernetes Authentication
tags:
  - kubernetes
categories:
  - Kubernetes
date: 2023-07-17 20:17:26
---
#kubernetes

https://kubernetes.io/zh-cn/docs/reference/access-authn-authz/authentication/

## 前言
K8s中的API Server是一个非常重要的组件，它直接和etcd进行通信，所有对资源的增删改查的请求都需要发送到API Server。因此，API Server需要谨慎的对达到的请求进行权限的控制。API Server中存在3种权限控制机制，分别是：
- Authentication(认证)：针对请求进行认证，识别对方身份，确保请求方具有访问集群的权限。
- Authorization(授权): 确保请求方有访问相关资源的权限。
- Admission(准入)：对请求进行拦截，做验证(Validation)和修改(Mutation)。

这三种认证机制都可以通过webhook进行扩展，这也体现了K8s强大的扩展能力。在基础设施方面，可以通过CNI,CSI,CRI扩展网络，存储和容器运行时。可以通过Device Plugin添加新的设备。可以通过Operator添加新的CRD和控制器，可以通过Scheduler Extender的方式，扩展调度器的调度能力。
本文主要介绍这三种权限控制机制。
![](img/Pastedimage20221028141550.png
)
## Authentication 认证

在开启HTTPs服务后，所有的请求都需要经过认证。不管请求是来自集群中节点上正在运行的Kubelet，运行着的Controller，还是来自远程的某个租户，都需要经过身份认证，才能访问Api server的CRUD方法。
客户端对服务器的认证很简单，双方在TLS握手时，可以验证服务器的证书的有效性。但是服务器也要认证客户端，只有受认证的客户端才可以访问服务器的API。
kube-apiserver支持多种认证机制，并且支持同时开启多个认证功能。当客户端发起请求时，只要有一个认证器通过，就认为认证成功，api server支持很多认证方法，下面做简单的介绍。

### Api Server的 Authentication配置

### 接口
在Kubernetes的apiserver组建中，定义了有关Api Server 进行Authentication的代码，在路径`k8s.io/apiserver/pkg/authentication/authenticator/interfaces.go` 中，定义了一些authenticator有关的接口
```go
// Token checks a string value against a backing authentication store and
// returns a Response or an error if the token could not be checked.
type Token interface {  
   AuthenticateToken(ctx context.Context, token string) (*Response, bool, error)
     
}

// Request attempts to extract authentication information from a request and
// returns a Response or an error if the request could not be checked.
type Request interface {  
   AuthenticateRequest(req *http.Request) (*Response, bool, error)  
}

// Password checks a username and password against a backing authentication// store and returns a Response or an error if the password could not be// checked.  
type Password interface {  
   AuthenticatePassword(ctx context.Context, user, password string) (*Response, bool, error)  
}

```
这里定义了三个借口，分别对Token， Request和Password进行验证，并返回Response，Response的定义如下
```go
type Response struct {  
   // Audiences is the set of audiences the authenticator was able to validate   // the token against. If the authenticator is not audience aware, this field   // will be empty.   
   Audiences Audiences  
   // User is the UserInfo associated with the authentication context.   
   User user.Info  
}
```
Response中记录如果经过验证成功后，用户的相关信息。

对`Token`, `Password` 和`Response`三个接口的实现也很有意思，通过定义函数类型，并且让函数类型调用自己来实现接口。 以Token为例，定义TokenFunc类型，然后TokenFunc类型去实现Token接口，在`AuthenticateToken`方法中，调用自己，来完成验证过程。
```go
// TokenFunc is a function that implements the Token interface.
type TokenFunc func(ctx context.Context, token string) (*Response, bool, error)  
  
// AuthenticateToken implements authenticator.Token.  
func (f TokenFunc) AuthenticateToken(ctx context.Context, token string) (*Response, bool, error) {  
   return f(ctx, token)  
}
```

在Api Server的启动时，会通过读取配置来创建需要的authenticators，

### 实现

#### X509 Client Cert
X509 客户端证书认证，也被称为 TLS 双向认证，即为服务端和客户端互相验证证书的正确性。使用此认证方式，只要是 CA 签名过的证书都能通过认证。在kubernetes-apiserver中，通过`--client-ca-file` 参数启用此认证方式。在`/etc/kubernetes/manifests/kube-apiserver.yaml`中，可以看到
```yml
spec:
  containers:
  - command:
    - kube-apiserver
    - --advertise-address=210.28.132.169
    - --allow-privileged=true
    - --etcd-servers=https://127.0.0.1:2379
    - --insecure-port=0
    - --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
    ....
```

我理解这里指定可以被认证的客户端证书，那么持有此证书的客户端可以被服务器认证。
校验客户端证书的过程如下。
```go
// AuthenticateRequest authenticates the request using presented client certificates
func (a *Authenticator) AuthenticateRequest(req *http.Request) (*authenticator.Response, bool, error) {  
   if req.TLS == nil || len(req.TLS.PeerCertificates) == 0 {  
      return nil, false, nil  
   }  
  
   // Use intermediates, if provided  
   optsCopy := a.opts  
   if optsCopy.Intermediates == nil && len(req.TLS.PeerCertificates) > 1 {  
      optsCopy.Intermediates = x509.NewCertPool()  
      for _, intermediate := range req.TLS.PeerCertificates[1:] {  
         optsCopy.Intermediates.AddCert(intermediate)  
      }   
	}
	  
   remaining := req.TLS.PeerCertificates[0].NotAfter.Sub(time.Now())  
   clientCertificateExpirationHistogram.Observe(remaining.Seconds()) 
   // 校验证书，如果通过，可以解析User的信息 
   chains, err := req.TLS.PeerCertificates[0].Verify(optsCopy)  
   if err != nil {  
      return nil, false, err  
   }  
  
   var errlist []error  
   for _, chain := range chains {  
      user, ok, err := a.user.User(chain)  
      if err != nil {  
         errlist = append(errlist, err)  
         continue  
      }  
  
      if ok {  
         return user, ok, err  
      }  
   }   return nil, false, utilerrors.NewAggregate(errlist)  
}
```

#### Static Token Auth

在启动API server时，可以通过静态令牌文件传入一些静态的tokens，进行认证，令牌文件的格式为`.csv`，实例如下
```csv
token,user,uid,"group1,group2"
token,user,uid,"group2,group3"
```

在向Api Server发送请求时，设置token
```
Authorization: Bearer $TOKEN
```
认证实现也比较简单，只需要比较用户在header中的token是否存在就好。

#### Bootstrap Tokens
为了支持平滑地启动引导新的集群，Kubernetes 包含了一种动态管理的持有者令牌类型， 称作 **启动引导令牌（Bootstrap Token）**。 这些令牌以 Secret 的形式保存在 `kube-system` 名字空间中，可以被动态管理和创建。 控制器管理器包含的 `TokenCleaner` 控制器能够在启动引导令牌过期时将其删除。

Bootstrap Token主要用于新建集群以及在现有集群中添加新节点，该令牌通过特殊的Secret定义(`bootstrap.kubernetes.io/token`)，定义在`kube-system` 命名空间中，并且会被Api Server读取，当过期后会被自动清理。

```go
// plugin/pkg/auth/authenticator/token/bootstrap/bootstrap.go
func (t *TokenAuthenticator) AuthenticateToken(ctx context.Context, token string) (*authenticator.Response, bool, error) {
	// 1. 校验 token 格式
	tokenID, tokenSecret, err := bootstraptokenutil.ParseToken(token)
	if err != nil {
		return nil, false, nil
	}

	// 2. 拼接 secret name，获取 secret 对象
	secretName := bootstrapapi.BootstrapTokenSecretPrefix + tokenID
	secret, err := t.lister.Get(secretName)
	if err != nil {
		if errors.IsNotFound(err) {
			klog.V(3).Infof("No secret of name %s to match bootstrap bearer token", secretName)
			return nil, false, nil
		}
		return nil, false, err
	}

	// 3. 校验 secret 有效，不在删除中
	if secret.DeletionTimestamp != nil {
		tokenErrorf(secret, "is deleted and awaiting removal")
		return nil, false, nil
	}

	// 4. 校验 secret 类型必须是 bootstrap.kubernetes.io/token
	if string(secret.Type) != string(bootstrapapi.SecretTypeBootstrapToken) || secret.Data == nil {
		tokenErrorf(secret, "has invalid type, expected %s.", bootstrapapi.SecretTypeBootstrapToken)
		return nil, false, nil
	}

	// 5. 校验 token secret 有效
	ts := bootstrapsecretutil.GetData(secret, bootstrapapi.BootstrapTokenSecretKey)
	if subtle.ConstantTimeCompare([]byte(ts), []byte(tokenSecret)) != 1 {
		tokenErrorf(secret, "has invalid value for key %s, expected %s.", bootstrapapi.BootstrapTokenSecretKey, tokenSecret)
		return nil, false, nil
	}

	// 6. 校验 token id 有效
	id := bootstrapsecretutil.GetData(secret, bootstrapapi.BootstrapTokenIDKey)
	if id != tokenID {
		tokenErrorf(secret, "has invalid value for key %s, expected %s.", bootstrapapi.BootstrapTokenIDKey, tokenID)
		return nil, false, nil
	}

	// 7. 校验 token 是否过期
	if bootstrapsecretutil.HasExpired(secret, time.Now()) {
		// logging done in isSecretExpired method.
		return nil, false, nil
	}

	// 8. 校验 secret 对象的 data 字段中，key 为 usage-bootstrap-authentication，value 为 true
	if bootstrapsecretutil.GetData(secret, bootstrapapi.BootstrapTokenUsageAuthentication) != "true" {
		tokenErrorf(secret, "not marked %s=true.", bootstrapapi.BootstrapTokenUsageAuthentication)
		return nil, false, nil
	}

	// 9. 获取 secret.data[auth-extra-groups]，与 default group 组合
	groups, err := bootstrapsecretutil.GetGroups(secret)
	if err != nil {
		tokenErrorf(secret, "has invalid value for key %s: %v.", bootstrapapi.BootstrapTokenExtraGroupsKey, err)
		return nil, false, nil
	}

	return &authenticator.Response{
		User: &user.DefaultInfo{
			Name:   bootstrapapi.BootstrapUserPrefix + string(id),
			Groups: groups,
		},
	}, true, nil
}
```

#### Service Account Token
其他认证方式都是从 kubernetes 集群外部访问 kube-apiserver 组件，而 ServiceAccount 是从 Pod 内部访问，提供给 Pod 中的进程使用。自定义的Controller，Scheduler等，都通过这种方式使用Api server，ServiceAccount 包含了 3 个部分的内容：
- Namespace: pod所在的命名空间
- CA：kube-apiserver的公钥证书，pod内部用于验证服务端。
- Token: 由kube-apiserver用私钥签发的token，实用base64编码的一个Bearer Token。
他们都通过 mount 命令挂载到 Pod 的文件系统中，
- Namespace 存储在 /var/run/secrets/kubernetes.io/serviceaccount/namespace，经过 Base64 加密；
- CA 的存储路径 /var/run/secrets/kubernetes.io/serviceaccount/ca.crt；
- Token 存储在 /var/run/secrets/kubernetes.io/serviceaccount/token 文件中;

ServiceAccount 通常是 kube-apiserver 自动创建，并通过准入控制器关联到 Pod 中。如果需要让某些Pod可以对Api Server进行访问，那么通常是创建ServiceAccount，并且设置`.spec.serviceAccountName` 进行指定。

```go
// pkg/serviceaccount/jwt.go
func (j *jwtTokenAuthenticator) AuthenticateToken(ctx context.Context, tokenData string) (*authenticator.Response, bool, error) {
	// 1. 校验 token 格式正确
	if !j.hasCorrectIssuer(tokenData) {
		return nil, false, nil
	}

	// 2. 解析 JWT 对象
	tok, err := jwt.ParseSigned(tokenData)
	...

	public := &jwt.Claims{}
	private := j.validator.NewPrivateClaims()

	// TODO: Pick the key that has the same key ID as `tok`, if one exists.
	var (
		found   bool
		errlist []error
	)
	// 3. 使用--service-account-key-file 提供的密钥，反序列化 JWT
	for _, key := range j.keys {
		if err := tok.Claims(key, public, private); err != nil {
			errlist = append(errlist, err)
			continue
		}
		found = true
		break
	}

	...

	// 4. 验证 namespace 是否正确、serviceAccountName、serviceAccountID 是否存在，token 是否失效
	sa, err := j.validator.Validate(ctx, tokenData, public, private)
	if err != nil {
		return nil, false, err
	}

	return &authenticator.Response{
		User:      sa.UserInfo(),
		Audiences: auds,
	}, true, nil
}
```

#### 其他
还有一些更复杂的认证机制
- OpenID Connect Token
- Webhook Token
- Authentication Proxy
等，可以看官方的相关文档：
https://kubernetes.io/zh-cn/docs/reference/access-authn-authz/authentication/#bootstrap-tokens

