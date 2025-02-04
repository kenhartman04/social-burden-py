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
        if self.gdf_layer is not None:
            logging.info("Shapefile is already loaded.")
            return self.layer

        try:
            gdf = gpd.read_file(self.shp_path)
            gdf['geometry']=gdf['geometry'].centroid
            gdf['CBG_latitude'] = gdf['geometry'].y
            gdf['CBG_longitude'] = gdf['geometry'].x
            if self.validate_layer(gdf):
                self.gdf_layer = gdf
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

    def merge_data(self, column):
        """
        Merge the shapefile data with the CSV data on the 'GISJOIN' column.

        :param column: Column from the CSV data to merge.
        :return: Merged GeoDataFrame.
        """
        if self.merged_data is not None:
            logging.info("Merged data is already created.")
            return self.merged_data

        if self.layer is None:
            self.load_layer()

        try:
            # Ensure GISJOIN is included in the ability data before merging
            if "GISJOIN" not in self.ability_data.columns:
                raise ValueError("GISJOIN column is missing in the CSV data.")
            if "GISJOIN" not in self.layer.columns:
                raise ValueError("GISJOIN column is missing in the shapefile.")

            # Merge the data on GISJOIN
            self.merged_data = self.layer.merge(
                self.ability_data[["GISJOIN", column]], on="GISJOIN", how="left"
            )

            logging.info(f"Merged data successfully created with {len(self.merged_data)} rows.")
            return self.merged_data

        except KeyError as ke:
            logging.error(f"Column '{column}' not found in CSV data: {ke}")
            raise
        except Exception as e:
            logging.error(f"Error merging shapefile and CSV data: {e}")
            raise

class FacilityInfo:
    def __init__(self, shp_path):
        """
        Initialize the class with the shapefile path.
        
        shp_path: Path to the shapefile
        """
        self.shp_path = shp_path
        self.gdf_layer = None  # placeholder for GeoDataFrame
        self.load_layer()

    def load_layer(self):
        """
        Load the shapefile as a GeoDataFrame.
        
        return GeoDataFrame of the loaded shapefile
        """
        if self.gdf_layer is not None:
            logging.info("Shapefile is already loaded.")
            return self.gdf_layer

        try:
            gdf = gpd.read_file(self.shp_path)
            gdf['geometry']=gdf['geometry'].centroid
            gdf['Facility_latitude'] = gdf['geometry'].y
            gdf['Facility_longitude'] = gdf['geometry'].x
            if self.validate_layer(gdf):
                self.gdf_layer = gdf
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
    
class ServiceLevels:
    def __init__(self, csv_path):
        """
        Initialize the class with the CSV path.
        
        csv_path: Path to the CSV file with service levels
        """
        self.sevice_levels_df = pd.read_csv(csv_path)
        
        # Extract Zero Distance Effort and Effort Per Foot
        self.J_l = self.service_levels_df.set_index("Facility Type")["Zero Distance Effort"].to_dict()
        self.M_l = self.service_levels_df.set_index("Facility Type")["Effort Per Foot"].to_dict()

        # Extract Service Level Matrix
        self.service_levels = self.service_levels_df.set_index("Facility Type").iloc[:, 2:].T
        logging.info("Service levels loaded successfully.")

    def get_service_levels(self):
        """
        Get the service levels from the CSV file.
        
        return: DataFrame of service levels
        """
        return self.service_levels
    
    def get_zero_distance_effort(self, facility_type):
        """
        Get the zero distance effort for a given facility type.
        
        facility_type: Type of facility
        return: Zero distance effort
        """
        return self.J_l.get(facility_type, 0.4)
    
    def get_effort_per_foot(self, facility_type):
        """
        Get the effort per foot for a given facility type.
        
        facility_type: Type of facility
        return: Effort per foot
        """
        return self.M_l.get(facility_type, 0.05)
    
    def get_service_level(self, facility_type, population_group):
        """
        Get the service level for a given facility type and population group.
        
        facility_type: Type of facility
        population_group: Population group
        return: Service level
        """
        return self.service_levels.loc[facility_type, population_group]
    

