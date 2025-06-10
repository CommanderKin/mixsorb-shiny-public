from shiny import ui, module

app_ui = ui.page_fluid(
    ui.output_ui("main_ui")
)


@module.ui
def results_panel_ui(exp_name):
    tab_title = exp_name
    return ui.nav_panel(
        tab_title,
        ui.p(f"We will have the processing results of the {exp_name} here soon"),
         ui.card(     
            ui.row(
                ui.column(4,ui.output_text_verbatim("test_msg")),
                ui.column(6,ui.output_plot("CO2_vs_time_plot")),
                ),
        ),
    )