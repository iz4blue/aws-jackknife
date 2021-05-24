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

# FIXME: 시작전에 db status 확인하기

response = client.modify_db_instance(
    DBInstanceIdentifier=reader['DBInstanceIdentifier'],
    #DBInstanceClass='db.t3.medium',
    DBInstanceClass='db.t3.large',
    ApplyImmediately=True,
)

print(response)

time.sleep(5)
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
    elif status == 'Configuring-enhanced-monitoring':
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
