# 📦 Intelligent EBS Volume Optimization using AWS Step Functions

## 🧠 Project Overview
This project automates the identification, conversion, and logging of EC2 EBS volumes using AWS Lambda, Step Functions, DynamoDB, and SNS. It is designed to optimize gp2 volumes to gp3 and send real-time notifications post-conversion.

---

## 🔧 Technologies Used
- **AWS Lambda** (Python)
- **AWS Step Functions**
- **Amazon EC2 (EBS)**
- **Amazon DynamoDB**
- **Amazon SNS**
- **IAM Roles & Policies**

---

## 🗂️ Folder Structure
```
ebs-volume-optimizer/
├── lambdas/
│   ├── 1_FilterVolumesLambda/
│   │   └── lambda_function.py
│   ├── 2_ModifyVolumesLambda/
│   │   └── lambda_function.py
│   └── 3_VerifyAndNotifyLambda/
│       └── lambda_function.py
│
├── step-function/
│   └── state_machine_definition.json
│
├── dynamodb/
│   └── table_schema.txt (optional)
│
├── sns/
│   └── topic_info.txt (optional)
│
├── README.md
└── architecture-diagram.png (optional)
```

---

## 🔁 Workflow Summary
1. **FilterVolumesLambda** – Filters EBS volumes with tag `AutoConvert=true` and type `gp2`.
```python
# lambdas/1_FilterVolumesLambda/lambda_function.py
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
```

2. **ModifyVolumesLambda** – Converts volumes from `gp2` to `gp3`.
```python
# lambdas/2_ModifyVolumesLambda/lambda_function.py
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
```

3. **VerifyAndNotifyLambda** – Logs volume data to DynamoDB and sends an SNS notification.
```python
# lambdas/3_VerifyAndNotifyLambda/lambda_function.py
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
```

4. **Step Function JSON Definition** – Connects all Lambda steps.
```json
// step-function/state_machine_definition.json
{
  "Comment": "EBS Volume Optimization Workflow",
  "StartAt": "FilterVolumes",
  "States": {
    "FilterVolumes": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-1:324037322062:function:FilterVolumesLambda",
      "Next": "ModifyVolumes"
    },
    "ModifyVolumes": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-1:324037322062:function:ModifyVolumesLambda",
      "Next": "VerifyAndNotify"
    },
    "VerifyAndNotify": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-1:324037322062:function:VerifyAndNotifyLambda",
      "End": true
    }
  }
}
```

---

## 🧪 Testing
You can test each Lambda individually using the AWS Console > Lambda > Test. Sample test input:
```json
[
  {
    "VolumeId": "vol-0a7d19d56af8d3ccc"
  }
]
```

---

## ✅ Output
- Successful conversion logs appear in **DynamoDB > VolumeConversionLogs**
- Notifications are sent to **SNS Topic Subscribers**
- Step Function visual logs show state transitions

---

## 📘 Notes
- Ensure IAM role `LambdaEBSRole` has permissions for EC2, DynamoDB, and SNS.
- Make sure the region is consistently `ap-south-1` across all services.
- DynamoDB table name must exactly match `VolumeConversionLogs`.

---

## 🙌 Author
Prashant Gharate  

---

## 🔗 Useful Links
- [Step Functions Console](https://console.aws.amazon.com/states/home)
- [Lambda Console](https://console.aws.amazon.com/lambda/home)
- [DynamoDB Console](https://console.aws.amazon.com/dynamodb/home)
- [SNS Console](https://console.aws.amazon.com/sns/v3/home)
