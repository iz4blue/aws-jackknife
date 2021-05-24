import boto3
import os

REGION='us-west-1'
KEY_ACCESS=os.environ.get('AWS_ACCESS_KEY_ID')
KEY_SECRET=os.environ.get('AWS_SECRET_ACCESS_KEY')
ID_AMI=os.environ.get('AWS_TARGET_AMI')
ID_TEMPLATE=os.environ.get('AWS_TARGET_TEMPLATE')

ec2 = boto3.resource(
    'ec2',
    region_name=REGION,
)

client = boto3.client(
    'ec2',
    region_name=REGION,
)

response = client.create_launch_template_version(
    LaunchTemplateId=ID_TEMPLATE,
    LaunchTemplateData={
        'ImageId': ID_AMI,
    }
)

version = response['LaunchTemplateVersion']['VersionNumber']
print(f"template version: {version}")

response = client.modify_launch_template(
    LaunchTemplateId=ID_TEMPLATE,
    DefaultVersion=f"{version}",
)

print(response)
