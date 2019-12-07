'''
This is the code I ran to create a new dataset and table to store stock data.

Useful resources:
https://stackoverflow.com/questions/51605921/bigquery-create-an-external-table-in-python
Creating a table with API

https://stackoverflow.com/questions/36314797/write-a-pandas-dataframe-to-google-cloud-storage-or-bigquery
test if exists, if not, create

https://cloud.google.com/docs/authentication/getting-started
How to set up authentication to connect to your Google Cloud project with python from your computer

https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types
The data types available in bigquery
'''
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


PROJECT_ID = ''
DATASET = ''
TABLENAME = ''


def dataset_exists(client, dataset_reference):
    """Return if a dataset exists.
    From: https://cloud.google.com/bigquery/docs/python-client-migration#dataset-exists

    Args:
        client (google.cloud.bigquery.client.Client):
            A client to connect to the BigQuery API.
        dataset_reference (google.cloud.bigquery.dataset.DatasetReference):
            A reference to the dataset to look for.

    Returns:
        bool: ``True`` if the dataset exists, ``False`` otherwise.
    """
    try:
        client.get_dataset(dataset_reference)
        return True
    except NotFound:
        return False


def table_exists(client, table_reference):
    """Return if a table exists.
    From: https://cloud.google.com/bigquery/docs/python-client-migration#dataset-exists

    Args:
        client (google.cloud.bigquery.client.Client):
            A client to connect to the BigQuery API.
        table_reference (google.cloud.bigquery.table.TableReference):
            A reference to the table to look for.

    Returns:
        bool: ``True`` if the table exists, ``False`` otherwise.
    """
    try:
        client.get_table(table_reference)
        return True
    except NotFound:
        return False


client = bigquery.Client()
dataset_ref = client.dataset(DATASET)

if not dataset_exists(client, dataset_ref):
    client.create_dataset(DATASET)

table_ref = bigquery.TableReference(dataset_ref, TABLENAME)

if not table_exists(client, table_ref):
    table_path = PROJECT_ID+'.'+DATASET+'.'+TABLENAME
    schemafield_col1 = bigquery.schema.SchemaField("etf","STRING")
    schemafield_col2 = bigquery.schema.SchemaField("pull_timestamp","DATETIME")
    schemafield_col3 = bigquery.schema.SchemaField("return","FLOAT64")
    schema = [schemafield_col1,schemafield_col2,schemafield_col3]
    table = bigquery.Table(table_path, schema)
    table = client.create_table(table)
