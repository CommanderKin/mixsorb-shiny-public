from shiny import render, reactive

import pandas as pd
import db_access as dba

def server(input, output, session):
    print("Server started")
    status_msg = reactive.Value("Waiting for input...")
    kusto_client = reactive.Value()
    experiments_list_df = reactive.Value(pd.DataFrame([]))

    @reactive.Effect
    @reactive.event(input.db_connect_button)
    def on_connect_to_db():
        try: 
            print("Connecting to DB")
            status_msg.set("Connecting to DB")
            client = dba.connect_to_db()
            assert isinstance(client,dba.KustoClient),  "Client creation failed"
            kusto_client.set(client)
            status_msg.set("DB connect successful")
        except Exception as e:
            print(f"DB connection failed: {e}")
            status_msg.set(f"Error: {e}")

    @reactive.Effect
    @reactive.event(input.run_query_button)
    def on_run_query():
        try: 
            status_msg.set("Running query")
            print("Running query")
            query_text = "| summarize ts = take_any(fileCreatedUtc) by fileName | sort by ts desc | limit " + str(input.n_exp_field())
            client = kusto_client()
            response_df = dba.run_query(client, query_text)
            assert isinstance(response_df, pd.DataFrame), "Something went wrong, query data is not a DF"
            experiments_list_df.set(response_df)
            print(experiments_list_df())
            status_msg.set(f"Query completed")
        except Exception as e:
            print(f"Query failed: {e}")
            status_msg.set(f"Query failed: {e}")


    @output
    @render.text
    def status():
        return status_msg()
    
    @output
    @render.data_frame
    def exp_list_table():
        return render.DataGrid(experiments_list_df(), width = 800)
