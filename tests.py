#DB libs
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.helpers import dataframe_from_result_table

import seaborn as sns
import matplotlib.pyplot as plt

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

def build_query(search_field,num_exp):
    query_text = '| extend baseFileName = extract(@"^(.*?)(?:_\d{3})?\.xml$", 1, fileName)' + \
    '| where baseFileName contains "' + search_field + '" | summarize ts = max(fileCreatedUtc) by baseFileName' + \
    '| sort by ts desc | limit ' + str(num_exp)

    return query_text

test_query = build_query("",10)

client = connect_to_db()

# test_df = run_query(client,test_query)

data_df = run_query(client,"| where fileName == '250522_CO34_132.xml' ")

  # Some boilerplate to initialise things
sns.set_theme(style="whitegrid")
sns.lineplot(data=data_df, x="rel_Time_s", y="TCD_VolumeFraction")
plt.show()


# print(test_df)