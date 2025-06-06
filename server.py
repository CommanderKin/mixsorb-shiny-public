from shiny import render, reactive

import pandas as pd
import numpy as np
import db_access as dba

def server(input, output, session):
    print("Server started")

    # global variables 
    status_msg = reactive.Value("Waiting for input...")
    kusto_client = reactive.Value()
    experiments_list_df = reactive.Value(pd.DataFrame([]))
    list_to_process = reactive.Value([])

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
            session.send_input_message("run_query_button", {"disabled": False}) # enable search button
        except Exception as e:
            print(f"DB connection failed: {e}")
            status_msg.set(f"Error: {e}")

    @reactive.Effect
    @reactive.event(input.run_query_button)
    def on_run_query():
        try: 
            status_msg.set("Running query")
            print("Running query")
            query_text = build_query()
            client = kusto_client()
            response_df = dba.run_query(client, query_text)
            assert isinstance(response_df, pd.DataFrame), "Something went wrong, query data is not a DF"
            response_df = clean_response_df(response_df)
            assert isinstance(response_df, pd.DataFrame), "Something went wrong, query data is not a DF"
            experiments_list_df.set(response_df)
            # update the dorop-down menu
            exp_list =[str(x) for x in response_df.iloc[:,0]]
            print(exp_list)
            session.send_input_message("select_exp",{ 
                "choices": [{"label":x, "value": x} for x in exp_list], ### DEBUG THIS: https://shiny.posit.co/py/api/core/ui.input_select.html
                "value": exp_list[0]
            })
            session.send_input_message("process_button", {"disabled": False})
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
        return render.DataGrid(experiments_list_df(), width = 1000)
    
    def build_query():
        if input.show_seq_checkbox():
            query_text = "| where fileName contains '" + str(input.search_field()) + \
                "' | summarize ts = max(fileCreatedUtc) by fileName | sort by ts desc | limit " + str(np.clip(input.n_exp_field(),1,30))
        else:
            query_text = '| extend baseFileName = extract(@"^(.*?)(?:_\d{3})?\.xml$", 1, fileName)' + \
            '| where baseFileName contains "' + str(input.search_field()) + '" | summarize ts = max(fileCreatedUtc), fileName = arg_max(fileCreatedUtc, fileName) by baseFileName' + \
            '| sort by ts desc | limit ' + str(np.clip(input.n_exp_field(),1,30))
        print(query_text)
        return query_text
    
    def clean_response_df(df:pd.DataFrame):
        try:
            if input.show_seq_checkbox():
                df.columns = ["File name", "Date/time created"]
            else:
                df.drop(columns = ['fileName'],inplace=True)
                df.columns = ["Experiment name","Date/time created","Sequence finlename??"]
            return df
        except Exception as e:
            print(f"Error cleaning df: {e}")



