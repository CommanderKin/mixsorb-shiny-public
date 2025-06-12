from shiny import render, reactive, ui, module
from ui_main import results_panel_ui

import pandas as pd
import numpy as np

import shortuuid # to create unique ids of the tabs

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import db_access as dba

def server(input, output, session):
    print("Server started")

    # global server variables 
    status_msg = reactive.Value("Waiting for input...") # status message 
    kusto_client = reactive.Value() # reactive value to store databese client
    experiments_list_df = reactive.Value(pd.DataFrame([])) # data frame with the list of experiments pulled from the DB
    results_tabs_dict = reactive.Value({})
    custom_trigger_value = reactive.Value(0)

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
            new_tab_id = shortuuid.uuid()
            exp_name = input.select_exp()
            new_tab = results_panel_ui(new_tab_id,exp_name)
            open_tabs = results_tabs_dict.get().copy() 
            open_tabs.update({new_tab_id:new_tab})
            assert isinstance(open_tabs,dict), "Something is wrong - updated tabs is not a dict"
            results_tabs_dict.set(open_tabs) # update the list that stores the open tabs objects 
            client = kusto_client.get()
            results_panel_server(new_tab_id,client,exp_name,results_tabs_dict,new_tab_id,custom_trigger_value)
            custom_trigger_value.set(custom_trigger_value.get() +1) # update the value to trigger a downstream function
            print(f"Generated new tab name: {exp_name}: id: {new_tab_id}")
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
            '| where baseFileName contains "' + str(input.search_field()) + '" | summarize ts = max(fileCreatedUtc) by baseFileName' + \
            '| sort by ts desc | limit ' + str(np.clip(input.n_exp_field(),1,30))
        print(query_text)
        return query_text
    

    def clean_response_df(df:pd.DataFrame):
        try:
            if input.show_seq_checkbox():
                df.columns = ["File name", "Date/time created"]
                df["Date/time created"] = df["Date/time created"].apply(lambda x : x.strftime('%x %X')) # 
            else:
                df.columns = ["Experiment name","Date/time created"]
                df["Date/time created"] = df["Date/time created"].apply(lambda x : x.strftime('%x %X'))
            return df
        except Exception as e:
            print(f"Error cleaning df: {e}")

    @output
    @render.ui
    def main_ui():
        panels_dict = results_tabs_dict.get()
        assert isinstance(panels_dict, dict), f"panels_dict is not a dict: {panels_dict}"
        panels = list(panels_dict.values())
        assert isinstance(panels, list), f"panels is not a list: {panels}"
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
                        ui.column(3, ui.input_text("search_field","File name contains")),
                        ui.column(2, ui.input_checkbox("show_seq_checkbox","Show individual sequences?")),
                        ui.column(1, ui.input_action_button("run_query_button", "Search", class_="btn btn-primary", disabled=True))
                        )
                ),ui.card(
                    ui.row(
                        ui.column(3,ui.input_select("select_exp","Choose an experiment to process",choices=["Waiting..."])),
                        ui.column(1, ui.input_action_button("process_button", "Process", class_="btn btn-primary", disabled=True))
                    )
                ),
                ui.card(ui.output_data_frame("exp_list_table")),
            ),
            *[x for x in panels],
            id = "main_ui_id"
        )
    
    # Reset the ui elements after redrawing the ui upon adding a new tab - runs every time the results_tabs_dict is changed (opening or closing the new tabs)
    @reactive.Effect 
    def reset_reactive_elements():
        dummy = custom_trigger_value.get() # access the trigger value. This "ties" this function to this value and forces it io run every time it changes
        if (len(experiments_list_df.get()) > 0 ): # Make sure it only runs when the experiments list is not empty
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
def results_panel_server(input,output,session, client, exp_name, open_tabs_dict, custom_id, trigger_value):
    query_text = "| where fileName == '" + exp_name + ".xml' | limit 100"
    response_df = dba.run_query(client, query_text)
    assert isinstance(response_df,pd.DataFrame)
    # Preliminary clean - will need to make it muich smarter
    # response_df.dropna(subset=['TCD_VolumeFraction'], axis="index", inplace=True)

    @reactive.Effect
    @reactive.event(input.close_tab_button)
    def on_close_tab():
        open_tabs = dict(open_tabs_dict.get()) # create a copy - otherwise it will not register that update of reactive value
        assert isinstance(open_tabs,dict), f"On_close_tab: open_tabs is not a dict: {open_tabs}" 
        open_tabs.pop(custom_id)
        #assert isinstance(updated_tabs,dict), f"On_close_tab: updated_tabs is not a dict: {updated_tabs}" 
        open_tabs_dict.set(open_tabs)
        trigger_value.set(trigger_value.get()-1)  # update the value to trigger a downstream function

    @output
    @render.text
    def test_msg():
        return exp_name
    
    @output
    @render.plot(alt = "CO2 vs time")
    def CO2_vs_time_plot():  
        time = [float(x) if x != "" else 0 for x in response_df["rel_Time_s"]]
        CO2 = [float(x) if x != "" else 0 for x in response_df["TCD_VolumeFraction"]]

        fig, ax = plt.subplots()
        ax.plot(time, CO2)
        ax.set_title("CO2 vs time")
        ax.set_xlabel("Relative time, s")
        ax.set_ylabel("CO2, ppm")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5)) # limit number of tick labels
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
        return fig








    