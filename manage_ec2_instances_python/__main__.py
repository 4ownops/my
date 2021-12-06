"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws
from manage_ec2_instances import ConfigurationReader, AwsAssumeRole, AwsQueue, AwsLambda


class Program:
    def __init__(self) -> None:
        config = ConfigurationReader('config.yaml')
        roles = config.get_roles()
        queues_config = config.get_sqs()
        lambda_config = config.get_section('lambda')

        lambda_execution_role_init = AwsAssumeRole(role_name=roles[0]['name'],
                                                   assume_policy=roles[0]['assume_role_policy'],
                                                   policies_configs=roles[0]['policies'])
        lambda_execution_role = lambda_execution_role_init.create_role()

        lambda_init = AwsLambda(lambda_config[0]['name'],
                                runtime=lambda_config[0]['runtime'],
                                app_folder=lambda_config[0]['app_folder'],
                                timeout=lambda_config[0]['timeout'],
                                handler=lambda_config[0]['handler'],
                                role_arn=lambda_execution_role.arn,
                                depends_on=lambda_execution_role)
        ec2_manage_lambda = lambda_init.create_lambda()
        pulumi.export('lambda_version', ec2_manage_lambda.version)

        queues = {}
        for queue_config in queues_config:
            queue_init = AwsQueue(queue_config['name'],
                                  delay_seconds=queue_config['delay_seconds'],
                                  max_message_size=queue_config['max_message_size'],
                                  message_retention_seconds=queue_config['message_retention_seconds'],
                                  receive_wait_time_seconds=queue_config['receive_wait_time_seconds'],
                                  policy_json=queue_config['policy'],
                                  depends_on=ec2_manage_lambda)
            queue = queue_init.create_queue()
            queues.update({queue_config['name']: queue})

        aliases = {}
        for alias_config in lambda_config[0]['aliases']:
            alias = lambda_init.create_alias(alias_name=alias_config['name'],
                                             function_name=ec2_manage_lambda.name,
                                             function_version=ec2_manage_lambda.version,
                                             depends_on=ec2_manage_lambda)
            aliases.update({alias_config['name']: alias})

        for trigger_config in lambda_config[0]['triggers']['sqs']:
            trigger_name = trigger_config['name']
            alias = aliases[trigger_config['alias_name']]
            queue = queues[trigger_config['name']]
            if trigger_config['status'] == 'enabled':
                is_active = True
            elif trigger_config['status'] == 'disabled':
                is_active = False
            else:
                raise status('Status undefined. You should use disabled or enabled')
            lambda_init.create_trigger(trigger_name,
                                       event_source_arn=queue.arn,
                                       function_arn=alias.arn,
                                       is_active=is_active,
                                       depends_on=alias)

        for trigger_config in lambda_config[0]['triggers']['event_bridge']:
            trigger_name = trigger_config['name']
            alias = aliases[trigger_config['alias_name']]
            start_schedule_expression = trigger_config['start_schedule_expression']
            stop_schedule_expression = trigger_config['stop_schedule_expression']
            role_arn = trigger_config['input']['role_arn']
            management_region = trigger_config['input']['management_region']
            tag_environment_name = trigger_config['input']['tag_environment_name']
            tag_environment_value = trigger_config['input']['tag_environment_value']
            if trigger_config['status'] == 'enabled':
                is_active = True
            elif trigger_config['status'] == 'disabled':
                is_active = False
            else:
                raise status('Status undefined. You should use disabled or enabled')
            lambda_init.create_scheduled_trigger(rule_name=trigger_name + "_start",
                                                 schedule_expression=start_schedule_expression,
                                                 alias=alias,
                                                 function=ec2_manage_lambda,
                                                 role_arn=role_arn,
                                                 management_region=management_region,
                                                 tag_environment_name=tag_environment_name,
                                                 tag_environment_value=tag_environment_value,
                                                 action='start',
                                                 is_active=is_active,
                                                 depends_on=alias
                                                 )
            lambda_init.create_scheduled_trigger(rule_name=trigger_name + "_stop",
                                                 schedule_expression=stop_schedule_expression,
                                                 alias=alias,
                                                 function=ec2_manage_lambda,
                                                 role_arn=role_arn,
                                                 management_region=management_region,
                                                 tag_environment_name=tag_environment_name,
                                                 tag_environment_value=tag_environment_value,
                                                 action='stop',
                                                 is_active=is_active,
                                                 depends_on=alias
                                                 )


if __name__ == "__main__":
    program = Program()
