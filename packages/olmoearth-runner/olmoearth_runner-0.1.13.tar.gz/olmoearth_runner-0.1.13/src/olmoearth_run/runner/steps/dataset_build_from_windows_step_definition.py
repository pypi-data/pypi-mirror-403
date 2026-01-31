import logging
import multiprocessing
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from rslearn.dataset import Dataset, Window
from rslearn.dataset.storage.file import FileWindowStorage, load_window
from upath import UPath

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.runner.metrics.dataset_builder import DatasetBuilderMetrics
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.dataset_builder import DatasetBuilder
from olmoearth_run.runner.tools.olmoearth_config.transpilers.olmoearth_to_rslearn import transpile_and_write_dataset_config
from olmoearth_run.shared.models.api.task_args import DatasetBuildFromWindowsTaskArgs
from olmoearth_run.shared.models.api.task_results import DatasetBuildFromWindowsTaskResults

logger = logging.getLogger(__name__)

multiprocessing.set_start_method("forkserver", force=True)


class DatasetBuildFromWindowsStepDefinition(BaseStepDefinition[DatasetBuildFromWindowsTaskArgs, DatasetBuildFromWindowsTaskResults]):
    """
    This completes the prepare, ingest, and materialize steps given windows have already been created for the
    dataset build workflow.
    """

    def run(self, task_args: DatasetBuildFromWindowsTaskArgs) -> DatasetBuildFromWindowsTaskResults:
        dataset_path = UPath(task_args.dataset_path)

        # JIT transpile OlmoEarthConfig to dataset config.json if using unified config
        if task_args.olmoearth_config_path:
            transpile_and_write_dataset_config(task_args.olmoearth_config_path, dataset_path)

        # Load existing windows from the dataset directory, filtering by worker assignment
        windows: list[Window] = []
        windows_dir = dataset_path / "windows"

        if windows_dir.exists():
            # Load windows from all groups
            for group_dir in windows_dir.iterdir():
                if group_dir.is_dir():
                    group_name = group_dir.name
                    logger.debug(f"Loading windows from group: {group_name}")

                all_windows = sorted(group_dir.iterdir())   # Sort for consistent ordering
                my_windows = all_windows[task_args.worker_index::task_args.total_workers]

                # Filter to only directories before parallel loading
                window_dirs = [w for w in my_windows if w.is_dir()]

                with ThreadPoolExecutor(max_workers=OlmoEarthSettings.NUM_WORKERS) as executor:
                    storage = FileWindowStorage(dataset_path)
                    future_to_window_dir = {executor.submit(load_window, storage, window_dir): window_dir for window_dir in window_dirs}

                    # Collect results as they complete
                    for future in as_completed(future_to_window_dir):
                        window_dir = future_to_window_dir[future]  # Get the original window_dir argument
                        window = future.result()
                        logger.debug(f"Worker {task_args.worker_index}: Loaded window: {window.name} from {window_dir}")
                        DatasetBuilderMetrics.record_windows_loaded(1)
                        windows.append(window)
        else:
            raise ValueError(f"Windows directory does not exist: {windows_dir}")

        # Log worker assignment information
        logger.info(f"Worker {task_args.worker_index}/{task_args.total_workers}: got {len(windows)} windows to process.")
        dataset = Dataset(dataset_path)
        # Dataset building is a very IO intensive task, so we can have more workers than CPU cores
        builder = DatasetBuilder(
            dataset=dataset,
            num_workers=(os.cpu_count() or 1) * OlmoEarthSettings.DATASET_BUILD_WORKERS_PER_CPU,
            min_window_success_rate=task_args.min_window_success_rate
        )
        builder.build_dataset(windows)
        total_size_mb = builder.get_partition_size_mb(str(dataset_path))

        return DatasetBuildFromWindowsTaskResults(dataset_build_path=str(dataset_path), dataset_size_mb=total_size_mb)
