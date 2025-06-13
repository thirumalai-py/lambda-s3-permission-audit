import boto3

s3 = boto3.client('s3')
sns = boto3.client('sns')

SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-1:975050024946:thiru-s3-public-buckets-topic'  # 🔁 Replace

def lambda_handler(event, context):
    response = s3.list_buckets()
    public_buckets = []

    for bucket in response['Buckets']:
        bucket_name = bucket['Name']
        try:
            # Check ACL
            acl = s3.get_bucket_acl(Bucket=bucket_name)
            for grant in acl['Grants']:
                grantee = grant.get('Grantee', {})
                if grantee.get('URI') in [
                    'http://acs.amazonaws.com/groups/global/AllUsers',
                    'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'
                ]:
                    public_buckets.append((bucket_name, 'ACL'))

            # Check Bucket Policy (if exists)
            try:
                policy_status = s3.get_bucket_policy_status(Bucket=bucket_name)
                if policy_status['PolicyStatus']['IsPublic']:
                    public_buckets.append((bucket_name, 'BucketPolicy'))
            except s3.exceptions.from_code('NoSuchBucketPolicy'):
                pass

        except Exception as e:
            print(f"Error checking {bucket_name}: {e}")

    # Send Notification if any public buckets found
    if public_buckets:
        message = "⚠️ Publicly accessible S3 buckets found:\n"
        for b, reason in public_buckets:
            message += f"- {b} ({reason})\n"

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="S3 Public Bucket Alert",
            Message=message
        )
        print("Notification sent.")
    else:
        print("✅ No public buckets found.")
