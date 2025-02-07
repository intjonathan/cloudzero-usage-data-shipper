import pandas as pd

class BaseUnitAllocationCsv:
    
    df = None
    stream_name = None
    file_name = None
    principal_map = None

    def streamName(self) -> str:
        return self.stream_name
    
    def fileName(self) -> str:
        return self.file_name
    
    def rows(self) -> list:
        return self.df.iterrows()
    
    def headers(self) -> list:
        return self.df.columns
    
    def setPrincipalMap(self, principalMapFile: str) -> bool:
        self.principal_map = pd.read_csv(principalMapFile)
        return True

