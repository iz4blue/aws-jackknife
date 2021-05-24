import boto3
from datetime import datetime
import time
import os

REGION='us-west-1'
KEY_ACCESS=os.environ.get('AWS_ACCESS_KEY_ID')
KEY_SECRET=os.environ.get('AWS_SECRET_ACCESS_KEY')
TAG_TARGET_EC2=os.environ.get('AWS_EC2_TARGET_TAG')

if not (KEY_ACCESS and KEY_SECRET and TAG_TARGET_EC2):
    print('환경변수로 다음을 지정 해주세요')
    print('AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, TAG_TARGET_EC2')
    exit(1)

DATE = datetime.strftime(datetime.now(), '%Y%m%d')
print(f"date tag: {DATE}")

ec2 = boto3.resource(
    'ec2',
    region_name=REGION,
)

client = boto3.client(
    'ec2',
    region_name=REGION,
)

response = client.describe_instances(
    Filters=[{'Name': 'tag:Name',
              'Values': [
                  TAG_TARGET_EC2,
              ]}
    ],
)

cnt = len(response['Reservations'])
if cnt != 1:
    if len(response['Reservations']) == 0:
        print('TAG로 검색된 결과가 없습니다.')
    elif len(response['Reservations']) > 1:
        print('TAG로 검색되는 결과가 2개 이상입니다.')
        print(response)

    exit(-1)

ec2_instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
ec2_instance = ec2.Instance(ec2_instance_id)
print(f"ec2 instance id: {ec2_instance_id}")

image = client.create_image(
    InstanceId=ec2_instance_id,
    Name=f"snapshot_{DATE}_{ec2_instance_id}",
    Description=f"desc {DATE} {ec2_instance_id}",
    NoReboot=True,
    TagSpecifications=[
        {
            'ResourceType': 'image',
            'Tags': [
                {
                    'Key': 'managed-snapshot',
                    'Value': f"{DATE}",
                }
            ],
        }
    ],
)

image_id = image['ImageId']
print(f"image id: {image_id}")

loop = 30
while True:
    response = client.describe_images(
        ImageIds=[image_id, ],
    )

    status = response['Images'][0]['State']

    if loop < 0:
        print('대기시간을 초과하였습니다.')
        exit(1)

    if status == 'pending':
        print('.', end='')
        time.sleep(5)
        loop -= 1
        continue
    elif status == 'available':
        print('')
        break
    else:
        print(status)
        time.sleep(5)
        loop -= 1
        continue

print(response)
