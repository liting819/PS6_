from shiny import App, render, ui, reactive
import pandas as pd
import matplotlib.pyplot as plt
import json
import geopandas as gpd
from shapely.geometry import shape


# UI
app_ui = ui.page_fluid(
    ui.input_select(id='types', label='Choose a Type_Subtype:', choices=[]),  
    ui.input_slider("hour_range", "Choose a range of time in a day:", min=1, max=24, value=[6, 12], post=":00"),
    ui.output_plot("ts"),
    ui.output_table("subsetted_data_table")
)


# Server
def server(input, output, session):
    # Load the full dataset
    @reactive.calc
    def full_data():
        df = pd.read_csv("/Users/tsaili-ting/Uchicago/Year2/Y2Fall/Python2/ps6/top_alerts_map_byhour/top_alerts_map_byhour.csv")
        return df
    
    # Dynamically update dropdown options
    @reactive.effect
    def _():
        if not full_data().empty:
            types = full_data()['subtype'].dropna()
            types_list = sorted(types.unique().tolist())
            ui.update_select("types", choices=types_list)

    # Filter data based on input
    @reactive.calc
    def subsetted_data():
        df = full_data()
        selected_type = input.types.get()

        top_alerts = df.groupby(["hour", "longitude", "latitude", "longitude_latitude", "subtype"]).agg(
            count=("longitude_latitude", "count")
        ).reset_index()

        top_alerts_df = top_alerts[top_alerts['subtype'].str.strip() == selected_type]

        # Check hour range
        selected = input.hour_range()
        start, end = selected
        start_time = f"{start:02d}:00"
        end_time = f"{end:02d}:00"

        top_alerts_df_byhour = top_alerts_df[
            (top_alerts_df["hour"] >= start_time) & (top_alerts_df["hour"] <= end_time)
        ].sort_values("count", ascending=False).head(10)

        return top_alerts_df_byhour

    # Render plot
    @render.plot
    def ts():
        df = subsetted_data()
        file_path = ("/Users/tsaili-ting/Uchicago/Year2/Y2Fall/Python2/ps6/top_alerts_map/Boundaries - Neighborhoods.geojson") 
        with open(file_path) as f:
            chicago_geojson = json.load(f)
        geo_data = [shape(feature['geometry']) for feature in chicago_geojson["features"]]
        gdf = gpd.GeoDataFrame(geometry=geo_data)

        fig, ax = plt.subplots(figsize=(8, 6))

        # Plot Chicago boundary
        gdf.boundary.plot(ax=ax, color='lightgray', linewidth=1)

        # Plot points
        ax.scatter(
            df['longitude'], 
            df['latitude'], 
            s=df['count'],  
            c='red', alpha=0.5
        )

        ax.set_title(f"Top alerts by hour in - {input.types.get()}")
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_xlim(-87.77, -87.58) 
        ax.set_ylim(41.67, 41.98)

        return fig

    # Render table
    @render.table
    def subsetted_data_table():
        df = subsetted_data()
        return df


# App
app = App(app_ui, server)