from anndata import AnnData
from typing import Union, Optional
import numpy as np

class BEAST_Data:
    def __init__(self, name: str, dataset_type: str, data: Union[AnnData, str], resolution:str, is_simulated: bool = False, is_prenormalized: bool = False):
        """
        A unified dataset structure for MOPITAS.
        Args:
            name (str): Name of the dataset.
            dataset_type (str): Type of the dataset ('spatial' or 'single-cell').
            data (Union[AnnData, str]): The dataset.
            resolution (str): Indicates whether the dataset is in 'single-cell' or 'subcellular' or 'voxel'.
            is_simulated (bool): Flag indicating whether the dataset is simulated.
            is_prenormalized (bool): Flag indicating whether the dataset is prenormalized.
        """

        self.name = name
        self.dataset_type = dataset_type
        self.resolution = resolution.lower()
        self.is_simulated = is_simulated
        self.is_prenormalized = is_prenormalized
        self.data: Optional[AnnData] = []
        self.pca = None
        self.umap = None
        self.copied = False

        self._validate_dataset_type()
        self._check_name_length()
        self._add_dataset(data)

        if dataset_type == "spatial":
            self._init_spatial()

    def _check_name_length(self):
        max_length = 400
        if len(self.name) > max_length:
            raise ValueError(f"Name cannot be longer than {max_length} characters.")

    def _validate_dataset_type(self):
        if self.dataset_type not in {"spatial", "single-cell"}:
            raise ValueError("Invalid dataset_type. Must be 'spatial' or 'single-cell'.")

    def _validate_dataset_resolution(self):
        if self.resolution  in {"subcellular", "single-cell", "voxel"}:
            if (self.resolution=="subcellular" or self.resolution=="single-cell") and self.data.var["cell_types"] is None:
                raise ValueError("The dataset must contain cell types. You can find a label transfer script in https://gitlab.sdu.dk/mopitas/benchmarking/docs/results_recreation label_transfer.")
        else:
            raise ValueError("Invalid dataset_resolution. Must be 'subcellular', 'single-cell' or 'voxel'.")


    def _add_dataset(self, input_data: Union[AnnData, str]):
        """
        Add a single dataset (AnnData object or file path) to the MOPITAS_Dataset.
        """
        from anndata import read_h5ad
        import os
        if isinstance(input_data, list):
            raise ValueError("Only a single AnnData object or file path is allowed, not a list.")

        if isinstance(input_data, AnnData):
            nonZeroCells = input_data.X.sum(axis=1) > 0
            input_data = input_data[nonZeroCells]
            self.data = input_data

            print(f"Added AnnData object to dataset '{self.name}'.")
        elif isinstance(input_data, str):
            print(f"Processing file path: {input_data}")
            if not os.path.exists(input_data):
                print(f"File {input_data} does not exist. Skipping.")
                return
            try:
                if input_data.endswith(".h5ad"):
                    dataset = read_h5ad(input_data)
                    self.data = dataset
                    print(f"Loaded dataset from: {input_data}")
                else:
                    print(f"Unsupported file format for {input_data}. Skipping.")
            except Exception as e:
                print(f"Error loading dataset from {input_data}: {e}")
        else:
            raise ValueError("Data should be either an AnnData object or a path to the .h5ad dataset.")

    def init_pca(self):
        """
        Compute PCA embeddings if not already computed.
        """
        from scipy.sparse import issparse
        from sklearn.decomposition import PCA
        if self.pca is None:
            if issparse(self.data.X):
                X = self.data.X.toarray()
            else:
                X = self.data.X
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(np.log2(X + 1))
            self.data.obsm["pca"] = pca_result
            self.pca = pca_result
            print("PCA embeddings computed and stored.")

    def init_umap(self):
        """
        Compute UMAP embeddings if not already computed.
        """
        from scipy.sparse import issparse
        from umap import UMAP
        if self.umap is None:
            if issparse(self.data.X):
                X = self.data.X.toarray()
            else:
                X = self.data.X
            umap_model = UMAP(n_components=2)
            umap_result = umap_model.fit_transform(np.log2(X + 1))
            self.data.obsm["umap"] = umap_result
            self.umap = umap_result
            print("UMAP embeddings computed and stored.")

    def _init_spatial(self) -> None:
        """
        Initializes spatial coordinates for the dataset by checking and constructing the necessary spatial information.
        """
        if self.data.is_view:
            self.data = self.data.copy()

        if "spatial" not in self.data.obsm:
            if {"X", "Y"}.issubset(self.data.obs.columns):
                self.data.obsm["spatial"] = self.data.obs[["X", "Y"]].values
            else:
                raise ValueError(
                    "The columns 'X' and 'Y' are required in obs to initialize spatial data."
                )

        if not {"X", "Y"}.issubset(self.data.obs.columns):
            if {"array_row", "array_col"}.issubset(self.data.obs.columns):
                self.data.obs["X"] = self.data.obs["array_col"]
                self.data.obs["Y"] = self.data.obs["array_row"]
            else:
                raise ValueError(
                    "Error the columns ´X' and 'Y' are not present in the dataset, and could not be constructed from 'array_row' and 'array_col'")

        self.data.obs["X"] = self.data.obs["X"].astype("float32")
        self.data.obs["Y"] = self.data.obs["Y"].astype("float32")

        if "spatial" not in self.data.obsm:
            self.data.obsm["spatial"] = self.data.obs[["X", "Y"]].values

        if "gene_id" not in self.data.var:
            self.data.var.index = self.data.var.index.str.replace(r"^X\.", "", regex=True)
            self.data.var["gene_id"] = self.data.var.index

        if "cell_type" not in self.data.obs.columns:
            if "Cell_Type" in self.data.obs.columns:
                self.data.obs["cell_type"] = self.data.obs["Cell_Type"]
            elif "Cell_type" in self.data.obs.columns:
                self.data.obs["cell_type"] = self.data.obs["Cell_type"]

        if "cell_type_distributions" in self.data.obsm and "cell_type_distribution" not in self.data.obsm:
            self.data.obsm["cell_type_distribution"] = self.data.obsm["cell_type_distributions"]

        if "voxelized_subdata" in self.data.uns:
            if "cell_type_distributions" in self.data.uns["voxelized_subdata"].obsm and "cell_type_distribution" not in self.data.uns["voxelized_subdata"].obsm:
                self.data.uns["voxelized_subdata"].obsm["cell_type_distribution"] = self.data.uns["voxelized_subdata"].obsm["cell_type_distributions"]

    def reduce_genes(self, num_genes: int = 100, criterion: str = "variance"):
        """
        Reduce the number of genes in the AnnData object.

        Modifies self.data in place and returns the reduced AnnData.
        """
        from scipy.sparse import issparse

        if self.data is None or not isinstance(self.data, AnnData):
            raise ValueError("No valid AnnData object found to reduce genes.")

        if self.data.shape[1] <= num_genes:
            print(
                f"The dataset already contains {self.data.shape[1]} genes "
                f"(<= {num_genes}). No reduction needed."
            )
            return self.data

        X = self.data.X

        if criterion == "variance":
            scores = X.var(axis=0).A1 if issparse(X) else X.var(axis=0)

        elif criterion == "mean":
            scores = X.mean(axis=0).A1 if issparse(X) else X.mean(axis=0)

        elif criterion == "random":
            scores = None

        else:
            raise ValueError(
                "criterion must be one of {'variance', 'mean', 'random'}"
            )

        if criterion == "random":
            selected = np.random.choice(self.data.shape[1], num_genes, replace=False)
        else:
            selected = np.argsort(scores)[-num_genes:]

        self.data = self.data[:, selected].copy()

        print(f"Reduced to {num_genes} genes using '{criterion}' criterion.")
        return self.data
