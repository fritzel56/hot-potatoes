# Seed Data

## File Overview
| File | Description |
|------|-------------|
| insert_seed_data.py | Opens any csvs in this folder and writes them to Google BigQuery. |

In order to calculate 1 year total returns, you need a full years worth of data; however, at the time of writing, Yahoo would only provide ~99 days of history using the query method I was using. Instead I manually downloaded a full year's worth of data from Yahoo and then used this code to upload it. You would have to do this once per stock of interest. You should end up with two files per stock of interest (one for historical prices and one for dividends). The naming convention should be as follows: for price data: `VCN.TO.csv`, for dividend data: `VCN.TO.DIV.csv`.

In order to use this, you need to have two tables set in Google BigQuery.

The first is for price data and can be created as follows (for more info on setting up Google BigQuery see bigquery_setup in v2):

```python
if not table_exists(client, table_ref):
    table_path = PROJECT_ID+'.'+DATASET+'.'+TABLENAME
    schemafield_col1 = bigquery.schema.SchemaField("ticker","STRING")
    schemafield_col2 = bigquery.schema.SchemaField("snap_date","DATETIME")
    schemafield_col3 = bigquery.schema.SchemaField("open","FLOAT64")
    schemafield_col4 = bigquery.schema.SchemaField("high","FLOAT64")
    schemafield_col5 = bigquery.schema.SchemaField("low","FLOAT64")
    schemafield_col6 = bigquery.schema.SchemaField("close","FLOAT64")
    schemafield_col7 = bigquery.schema.SchemaField("close_adj","FLOAT64")
    schemafield_col8 = bigquery.schema.SchemaField("volume","INT64")
    schema = [schemafield_col1,schemafield_col2,schemafield_col3,schemafield_col4,schemafield_col5,schemafield_col6,schemafield_col7,schemafield_col8]
    table = bigquery.Table(table_path, schema)
    table = client.create_table(table)
```

The second is for dividend data and can be created as follows:

```python
if not table_exists(client, table_ref):
    table_path = PROJECT_ID+'.'+DATASET+'.'+TABLENAME
    schemafield_col1 = bigquery.schema.SchemaField("ticker","STRING")
    schemafield_col2 = bigquery.schema.SchemaField("snap_date","DATETIME")
    schemafield_col3 = bigquery.schema.SchemaField("amount","FLOAT64")
    schema = [schemafield_col1,schemafield_col2,schemafield_col3]
    table = bigquery.Table(table_path, schema)
    table = client.create_table(table)
```

To run `insert_seed_data.py`, you need to have the following environment variables set:

| Variable Name | Variable Definition |
|---------------|---------------------|
| PROJECT | Name of the Google Cloud project associated with the BigQuery datasets. |
| DATASET | Name of the BigQuery dataset associated with your tables. |
| PRICE_TABLENAME | Name of the table where the price data will be stored. |
| DIVIDEND_TABLENAME | Name of the table where the dividend data will be stored. |
