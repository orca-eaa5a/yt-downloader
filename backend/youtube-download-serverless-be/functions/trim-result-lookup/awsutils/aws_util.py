import os
import boto3
import logging
logging.getLogger().setLevel(logging.INFO)

DYN_TABLE_NAME = os.environ.get('TrimCacheDynDB')
REGION = os.environ.get('AWS_REGION')
DYN_TABLE_PARTIOTN_KEY = os.environ.get('TrimCacheDynTablePartitionKey')
DYN_TABLE_SORT_KEY = os.environ.get('TrimCacheDynTableSortKey')

def get_dynamodb_client(region=None):
    if not region:
        region = REGION
    return boto3.client('dynamodb', region_name=region)

def dyn_get_item(dyn_client, table_name, key):
    try:
        resp = dyn_client.get_item(
            TableName=table_name,
            Item=key)
    except Exception as e:
        logging.error("dynamodb get_item error with: {}".format(str(e)))
        return None

    if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        logging.error("dynamodb get_item failed with: {}".format(resp['ResponseMetadata']['HTTPStatusCode']))
        return None
    return resp
    # pk_expression = ":{}".format(DYN_TABLE_PARTIOTN_KEY)
    # sk_expression = ":{}".format(DYN_TABLE_SORT_KEY)
    # return dyn_client.query(
    #     TableName=table_name,
    #     ExpressionAttributeValues={
    #         pk_expression: { 'S': key },
    #         sk_expression: {'S': sortkey}
    #     },
    #     KeyConditionExpression ='{}=:{} AND {}=:{}'.format(
    #         DYN_TABLE_PARTIOTN_KEY, DYN_TABLE_PARTIOTN_KEY,
    #         DYN_TABLE_SORT_KEY, DYN_TABLE_SORT_KEY
    #     )
    # )





