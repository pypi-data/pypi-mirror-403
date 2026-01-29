import folium
import geopandas as gpd
import pandas as pd
from .const import style_function

class ShowMaps:

    def __init__(self, block_shapes = None):
        
        self.gdf = block_shapes

    def read_shapefile(self, shapefile_path: str):
        # Read shapefile using geopandas
        self.gdf = gpd.read_file(shapefile_path)
        return self.gdf

    def show_map(self, fields_to_display=None):
        # Ensure CRS is WGS84
        gdf = self.gdf

        if gdf is None:
            print("No GeoDataFrame loaded. Please load a shapefile first.")
            return None

        if gdf.crs != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')

        # 👇 Fix: Convert datetime (and other non-JSON-serializable) columns to strings
        for col in gdf.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].astype(str)

        # Optional: Also handle other problematic types (e.g. None -> 'null', etc.)
        # But datetime is the usual culprit

        # Create map
        # centroid = gdf.geometry.unary_union.centroid
        # using union_all to get the centroid of all geometries (replaces deprecated unary_union)
        centroid = gdf.geometry.union_all().centroid

        m = folium.Map(location=[centroid.y, centroid.x], zoom_start=10)
        folium.TileLayer('OpenStreetMap').add_to(m)
        folium.TileLayer(tiles="Cartodb Positron",
                            attr='&copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors'
                            ).add_to(m)
        folium.TileLayer(tiles='Stamen Terrain',
                            attr='&copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors'
                            ).add_to(m)        
        folium.TileLayer(   tiles = 'https://tile.thunderforest.com/neighbourhood/{z}/{x}/{y}.png?apikey=734c0be502084e9cbc4ed238f91b0a3d',
                            attr= 'Thunderforest',
                            name= 'Thunderforest').add_to(m)
        folium.TileLayer(   tiles = 'https://tile.thunderforest.com/transport/{z}/{x}/{y}.png?apikey=734c0be502084e9cbc4ed238f91b0a3d',
                            attr= 'Thunderforest_trans',
                            name= 'Thunderforest_trans').add_to(m)
        folium.TileLayer(
                    tiles='https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoianZjMjY4OCIsImEiOiJja3Qwd2diczQwNGt1Mm9tbHJ1OWV5Y2hyIn0.Qwjn6ADRv_SSocKX9rEk6A',
                    attr='Mapbox Satellite',
                    name = 'Mapbox Satellite'
                ).add_to(m)

        attr = (
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
            'contributors, &copy; <a href="https://cartodb.com/attributions">CartoDB</a>'
                )
        tiles = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png"
        folium.TileLayer(tiles=tiles, attr=attr, name='CartoDB Positron No Labels').add_to(m)

        # Add GeoJSON, and related information in the gdf file, such as GA_ID, Block Name, Operator, etc.
        
        # Set default fields to display if none provided
        if fields_to_display is None:
            # Use first few columns as default, excluding geometry
            available_fields = [col for col in gdf.columns if col != 'geometry']
            fields_to_display = available_fields[:5] if len(available_fields) > 5 else available_fields

        folium.GeoJson(
            gdf.__geo_interface__,
            name='Shapefile',
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=fields_to_display),
        ).add_to(m)

        folium.LayerControl().add_to(m)

        return m
