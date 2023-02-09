import os
import datetime
import pandas as pd
from io import BytesIO
from google.cloud import storage

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'ServiceKey_GCS.json'


class GCS:
    def __init__(self, bucket_name: str = 'sm_data_bucket'):
        self.bucket_name = bucket_name
        self.preprocessing()
    
    def preprocessing(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.get_bucket(self.bucket_name)        

    # define function that uploads a file from the bucket
    def upload_file(self, source_file_name, destination_file_name): 
        blob = self.bucket.blob(destination_file_name)
        blob.upload_from_filename(source_file_name)

    # define function that downloads a file from the bucket
    def download_file(self, file_name, destination_file_name): 
        blob = self.bucket.blob(file_name)
        blob.download_to_filename(destination_file_name)

    def get_file_url(self, file_name, expire_in=datetime.datetime.today() + datetime.timedelta(1)): 
        url = self.bucket.blob(file_name).generate_signed_url(expire_in)
        return url

    # define function that list files in the bucket
    def list_files(self): 
        file_list = self.storage_client.list_blobs(self.bucket_name)
        file_list = [file.name for file in file_list]
        return file_list
    
    # read parquet
    def read_parquet(self, file_name, **kwargs)->pd.DataFrame:
        blob = self.bucket.blob(file_name)
        df = pd.read_parquet(BytesIO(blob.download_as_bytes()), **kwargs)
        return df

    # read csv file
    def read_csv(self, file_name, **kwargs)->pd.DataFrame:
        blob = self.bucket.blob(file_name)
        df = pd.read_csv(BytesIO(blob.download_as_bytes()), **kwargs)
        return df

    # read excel file
    def read_excel(self, file_name, **kwargs)->pd.DataFrame:
        blob = self.bucket.blob(file_name)
        df = pd.read_excel(BytesIO(blob.download_as_bytes()), **kwargs)
        return df

    # to parquet file
    def to_parquet(self, df: pd.DataFrame, file_name: str, **kwargs)->pd.DataFrame:
        data = BytesIO()
        df.to_parquet(data, **kwargs)
        data.seek(0)
        blob = self.bucket.blob(file_name)
        blob.upload_from_file(data)

    # to csv file
    def to_csv(self, df: pd.DataFrame, file_name: str, **kwargs)->pd.DataFrame:
        data = BytesIO()
        df.to_csv(data, **kwargs)
        data.seek(0)
        blob = self.bucket.blob(file_name)
        blob.upload_from_file(data)

    # to csv file
    def to_excel(self, df: pd.DataFrame, file_name: str, **kwargs)->pd.DataFrame:
        data = BytesIO()
        df.to_excel(data, **kwargs)
        data.seek(0)
        blob = self.bucket.blob(file_name)
        blob.upload_from_file(data)