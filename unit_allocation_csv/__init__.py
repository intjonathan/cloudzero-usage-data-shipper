import pandas as pd
from .unit_allocation_csv import UnitAllocationCsv

def createUnitAllocationCsv(csv_path):
        df = pd.read_csv(csv_path)
        if any('cost:' in col for col in df.columns):
            return UnitAllocationCsv(csv_path)
        else:
            raise ValueError('Not a valid UnitAllocationCsv file')