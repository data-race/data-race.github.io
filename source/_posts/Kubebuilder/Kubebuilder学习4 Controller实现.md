---
title: Kubebuilder学习4 Controller实现
tags:
  - kubebuilder
categories:
  - Kubebuilder
date: 2023-07-17 20:17:27
---
#kubebuilder 

Controller是K8s的核心，也是所有Operator的核心。Controller的任务是对于任意给定的对象，对象的期望状态必须和观测到的状态是一致的，每一个Controller关注一个Kind，也就是负责一种类型的所有对象。我们将这个过程叫做Reconcile。

在Controller中，Reconcile的过程由Reconciler的方法来完成，这也是我们需要实现的主要部分。

``` go
type ApiExampleReconciler struct {
	client.Client
	Log    logr.Logger
	Scheme *runtime.Scheme
}
```

Reconciler有一些成员，其中Log用于输出controller进行Reconcile的过程中的日志，client和集群进行交互，Scheme记录我们的资源类型的结构信息。

在Reconcile中，我们需要做以下的事情：
1. Load我们需要进行Reconcile的Cronjob对象
2. List由这个对象创建的所有子任务，并更新它们的状态
3. 根据HistoryLimit，删除多余的历史任务
4. 查看Cronjob是否被推迟了
5. 获取下一次进行调度的时间
6. 如果需要进行Schedule，并且并发规则允许切没有超过DeadLine，那么创建新任务



## Load the CronJob by name
``` go
func (r *ApiExampleReconciler) Reconcile(req ctrl.Request) (ctrl.Result, error)
{...}
```
首先我们看Reconcile函数的定义，参数是一个ctrl.Request	，这个类型只记录我们需要编排的对象的Name和Namespace。
因此，获取我们的CronJob只需要通过req参数就可以：
``` go
ctx := context.Background()
logger := r.Log.WithValues("apiexample", req.NamespacedName)

// 1 Load the CronJob By name: 这一步是根据 
// Reconcile的参数，来fetch具体的对象
var cronJob myappv1alpha1.ApiExample
if err := r.Get(ctx, req.NamespacedName, &cronJob); err != nil {
	logger.Error(err, "unable to fetch object")
	return ctrl.Result{}, client.IgnoreNotFound(err)
}
```

> Reconciler is a function provided to a Controller that may be called at anytime with the Name and Namespace of an object.When called, the Reconciler will ensure that the state of the system matches what is specified in the object at the time the Reconciler is called. Example: Reconciler invoked for a ReplicaSet object.  The ReplicaSet specifies 5 replicas but only 3 Pods exist in the system.  The Reconciler creates 2 more Pods and sets their OwnerReference to point at the ReplicaSet with controller=true.

Reconcile并不会一直被触发，当我们返回一个空的ctrl.Result时，意味着这次Reconcile成功了，那么直到出现一些变化，否则Reconcile不会再编排这个reconcile成功的对象。变化的捕捉我猜测是通过ownerReference来实现的。
## List all active jobs,
这一步获取所有由该CronJob创建的子任务：
``` go
var childJobs corev1.PodList
if err := r.List(ctx, &childJobs, client.InNamespace(req.Namespace), client.MatchingFields{jobOwnerKey: req.Name}); err != nil {
	logger.Error(err, "unable to list child jobs")
	return ctrl.Result{}, err
}
```
这里在List的时候使用了索引jobOwnerKey来过滤，索引的添加在SetUpWithManager函数中：
``` go
func (r *ApiExampleReconciler) SetupWithManager(mgr ctrl.Manager) error {
	if r.Clock == nil {
		r.Clock = realClock{}
	}
	if err := mgr.GetFieldIndexer().IndexField(&corev1.Pod{}, jobOwnerKey, func(rawObject runtime.Object) []string {
		job := rawObject.(*corev1.Pod)
		owner := metav1.GetControllerOf(job)
		if owner == nil {
			return nil
		}

		if owner.APIVersion != apiGVStr || owner.Kind != "ApiExample" {
			return nil
		}
		return []string{owner.Name}
	}); err != nil {
		return err
	}

	return ctrl.NewControllerManagedBy(mgr).
		For(&myappv1alpha1.ApiExample{}).
		Owns(&corev1.Pod{}).
		Complete(r)
}
```
这里应该也可以使用更简单的Label来进行过滤，因为ListOption也允许使用LabelSelector来过滤。
![](img/00C78CC4-CC7D-41FE-BCEC-58EAC49DE1FA.png
)

## 更新状态
我们已经获取了CronJob创建的所有子任务，下一步就是更新CronJob的状态了，首先将这些子任务按照完成情况分类，然后将最新的子任务调度时间做为CronJob的Status中的LastScheduleTime，并且更新Active的任务队列：
``` go
// 3 classify child jobs by status
var activeJobs []*corev1.Pod
var successfulJobs []*corev1.Pod
var failedJobs []*corev1.Pod
var mostRecentTime *time.Time // find the last run so we can update the status

// if a pod is succeeded of failed, we consider it marked as finished
isJobFinished := func(job *corev1.Pod) (bool, corev1.PodPhase) {
	if job.Status.Phase == corev1.PodSucceeded || job.Status.Phase == corev1.PodFailed {
		return true, job.Status.Phase
	}
	return false, ""
}

getScheduledTimeForJob := func(job *corev1.Pod) (*time.Time, error) {
	timeRaw := job.Annotations[scheduledTimeAnnotation]
	if len(timeRaw) == 0 {
		return nil, nil
	}

	timeParsed, err := time.Parse(time.RFC3339, timeRaw)
	if err != nil {
		return nil, err
	}
	return &timeParsed, nil
}

for _, job := range childJobs.Items {
	_, finishedType := isJobFinished(&job)
	switch finishedType {
	case "": // ongoing
		activeJobs = append(activeJobs, &job)
	case corev1.PodSucceeded:
		successfulJobs = append(successfulJobs, &job)
	case corev1.PodFailed:
		failedJobs = append(failedJobs, &job)
	}

	scheduledTimeForJob, err := getScheduledTimeForJob(&job)
	if err != nil {
		logger.Error(err, "unable to parse scheduled time for job:", &job)
		continue
	}

	if scheduledTimeForJob != nil {
		if mostRecentTime == nil {
			mostRecentTime = scheduledTimeForJob
		} else if mostRecentTime.Before(*scheduledTimeForJob) {
			mostRecentTime = scheduledTimeForJob
		}
	}
}

if mostRecentTime != nil {
	cronJob.Status.LastScheduleTime = &metav1.Time{Time: *mostRecentTime}
} else {
	cronJob.Status.LastScheduleTime = nil
}

cronJob.Status.Active = nil

for _, activeJob := range activeJobs {
	jobRef, err := ref.GetReference(r.Scheme, activeJob)
	if err != nil {
		logger.Error(err, "unable to make reference to active job", "job", activeJob)
		continue
	}
	cronJob.Status.Active = append(cronJob.Status.Active, *jobRef)
}

logger.V(1).Info("job count", "active jobs", len(activeJobs), "successful jobs", len(successfulJobs), "failed jobs", len(failedJobs))

if err := r.Update(ctx, &cronJob); err != nil {
	logger.Error(err, "Unable to update CronJob status")
	return ctrl.Result{}, err
}


```

## 清理历史任务
根据CronJob.Spec中的History Limit，我们清理历史任务：
``` go
// 4 Clean up old jobs according to history limit
if cronJob.Spec.FailedJobHistoryLimit != nil {
	sort.Slice(failedJobs, func(i, j int) bool {
		if failedJobs[i].Status.StartTime == nil {
			return failedJobs[j].Status.StartTime != nil
		}
		return failedJobs[i].Status.StartTime.Before(failedJobs[j].Status.StartTime)
	})

	for i, job := range failedJobs {
		if int32(i) >= int32(len(failedJobs))-*cronJob.Spec.FailedJobHistoryLimit {
			break
		}
		if err := r.Delete(ctx, job, client.PropagationPolicy(metav1.DeletePropagationBackground)); client.IgnoreNotFound(err) != nil {
			logger.Error(err, "Unable to delete old failed job", "job", job)
		} else {
			logger.V(0).Info("delete old failed job", "job", job)
		}
	}
}

if cronJob.Spec.SuccessfulJobHistoryLimit != nil {
	sort.Slice(successfulJobs, func(i, j int) bool {
		if successfulJobs[i].Status.StartTime == nil {
			return successfulJobs[j].Status.StartTime != nil
		}
		return successfulJobs[i].Status.StartTime.Before(successfulJobs[j].Status.StartTime)
	})

	for i, job := range successfulJobs {
		if int32(i) >= int32(len(successfulJobs))-*cronJob.Spec.SuccessfulJobHistoryLimit {
			break
		}
		if err := r.Delete(ctx, job, client.PropagationPolicy(metav1.DeletePropagationBackground)); client.IgnoreNotFound(err) != nil {
			logger.Error(err, "Unable to delete old successful job", "job", job)
		} else {
			logger.V(0).Info("delete old successful job", "job", job)
		}
	}
}

```


## 检测是否被挂起
``` go
if cronJob.Spec.Suspend != nil && *cronJob.Spec.Suspend {
	logger.V(1).Info("cronjob suspended, skipping")
	return ctrl.Result{}, nil
}
```


## 获取下一次Schedule时间
``` go
getNextSchedule := func(cronJob *myappv1alpha1.ApiExample, now time.Time) (lastMissed time.Time, next time.Time, err error) {
	sched, err := cron.ParseStandard(cronJob.Spec.Schedule)
	if err != nil {
		return time.Time{}, time.Time{}, fmt.Errorf("Unparseable schedule: %q: %v", cronJob.Spec.Schedule, err)
	}

	var earliestTime time.Time
	if cronJob.Status.LastScheduleTime != nil {
		earliestTime = cronJob.Status.LastScheduleTime.Time
	} else {
		earliestTime = cronJob.ObjectMeta.CreationTimestamp.Time
	}
	if cronJob.Spec.StartingDeadlineSeconds != nil {
		schedulingDeadline := now.Add(-time.Second * time.Duration(*cronJob.Spec.StartingDeadlineSeconds))

		if schedulingDeadline.After(earliestTime) {
			earliestTime = schedulingDeadline
		}
	}

	if earliestTime.After(now) {
		return time.Time{}, sched.Next(now), nil
	}
	starts := 0
	for t := sched.Next(earliestTime); !t.After(now); t = sched.Next(t) {
		lastMissed = t
		starts++
		if starts > 100 {
			return time.Time{}, time.Time{}, fmt.Errorf("Too many missed start times(>100)")
		}
	}
	return lastMissed, sched.Next(now), nil
}

// 其中，missedRun是上一次因为各种原因而错过调度的时间
// nextRun是将要被调度的时间
missedRun, nextRun, err := getNextSchedule(&cronJob, r.Now())
if err != nil {
	logger.Error(err, "unable to figure out Cronjob schedule")
	return ctrl.Result{}, nil
}

scheduleResult := ctrl.Result{
	RequeueAfter: nextRun.Sub(r.Now()),
}
logger = logger.WithValues("now", r.Now(), "next run", nextRun)

```

## 根据情况决定是否要创建子任务
``` go
// 7 Run a new job if it's on schedule, not past the deadline and not blocked by our concurrency policy
if missedRun.IsZero() {
	logger.V(1).Info("no upcoming scheduled times, sleeping until next")
	return scheduleResult, nil
}

logger = logger.WithValues("current run", missedRun)
tooLate := false

if cronJob.Spec.StartingDeadlineSeconds != nil {
	tooLate = missedRun.Add(time.Duration(*cronJob.Spec.StartingDeadlineSeconds) * time.Second).Before(r.Now())
}
if tooLate {
	logger.V(1).Info("missed starting deadline for last run, sleeping till next")
	return scheduleResult, nil
}

if cronJob.Spec.ConcurrencyPolicy == myappv1alpha1.ForbidConcurrent && len(activeJobs) > 0 {
	logger.V(1).Info("concurrency policy blocks concurrent runs, skipping", "num active", len(activeJobs))
	return scheduleResult, nil
}

if cronJob.Spec.ConcurrencyPolicy == myappv1alpha1.ReplaceConcurrent {
	for _, activeJob := range activeJobs {
		if err := r.Delete(ctx, activeJob, client.PropagationPolicy(metav1.DeletePropagationBackground)); client.IgnoreNotFound(err) != nil {
			logger.Error(err, "unable to delete active job", "job", activeJob)
			return ctrl.Result{}, err
		}
	}
}

// 8 actually create the job pod 
job, err := generateJobPod(&cronJob, missedRun, r.Scheme)
if err != nil {
	logger.Error(err, "Unable to construct job from template")
	return scheduleResult, nil
}

if err := r.Create(ctx, job); err != nil {
	logger.Error(err, "unable to create child job", job)
	return ctrl.Result{}, err
}

logger.V(1).Info("create job for Cronjob run", "job", job)

return scheduleResult, nil

```

我们首先根据missedRun来确定是否有需要进行调度的，如果没有，则直接返回。否则看missedRun到now到这段时间是否超过了Deadline，如果超过了，那么只好等待下一次，如果没超过，再根据concurrencyPolicy来进行判断。

如果不允许并行，那么只好等下一次。
如果是使用替代规则，那么强行结束当前active等任务。

最后，我们创建新任务。
``` go
func generateJobPod(cronJob *myappv1alpha1.ApiExample, scheduleTime time.Time, scheme *runtime.Scheme) (*corev1.Pod, error) {
	name := fmt.Sprintf("%s-%d", cronJob.Name, scheduleTime.Unix())
	job := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:        name,
			Namespace:   cronJob.Namespace,
			Labels:      make(map[string]string),
			Annotations: make(map[string]string),
		},
		Spec: *cronJob.Spec.JobTemplate.Spec.DeepCopy(),
	}

	for k, v := range cronJob.Spec.JobTemplate.Annotations {
		job.Annotations[k] = v
	}
	for k, v := range cronJob.Spec.JobTemplate.Labels {
		job.Labels[k] = v
	}

	job.Annotations[scheduledTimeAnnotation] = scheduleTime.Format(time.RFC3339)

	if err := ctrl.SetControllerReference(cronJob, job, scheme); err != nil {
		return nil, err
	}
	return job, nil
}
```

注意，在新任务创建时，我们调用了ctrl.SetControllerReference来设置job的owner，这样才能在设置indexfield的时候根据owner设置indexfield，从而在List的时候根据indexfield迅速找到所有子任务。
至此，Controller已经完成了。