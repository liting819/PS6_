from shiny import App, render, ui, reactive
import pandas as pd
import matplotlib.pyplot as plt
import json
import geopandas as gpd
from shapely.geometry import shape
import numpy as np

app_ui = ui.page_fluid(
    ui.input_select(id='types', label='Choose a Type_Subtype:', choices=[]),  
    ui.input_slider("obs", "Choose a time in a day:", min=1, max=24, value=12, post = ":00"),
    ui.output_plot("ts"),
    ui.output_table("subsetted_data_table")
)

def server(input, output, session):
    
    # Load the full dataset
    @reactive.calc
    def full_data():
        df = pd.read_csv("/Users/tsaili-ting/Uchicago/Year2/Y2Fall/Python2/ps6/top_alerts_map_byhour/top_alerts_map_byhour.csv")
        return df
    

    @reactive.effect
    def _():
        types = full_data()['subtype'].dropna()  
        types_list = sorted(types.unique().tolist()) 
        ui.update_select("types", choices=types_list)


    @reactive.calc
    def subsetted_data():
        df = full_data()

        selected_type = input.types.get() 

        top_alerts = df.groupby(["hour","longitude","latitude","longitude_latitude","subtype"]).agg(count = ("longitude_latitude","count")).reset_index()
  
        top_alerts_df = top_alerts[top_alerts['subtype'].str.strip() == selected_type]
       
        slider_hour = input.obs.get()
        
        selected_hour = f"{slider_hour:02d}:00"

        top_alerts_df_byhour = top_alerts_df.loc[top_alerts_df["hour"]==selected_hour].sort_values("count",ascending=False).head(10)

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

        gdf.boundary.plot(ax=ax, color='lightgray', linewidth=1)

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


    @render.table()
    def subsetted_data_table():
        df = subsetted_data()
        return df

app = App(app_ui, server)