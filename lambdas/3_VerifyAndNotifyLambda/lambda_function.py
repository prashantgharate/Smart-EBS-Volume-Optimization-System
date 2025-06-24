import boto3
import datetime
import json

ec2 = boto3.client('ec2', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
sns = boto3.client('sns', region_name='ap-south-1')

table_name = 'VolumeConversionLogs'
topic_arn = 'arn:aws:sns:ap-south-1:324037322062:EBSVolumeConvertedTopic'

def lambda_handler(event, context):
    table = dynamodb.Table(table_name)

    if isinstance(event, str):
        event = json.loads(event)
    if isinstance(event, dict):
        event = [event]

    for vol in event:
        try:
            volume_id = vol['VolumeId']
            vol_details = ec2.describe_volumes(VolumeIds=[volume_id])
            volume = vol_details['Volumes'][0]

            volume_type = volume['VolumeType']
            size = volume['Size']
            state = volume['State']
            attachments = volume.get('Attachments', [])
            instance_id = attachments[0]['InstanceId'] if attachments else 'Unknown'

            log = {
                'VolumeID': volume_id,
                'InstanceId': instance_id,
                'VolumeType': volume_type,
                'Size': size,
                'Region': 'ap-south-1',
                'Timestamp': datetime.datetime.utcnow().isoformat(),
                'Status': state
            }

            table.put_item(Item=log)

            sns.publish(
                TopicArn=topic_arn,
                Subject='EBS Volume Status Logged',
                Message=f"Volume ID: {volume_id}, Status: {state}"
            )

        except Exception as e:
            print(f"❌ Error processing volume: {vol}")
            print(f"🔴 Reason: {str(e)}")

    return {'status': 'logged and notified'}
