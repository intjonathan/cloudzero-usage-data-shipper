import boto3
import argparse
import os
import json
import pandas as pd
import unit_csv_to_cz_json
import cz_telem_shipper
import tempfile
import atexit
import shutil
import download_and_ship as ds
from unit_allocation_csv import createUnitAllocationCsv, unit_allocation_csv
from unit_allocation_csv.base_unit_allocation_csv import BaseUnitAllocationCsv

parser = argparse.ArgumentParser()

parser.add_argument("-b", "--csv-s3-bucket", type=str,
                     help="Bucket to search for unit cost CSV files. default: unit-cost-telemetry")
parser.add_argument("-p", "--prefix", 
                    help="Comma-separated S3 path prefixes to search for CSV files", type=str)

parser.add_argument("-f", "--csv-file", help="Local CSV file to read instead of S3")

parser.add_argument("-t", '--timestamp-test', action='store_true', 
                    help="Overrides timestamp in CSV to now (UTC) for testing visibility")

parser.add_argument("-m", "--principal-mappings-file",
                    help="Path to the CSV containing the principal name mappings. Only compatible with the --csv-file argument. Does nothing when used with --csv-s3-bucket. If provided, the principal field in the telemetry CSV will be used as a lookup key to the principal column in this CSV, and the associated value in the princpal_name column used when reporting.",
                    type=str, default=None)

parser.add_argument("-a", "--cz-api-key", help="API key for CloudZero", type=str)

args = parser.parse_args()

if args.csv_s3_bucket is not None and args.csv_file is not None:
    print("ERROR: You must specify either --csv-s3-bucket or --csv-file, not both.\n")
    parser.print_help()
    exit(1)

if args.csv_s3_bucket is not None:

    if args.principal_mappings_file:
        print("WARNING: --principal-mappings-file will be looked for in S3, not locally.")
        
    s3 = boto3.client('s3')

    ds.download_and_ship_allocation_telemetry(s3, 
                                              args.csv_s3_bucket, 
                                              args.prefix,
                                              args.principal_mappings_file,
                                              args.cz_api_key)
elif args.csv_file is not None:
    temp_dir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, temp_dir)
    usage_csv = createUnitAllocationCsv(args.csv_file)
    usage_csv.setPrincipalMap(args.principal_mappings_file)
    output_json_object = usage_csv.toCzAllocationApiFormat(temp_dir, args.timestamp_test)

    cz_telem_shipper.ship_cz_telemetry(args.cz_api_key, 
                                        output_json_object.stream_name,
                                        json.load(open(output_json_object.file_name, "r")))
    print(f"Deleting {output_json_object.file_name}...")
    os.remove(output_json_object.file_name)

else:
    parser.print_help()
