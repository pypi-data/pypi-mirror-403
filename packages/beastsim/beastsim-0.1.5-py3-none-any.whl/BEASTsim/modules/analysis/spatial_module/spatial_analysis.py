class SpatialAnalysis:
    def __init__(self, parameters) -> None:
        self.parameters = parameters

        # Imports
        from BEASTsim.modules.analysis.spatial_module.simulation_analysis import SimulationAnalysis
        from BEASTsim.modules.analysis.spatial_module.cell_mapping.cell_mapping_analysis import CellMappingAnalysis
        from BEASTsim.modules.analysis.spatial_module.SVG.SVG_SpatialDE import SVG_SpatialDE

        # Modules
        self.simulation_analysis = SimulationAnalysis(parameters)
        self.cell_mapping_analysis = CellMappingAnalysis(parameters)
        self.SVG_analysis= SVG_SpatialDE(parameters)
