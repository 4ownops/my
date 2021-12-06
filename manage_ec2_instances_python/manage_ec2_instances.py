import pulumi_aws as aws
import json
import yaml
import copy
from pulumi import export, output, Input, AssetArchive, FileArchive, CustomResource, ResourceOptions
from typing import Union


class ConfigurationReader:
    def __init__(self, configuration_file: str) -> None:
        with open(configuration_file, 'r') as config:
            self.configuration = yaml.safe_load(config)

    def get_section(self, section_name: str) -> Union[list, dict]:
        return copy.deepcopy(self.configuration[section_name])

    def get_roles(self):
        _roles = self.get_section('roles')
        return _roles

    def get_sqs(self):
        sqs = self.get_section('sqs')
        return sqs


class AwsAssumeRole:
    def __init__(self,
                 role_name: str,
                 policies_configs: list,
                 assume_policy: str):
        self.role_name = role_name
        self.policies_configs = policies_configs
        self.assume_policy = assume_policy
        self.policies_arns = []

    def create_role(self) -> aws.iam.role.Role:
        for policy_config in self.policies_configs:
            with open(policy_config['path_to_json']) as f_policy:
                policy_json = json.load(f_policy)
            policy = aws.iam.Policy(policy_config['name'], policy=json.dumps(policy_json))
            self.policies_arns.append(policy.arn)
            export('policy_arn', policy.arn)
        with open(self.assume_policy) as f_assume_policy:
            assume_policy_json = json.load(f_assume_policy)
        role = aws.iam.Role(self.role_name,
                            assume_role_policy=json.dumps(assume_policy_json),
                            managed_policy_arns=self.policies_arns,
                            name=self.role_name)

        export('roleArn', role.arn)
        return role


class AwsQueue:
    def __init__(self,
                 queue_name: str,
                 delay_seconds: int,
                 max_message_size: int,
                 message_retention_seconds: int,
                 receive_wait_time_seconds: int,
                 policy_json: str,
                 depends_on: CustomResource
                 ) -> None:
        self.queue_name = queue_name
        self.delay_seconds = delay_seconds
        self.max_message_size = max_message_size
        self.message_retention_seconds = message_retention_seconds
        self.receive_wait_time_seconds = receive_wait_time_seconds
        self.policy_json = policy_json
        self.depends_on = depends_on

    def create_queue(self) -> aws.sqs.Queue:
        if self.policy_json != 'None':
            with open(self.policy_json) as f:
                policy = json.load(f)
            queue = aws.sqs.Queue(self.queue_name,
                                  name=self.queue_name,
                                  delay_seconds=self.delay_seconds,
                                  max_message_size=self.max_message_size,
                                  message_retention_seconds=self.message_retention_seconds,
                                  receive_wait_time_seconds=self.receive_wait_time_seconds,
                                  policy=json.dumps(policy),
                                  kms_data_key_reuse_period_seconds=300,
                                  kms_master_key_id="alias/aws/sqs",
                                  opts=ResourceOptions(depends_on=[self.depends_on])
                                  )
        else:
            queue = aws.sqs.Queue(self.queue_name,
                                  name=self.queue_name,
                                  delay_seconds=self.delay_seconds,
                                  max_message_size=self.max_message_size,
                                  message_retention_seconds=self.message_retention_seconds,
                                  receive_wait_time_seconds=self.receive_wait_time_seconds,
                                  kms_data_key_reuse_period_seconds=300,
                                  kms_master_key_id="alias/aws/sqs"
                                  )
        export('queue_arn', queue.arn)
        return queue


class AwsLambda:
    def __init__(self,
                 name: str,
                 runtime: str,
                 app_folder: str,
                 timeout: int,
                 handler: int,
                 role_arn: output.Output,
                 depends_on: CustomResource
                 ) -> None:
        self.name = name
        self.runtime = runtime
        self.app_folder = app_folder
        self.timeout = timeout
        self.handler = handler
        self.role_arn = role_arn
        self.depends_on = depends_on

    def create_lambda(self) -> aws.lambda_.Function:
        aws_lambda = aws.lambda_.Function(self.name,
                                          name=self.name,
                                          runtime=self.runtime,
                                          code=AssetArchive({
                                              ".": FileArchive(self.app_folder),
                                          }),
                                          timeout=self.timeout,
                                          handler=self.handler,
                                          role=self.role_arn,
                                          publish=bool(True),
                                          opts=ResourceOptions(depends_on=[self.depends_on]))
        export('lambda_arn', aws_lambda.arn)
        return aws_lambda

    def create_alias(self,
                     alias_name: str,
                     function_name: output.Output,
                     function_version: output.Output,
                     depends_on: CustomResource) -> aws.lambda_.Alias:
        alias = aws.lambda_.Alias(alias_name,
                                  name=alias_name,
                                  function_name=function_name,
                                  function_version=function_version,
                                  opts=ResourceOptions(depends_on=[depends_on]))
        return alias

    def create_trigger(self,
                       trigger_name: str,
                       event_source_arn: output.Output,
                       function_arn: output.Output,
                       is_active: bool,
                       depends_on: CustomResource) -> aws.lambda_.EventSourceMapping:
        trigger = aws.lambda_.EventSourceMapping(trigger_name,
                                                 event_source_arn=event_source_arn,
                                                 function_name=function_arn,
                                                 enabled=is_active,
                                                 opts=ResourceOptions(depends_on=[depends_on]))
        return trigger

    def create_scheduled_trigger(self,
                                 rule_name: str,
                                 schedule_expression: str,
                                 alias: aws.lambda_.Alias,
                                 function: aws.lambda_.Function,
                                 role_arn: str,
                                 management_region: str,
                                 tag_environment_name: str,
                                 tag_environment_value: str,
                                 action: str,
                                 is_active: bool,
                                 depends_on: CustomResource) -> None:
        input_object = json.dumps({'role_arn': role_arn,
                                   'management_region': management_region,
                                   'tag_environment_name': tag_environment_name,
                                   'tag_environment_value': tag_environment_value,
                                   'action': action})
        rule = aws.cloudwatch.EventRule(resource_name=rule_name,
                                        schedule_expression=schedule_expression,
                                        is_enabled=is_active)
        target = aws.cloudwatch.EventTarget(resource_name=rule_name,
                                            arn=alias.arn,
                                            rule=rule.id,
                                            input=input_object,
                                            opts=ResourceOptions(depends_on=[depends_on]))
        allow_lambda_event = aws.lambda_.Permission('aws_events_' + rule_name,
                                                    action="lambda:InvokeFunction",
                                                    function=function.name,
                                                    principal="events.amazonaws.com",
                                                    source_arn=rule.arn,
                                                    qualifier=alias.name,
                                                    opts=ResourceOptions(depends_on=[depends_on]))
