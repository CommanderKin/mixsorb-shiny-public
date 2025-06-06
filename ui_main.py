from shiny import ui

app_ui = ui.page_fluid(
    ui.h2("Connect To DB"),
    ui.input_action_button("db_connect_button", "Connect to DB"),
    ui.output_text_verbatim("status"),
    ui.input_numeric("n_exp_field","N last experiments",10,min = 1, max = 30),
    ui.input_action_button("run_query_button", "Show N last"),
    ui.output_data_frame("exp_list_table")
)