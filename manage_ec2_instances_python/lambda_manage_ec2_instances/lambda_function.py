import boto3
from botocore.exceptions import ClientError


def print_arguments(fn):  # experiment decorator like logger
    def wrapper(*args, **kwargs):
        print(args, kwargs)
        fn(*args, **kwargs)

    return wrapper


class ManageEnvironments:
    @print_arguments
    def __init__(self, role_arn: str, region: str, tag_name: str, tag_value: str, action: str) -> None:
        self.role_arn = role_arn
        self.region = region
        self.tag_name = tag_name
        self.tag_value = tag_value
        self.action = action

    @staticmethod
    def get_instance_name(instance) -> str:
        for tag in instance.tags:
            if tag['Key'] == 'Name':
                return tag['Value']

    @staticmethod
    def get_instances_by_tag(self, tag_name: str, tag_value: str, ec2: boto3.resource) -> list:
        instances = []
        for instance in ec2.instances.all():
            instance_obj = {}
            for tag in instance.tags:
                if tag['Key'] == tag_name and tag['Value'] == tag_value:
                    instance_obj.update({'Name': self.get_instance_name(instance), 'Instance': instance})
                    instances.append(instance_obj)
        return instances

    def manage_environment(self) -> None:
        sts_client = boto3.client('sts')
        response = sts_client.assume_role(RoleArn=self.role_arn, RoleSessionName='session')
        aws_public_key = response['Credentials']['AccessKeyId']
        aws_secret_key = response['Credentials']['SecretAccessKey']
        aws_session_token = response['Credentials']['SessionToken']
        ec2 = boto3.resource('ec2', region_name=self.region, aws_access_key_id=aws_public_key,
                             aws_secret_access_key=aws_secret_key, aws_session_token=aws_session_token)
        instances = self.get_instances_by_tag(self, self.tag_name, self.tag_value, ec2)
        for instance in instances:
            if self.action == 'start':
                try:
                    instance['Instance'].start()
                    print(f"{instance['Name']} started")
                except ClientError as e:
                    print(e)
            elif self.action == 'stop':
                try:
                    instance['Instance'].stop()
                    print(f"{instance['Name']} stopped")
                except ClientError as e:
                    print(e)
            else:
                print('Unknown action. Nothing to do')


def lambda_handler(event, context):
    if event.get('Records', None) is not None:  # SQS event processing
        for record in event['Records']:
            role_arn = record['messageAttributes']['role_arn']['stringValue']
            region = record['messageAttributes']['management_region']['stringValue']
            tag_name = record['messageAttributes']['tag_environment_name']['stringValue']
            tag_value = record['messageAttributes']['tag_environment_value']['stringValue']
            action = record['messageAttributes']['action']['stringValue']
            ManageEnvironments(role_arn=role_arn, region=region, tag_name=tag_name,
                               tag_value=tag_value,
                               action=action).manage_environment()
    else:
        role_arn = event['role_arn']
        region = event['management_region']
        tag_name = event['tag_environment_name']
        tag_value = event['tag_environment_value']
        action = event['action']
        ManageEnvironments(role_arn=role_arn, region=region, tag_name=tag_name,
                           tag_value=tag_value,
                           action=action).manage_environment()
