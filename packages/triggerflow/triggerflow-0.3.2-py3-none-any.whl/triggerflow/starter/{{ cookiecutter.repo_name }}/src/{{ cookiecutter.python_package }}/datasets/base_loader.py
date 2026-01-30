import logging, json
from abc import abstractmethod
from kedro.io import AbstractDataset
from trigger_loader.loader import TriggerLoader
import pandas as pd
import numpy as np
from pathlib import Path


class BaseLoader(AbstractDataset):
    """
    Abstract Base Class for using the TriggerLoader.

    Users must inherit from this class and implement the abstract methods.
    The core processing logic in `_load` is fixed and cannot be overridden.
    """

    def __init__(self, sample_json: str, settings: str, config: str):
        self.sample_json = sample_json
        with open(settings, "r") as f:
            self.settings = json.load(f)
        with open(config, "r") as f:
            self.config = json.load(f)

        # get logger for reporting
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing loader: {self.__class__.__name__}")

    @abstractmethod
    def transform(self, events):
        """
        USER MUST IMPLEMENT.
        """
        pass

    def _load(self) -> pd.DataFrame:
        """
        CORE LOGIC (NOT OVERRIDABLE): Loads and processes a single ROOT file.
        """

        self.logger.info(f"Start Loading...")
        loader = TriggerLoader(
            sample_json=self.sample_json,
            transform=self.transform,
            output_path=self.settings["output_dir"]
        )

        if self.settings["run_local"]:
            loader.run_local(
                num_workers=self.settings["num_workers"],
                chunksize=self.settings["chunksize"]
            )
        else:
            loader.run_distributed(
                cluster_type=self.settings["cluster_type"],
                cluster_config=self.config,
                chunksize=self.settings["chunksize"],
                jobs=self.settings["jobs"]
            )

        # load last parquet file from manifest file for each dataset key
        # from the meta_data
        dataset_keys = set(loader.meta_data.keys())
        manifest_path = Path(self.settings["output_dir"]) / "manifest.json"

        last_records = {key: None for key in dataset_keys}

        with manifest_path.open() as f:
            for line in f:
                record = json.loads(line)
                dataset = record.get("dataset")

                if dataset in last_records:
                    last_records[dataset] = record

        # sanity check
        missing = [k for k, v in last_records.items() if v is None]
        if missing:
            raise ValueError(f"No manifest entry found for datasets: {missing}")

        final_dfs = []
        for dataset_key, record in last_records.items():
            file_path = record["parquet_file"]
            df = pd.read_parquet(file_path)

            if loader.meta_data[dataset_key]["is_signal"]:
                df["is_signal"] = np.ones(len(df), dtype=int)
                df["y"] = np.ones(len(df), dtype=int)
            else:
                df["is_signal"] = np.zeros(len(df), dtype=int)
                df["y"] = np.zeros(len(df), dtype=int)

            final_dfs.append(df)

        return pd.concat(final_dfs, ignore_index=True)

    def _save(self, data: pd.DataFrame) -> pd.DataFrame:
        return data

    def _describe(self) -> dict:
        return {"sample_json": self.sample_json, "settings": self.settings, "config": self.config}
