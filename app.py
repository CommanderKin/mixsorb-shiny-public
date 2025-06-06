import seaborn as sns

import db_access as dba

# Import data from shared.py
from shared import df

from shiny import App, render, ui, reactive

app_ui = ui.page_fluid(
    ui.h2("Connect To DB"),
    ui.input_action_button("db_connect", "Connect to DB"),
    ui.output_text_verbatim("status")
)


def server(input, output, session):
    print("Server started YAAAQAAYYYY ")
    status_msg = reactive.Value("Waiting for input...")

    @reactive.Effect
    @reactive.event(input.db_connect)
    def on_connect_to_db():
        try: 
            print("Connecting to DB")
            status_msg.set("Connecting to DB")
            client = dba.connect_to_db()
            status_msg.set("DB connect successful")
        except Exception as e:
            print(f"DB connection failed: {e}")
            status_msg.set(f"Error: {e}")

    @output
    @render.text
    def status():
        return status_msg()

app = App(app_ui, server)
