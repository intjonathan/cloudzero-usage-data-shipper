# CloudZero Unit Cost CSV Format

The unit cost data shipper reads gzipped CSV files from an S3 bucket and sends the data to CloudZero via their [Allocation API](https://docs.cloudzero.com/reference/sumallocationtelemetry). Users that want an asynchronous way to ship unit cost data to CloudZero, or need to separate their cost data query from the system that sends it, may find this useful.

Please read the Allocation API documentation (linked above) to familiarize yourself with its concepts, particularly the telemetry stream name and filter concepts.

Files with this specified format may be placed in an S3 bucket, and code from this repository runs in a Lambda container to read the file and ship it to CloudZero.

## Filename `telemetry-stream`

The telemetry stream name in the file's name will be used when reporting the data to CloudZero. This should be a well-known name with a clear definition, as each telemetry stream in CloudZero is usually long-lived, and maps to an immutable set of dimension keys.

The files should contain at most 1 day of data or 1 million rows, whichever is smaller. The file name should contain the file creation time in ISO 8601 UTC style at the end of the filename in the following format:

`<telemetry-stream-name>_YYYY-MM-DD-HH-mm-SSZ.csv.gz`

The beginning of the filename must not start with the string `principal-map`, as that is reserved for the stream principal name mappings file (covered later).

The first time data is reported using a given stream name, the `cost:` columns in the file will be registered for that stream and fixed in place. No changes to the `cost:` columns are permitted for that stream name without deleting the stream - and its associated data - and recreating it with new columns. The `cost:` columns are covered in more detail below.

Examples:

* `dlp-document-scan-cpu-ms_2024-05-23-00-03-00Z.csv.gz`
* `casb-user-storage-bytes_2024-05-01-00-03-00Z.csv.gz`
* `qa-email-scan-memory-mb_2024-12-23-00-03-00Z.csv.gz`
* `hcasb-search-cpu-ms_2024-11-24-02-03-00Z.csv.gz`
* `dps-unique-device-count_2024-05-02-04-03-00Z.csv.gz`

## Columns

The CSV files will have the following column header pattern:

`timestamp,granularity,usage,principal,cost:<dimension 1>,cost:<dimension 2>,...,cost:<dimension N>`

See the header semantics sections for more detail.

Values need not be quoted, as none of the values in the file may contain CRLF or quote characters.

The columns have the following semantics.

### `timestamp`

An ISO 8601 Datetime string. Specifies the **ending** of the covered time span specified in granularity. Timestamps up to two years in the past are accepted, future times are not.

### `granularity`

A string of value `HOURLY` or `DAILY`. Specifies the time span in which the reported usage occurred. When combined with the timestamp, allows for a mix of aggregations when reporting usage data.

### `usage`

The integer amount of consumption in the given timespan, in units specified in the telemetry stream name. This must be a positive value; rows with usage less than or equal to 0 will be skipped.

Example: usage rows in the bytes-stored-for-user stream represent bytes.

### `principal`

Value is optional. A customer ID, tenant name, or product name, as appropriate for the telemetry-stream.

Examples:

* `<customer-user-id>` (for telemetry-stream bytes-stored-for-user)
* `CASB` (for telemetry-stream cpu-ms-for-product)

These values will be viewable in the CloudZero interface when using a Dimension or dashboard created to display the telemetry stream. Its usage maps to the `element_name` field in the CloudZero Allocation API.

### `cost:<dimension N>`

One or more columns containing the dimension key(s) used in the filter object of a CloudZero telemetry API request. The values of this column shall be the value of the dimension filter. 

Each CloudZero telemetry stream has a fixed set of dimension keys associated with it. For an example stream named `cpu-ms-for-document-scan`, the dimension keys might specify the Kubernetes cluster and region. Those keys should appear as `cost:` columns. The values in those columns should be the values of the dimensions where usage occurred. See the example below.

**Note:** The naming of these columns must exactly match CloudZero’s API name for the dimension keys. These API names appear as the `partition=` parameter in CZ explorer URLs, and may differ from the friendly presentation in UI elements. Many built-in CloudZero dimension names may be used directly, however, dimensions created in the CostFormation file must be prefixed with `custom:`, leading to header names like `cost:custom:Account w/Allocation`, which is clumsy for humans but easy for computers.

Multiple row values for these dimensions may be specified using `|` characters as a separator. Usage which occurred in multiple regions, for example, may be represented in the cost:region column as the value  `us-east-1|us-west-2|us-west-1`.

Empty values in cost: columns are not permitted and such rows will be ignored. Costs which don’t apply to a given dimension must be submitted as a separate telemetry stream file without that `cost:` column.

## Example File Contents

```csv
timestamp,granularity,usage,principal,cost:k8s_cluster,cost:region
2024-02-13 00:05:00Z,HOURLY,188,oepzNc49ng,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,306,WB1Ied8QhH,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,360,hHqtizTu4R,document,us-east-1|us-west-1
2024-02-13 00:05:00Z,HOURLY,215,5CBHb05HoG,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,433,DKEX4QE3Gk,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,79,kjO4uEHJ4U,document,us-east-1
2024-02-13 00:05:00Z,HOURLY,106,No9IKytCo3,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,460,ldXijV8imQ,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,273,DKcsCjozKU,document,us-east-1
2024-02-13 00:05:00Z,HOURLY,174,9654681690,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,244,1321512927,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,378,8645919391,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,68,72955105569,document,us-west-1
2024-02-13 00:05:00Z,HOURLY,2,799700312489,document,us-west-1
```

## Principal Name Mappings Files

A file may be provided for each named telemetry stream containing a map from the value in the telemetry `principal` column to another arbitrary string. The purpose of this file is to allow reporting telemetry data separately from any required customer ID/Name lookups. Some systems store this data in very different places, so with this pattern the telemetry and names may be reported separately and joined at the time of reporting to CloudZero.

The mappings file shall be placed alongside the telemetry CSV file in S3, and named like

`principal-map-<telemetry-stream-name>.csv`

Following the examples above, two principal maps may be provided:

`principal-map-cpu-ms-for-document-scan.csv`
`principal-map-bytes-stored-for-user.csv`

If this file is present alongside the telemetry CSV, it will be used to look up the principal value in the telemetry file, and then use associated name in the map when reporting data to CloudZero.

The format of the principal map shall be as follows:

```csv
principal,principal_name
oepzNc49ng,customer_name_one
kjO4uEHJ4U,customer_name_two
```

If no associated row in the principal map is found for a row in the telemetry file, the principal value in the telemetry file will be used directly.

The mappings file will be loaded at the start of execution and used for the duration. There is no versioning on the file, and it may be updated at any desired cadence.

TODO: Merge these  sections

## Principal Maps

Sometimes, the CSV format's `principal` column must be populated by a tool which doesn't have access to the human-readable names that would work best there. For example, a tool handling customer requests might have the usage data but only see customer GUIDs, while another system handles the association of those GUIDs to friendly names.

This tool permits the joining of the data and the names by use of a simple CSV called a principal map.

When processing a CSV file, an associated principal map is also consulted to see if any rows have matches. If a match is found, the `principal_name` is used instead as the `element_name` for that record in CloudZero.

For an example telemetry CSV file containing the following rows:

```csv
timestamp,granularity,telemetry-stream,region,usage,principal
2024-03-31 14:00:00Z,DAILY,finops-test-stream,us-west-1,833971,62a1b8151dee4543bc85b0d263c3cad2
2024-03-31 14:00:00Z,DAILY,finops-test-stream,us-west-1,193809,1de7db7354644869a80ae59917a7d0a8
2024-03-31 14:00:00Z,DAILY,finops-test-stream,us-west-1,127628,16d1de8bc96e435a8d4fc957f7af4850
2024-03-31 14:00:00Z,DAILY,finops-test-stream,us-west-1,117118,92b5cbfde0ed4d2dbfebbb2a3c3a4979
```

A pincipal map named `principal-map-finops-test-stream.csv` will be consulted. The contents of that files could be as follows:

```csv
principal,principal_name
1de7db7354644869a80ae59917a7d0a8,alice
92b5cbfde0ed4d2dbfebbb2a3c3a4979,bob
16d1de8bc96e435a8d4fc957f7af4850,eve
```

When reporting the data to CloudZero, the principal values will be matched between the two files. The data will be reported as if the original CSV contained the following:

```csv
timestamp,granularity,telemetry-stream,region,usage,principal
2024-03-31 14:00:00Z,DAILY,finops-test-stream,us-west-1,833971,62a1b8151dee4543bc85b0d263c3cad2
2024-03-31 14:00:00Z,DAILY,finops-test-stream,us-west-1,193809,alice
2024-03-31 14:00:00Z,DAILY,finops-test-stream,us-west-1,127628,eve
2024-03-31 14:00:00Z,DAILY,finops-test-stream,us-west-1,117118,bob
```

Notice that the row missing an entry in the principal maps is unchanged.

### Usage in CLI

You may pass a principal map via the `--principal-mappings-file` argument when used with `--csv-file`.

### Usage in Lambda

When searching S3 for CSV files, the pairing of map to CSV is performed by using the telemetry stream name. The method is as follows:

1. All files in the bucket with names like `principal-map-(.*).csv` are identified.
1. The string in capture group 1 is treated as the telemetry stream name that the principal mapping is for.
1. Any records in CSV files which have a principal matching a row in that mapping will use the associated principal_name.

Example:

A file in the S3 bucket `customer-cpu-ms-2024-03-21-00-00-00Z.csv.gz` has rows with `telemetry-stream` value `cust-ondie-time`.

Also present in the bucket is a file named `principal-map-cust-ondie-time.csv`. This file will be used to map the principal names.

Any rows in the CSV which contain a principal not found in the map will be passed through to CloudZero as-is.

Principal maps are not versioned and may be updated at any cadence.
