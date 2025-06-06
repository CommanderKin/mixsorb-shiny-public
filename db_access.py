#DB libs
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.helpers import dataframe_from_result_table

### sample query:
# query_get_10_last = "| summarize ts = take_any(fileImportUtc) by fileName | sort by ts desc | limit 10"

    # DB Configuration ===
cluster = "https://sc-iot-dev-adx.northeurope.kusto.windows.net"
database = "skytree-cloud-rnd"
table = "MixSorbBronze"

def connect_to_db():
    # === Connect to ADX ===
    try:
        kcsb = KustoConnectionStringBuilder.with_interactive_login(cluster)
        # kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(cluster) # needs CLI connection
        # kcsb = KustoConnectionStringBuilder.with_aad_device_authentication(cluster) # Asks for a code every time
        client = KustoClient(kcsb)
        client.execute(database,f"{table} | summarize ts = max(fileCreatedUtc) by fileName | sort by ts desc | limit 10") # Run an empty query - otherwise it willforce me to log in on the first time I run an actual query. 
        print("Connected to DB")
        return client
    except Exception as e:
        print(f"Couldn't connect to DB: {e}")

def run_query(client, query_text):
    try: 
        query = f"{table} " + query_text
        response = client.execute(database, query)
        response_df = dataframe_from_result_table(response.primary_results[0])
        # print(response_df)
        return response_df
    except Exception as e:
        print(f"Query failed: {e}")

## TESTING 

# query_get_10_last = "| summarize ts = take_any(fileImportUtc) by fileName | sort by ts desc | limit 10"
# test_query_2 = "| where rel_time_s != \"0\" | take 10"

# client = connect_to_db()
# response = run_query(client,query_get_10_last)
# response_df = dataframe_from_result_table(response.primary_results[0])

# print(response_df)