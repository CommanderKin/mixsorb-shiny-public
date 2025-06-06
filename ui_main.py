from shiny import ui

app_ui = ui.page_fluid(
    ui.navset_tab(
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
        ui.nav_panel("Results", 
                    "Results will be here"
        )
    )
)