import geopandas as gpd
import pandas as pd
import logging


class PopulationGroupInfo:
    def __init__(self, shp_path, csv_path):
        """
        Initialize the class with the shapefile and CSV paths.
        
        shp_path: Path to the shapefile
        csv_path: Path to the CSV file with ability attributes
        """
        self.shp_path = shp_path
        self.csv_path = csv_path
        self.layer = None  # placeholder for GeoDataFrame
        self.ability_data = None  # placeholder for CSV data
        self.merged_data = None  # placeholder for merged GeoDataFrame
        self.load_ability_data()

    def load_ability_data(self):
        """
        Load the CSV file containing the ability attributes.
        """
        try:
            self.ability_data = pd.read_csv(self.csv_path)
            if 'GISJOIN' not in self.ability_data.columns:
                raise ValueError("The CSV file must contain a 'GISJOIN' column.")
            logging.info(f"CSV file loaded successfully with {len(self.ability_data)} rows.")
        except Exception as e:
            logging.error(f"Error loading CSV file: {e}")
            raise

    def load_layer(self):
        """
        Load the shapefile as a GeoDataFrame.
        
        return GeoDataFrame of the loaded shapefile
        """
        if self.layer is not None:
            logging.info("Shapefile is already loaded.")
            return self.layer

        try:
            gdf = gpd.read_file(self.shp_path)
            gdf['geometry']=gdf['geometry'].centroid
            gdf['CBG_latitude'] = gdf['geometry'].y
            gdf['CBG_longitude'] = gdf['geometry'].x
            if self.validate_layer(gdf):
                self.layer = gdf
                logging.info(f"Shapefile loaded successfully with {len(gdf)} geometries.")
                return gdf
            else:
                raise ValueError("Shapefile validation failed.")
        except Exception as e:
            logging.error(f"Error loading shapefile: {e}")
            raise

    def validate_layer(self, gdf):
        """
        Validate the GeoDataFrame for the shapefile.
        
        GeoDataFrame to validate
        return: True if valid, False otherwise
        """
        if gdf.empty:
            logging.warning("The shapefile is empty.")
            return False
        if 'geometry' not in gdf.columns:
            logging.warning("The shapefile does not have a 'geometry' column.")
            return False
        if 'GISJOIN' not in gdf.columns:
            logging.warning("The shapefile does not have a 'GISJOIN' column.")
            return False

            # Validate geometries
        invalid_geometries = gdf[~gdf['geometry'].is_valid]
        if not invalid_geometries.empty:
            logging.warning(f"The shapefile contains {len(invalid_geometries)} invalid geometries.")
            return False
            
        return True

    def merge_data(self):
        """
        Merge the shapefile data with the CSV data on the 'GISJOIN' column.
        
        return Merged GeoDataFrame
        """
        if self.merged_data is not None:
            logging.info("Merged data is already created.")
            return self.merged_data

        if self.layer is None:
            self.load_layer()

        try:
            self.merged_data = self.layer.merge(
                self.ability_data, on="GISJOIN", how="left"
            )
            logging.info(f"Merged data successfully created with {len(self.merged_data)} rows.")
            return self.merged_data
        except Exception as e:
            logging.error(f"Error merging shapefile and CSV data: {e}")
            raise
