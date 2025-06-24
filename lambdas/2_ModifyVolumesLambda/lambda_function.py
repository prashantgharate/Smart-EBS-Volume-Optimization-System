import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='ap-south-1')

    for vol in event:
        response = ec2.modify_volume(
            VolumeId=vol['VolumeId'],
            VolumeType='gp3'
        )
    return {
        'status': 'submitted for conversion',
        'volumes': [v['VolumeId'] for v in event]
    }
