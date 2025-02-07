import boto3
import argparse
import os
import json
import pandas as pd
import unit_csv_to_cz_json
import cz_telem_shipper
import re
import atexit
import tempfile
import shutil

from unit_allocation_csv import createUnitAllocationCsv


def download_and_ship_allocation_telemetry( 
        s3_client, s3_bucket, s3_prefix, 
        use_principal_mappings,
        cz_api_key
):
    s3_prefix_list = s3_prefix.split(',')
    s3_objects = []
    principal_maps = {}
    for prefix in s3_prefix_list:
       response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
       s3_objects.extend(response['Contents'])

    print(f"Found {len(s3_objects)} objects in bucket '{s3_bucket}' with prefixes {s3_prefix_list}:")
    for obj in s3_objects:
        print(f"  {obj['Key']}")

    # Identify and download principal map files
    principal_maps = {}
    print (f"Use principal mappings: {use_principal_mappings}")
    if use_principal_mappings:
        for obj in s3_objects:
            if 'principal-map' in obj['Key']:
                principal_map_filename = os.path.basename(obj['Key'])
                principal_map_no_prefix = principal_map_filename.split('principal-map-')[1]
                principal_map_streamname = os.path.splitext(principal_map_no_prefix)[0]
                principal_maps[principal_map_streamname] = None

                principal_map_file = tempfile.mkstemp(".json")[1]
                atexit.register(os.remove, principal_map_file)
                s3_client.download_file(s3_bucket, obj['Key'], principal_map_file)
                principal_maps[principal_map_streamname] = principal_map_file

    print(f"Principal maps: {principal_maps}")
    # Process the remaining telemetry files
    for obj in s3_objects:
        file_key = obj['Key']
        if "/sent/" in file_key or "principal-map" in file_key:
            continue
        if re.match(r".*\.csv\.gz$", file_key) or re.match(r".*\.csv$", file_key):
           print(f"Processing file: {file_key}") 
        else:
            # Skip non-CSV files
            print(f"Skipping non-CSV file in bucket: {file_key}")
            continue
        
        file_name = os.path.basename(file_key)
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, temp_dir)

        local_file_path = os.path.join(temp_dir, file_name)
        print(f"Downloading {file_key} to {local_file_path}...")
        s3_client.download_file(s3_bucket, file_key, local_file_path)

        # Run the json conversion and ship telemetry code for each downloaded file
        csv_object = createUnitAllocationCsv(local_file_path)
        # This might not exist in the principal map dict - it's okay
        if csv_object.streamName() in principal_maps:
            csv_object.setPrincipalMap(principal_maps[csv_object.streamName()])

        output = csv_object.toCzAllocationApiFormat(temp_dir, stream_mappings_file)

        if output is None:
            print(f"Skipping {file_key} due to an error during processing")
            continue

        print(f"Sending telemetry for {output} to CloudZero...")
        cz_telem_shipper.ship_cz_telemetry(cz_api_key, 
                                            output.stream_name,
                                            json.load(open(output.file_name, "r")))
        print(f"Deleting {output.file_name}...")
        os.remove(output.file_name)

        # Move the CSV file to the "sent" folder in S3, unless it's a test file
        # sent_file_key = os.path.join(s3_prefix, "sent", file_name)
        sent_file_key_prefix = os.path.join(os.path.split(file_key)[0], 'sent')
        sent_file_key = os.path.join(sent_file_key_prefix, os.path.basename(file_key))
        if 'test' not in s3_prefix:
            print(f"S3 Copying {file_key} to {sent_file_key}...")
            s3_client.copy_object(Bucket=s3_bucket, 
                      CopySource={'Bucket': s3_bucket, 'Key': file_key}, 
                      Key=sent_file_key)
            print(f"S3 Deleting {file_key}...")
            s3_client.delete_object(Bucket=s3_bucket, Key=file_key)
        else:
            print(f"Would copy {file_key} to {sent_file_key}, but...")
            print(f"Leaving {file_key} in place due to 'test' prefix")
        
        os.remove(local_file_path)
        