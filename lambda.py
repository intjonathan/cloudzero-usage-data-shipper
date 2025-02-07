import boto3
import os
import json
import unit_csv_to_cz_json
import cz_telem_shipper
import download_and_ship as ds

def handle(a, b):
    params_path = os.environ.get('SSM_PARAMETER_STORE_FOLDER_PATH')
    s3_bucket = os.environ.get('CSV_S3_BUCKET')
    s3_prefix = os.environ.get('CSV_S3_PREFIX')
    use_principal_mappings = os.environ.get('USE_PRINCIPAL_MAPPINGS') if os.environ.get('USE_PRINCIPAL_MAPPINGS') is not None else True

    print(f"Starting execution with arguments...")
    print(f"SSM Params Path: {params_path}")
    print(f"s3_bucket and prefix: '{s3_bucket}' '{s3_prefix}'")
    print(f"use_principal_mappings: {use_principal_mappings}")
    if os.environ.get('AWS_SECRET_ACCESS_KEY') is not None:
        printable_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')[-8:]
    print(f"AKI: {os.environ.get('AWS_ACCESS_KEY_ID')} SAK suffix: {printable_secret_access_key}")

    client = boto3.client('ssm', 'us-east-1')
    cz_api_key = client.get_parameter(
        Name = os.path.join(params_path, "cz-api-key"),
        WithDecryption = True )['Parameter']['Value']
    
    
    s3 = boto3.client('s3')

    ds.download_and_ship_allocation_telemetry(s3, s3_bucket, s3_prefix,
                                              use_principal_mappings,
                                              cz_api_key)