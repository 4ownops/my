# Manage aws ec2 instances

Python application for AWS Lambda.
Application recieve SQS event or event from Event Bridge and start or stop aws ec2 instances by tag.
For IaC used pulumi.

Example for stop ec2 instances:
python .\message_sender.py -management_region ap-southeast-2 -role_arn arn:aws:iam::#{aws_account_id}:role/start_stop_ec2_assume_role -tag_environment_name env -tag_environment_value dev -action stop