import boto3
import time
import os

REGION='us-west-1'
KEY_ACCESS=os.environ.get('AWS_ACCESS_KEY_ID')
KEY_SECRET=os.environ.get('AWS_SECRET_ACCESS_KEY')
NAME_CLUSTER=os.environ.get('RDS_CLUSTER_IDENTIFIER')
TYPE_INSTANCE=os.environ.get('RDS_INSTANCE_TYPE')

if not (KEY_ACCESS and KEY_SECRET and NAME_CLUSTER and TYPE_INSTANCE):
    print('환경변수로 다음을 지정 해주세요')
    print('AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, RDS_CLUSTER_IDENTIFIER, RDS_INSTANCE_TYPE')
    exit(1)

client = boto3.client(
    'rds',
    region_name=REGION,
    aws_access_key_id=KEY_ACCESS,
    aws_secret_access_key=KEY_SECRET,
)

response = client.describe_db_clusters(
    DBClusterIdentifier=NAME_CLUSTER,
)

status = response['DBClusters'][0]['Status']
if len(response['DBClusters']) != 1:
    print('하나의 클러스터만 검색되지 않았습니다.')
    exit(-1)

if status == 'available':
    pass
elif status == 'scaling-capacity':
    print('이미 사이즈 변경중 입니다.')
    exit(0)
else:
    print(f"경고: 예상하지 못한 상태입니다:{status}")
    exit(-1)

cluster = response['DBClusters'][0]
print(f"endpoint: {cluster['Endpoint']}")
print(f"readpoint: {cluster['ReaderEndpoint']}")

cluster_member = cluster['DBClusterMembers']

for instance in cluster_member:
    if instance['IsClusterWriter'] == True:
        writer = instance

    if instance['IsClusterWriter'] == False:
        reader = instance

print(f"reader: {reader}")
print(f"writer: {writer}")

response = client.describe_db_instances(
    DBInstanceIdentifier=reader['DBInstanceIdentifier'],
)

if response['DBInstances'][0]['DBInstanceClass'] == TYPE_INSTANCE:
    print('번경하려는 DB 사이즈가 동일합니다.')
    exit(-1)

if response['DBInstances'][0]['DBInstanceStatus'] != 'available':
    print('reader DB 상태가 available 상태가 아닙니다.')
    exit(-1)

response = client.describe_db_instances(
    DBInstanceIdentifier=writer['DBInstanceIdentifier'],
)

if response['DBInstances'][0]['DBInstanceStatus'] != 'available':
    print('writer DB 상태가 available 상태가 아닙니다.')
    exit(-1)

response = client.modify_db_instance(
    DBInstanceIdentifier=reader['DBInstanceIdentifier'],
    DBInstanceClass=TYPE_INSTANCE,
    ApplyImmediately=True,
)

print(response)

loop = 100
pending_item = {'initial': ''}
while not (len(pending_item) == 0 or loop < 0):
    time.sleep(5)
    response = client.describe_db_instances(
        DBInstanceIdentifier=reader['DBInstanceIdentifier'],
    )

    pending_item = response['DBInstances'][0]['PendingModifiedValues']
    loop -= 1

if loop <= 0:
    print('DB 사이즈 변경이 너무 오래 대기중입니다.')
    print(response)
    exit(-1)

loop = 100
while True:
    response = client.describe_db_instances(
        DBInstanceIdentifier=reader['DBInstanceIdentifier'],
    )

    status = response['DBInstances'][0]['DBInstanceStatus']
    if loop < 0:
        print('대기시간을 초과하였습니다.')
        exit(1)

    if status == 'modifying':
        print('m', end='')
        time.sleep(10)
        loop -= 1
        continue
    elif status == 'configuring-enhanced-monitoring':
        print('c', end='')
        time.sleep(10)
        loop -= 1
        continue
    elif status == 'available':
        print('')
        break
    else:
        print(status)
        time.sleep(10)
        loop -= 1
        continue

response = client.reboot_db_instance(
    DBInstanceIdentifier=writer['DBInstanceIdentifier'],
)

print(response)
