from pydantic_settings import BaseSettings
from async_lru import alru_cache
from pydantic import Field, SecretStr
from dataclasses import dataclass
from pathlib import Path


class Settings(BaseSettings):
    """
    Setting layer is to read the environmentail variable directly with the help of BaseSetting.

    Class will inheriting BaseSetting will detect and read env varaiable automatically no need and load_env.
   
     Here the operation:
        functionalities python attribute name read the value befor, it will validating their expected type 'str' and 
        required Fiel(...) is mandatory!. alias read the 'DB_TYPE' varaible value from environment.
    
    @dataclass  decorator will automatically create the __init__ constructor.
        forzen=True : immutable // this provide secerts from accidental runtime changes.
    
    """
    db_type       : str       = Field(..., alias="DB_TYPE")
    db_host       : str       = Field(..., alias="DB_HOST")
    db_port       : str       = Field(..., alias="DB_PORT")
    db_user       : str       = Field(..., alias="DB_USERNAME")
    db_pass       : SecretStr = Field(..., alias="DB_PASSWORD")
    db_schema     : str       = Field(..., alias="DB_SCHEMA")
    db_name       : str       = Field(..., alias="DB_NAME")
    min_connection: int       = 15
    max_connection: int       = 20

    class Config:
        env_file =".env"




#Dataclass Constructor
@dataclass(frozen=True)
class All_Credentials:
    """
    @dataclass  decorator will automatically create the __init__ constructor.
    forzen=True : immutable // this provide secerts from accidental runtime changes.
    
    """
    db_env: Settings



@alru_cache()
async def access_env() -> All_Credentials:
    return All_Credentials(db_env=Settings(),)

#TRY-2
@alru_cache()
async def access_env():
    return Settings()

