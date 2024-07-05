import boto3
import logging

# Initialize clients
ecs_client = boto3.client('ecs')
cloudwatch_client = boto3.client('cloudwatch')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def stop_task(cluster_name, task_id):
    """Stop a specific ECS task."""
    try:
        response = ecs_client.stop_task(
            cluster=cluster_name,
            task=task_id,
            reason='Stopped by Lambda function'
        )
        print(f"Successfully stopped task: {task_id}")
        return response
    except Exception as e:
        logger.error(f"Error stopping task: {e}")
        return None

def get_task_id(event):
    """Extract task ID from CloudWatch alarm ARN."""
    alarm_arn = event.get('alarmArn', '')
    if not alarm_arn:
        logger.error("alarmArn not found in event")
        return None

    try:
        task_id = alarm_arn.split(':')[-1].split('-')[-2]
        print(f"Extracted task id: {task_id}")
        return task_id
    except IndexError as e:
        logger.error(f"Error extracting task ID: {e}")
        return None

def get_cluster_name(event):
    """Extract ECS cluster name from CloudWatch alarm data."""
    metrics = event.get('alarmData', {}).get('configuration', {}).get('metrics', [])
    for metric in metrics:
        namespace = metric.get('metricStat', {}).get('metric', {}).get('namespace', None)
        if namespace:
            print(f"Extracted cluster name: {namespace}")
            return namespace
    logger.error("Cluster name not found in event")
    return None

def get_service_name(event):
    """Extract service name from CloudWatch alarm ARN."""
    alarm_arn = event.get('alarmArn', '')
    try:
        ecs_demo_service = '-'.join(alarm_arn.split(':')[-1].split('-')[3:6])
        print(f"Extracted service name: {ecs_demo_service}")
        return ecs_demo_service
    except IndexError as e:
        logger.error(f"Error extracting service name: {e}")
        return None

def get_running_task_count(cluster_name, service_name):
    """Get the count of running tasks for a given service."""
    try:
        response = ecs_client.list_tasks(
            cluster=cluster_name,
            serviceName=service_name,
            desiredStatus='RUNNING'
        )
        running_tasks = response['taskArns']
        print(f"Running tasks count: {len(running_tasks)}")
        return len(running_tasks)
    except Exception as e:
        logger.error(f"Error listing running tasks: {e}")
        return 0

def lambda_handler(event, context):
    """AWS Lambda handler to close unhealthy ECS tasks."""
    print('=== Start closing unhealthy task ===')

    task_id = get_task_id(event)
    cluster_name = get_cluster_name(event)
    service_name = get_service_name(event)

    if task_id and cluster_name and service_name:
        running_task_count = get_running_task_count(cluster_name, service_name)
        if running_task_count > 1:
            stop_task(cluster_name, task_id)
        else:
            print('Not enough running tasks to stop one')

    print('=== END ===')
    return None