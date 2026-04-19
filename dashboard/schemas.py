from pydantic import BaseModel, AwareDatetime, ConfigDict
from ipaddress import IPv4Address

class CurrentProcessesSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)
    process_id : int
    database_id:int
    database_name : str
    username:str
    application_name:str
    client_address: IPv4Address|None
    connection_start_time : AwareDatetime
    query_start_time: AwareDatetime
    state_change_time: AwareDatetime
    query_id: int
    query:str

class TableSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    table_id: int
    schema_name: str
    table_name:str
    count_sequential_scan:int 
    last_sequential_scan: AwareDatetime | None

class IndexSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    table_id: int
    index_id: int
    schema_name: str
    table_name: str
    index_name: str
    count_scans: int
    last_scan_time: AwareDatetime | None






