from shiny import ui, module

app_ui = ui.page_fluid(
    ui.output_ui("main_ui")
)


@module.ui
def results_panel(panel_number,exp_name):
    tab_title = f"New tab {panel_number}"
    return ui.nav_panel(
        tab_title,
        ui.p(f"We will have the processing results of the {exp_name} here soon"),
    )