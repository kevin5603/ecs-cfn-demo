import boto3

# Initialize clients
ecs_client = boto3.client('ecs')
cloudwatch_client = boto3.client('cloudwatch')

# role policy require
def stop_task(cluster_name, task_id):
    try:
        response = ecs_client.stop_task(
            cluster=cluster_name,
            task=task_id,
            reason='Stopped by Lambda function'
        )
        print(f"Successfully stopped task: {task_id}")
        return response
    except Exception as e:
        print(f"Error stopping task: {e}")
        return None


def get_task_id(event):
    alarm_arn = event.get('alarmArn', '')
    if not alarm_arn:
        print("alarmArn not found in event")
        return None

    task_id = alarm_arn.split(':')[-1].split('-')[-2]
    print(f"Extracted task id: {task_id}")
    return task_id


def get_cluster_name(event):
    metrics = event.get('alarmData', {}).get('configuration', {}).get('metrics', [])
    for metric in metrics:
        metric_stat = metric.get('metricStat', {})
        namespace = metric_stat.get('metric', {}).get('namespace', None)
        if namespace:
            print(f"Extracted cluster name: {namespace}")
            return namespace
    print("Cluster name not found in event")
    return None


def get_running_task_count(cluster_name):
    try:
        response = ecs_client.list_tasks(
            cluster=cluster_name,
            desiredStatus='RUNNING'
        )
        running_tasks = response['taskArns']
        print(f"Running tasks count: {len(running_tasks)}")
        return len(running_tasks)
    except Exception as e:
        print(f"Error listing running tasks: {e}")
        return 0


def lambda_handler(event, context):
    print('=== Start closing unhealthy task ===')

    task_id = get_task_id(event)
    cluster_name = get_cluster_name(event)

    if task_id and cluster_name:
        running_task_count = get_running_task_count(cluster_name)
        if running_task_count > 1:
            # TODO - call heap dump API
            stop_task(cluster_name, task_id)
        else:
            print('Not enough running tasks to stop one')
    else:
        if not task_id:
            print('TaskId not found')
        if not cluster_name:
            print('Cluster name not found')

    print('=== END ===')
    return None
