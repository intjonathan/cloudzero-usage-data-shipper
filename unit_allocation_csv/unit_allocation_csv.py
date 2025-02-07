from datetime import datetime, timezone
import os
from posixpath import basename, splitext
import json
import re
import sys
import pandas as pd

from converted_cz_json_file import ConvertedCzJsonFile
from . import base_unit_allocation_csv

class UnitAllocationCsv(base_unit_allocation_csv.BaseUnitAllocationCsv):
    def __init__(self, csv_path):
        self.file_name = csv_path
        # match filename before first underscore
        # e.g. "unit-cost-telemetry_2021-06-01.csv" -> "unit-cost-telemetry"
        self.stream_name = re.match("(\S+)_", basename(splitext(csv_path)[0]))[1]
        self.df = pd.read_csv(csv_path)


    def setPrincipalMap(self, principalMapFile: str) -> bool:
        self.principal_map = pd.read_csv(principalMapFile)
        return True

    def toCzAllocationApiFormat(self,
                                destinationPath: str,
                                mungeTimestamps: bool = False) -> ConvertedCzJsonFile:

        if mungeTimestamps:
            print("Warning: CSV timestamps will be overridden with current UTC time.")
            self.df["timestamp"] = str(datetime.now(timezone.utc)).split(".")[0]+"Z"

        # Example CSV headers:
        # timestamp ,granularity, usage, principal, cost:custom:telemetry-target-dup-account, cost:region
        # Example output JSON object:
        # {
        #     "timestamp": re.sub(r'(\d\d)-(\d\d)-(\d\d)Z', r'\1:\2:\3Z', row['timestamp']),
        #     "granularity": row['granularity'],
        #     "filter": { "custom:telemetry-target-dup-account": ["8675309"], "region": ["us-east-1"] },
        #     "value": row['usage'],
        #     "element_name": row['principal']
        # }

        output_json = []

        filter_columns = [col for col in self.df.columns if col.startswith('cost:')]
        # remove the 'cost:' prefix
        # filter_columns = [col[5:] for col in filter_columns]

        for index, row in self.df.iterrows():
            if int(row['usage']) <= 0:
                # print(f"Skipping row with usage <= 0")
                continue

            filter_row = {}
            for col in filter_columns:
                # if row[col] is a string, split it by '|'
                if isinstance(row[col], str):
                    filter_row[col[5:]] = re.split("\|", row[col].strip())
                    skip_row = False
                # Otherwise, we can't use it so move on
                else:
                    print(f"{self.file_name}: Skipping row with invalid {col} filter value: {row[col]}")
                    skip_row = True

            if skip_row:
                continue

            if self.principal_map is not None:
                principal_name_series = self.principal_map.loc[self.principal_map['principal'] == row['principal']]
                if len(principal_name_series) > 0:
                    principal = principal_name_series['principal_name'].values[0]
                else:           
                    principal = row['principal'].strip()    
            else:
                principal = row['principal'].strip()

            row_dict = {
                "timestamp": re.sub(r'(\d\d)-(\d\d)-(\d\d)Z', r'\1:\2:\3Z', row['timestamp']),
                "granularity": row['granularity'].strip(),
                "filter": filter_row,
                "value": row['usage'],
                "element_name": principal
            }

            output_json.append(row_dict)

        # json.dump(output_json, sys.stdout, indent=4)
        output_file_path = os.path.join(destinationPath,
                                        os.path.splitext(os.path.basename(self.file_name))[0] + '.json')

        json.dump(output_json, open(output_file_path, "w"), indent=4)

        output_file = ConvertedCzJsonFile(self.stream_name, output_file_path)

        print(f"Converted {self.file_name} to files: {output_file}")
        return output_file
