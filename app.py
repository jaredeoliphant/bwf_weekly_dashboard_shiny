from shiny import App, ui, reactive, render
from dotenv import load_dotenv
import os
import pandas as pd
from arcgis.gis import GIS

# to deploy
# rsconnect deploy shiny C:\Users\jared\Documents\brightwater\shinyapps\reporting_dashboard --name brightwater --title SWEreport

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

gis = GIS(
    "https://bwf.maps.arcgis.com/",
    username=os.getenv("UNAME"),
    password=os.getenv("PASSWORD"),
)

tables = {
    "akrofufu1": gis.content.get(os.getenv("AKROFUFU1")).tables[0],
    "akrofufu2": gis.content.get(os.getenv("AKROFUFU2")).tables[0],
    "abomosu1": gis.content.get(os.getenv("ABOMOSU1")).tables[0],
    "abomosu2": gis.content.get(os.getenv("ABOMOSU2")).tables[0],
    "asamama": gis.content.get(os.getenv("ASAMAMA")).tables[0],
    "asunafo": gis.content.get(os.getenv("ASUNAFO")).tables[0],
    "ekorso": gis.content.get(os.getenv("EKORSO")).tables[0],
    "akakom": gis.content.get(os.getenv("AKAKOM")).tables[0],
    "sankubenase": gis.content.get(os.getenv("SANKUBENASE")).tables[0],
}


community_choices = dict(
    zip(
        [
            "GH2402 - Akrofufu 1",
            "GH2402 - Akrofufu 2",
            "GH2302 - Abomosu 1",
            "GH2302 - Abomosu 2",
            "GH2301 - Asamama",
            "GH2203 - Asunafo",
            "GH2202 - Ekorso",
            "GH2201 - Akakom",
            "GH2101 - Sankubenase",
        ],
        list(tables.keys()),
    )
)


def get_raw_data(village, as_sdf=True):
    if tables.get(village):
        return tables[village].query().sdf


# UI
app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "projects",
                "Select Project to Display",
                choices=list(community_choices.keys()),
                multiple=False,
            ),
            ui.input_dark_mode(id="mode"),
        ),
        ui.navset_tab(
            ui.nav_panel(
                "Last 5 Weeks",
                ui.output_data_frame("dataframe_last5"),
            ),
            ui.nav_panel(
                "Cummulative Numbers",
                ui.output_data_frame("dataframe_cummalative"),
            ),
        ),
    ),
    title="Bright Water Reporting Dashboard",
    id="page",
)


# Server
def server(input, output, session):

    @reactive.effect
    @reactive.event(input.make_dark)
    def _():
        ui.update_dark_mode("dark")

    @reactive.effect
    @reactive.event(input.make_light)
    def _():
        ui.update_dark_mode("light")

    @render.data_frame
    def dataframe_last5():
        return (
            get_raw_data(community_choices[input.projects()])
            .query('Last5Weeks == "1"')
            .assign(SWE=lambda df_: df_.BrightWaterID + " - " + df_.Namebwe)
            .rename(columns={"InitialHouseholdSurveys":"Initial Household Surveys",
                             "FollowUpHouseholdSurveys":"Follow Up Household Surveys",
                             "HHoldWaterTests":"Household Water Tests",
                             'CommWaterTests':"Community Water Tests",
                             'HHoldTeachingVisits':"Household Teaching Visits",})
            .loc[
                :,
                [
                    "SWE",
                    "Community",
                    "Week",
                    "Initial Household Surveys",
                    "Follow Up Household Surveys",
                    "Household Water Tests",
                    "Community Water Tests",
                    "Household Teaching Visits",
                ],
            ]
        )

    @render.data_frame
    def dataframe_cummalative():
        return (
            get_raw_data(community_choices[input.projects()])
            .groupby(["BrightWaterID", "Namebwe"])
            .agg(
                {
                    "InitialHouseholdSurveys": "sum",
                    "FollowUpHouseholdSurveys": "sum",
                    "HHoldWaterTests": "sum",
                    "CommWaterTests": "sum",
                    "HHoldTeachingVisits": "sum",
                }
            )
            .reset_index()
            .assign(SWE=lambda df_: df_.BrightWaterID + " - " + df_.Namebwe)
            .rename(columns={"InitialHouseholdSurveys":"Initial Household Surveys",
                             "FollowUpHouseholdSurveys":"Follow Up Household Surveys",
                             "HHoldWaterTests":"Household Water Tests",
                             'CommWaterTests':"Community Water Tests",
                             'HHoldTeachingVisits':"Household Teaching Visits",})
            .loc[
                :,
                [
                    "SWE",
                    "Initial Household Surveys",
                    "Follow Up Household Surveys",
                    "Household Water Tests",
                    "Community Water Tests",
                    "Household Teaching Visits",
                ],
            ]
        )


app = App(app_ui, server)
