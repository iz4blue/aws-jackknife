import boto3
import time
import os

REGION='us-west-1'
KEY_ACCESS=os.environ.get('AWS_ACCESS_KEY_ID')
KEY_SECRET=os.environ.get('AWS_SECRET_ACCESS_KEY')
NAME_CLUSTER=os.environ.get('RDS_CLUSTER_IDENTIFIER')
try:
    SIZE_CLUSTER=os.environ.get('RDS_CLUSTER_SIZE')
    SIZE_CLUSTER=int(SIZE_CLUSTER)
except ValueError as e:
    print(f"RDS_CLUSTER_SIZE 지정은 숫자로 해야 합니다:{SIZE_CLUSTER}")
    exit(-1)

if not (KEY_ACCESS and KEY_SECRET and NAME_CLUSTER and SIZE_CLUSTER):
    print('환경변수로 다음을 지정 해주세요')
    print('AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, RDS_CLUSTER_IDENTIFIER, RDS_CLUSTER_SIZE')
    exit(1)

if SIZE_CLUSTER not in (1, 2, 4, 8, 16, 32, 64, 128, 256):
    print(f"다음 사이즈는 혀용되지 않습니다:{SIZE_CLUSTER}")
    exit(-1)

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

response = client.modify_current_db_cluster_capacity(
    DBClusterIdentifier=NAME_CLUSTER,
    Capacity=SIZE_CLUSTER,
    SecondsBeforeTimeout=300,
    TimeoutAction='RollbackCapacityChange',
)

print(response)

time.sleep(10)

response = client.describe_db_clusters(
    DBClusterIdentifier='joseph-cluster',
)
print(response['DBClusters'][0]['Status'])
