# Kubernetes汇总

kubernetes的API对象

Namespace
Pod
ReplicaSet
Deployment
Health Check
Service，Endpoint,EndpointSlices   ***实现同一labels下的多个pod流量负载均衡
Labels    	标签，服务间选择访问的重要依据
Ingress   	K8S流量入口
DaemonSet  用来发布守护应用，例如我们部署的CNI插件
HPA               自动水平伸缩
Volume         存储卷
Pv，pvc StorageClass   持久化存储，持久化存储生命，动态存储PV
StatefulSet    用来发布有状态应用
Job，CronJob  一次性任务及定时任务
Configmap,sercret      服务配置以及服务加密配置
Kube-proxy  提供service服务流量转发的功能支持，不需要实际操作
RBAC，serviceAccount，role,rolebindings,clusterrole,clusterrolebindings  基于角色访问控制
Events	k8s事件流，可以用来监控相关事件，也不需要实际操作



下载官方kubectl镜像，通过配置秘钥和访问IP等信息，使得该镜像可以访问指定的master集群，并可以在集群外部环境执行kubectl命令
，通过deployment部署所需pod



### 无状态服务   deployment

记不清楚的命令可以在基础命令后加上 -help 查看详细说明
老版本：1.17  1.18
```shell
kubectl create service clusterip nginx --tcp=80:80 --dry-run=true -o yaml
```

新版本：
1.24及以后
```shell
kubectl create service clusterip nginx --tcp=80:80 --dry-run=client -o yaml
```



这条命令就是上面创建deployment的命令，

我们在后面加上`--dry-run -o yaml`,--dry-run代表这条命令不会实际在K8s执行，
-o yaml是会将试运行结果以yaml的格式打印出来，这样我们就能轻松获得yaml配置了

```shell
kubectl create deployment nginx --image=nginx --dry-run -o yaml  

kubectl get pod -label/l app=$label_name
```



一定要记得，在部署k8s CRI的时候，要在后边加上 --record 参数的命令,k8s事件流才会有详细的记录，这就是为什么在生产/测试中操作一定得加上的原因了

升级nginx的版本

```shell
kubectl set image deployments/nginx nginx=nginx:1.21.6 --record
```

这里假设是我们在发版服务的新版本，结果线上反馈版本有问题，需要马上回滚，看看在K8s上怎么操作吧

首先通过命令查看当前历史版本情况，只有接了`--record`参数的命令操作才会有详细的记录，这就是为什么在生产中操作一定得加上的原因了

```shell
kubectl rollout history deployment nginx 

deployment.apps/nginx 
REVISION  CHANGE-CAUSE
1         <none>
2         kubectl set image deployment/nginx nginx=docker.io/library/nginx:1.25.1 --record=true
3         kubectl set image deployments/nginx nginx=nginx:1.21.6 --record=true
```

根据历史发布版本前面的阿拉伯数字序号来选择回滚版本，这里我们回到上个版本号，也就是选择2 ，执行命令如下：

```shell
kubectl rollout undo deployment nginx --to-revision=2

deployment.apps/nginx rolled back
```

等一会pod更新完成后，看下结果已经回滚完成了，怎么样，在K8s操作就是这么简单：

```
# curl ${nginx_svc}/1                                
<html>
<head><title>404 Not Found</title></head>
<body bgcolor="white">
<center><h1>404 Not Found</h1></center>
<hr><center>nginx/1.25.1</center>
</body>
</html>
```

kubectl -n $namespace apply -f $deployment_name+.yaml
需要去看下每刻的ingress-nginx yaml文件，主要参考下
kind:Ingress下  annotations的具体配置
看下spec是怎么写的



### 服务健康检测

Liveness   Readiness







### Service Endpoint  Endpoint  Slices

另一种创建service的方法

```shell
kubectl expose deployment nginx --port=80 --target-port=80 --dry-run=client -o yaml
```

想让外部访问到，需要将svc(service) 类型修改为 NodePort
一般云平台环境，是通过Ingress-nginx暴露服务端口

测试不同namespace的pod互相访问，引申出一个在中汽研的k8s环境下的问题
是不是gitlab-runner 的 dind ，就是因为在集群里部署的时候，k8s版本过低，网络通讯原因导致了pod无法访问到指定的harbor，然后报错

生产环境Service调优
将对外策略从Cluester调整为Local，避免一层SNAT转换，减少网络开销。
个人见解，对于高可用服务来说，可以不做调整，如果是单点服务，可以这么操作。
当然目前还对服务内部方位 Service_Name 方式不清楚，这个见解待定
优化后定点访问，避免一定的网络资源浪费
通过给svc设置指定的nodeSelector  等于设置亲和度

目前在1.17 想在同一SVC下配置多个port转发，只能先用命令配置一个端口转发，
然后kubectl edit svc $svc_name 调配，在spec项加入，以name进行区分，否则会报错
导出yaml文件就在命令后加入 -o yaml > $name.yaml



```yaml
apiVersion: v1
kind: Service
metadata:
  creationTimestamp: "2023-12-03T13:55:45Z"
  labels:
    app: nginx
  name: nginx
  namespace: default
  resourceVersion: "46268160"
  selfLink: /api/v1/namespaces/default/services/nginx
  uid: 7bd4b6a2-2e07-480c-bcc1-854a85979b18
spec:
  clusterIP: 10.101.146.218
  ports:
  - port: 80
    protocol: TCP
    targetPort: 80
    name: web-nginx
  - port: 8081
    protocol: TCP
    targetPort: 8081
    name: test-nginx
  selector:
    app: nginx
  sessionAffinity: None
  type: ClusterIP
status:
  loadBalancer: {}
```



### 资源身份标签 Labels







### Calico网络流量剖析

ipip	协议号 4
icmp      协议号 1

bgp  局域网网络协议   只能运行在数据链路层 （Internet 2层）
ipip 协议  支持  数据链路层 和 网络层
通常我们用的云平台vpc网络，都是I3 层的，只知道对端的IP，不知道其他MAC信息





### helm包管理

基于kubeeasz项目

```shell
# 做下软链接到bin目录
# ln -svf /etc/kubeasz/bin/helm /usr/bin/

# 国内安装源
# 添加国内适合的helm安装源
helm repo add kaiyuanshe http://mirror.kaiyuanshe.cn/kubernetes/charts
helm repo add azure http://mirror.azure.cn/kubernetes/charts
helm repo ls
# 更新下安装源
helm repo update

# 我们这里以安装mysql为例
helm search repo mysql

# 先来模拟安装一下，看看会显示什么
helm install --namespace kube-system  bogemysql ./mysql-1.6.9.tgz --dry-run --debug

install.go:200: [debug] Original chart version: ""
install.go:217: [debug] CHART PATH: /root/.cache/helm/repository/mysql-1.6.9.tgz

***** 引申出来一个问题，gitlab/github 提交代码错误操作，导致版本混乱的处理方法
简单处理方法是由组长统一审批管理，提交代码
方法论：给开发贯彻提交前先拉取的原则，如果不遵守，如何及时发现？  如果发现不及时如何处理

```



### netshoot k8s网络故障排查

https://github.com/nicolaka/netshoot

https://githubfast.com/nicolaka/netshoot



### k8s排错debug，在pod内进行tcpdump流量抓包

```shell
kubectl create deployment nginx --image=nginx:1.21.6
kubectl expose deployment nginx --port=80 --target-port=80

kubectl -n default debug container-name -it --image=docker.io/nicolaka/netshoot --copy-to=nginx-debugger

# 如果为了模拟接入生产环境，可以手动给该debug 容器编写分配对应生产环境pod的label

kubectl label pod nginx-debugger app=nginx

```



### Ingress-Nginx 控制器:生产环境实战配置

```shell
resources 配置会影响到该pod的优先级，如果limits 和 requests越接近，优先级则越高
需要查询一下，还有没有其他影响pod优先级的操作或设置

# 给node节点添加/查看/去除  label标签
kubect label node $node_name ingrees-nginx=true
kubectl get node --show-labels
kubectl label node $node_name ingress-nginx-

#
kubectl taint nodes $node_name ingress-nginx="true":NoExecute
kubectl taint nodes $node_name ingress-nginx:NoExecute-

打上污点后，想在打了指定污点的node上部署pod，需要pod做一个容忍度(pod关于污点的亲合度问题)
      tolerations:
      - operator: Exists
#      tolerations:
#      - effect: NoExecute
#        key: boge/ingress-controller-ready
#        operator: Equal
#        value: "true"

# 这里我先自签一个https的证书

#1. 先生成私钥key
# openssl genrsa -out test.key 2048
Generating RSA private key, 2048 bit long modulus
..............................................................................................+++
.....+++
e is 65537 (0x10001)

#2.再基于key生成tls证书(注意：这里我用的*.test.com，这是生成泛域名的证书，后面所有新增加的三级域名都是可以用这个证书的)
# openssl req -new -x509 -key test.key -out test.csr -days 360 -subj /CN=*.test.com

# 看下创建结果
# ll
total 8
-rw-r--r-- 1 root root 1099 Nov 27 11:44 test.csr
-rw-r--r-- 1 root root 1679 Nov 27 11:43 test.key

```





### 解决K8S 中 Ingress-Nginx 控制器无法获取真实客户端IP的问题

```shell
网络知识延展: DCDN,WAF,高防线路
DCDN考虑流量带来的成本提升
WAF屏蔽随机URL访问
传统网络攻击  CC  DDOS(DCDN和WAF很难完全抵御)
高防线路则可以阻止大流量的 CC  DDOS攻击

      -->动态加速线路(DCDN)
CLIENT--> WAF               --->负载均衡--->Ingress-Nginx--->后端服务POD
      -->高防线路

前部的安全服务，把一些XFF(客户端的头部信息)信息传递过来。
直接获取的内容，为 remote addr，为安全服务的IP
需要在Ingress-Nginx上添加一个配置
# kubectl -n kube-system edit configmaps nginx-configuration

apiVersion: v1
data:
  ......
  compute-full-forwarded-for: "true"
  forwarded-for-header: "X-Forwarded-For"
  use-forwarded-headers: "true"

```



### 快速定位业务服务慢的问题：利用 Ingress-Nginx 和日志查询实现高效故障排查







### K8s HPA：自动水平伸缩Pod，实现弹性扩展和资源优化

HPA Horizontal Pod Autoscaling







### 深入理解K8s配置管理：ConfigMap和Secret的终极指南

```shell
Examples:
  # Create a new configmap named my-config based on folder bar
  kubectl create configmap my-config --from-file=path/to/bar

  # Create a new configmap named my-config with specified keys instead of file basenames on disk
  kubectl create configmap my-config --from-file=key1=/path/to/bar/file1.txt --from-file=key2=/path/to/bar/file2.txt

  # Create a new configmap named my-config with key1=config1 and key2=config2
  kubectl create configmap my-config --from-literal=key1=config1 --from-literal=key2=config2

  # Create a new configmap named my-config from the key=value pairs in the file
  kubectl create configmap my-config --from-file=path/to/bar

  # Create a new configmap named my-config from an env file
  kubectl create configmap my-config --from-env-file=path/to/bar.env
  
创建configmap，字符对应
# kubectl create configmap localconfig-env --from-literal=log_level_test=TEST --from-literal=log_level_produce=PRODUCE
创建configmap, 对应本地当前目录config文件生成
#kubectl create configmap localconfig-env --from-file=log_level_test=TEST.conf --from-file=log_level_produce=PRODUCE.conf --dry-run=true -o yaml

# kubectl create secret generic mysecret --from-literal=mysql-root-passwd='Test-123' --from-literal=redis-root-passwd='Test-123'




xxl-job是分布式任务调度系统，java写的，国人开源，用的大公司还不少
```





### K8s数据安全无忧——持久化存储详解一

```shell
K8S volume
pod的持久化存储
1. emptyDir
临时存储,POD内容器发生重启，不会造成emptyDir里内容丢失，但pod被重启，emptyDir内容会丢失。
empty和pod生命周期相同。

        volumeMounts:
          - name: html-files  # 注意这里的名称和上面nginx容器保持一样，这样才能相互进行访问  -- 同一POD下，多容器共享同一目录，通过挂载volume-name保持一致实现
            mountPath: "/html"  # 将数据挂载到当前这个容器的这个目录下
      volumes:
        - name: html-files   # 最后定义这个卷的名称也保持和上面一样
          emptyDir:          # 这就是使用emptyDir卷类型了
            medium: Memory   # 这里将文件写入内存中保存，这样速度会很快，配置为medium: "" 就是代表默认的使用本地磁盘空间来进行存储
            sizeLimit: 10Mi  # 因为内存比较珍贵，注意限制使用大小


挂载 volumeMounts
volumeMounts:
        - name: testconfig
          mountPath: "/etc/local_config_test.py"
          subPath: localconfig-test
        - name: testconfig
          mountPath: "/etc/local_config_produce.py"
          subPath: localconfig-produce
          readOnly: true
        - name: testsecret
          mountPath: "/etc/id_rsa"
          subPath: my_id_rsa
          readOnly: true
        - name: testsecret
          mountPath: "/etc/id_rsa.pub"
          subPath: my_id_rsa_pub
          readOnly: true

subPath  仅仅单独挂载指定的文件，不影响挂载目录文件等

      volumes:
      - name: testconfig   #对应到volumeMounts 下的name名称，必须保持一致
        configMap:
          name: localconfig-file
          defaultMode: 0660
      - name: testsecret
        secret:
          secretName: mysecret
          defaultMode: 0600


2. hostPath
只挂载在当前node的本地目录
应用于 DaemonSet 和 StatusSet
    volumeMounts:
    - mountPath: /host/driver
      name: flexvol-driver-host
......
  volumes:
......
  - hostPath:
      path: /usr/libexec/kubernetes/kubelet-plugins/volume/exec/nodeagent~uds   #宿主机的绝对路径
      type: DirectoryOrCreate  #目录不存在则创建
    name: flexvol-driver-host
```

### K8s数据安全无忧——持久化存储详解二

```shell
3. PersistenVolume(PV)  &&  PersistentVolumeClaim(PVC)
PVC关联对应PV进行消费


本地配置NFS
# 我们这里在10.0.1.201上安装（在生产中，大家要提供作好NFS-SERVER环境的规划）
# yum -y install nfs-utils
# ubuntu安装NFS服务端
# apt-get install nfs-kernel-server -y


# 创建NFS挂载目录
# mkdir /nfs_dir
# chown nobody.nogroup /nfs_dir

# 修改NFS-SERVER配置
# echo '/nfs_dir *(rw,sync,no_root_squash)' > /etc/exports

# 重启服务
# systemctl restart rpcbind.service
# systemctl restart nfs-kernel-server.service 
# systemctl restart nfs-utils.service 
# systemctl restart nfs-server.service 

# 增加NFS-SERVER开机自启动
# systemctl enable nfs-server.service 

------------------------------------------------------------
# cat pv1.yaml 
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv1
  labels:
    type: test-claim    # 这里建议打上一个独有的标签，方便在多个pv的时候方便提供pvc选择挂载
spec:
  capacity:
    storage: 1Gi     # <----------  1
  accessModes:
    - ReadWriteOnce     # <----------  2
  persistentVolumeReclaimPolicy: Recycle     # <----------  3
  storageClassName: nfs     # <----------  4
  nfs:
    path: /nfs_dir/pv1     # <----------  5
    server: 10.0.1.201
------------------------------------------------------------
1. capacity 指定 PV 的容量为 1G。

2. accessModes 指定访问模式为 ReadWriteOnce，支持的访问模式有：
   ReadWriteOnce – PV 能以 read-write 模式 mount 到单个节点。
   ReadOnlyMany – PV 能以 read-only 模式 mount 到多个节点。
   ReadWriteMany – PV 能以 read-write 模式 mount 到多个节点。

3. persistentVolumeReclaimPolicy 指定当 PV 的回收策略为 Recycle，支持的策略有：
   Retain – 需要管理员手工回收。
   Recycle – 清除 PV 中的数据，效果相当于执行 rm -rf /thevolume/*。
   Delete – 删除 Storage Provider 上的对应存储资源，例如 AWS EBS、GCE PD、Azure Disk、OpenStack Cinder Volume 等。

4. StorageClassName 指定 PV 的 class 为 nfs。相当于为 PV 设置了一个分类，PVC 可以指定 class 申请相应 class 的 PV。

5. 指定 PV 在 NFS 服务器上对应的目录，这里注意，我测试的时候，需要手动先创建好这个目录并授权好，不然后面挂载会提示目录不存在 mkdir /nfsdata/pv1 && chown -R nobody.nogroup /nfsdata 。

```





### 5.2k star 开源分布式存储服务Rancher-Longhorn在k8s上部署





### K8S下的有状态服务StatefulSet





### 在 K8s中部署Job和CronJob

```shell
*** job 和 cronjob 的优势是可以访问内部资源
普通服务器 有一个 cronsun服务，go语言开发的 crontab 的分布式版本

# 创建job的kubernetes help内容
# kubectl create job -h
# 创建job 查看生成的yaml文件
# kubectl create job test-job --image=busybox --dry-run -o yaml -- date


# 创建cronjob的kubernetes help内容
# kubectl create cronjob/cj -h
# 创建job 查看生成的yaml文件
# kubectl create cronjob test-job --image=busybox --dry-run -o yaml -- date

> kubectl create cronjob -h
Create a cronjob with the specified name.

Aliases:
cronjob, cj

Examples:
  # Create a cronjob
  kubectl create cronjob my-job --image=busybox
  
  # Create a cronjob with command
  kubectl create cronjob my-job --image=busybox -- date
  
  # Create a cronjob with schedule
  kubectl create cronjob test-job --image=busybox --schedule="*/1 * * * *"

Options:
      --allow-missing-template-keys=true: If true, ignore any errors in templates when a field or map key is missing in
the template. Only applies to golang and jsonpath output formats.
      --dry-run=false: If true, only print the object that would be sent, without sending it.
      --image='': Image name to run.
  -o, --output='': Output format. One of:
json|yaml|name|go-template|go-template-file|template|templatefile|jsonpath|jsonpath-file.
      --restart='': job's restart policy. supported values: OnFailure, Never
      --save-config=false: If true, the configuration of current object will be saved in its annotation. Otherwise, the
annotation will be unchanged. This flag is useful when you want to perform kubectl apply on this object in the future.
      --schedule='': A schedule in the Cron format the job should be run with.
      --template='': Template string or path to template file to use when -o=go-template, -o=go-template-file. The
template format is golang templates [http://golang.org/pkg/text/template/#pkg-overview].
      --validate=true: If true, use a schema to validate the input before sending it

Usage:
  kubectl create cronjob NAME --image=image --schedule='0/5 * * * ?' -- [COMMAND] [args...] [flags] [options]

Use "kubectl options" for a list of global command-line options (applies to all commands).

```



### K8s中的RBAC角色访问控制策略

```shell
Role-Based Access Control
RBAC可以细化管理k8s集群访问人员权限。
                  |--- Role        --- RoleBinding          仅在指定namespace中生效
ServiceAccount ---|
                  |--- ClusterRole --- ClusterRoleBinding   全局生效

# kubectl create serviceaccount --namespace kube-system tiller
# kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
# kubectl patch deploy --namespace kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'

应用经验主要集中在两个脚本内容的使用
```



### Kubectl插件应用



```
主要是通过shell命令编写一些脚本，以及命名方式为 kubectl-xxxx
并放置到系统的 $PATH  路径下，便于运维管理k8s集群
```



### K8s部署优化：利用亲和性、反亲和性、污点、容忍和节点选择器的威力









### 利用operator部署生产级别的Elasticserach集群和kibana

Kubernetes Operator 是一种用于扩展 Kubernetes 功能的软件。它的主要功能包括:

1. 自动化操作 - Operator 可以自动执行诸如部署、扩缩容、升级、备份等常见操作。用户不需要手动一个个 Pod 去执行这些任务。

2. 无状态应用管理 - Operator 很适合管理那些无状态的应用,比如数据库、缓存等。它通过控制器模式让应用始终处于预期的状态。

3. 减少重复工作 - Operator 让用户从重复的日常工作中解脱出来,这些工作可以交给 Operator 来自动完成。

4. 基于 CRD 扩展 - Operator 通过自定义资源定义(CRD)扩展 Kubernetes 的 API,并基于这些 CRD 来实现自定义控制循环。

5. 结合服务目录 - Operator 可以与服务目录(如 Service Catalog)集成,来启用基于权限的资源控制和分发。

   总的来说,Kubernetes Operator 的核心思想是通过程序化和自动化的方式来管理和扩展 Kubernetes 集群。它极大地简化了在 Kubernetes 上安装和运行复杂应用的过程。

Operator 的工作原理基于 Kubernetes 的控制器模式。它会不断地监测 Kubernetes 集群的状态,一旦发现自定义资源(CR)的实际状态与预期状态不符,Operator 就会执行相应的操作以使其达到预期状态。这种模式使得 Operator 可以实现自我修复和自动恢复的功能。

常见的 Kubernetes Operator 包括 Rook 提供存储解决方案的 Operator,Prometheus Operator 用于监控集群的 Operator,Istio Operator 用于服务网格的 Operator 等。这些 Operator 为 Kubernetes 生态带来了很大的便利。

```shell
# 部署eck operator
kubectl create -f https://download.elastic.co/downloads/eck/2.10.0/crds.yaml
kubectl apply -f https://download.elastic.co/downloads/eck/2.10.0/operator.yaml
kubectl -n elastic-system get pod
kubectl -n elastic-system logs -f statefulset.apps/elastic-operator
kubectl create ns es
```









# 2021年随笔



### Prometheus监控操作

```shell
*******
find ./ -type f | xargs grep 'image: ' | sort | uniq | awk '{print $3}'|grep ^[a-zA-Z]|grep -Evw 'error|kubeRbacProxy'|sort -rn|uniq
罗列 Prometheus && Grafana 所需的镜像
其中rancher/metrics-server-amd64  可以平替 gcr.io/google_containers/metrics-server-amd64
*******

通过加载镜像将Prometheus部署在master上，然后解决Prometheus无法监控到 kube-controller-manager 和 kube-scheduler 的问题

点击上方菜单栏Status --- Targets ，我们发现kube-controller-manager和kube-scheduler未发现

monitoring/kube-controller-manager/0 (0/0 up) 
monitoring/kube-scheduler/0 (0/0 up) 

# 获取下metrics指标看看
curl $master_ip:10251/metrics
curl $master_ip:10252/metrics
如果能获取到，则不需要调整systemd，如果不能获取，则需要调整kube-controller-manager.service 和 kube-scheduler.service  


然后因为K8s的这两上核心组件我们是以二进制形式部署的，为了能让K8s上的prometheus能发现，我们还需要来创建相应的service和endpoints来将其关联起来

注意：我们需要将endpoints里面的NODE IP换成我们实际情况的

apiVersion: v1
kind: Service
metadata:
  namespace: kube-system
  name: kube-controller-manager
  labels:
    k8s-app: kube-controller-manager
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - name: http-metrics
    port: 10252
    targetPort: 10252
    protocol: TCP

---
apiVersion: v1
kind: Endpoints
metadata:
  labels:
    k8s-app: kube-controller-manager
  name: kube-controller-manager
  namespace: kube-system
subsets:
- addresses:
  - ip: 10.0.1.201
  - ip: 10.0.1.202
  ports:
  - name: http-metrics
    port: 10252
    protocol: TCP

---

apiVersion: v1
kind: Service
metadata:
  namespace: kube-system
  name: kube-scheduler
  labels:
    k8s-app: kube-scheduler
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - name: http-metrics
    port: 10251
    targetPort: 10251
    protocol: TCP

---
apiVersion: v1
kind: Endpoints
metadata:
  labels:
    k8s-app: kube-scheduler
  name: kube-scheduler
  namespace: kube-system
subsets:
- addresses:
  - ip: 10.0.1.201
  - ip: 10.0.1.202
  ports:
  - name: http-metrics
    port: 10251
    protocol: TCP
将上面的yaml配置保存为repair-prometheus.yaml，然后创建它

kubectl apply -f repair-prometheus.yaml

创建完成后确认下

# kubectl -n kube-system get svc |egrep 'controller|scheduler'
kube-controller-manager   ClusterIP   None            <none>        10252/TCP                      58s
kube-scheduler            ClusterIP   None            <none>        10251/TCP                      58s

记得还要修改一个地方

# kubectl -n monitoring edit servicemonitors.monitoring.coreos.com kube-scheduler 
# 将下面两个地方的https换成http
    port: https-metrics
    scheme: https

# kubectl -n monitoring edit servicemonitors.monitoring.coreos.com kube-controller-manager
# 将下面两个地方的https换成http
    port: https-metrics
    scheme: https
```







### Prometheus监控操作 后续



```shell
通过一开始布置pod时，定义Prometheus监控端口，使Prometheus-Server可以收集信息




# kubectl label node xx.xx.xx.xx boge/ingress-controller-ready=true
# kubectl get node --show-labels
# kubectl label node xx.xx.xx.xx boge/ingress-controller-ready-


# 污点
# kubectl taint nodes xx.xx.xx.xx boge/ingress-controller-ready="true":NoExecute
# kubectl taint nodes xx.xx.xx.xx boge/ingress-controller-ready:NoExecute-

# 容忍
  tolerations:
  - operator: Exists
#   tolerations:
#   - effect: NoExecute
#     key: boge/ingress-controller-ready
#     operator: Equal
#     value: "true"

```























