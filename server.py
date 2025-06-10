from shiny import render, reactive, ui, module
from ui_main import results_panel

import pandas as pd
import numpy as np
import db_access as dba

def server(input, output, session):
    print("Server started")

    # global variables 
    status_msg = reactive.Value("Waiting for input...") # status message 
    kusto_client = reactive.Value() # reactive value to store databese client
    experiments_list_df = reactive.Value(pd.DataFrame([])) # data frame with the list of experiments pulled from the DB
    results_tabs = reactive.Value([]) # reacive value that stores all the currently present tabs with exp results

    #Presss CONNECT TO DB button
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

    # Press SEARCH button
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
            # update the drop-down menu
            exp_list =[str(x) for x in response_df.iloc[:,0]]
            ui.update_select(
                "select_exp",
                label = "Choose an experiment to process",
                choices = exp_list,
                selected = exp_list[0]
            )
            session.send_input_message("process_button", {"disabled": False})
            print(experiments_list_df())
            status_msg.set(f"Query completed")
        except Exception as e:
            print(f"Query failed: {e}")
            status_msg.set(f"Query failed: {e}")

    # Press PROCESS button
    @reactive.Effect
    @reactive.event(input.process_button)
    def on_process():
        try:
            new_tab_id = "results_tab_"+ str(len(results_tabs.get()) + 1)
            new_tab_number = new_tab_id,len(results_tabs.get()) + 1
            new_tab_content = input.select_exp()
            updated_tabs = results_tabs.get() + [results_panel(new_tab_id,new_tab_number,new_tab_content)]
            results_tabs.set(updated_tabs)
            reset_reactive_elements()
        except Exception as e:
            status_msg.set(f"Tab creation failed: {e}")

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

    @output
    @render.ui
    def main_ui():
        return ui.navset_tab(
            ui.nav_panel(
                "Main",
                ui.h3("Get list of experiments from the database"),
                ui.card(     
                    ui.row(
                        ui.column(2, ui.input_action_button("db_connect_button", "Connect to DB", class_="btn btn-primary")),
                        ui.column(2, ui.div("Status: ", class_="text-end")),
                        ui.column(4, ui.output_text_verbatim("status"))
                        ),
                ),
                ui.card(
                    ui.row(
                        ui.column(1, ui.input_numeric("n_exp_field","N exp:",10, min = 1, max = 30)),
                        ui.column(3, ui.input_text("search_field","Finelname contains")),
                        ui.column(2, ui.input_checkbox("show_seq_checkbox","Show individual sequences?")),
                        ui.column(1, ui.input_action_button("run_query_button", "Search", class_="btn btn-primary", disabled=True))
                        )
                ),
                ui.row(
                    ui.column(3,ui.input_select("select_exp","Choose an experiment to process",choices=["Waiting..."])),
                    ui.column(1, ui.input_action_button("process_button", "Process", class_="btn btn-primary", disabled=True))
                ),
                ui.card(ui.output_data_frame("exp_list_table")),
            ),
            *[panel for panel in results_tabs.get()],
            id = "main_ui_id"
        )
    
    # Reset the ui elements after redrawing the ui upon adding a new tab
    def reset_reactive_elements():
        session.send_input_message("process_button", {"disabled": False})
        session.send_input_message("run_query_button", {"disabled": False})
        exp_list =[str(x) for x in experiments_list_df.get().iloc[:,0]]
        ui.update_select(
            "select_exp",
            label = "Choose an experiment to process",
            choices = exp_list,
            selected = exp_list[0]
        )

@module.server
def row_server(input, output, session):
    @output
    @render.text
    def text_out():
        pass

