import boto3, argparse
from botocore.exceptions import ClientError

class ArgParse:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-management_region', help='aws management region')
        self.parser.add_argument('-role_arn', help='managed role arn')
        self.parser.add_argument('-tag_environment_name', help='aws tag name')
        self.parser.add_argument('-tag_environment_value', help='aws tag value')
        self.parser.add_argument('-action', help='start or stop')
    
    def parse(self) -> argparse.Namespace:
        _parser = self.parser
        args_namespace = _parser.parse_args()
        return args_namespace

class SendSQSMessage:
    def __init__(self,
                 role_arn: str,
                 management_region: str,
                 tag_environment_name: str,
                 tag_environment_value: str,
                 action: str
                 ) -> None:
        self.role_arn = role_arn
        self.management_region = management_region
        self.tag_environment_name = tag_environment_name
        self.tag_environment_value = tag_environment_value
        self.action = action
        self.boto3_session_region = 'eu-central-1'
        self.queue_name = 'manage_ec2_instances_queue'

    def attrib_config(self, **options) -> dict: # experiments with **kwargs
        management_dict = {}
        for item in options.items():
            management = {item[0]: {'StringValue': item[1], 'DataType': 'String'}}
            management_dict.update(management)
        return(management_dict)

    def send(self) -> None:
        session = boto3.Session(region_name=self.boto3_session_region)
        sqs = session.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=self.queue_name)
        attributes = self.attrib_config(role_arn = self.role_arn, 
            management_region = self.management_region,
    		tag_environment_name = self.tag_environment_name,
            tag_environment_value = self.tag_environment_value,
            action = self.action)
        response = queue.send_message(MessageBody=self.tag_environment_value, MessageAttributes=attributes)
        if response.get('Failed') != None:
            raise Error(response.get('Failed'))
        else:
            print('Message sent!')
            print(response)

if (__name__ == '__main__'):
    parser_init = ArgParse()
    parser = parser_init.parse()
    sqs_init = SendSQSMessage(parser.role_arn, parser.management_region, parser.tag_environment_name, parser.tag_environment_value, parser.action)
    sqs_init.send()
