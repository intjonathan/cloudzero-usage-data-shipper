# CloudZero Usage Data CSV Shipper

This tool transmits allocated usage data from CSV files in S3 to CloudZero's telemetry allocation API. It runs in Lambda Containers, reads the data from S3, converts to CZ allocation telemetry, uploads that to CZ, then moves the files in S3 to a different bucket prefix on completion.

## Requirements

* CloudZero API key
* S3 bucket access
* CSV files as input. The files should be formatted as defined in this document: [CSV_README.md](CSV_README.md)

## Usage

### Command Line

Requirements:

* Python 3.9+
* (optional) awscli with access to the target S3 bucket via the default profile.

Install the libraries in `requirements.txt`, then run `cli.py --help` to get a list of important arguments.

If a local CSV file is specified, the tool will upload the data inside to CZ as allocation telemetry. Otherwise, the tool will look for AWS credentials in your environment, and S3 will be used to fetch all CSV files from the specified bucket, ship the data inside to CZ as allocation telemetry, and the files in S3 moved to a `/sent/` prefix inside the bucket when complete.

### Lambda

Requirements:

* A lambda container function configured with this image built in an ECR registry.
* Permissions on the function's role sufficient to access an S3 bucket with read/write, and read SSM parameters under the supplied prefix.
* Environment variables on the Lambda function:
  * `SSM_PARAMETER_STORE_FOLDER_PATH`: Path to the AWS Systems Manager Parameter Store keys. See below for more.
  * `CSV_S3_BUCKET`: S3 bucket name to search for CSV files.
  * `CSV_S3_PREFIX`: Comma-separated list of prefixes to examine inside the bucket. Other paths are ignored.
* Optional environment variables:
  * `USE_PRINCIPAL_MAPPINGS`: whether to search the s3 bucket for principal mappings files. Default is `True`. See [CSV_README](CSV_README.md) for more.

#### Deploying Lambda Images

Build a container from this repository's Dockerfile using whatever container builder you prefer. Push it to your ECR registry, and create a Lambda Container function based on that repository. Deploy your image using Lambda. Once the image deploys, you can use the Test tab and run an empty test event through it. This will emit loglines indicating what it did. Unless there are files to process, it won't do much, but at least you can see it check.

If you want to have it do some work, you can place a CSV test file in the S3 bucket path and do a test run. The lambda should pick up the file and send it to CloudZero, generating log output in the process for examination. Creating a test file is up to you, as each CloudZero instance has its own dimensions.

#### Systems Manager Parameters

Lambda execution uses AWS Systems Manager Parameter Store to retrieve the CloudZero API key. The key should be encrypted. It will be retrieved from:

`{SSM_PARAMETER_STORE_FOLDER_PATH}/cz-api-key`

#### Testing Lambda Invocation Locally

The container will need AWS authentication variables imported from your shell:

```bash
docker run -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
-e SSM_PARAMETER_STORE_FOLDER_PATH=/<your-parameter-store-prefix> \
-e USE_PRINCIPAL_MAPPINGS=True -e CSV_S3_BUCKET=<your-s3-bucket> \
-e CSV_S3_PREFIX=finops -p 9000:8080 <image-id>:<image-label>
```

This starts the Lambda listener on the container network interface, on port 9000. Then in another terminal, run:

```bash
curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

Output will be produced in the terminal.

## Monitoring

To monitor performance and errors, use the Lambda monitoring tab for your deployed function. A healthy run cycle will show hourly spikes in duration, and 100% success rate with no errors.

To see the logs, use the function's CloudWatch log group. A healthy log run that ships data will show each step for every processed file - download, convert, ship to CZ, and archive to the `/sent` prefix.

You may also observe the [telemetry stream overview page](https://app.cloudzero.com/telemetry) in CloudZero. Any streams with request activity should have very steady charts and no recent errors.

Finally, an avaliable CZ Analytics dashboard called Telemetry Stream Management provides a view into what CZ sees of the data and request rates. Ask your CZ support representative to add this board to your account if it's not yet present.

_CloudZero CSV Unit Cost Shipper, v0.0.1, Copyright 2023, Jonathan Owens, © The Apache Software Foundation, is distributed under the Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)_
