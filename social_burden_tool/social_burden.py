import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import haversine_distances
import logging

class SocialBurdenCalculator:
    def __init__(self, population_info, facility_info, service_levels):
        """
        population_info: PopulationGroupInfo instance (GeoDataFrame with population locations)
        facility_info: FacilityInfo instance (GeoDataFrame with facilities)
        service_levels: ServiceLevels instance (Dataframe with Service levels for facilities)
        """
        self.population_info = population_info
        self.facility_info = facility_info
        self.service_levels = service_levels
        self.I_matrix = None  # Pairwise Effort Matrix (I_{n,l})
        self.G_matrix = None  # Service Accessibility Matrix (G_{n,l})
        self.E_matrix = None  # Effort Matrix (E_{n,m})
        self.B_matrix = None  # Social Burden Matrix (SB_{n,m})

    def compute_pairwise_effort(self):
        """ Compute Pairwise Effort Matrix I_{n,l} using Equation (4). """
        # Pairwise Effort Calculation (Equation 4 from the Measuring Social Infrastructure Service Burden Paper)
        # I_{n,l} = J_l + D_{n,l} * M_l
        # Where:
        #   I_{n,l} = Effort between population group n and facility l
        #   J_l     = Zero Distance Effort for facility l
        #   D_{n,l} = Distance between population group n and facility l
        #   M_l     = Effort Per Foot for facility l
        pop_gdf = self.population_info.gdf_layer
        fac_gdf = self.facility_info.gdf_layer

        pop_coords = np.radians(pop_gdf[["CBG_longitude", "CBG_latitude"]].values)
        fac_coords = np.radians(fac_gdf[["Facility_longitude", "Facility_latitude"]].values)

        # Distance Matrix D_{n,l} calculating great circle distance in meters
        D_matrix = haversine_distances(pop_coords, fac_coords) * 6371000  # Convert to meters

        # Map facility types to efforts
        fac_types = fac_gdf["Facility Type"].values
        J_l_values = np.array([self.service_levels.get_zero_distance_effort(ft) for ft in fac_types])  # Zero Distance Effort. Default 0.4 if missing
        M_l_values = np.array([self.service_levels.get_effort_per_foot(ft) for ft in fac_types])  # Effort per foot. Default 0.05 if missing

        # I_{n,l} = J_l + D_{n,l} * M_l (Expanding J_l and M_l to match shape)
        self.I_matrix = J_l_values + (D_matrix * M_l_values)

        logging.info("Computed Pairwise Effort Matrix I_{n,l}.")

    def compute_service_accessibility(self):
        """ Compute Service accessibility Matrix G_{n,l} using G_{n,l} = 1 / I_{n,l}. """
        if self.I_matrix is None:
            self.compute_pairwise_effort()

        # Compute G_{n,l} = 1 / I_{n,l} (Avoid division by zero)
        self.G_matrix = np.where(self.I_matrix > 0, 1 / self.I_matrix, 0)  # Replace zero efforts with infinity

        logging.info("Computed Service Accessibility Matrix G_{n,l}.")

    def compute_effort_matrix(self):
        """ Compute Effort Matrix E_{n,m} using Equation (3)  E_{n,m} = 1 / sum_l (G_{n,l} * S_{l,m}) """
        
        if self.G_matrix is None:
            self.compute_service_accessibility()

        # Extract Service Level Matrix S_{l,m} based on facility types
        fac_types = self.facility_info.gdf_layer["Facility Type"].values
        S_lm = np.array([self.service_levels[ft].values for ft in fac_types]).T  # Get service levels for facilities

        # Compute weighted service availability sum_l (G_{n,l} * S_{l,m})
        weighted_service = np.dot(self.G_matrix, S_lm)

        # Fix: Replace zeros with a small constant to avoid division by zero
        weighted_service[weighted_service == 0] = np.nan  # Use NaN to indicate undefined values

        # Compute effort matrix
        self.E_matrix = 1 / weighted_service

        # Replace NaN values with a large number to indicate inaccessible services
        self.E_matrix = np.nan_to_num(self.E_matrix, nan=1e6)  # Large number to represent "high effort"
        """ Handles G_{n,l} > 0, S_{l,m}> 0 normally/  G_{n,l} = 0, S_{l,m} = 1 (Effort = high)/ G_{n,l} > 0, S_{l,m} = 0 (Effort=no contribution)/ G_{n,l} = 0, S_{l,m} > 0 (Effort = Inf) """
        logging.info("Computed Effort Matrix E_{n,m}.")


    def compute_social_burden(self, ability_column):
        """ Compute Social Burden Matrix SB_{n,m} using SB_{n,m} = E_{n,m} / A_n. """
        if self.E_matrix is None:
            self.compute_effort_matrix()

        # Retrieve Ability Scores A_n
        pop_gdf = self.population_info.merge_data(ability_column)
        ability_values = pop_gdf[ability_column].values.reshape(-1, 1)  # Column vector (n x 1)

        # Compute SB_{n,m} = E_{n,m} / A_n
        self.B_matrix = self.E_matrix / ability_values

        logging.info("Computed Social Burden Matrix SB_{n,m}.")

        return pd.DataFrame(self.B_matrix, columns=self.service_levels.index)

    def save_results(self, output_path):
        """ Save Social Burden results to CSV. """
        if self.B_matrix is None:
            raise ValueError("Social Burden has not been computed yet.")

        pd.DataFrame(self.B_matrix).to_csv(output_path, index=False)
        logging.info(f"Saved Social Burden results to {output_path}.")
