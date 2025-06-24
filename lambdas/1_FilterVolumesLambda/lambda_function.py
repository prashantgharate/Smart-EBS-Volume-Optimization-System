import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='ap-south-1')
    volumes = ec2.describe_volumes(
        Filters=[
            {'Name': 'tag:AutoConvert', 'Values': ['true']},
            {'Name': 'volume-type', 'Values': ['gp2']}
        ]
    )

    output = []
    for v in volumes['Volumes']:
        output.append({
            'VolumeId': v['VolumeId'],
            'AvailabilityZone': v['AvailabilityZone']
        })
    return output
