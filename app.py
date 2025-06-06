import seaborn as sns
import pandas as pd

import db_access as dba

from shiny import App, render, ui, reactive

app_ui = ui.page_fluid(
    ui.h2("Connect To DB"),
    ui.input_action_button("db_connect_button", "Connect to DB"),
    ui.output_text_verbatim("status"),
    ui.input_numeric("n_exp_field","N last experiments",10,min = 1, max = 30),
    ui.input_action_button("run_query_button", "Show N last"),
    ui.output_data_frame("exp_list_table")
)


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
        status_msg.set("Running query")
        print("Running query")
        query_text = "| summarize ts = take_any(fileCreatedUtc) by fileName | sort by ts desc | limit " + str(input.n_exp_field())
        client = kusto_client()
        response_df = dba.run_query(client, query_text)
        assert isinstance(response_df, pd.DataFrame), "Something went wrong, query data is not a DF"
        experiments_list_df.set(response_df)
        print(experiments_list_df())

    @output
    @render.text
    def status():
        return status_msg()
    
    @output
    @render.data_frame
    def exp_list_table():
        return experiments_list_df()

app = App(app_ui, server)
