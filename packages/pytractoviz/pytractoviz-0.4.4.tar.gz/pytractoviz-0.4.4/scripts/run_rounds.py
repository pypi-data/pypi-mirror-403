#!/usr/bin/env python3
"""Script to run quality check workflow in separate rounds for memory management.

This script allows running different types of image generation in separate rounds,
so that memory can be cleared between rounds. It also supports generating atlas views
once for all subjects instead of per subject.
"""

from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import sys
from pathlib import Path

# Try to import fcntl (Unix/Linux only)
try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


from pytractoviz.html import create_quality_check_html
from pytractoviz.viz import TractographyVisualizer

logger = logging.getLogger(__name__)


def load_config(config_file: Path) -> dict:
    """Load configuration from JSON file."""
    with open(config_file, "r") as f:
        config = json.load(f)

    atlases = {}
    afiles = [str(apath) for apath in Path(config.get("atlas_dir", "")).glob("*.trk")]
    for a in afiles:
        aname = Path(a).stem.split(".")[0]
        atlases[aname] = a

    subjects = config.get("subject_list", "")
    subject_refs = {}
    metrics = {}
    orig_space = {}
    mni_space = {}
    anat_dir = Path(config.get("anat_dir", ""))
    dwi_dir = Path(config.get("dwi_dir", ""))
    bundle_dir = Path(config.get("bundle_dir", ""))

    for s in subjects:
        subject_refs[s] = list(anat_dir.glob(f"{s}/anat/{s}_space-ACPC_desc-brain_mask.nii.gz"))[0]

        subj_metrics = {}
        subj_metrics["FA"] = list(
            dwi_dir.glob(f"{s}/dwi/{s}_acq-multiband_dir-AP_space-ACPC_model-tensor_param-fa_dwimap.nii.gz")
        )[0]
        metrics[s] = subj_metrics

        orig_bundles = {}
        bundle_paths = [bpath for bpath in Path(bundle_dir / s).glob("nat_bundles/*trk")]
        for bpath in bundle_paths:
            if "_R_" in bpath.stem or "_L_" in bpath.stem or "CC_F" in bpath.stem:
                aname = "_".join(bpath.stem.split(".")[1].split("_")[0:2])
            else:
                aname = bpath.stem.split(".")[1].split("_")[0]
            orig_bundles[aname] = bpath
        orig_space[s] = orig_bundles

        mni_bundles = {}
        bundle_paths = [bpath for bpath in Path(bundle_dir / s).glob("mni_bundles/*trk")]
        for bpath in bundle_paths:
            if "_R_" in bpath.stem or "_L_" in bpath.stem or "CC_F" in bpath.stem:
                aname = "_".join(bpath.stem.split(".")[1].split("_")[0:2])
            else:
                aname = bpath.stem.split(".")[1].split("_")[0]
            mni_bundles[aname] = bpath
        mni_space[s] = mni_bundles

    config["ref_img"] = subject_refs
    config["subjects_original_space"] = orig_space
    config["subjects_mni_space"] = mni_space
    config["atlas_files"] = atlases
    config["metric_files"] = metrics

    return config


def save_results(results: dict, output_file: Path) -> None:
    """Save results dictionary to JSON file with file locking for thread safety.

    Uses atomic write (write to temp file then rename) to prevent corruption
    when multiple processes write simultaneously.
    """
    # Convert Path objects to strings for JSON serialization
    results_serializable: dict[str, dict[str, dict[str, str]]] = {}
    for subject_id, subject_tracts in results.items():
        results_serializable[subject_id] = {}
        if isinstance(subject_tracts, dict):
            for tract_name, media_dict in subject_tracts.items():
                results_serializable[subject_id][tract_name] = {}
                if isinstance(media_dict, dict):
                    for media_type, file_path in media_dict.items():
                        results_serializable[subject_id][tract_name][media_type] = str(file_path)

    # Atomic write: write to temp file, then rename
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory for atomic rename
    temp_file = output_file.with_suffix(output_file.suffix + ".tmp")

    try:
        with open(temp_file, "w") as f:
            json.dump(results_serializable, f, indent=2)
        # Atomic rename (works on Unix/Linux, Windows may need different approach)
        temp_file.replace(output_file)
    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        raise


def load_results(results_file: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Load results dictionary from JSON file with file locking for thread safety."""
    results_file = Path(results_file)
    if not results_file.exists():
        return {}

    # Use file locking to prevent reading while another process is writing
    if HAS_FCNTL:
        try:
            with open(results_file, "r") as f:
                # Try to acquire shared lock (non-blocking)
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                except (IOError, OSError):
                    # If we can't get lock, wait a bit and try again
                    # This handles the case where another process is writing
                    import time

                    time.sleep(0.1)
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)

                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (IOError, OSError) as e:
            # If file locking fails, fall back to regular read
            logger.warning("File locking failed, using regular read: %s", e)
            with open(results_file) as f:
                return json.load(f)
    else:
        # No fcntl available (Windows), use regular read
        # Note: This is not thread-safe but better than failing
        with open(results_file) as f:
            return json.load(f)


def merge_results(existing: dict, new: dict) -> dict:
    """Merge new results into existing results."""
    for subject_id, subject_tracts in new.items():
        if subject_id not in existing:
            existing[subject_id] = {}
        if isinstance(subject_tracts, dict):
            for tract_name, media_dict in subject_tracts.items():
                if tract_name not in existing[subject_id]:
                    existing[subject_id][tract_name] = {}
                if isinstance(media_dict, dict):
                    existing[subject_id][tract_name].update(media_dict)
    return existing


def save_and_merge_results(
    new_results: dict,
    results_file: Path,
    max_retries: int = 10,
    retry_delay: float = 0.1,
) -> None:
    """Atomically merge new results into existing results file.

    This function handles concurrent writes by:
    1. Loading existing results with file lock
    2. Merging new results
    3. Saving with atomic write

    Parameters
    ----------
    new_results : dict
        New results to merge.
    results_file : Path
        Path to results JSON file.
    max_retries : int, optional
        Maximum number of retries if file is locked. Default is 10.
    retry_delay : float, optional
        Delay between retries in seconds. Default is 0.1.
    """
    results_file = Path(results_file)

    for attempt in range(max_retries):
        try:
            # Load existing results with lock
            existing_results = load_results(results_file)

            # Merge results
            merged_results = merge_results(existing_results.copy(), new_results)

            # Save with atomic write
            save_results(merged_results, results_file)

            # Success!
            return
        except (IOError, OSError) as e:
            if attempt < max_retries - 1:
                # Wait and retry
                import time

                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                logger.debug(
                    "Retry %d/%d: File locked, waiting...",
                    attempt + 1,
                    max_retries,
                )
            else:
                # Last attempt failed
                logger.error("Failed to save results after %d attempts: %s", max_retries, e)
                raise


def split_subjects_into_batches(
    subjects: dict[str, dict[str, str | Path]],
    num_batches: int,
) -> list[dict[str, dict[str, str | Path]]]:
    """Split subjects dictionary into batches.

    Parameters
    ----------
    subjects : dict[str, dict[str, str | Path]]
        Dictionary mapping subject IDs to their tract files.
    num_batches : int
        Number of batches to create.

    Returns
    -------
    list[dict[str, dict[str, str | Path]]]
        List of subject dictionaries, one per batch.
    """
    subject_ids = sorted(subjects.keys())
    total_subjects = len(subject_ids)

    if num_batches <= 0:
        raise ValueError("num_batches must be positive")

    if num_batches >= total_subjects:
        # More batches than subjects - each subject gets its own batch
        return [{sid: subjects[sid]} for sid in subject_ids]

    # Calculate batch size
    batch_size = max(1, total_subjects // num_batches)
    batches: list[dict[str, dict[str, str | Path]]] = []

    for i in range(0, total_subjects, batch_size):
        batch_subject_ids = subject_ids[i : i + batch_size]
        batch = {sid: subjects[sid] for sid in batch_subject_ids}
        batches.append(batch)

    return batches


def get_slurm_array_task_id() -> int | None:
    """Get SLURM array task ID from environment.

    Returns
    -------
    int | None
        Array task ID (0-indexed or 1-indexed depending on SLURM_ARRAY_TASK_MIN)
        if running in SLURM array job, None otherwise.
    """
    array_task_id = os.environ.get("SLURM_ARRAY_TASK_ID")
    if array_task_id is not None:
        try:
            task_id = int(array_task_id)
            # Check if array is 0-indexed by looking at SLURM_ARRAY_TASK_MIN
            array_task_min = os.environ.get("SLURM_ARRAY_TASK_MIN")
            if array_task_min is not None:
                try:
                    min_id = int(array_task_min)
                    # If min is 0, array is 0-indexed; if min is 1, array is 1-indexed
                    # Return as-is (will be handled by batch filtering logic)
                    return task_id
                except ValueError:
                    pass
            # Default: assume 0-indexed (most common for custom setups)
            return task_id
        except ValueError:
            logger.warning("Invalid SLURM_ARRAY_TASK_ID: %s", array_task_id)
            return None
    return None


def get_slurm_array_task_count() -> int | None:
    """Get SLURM array task count (total number of tasks) from environment.

    Returns
    -------
    int | None
        Total number of array tasks if running in SLURM array job, None otherwise.
    """
    # Try SLURM_ARRAY_TASK_COUNT first (most reliable)
    array_task_count = os.environ.get("SLURM_ARRAY_TASK_COUNT")
    if array_task_count is not None:
        try:
            return int(array_task_count)
        except ValueError:
            logger.warning("Invalid SLURM_ARRAY_TASK_COUNT: %s", array_task_count)

    # Fall back to SLURM_ARRAY_TASK_MAX (maximum task ID)
    array_task_max = os.environ.get("SLURM_ARRAY_TASK_MAX")
    if array_task_max is not None:
        try:
            max_id = int(array_task_max)
            # If we have a min, calculate count; otherwise assume it starts at 1
            array_task_min = os.environ.get("SLURM_ARRAY_TASK_MIN")
            if array_task_min is not None:
                try:
                    min_id = int(array_task_min)
                    return max_id - min_id + 1
                except ValueError:
                    pass
            # Assume array starts at 1 (most common case)
            return max_id
        except ValueError:
            logger.warning("Invalid SLURM_ARRAY_TASK_MAX: %s", array_task_max)

    return None


def get_subjects_for_batch(
    subjects: dict[str, dict[str, str | Path]],
    batch_index: int,
    num_batches: int,
    batch_start_index: int = 0,
) -> list[str]:
    """Get list of subject IDs for a specific batch.

    Parameters
    ----------
    subjects : dict[str, dict[str, str | Path]]
        Dictionary mapping subject IDs to their tract files.
    batch_index : int
        Batch index (0-indexed or 1-indexed depending on batch_start_index).
    num_batches : int
        Total number of batches.
    batch_start_index : int, optional
        Starting index for batches (0 for 0-indexed, 1 for 1-indexed). Default is 0.

    Returns
    -------
    list[str]
        List of subject IDs in the specified batch.
    """
    batch = filter_subjects_by_batch(subjects, batch_index, num_batches, batch_start_index)
    return sorted(batch.keys())


def filter_subjects_by_batch(
    subjects: dict[str, dict[str, str | Path]],
    batch_index: int,
    num_batches: int,
    batch_start_index: int = 0,
) -> dict[str, dict[str, str | Path]]:
    """Filter subjects to only include those in the specified batch.

    Parameters
    ----------
    subjects : dict[str, dict[str, str | Path]]
        Dictionary mapping subject IDs to their tract files.
    batch_index : int
        Batch index (0-indexed or 1-indexed, depending on batch_start_index).
    num_batches : int
        Total number of batches.
    batch_start_index : int, optional
        Starting index for batches (0 for 0-indexed, 1 for 1-indexed). Default is 0.

    Returns
    -------
    dict[str, dict[str, str | Path]]
        Filtered subjects dictionary containing only subjects in the specified batch.
    """
    batches = split_subjects_into_batches(subjects, num_batches)

    # Convert batch_index to 0-indexed for list access
    if batch_start_index == 0:
        # Already 0-indexed
        list_index = batch_index
        min_batch = 0
        max_batch = len(batches) - 1
    else:
        # 1-indexed, convert to 0-indexed
        list_index = batch_index - 1
        min_batch = 1
        max_batch = len(batches)

    if batch_index < min_batch or batch_index > max_batch:
        raise ValueError(
            f"Batch index {batch_index} is out of range ({min_batch}-{max_batch})",
        )

    if list_index < 0 or list_index >= len(batches):
        raise ValueError(
            f"Batch index {batch_index} (list index {list_index}) is out of range for {len(batches)} batches",
        )

    return batches[list_index]


def filter_subjects_by_list(
    subjects: dict[str, dict[str, str | Path]],
    subject_list: list[str],
) -> dict[str, dict[str, str | Path]]:
    """Filter subjects to only include those in the provided list.

    Parameters
    ----------
    subjects : dict[str, dict[str, str | Path]]
        Dictionary mapping subject IDs to their tract files.
    subject_list : list[str]
        List of subject IDs to include.

    Returns
    -------
    dict[str, dict[str, str | Path]]
        Filtered subjects dictionary containing only subjects in the list.
    """
    filtered = {
        subject_id: subject_tracts for subject_id, subject_tracts in subjects.items() if subject_id in subject_list
    }

    # Warn about missing subjects
    missing = set(subject_list) - set(subjects.keys())
    if missing:
        logger.warning("Subjects not found in config: %s", ", ".join(sorted(missing)))

    return filtered


def load_subject_list(subject_file: Path) -> list[str]:
    """Load subject IDs from a file (one per line).

    Parameters
    ----------
    subject_file : Path
        Path to file containing subject IDs, one per line.

    Returns
    -------
    list[str]
        List of subject IDs.
    """
    with open(subject_file) as f:
        subjects = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    return subjects


def run_round(
    round_name: str,
    config: dict,
    results_file: Path,
    output_dir: Path,
    batch_index: int | None = None,
    num_batches: int | None = None,
    batch_start_index: int = 0,
) -> None:
    """Run a specific round of image generation.

    Parameters
    ----------
    round_name : str
        Name of the round to run.
    config : dict
        Configuration dictionary.
    results_file : Path
        Path to results JSON file.
    output_dir : Path
        Output directory.
    batch_index : int | None, optional
        Batch index (0-indexed or 1-indexed depending on batch_start_index) if running in batch mode.
        If None, processes all subjects.
    num_batches : int | None, optional
        Total number of batches. Required if batch_index is provided.
    batch_start_index : int, optional
        Starting index for batches (0 for 0-indexed, 1 for 1-indexed). Default is 0.
    """
    logger.info("=" * 80)
    logger.info("Starting round: %s", round_name)
    logger.info("=" * 80)

    # Load existing results
    existing_results = load_results(results_file)

    # Create visualizer
    visualizer = TractographyVisualizer(
        output_directory=str(output_dir),
        n_jobs=config.get("n_jobs", 1),
        figure_size=tuple(config.get("figure_size", [800, 800])),
    )

    # Determine which checks to skip
    all_checks = [
        "anatomical_views",
        "atlas_comparison",
        "cci",
        "before_after_cci",
        "afq_profile",
        "bundle_assignment",
        "shape_similarity",
    ]

    # Determine skip_checks based on round
    if round_name == "anatomical":
        skip_checks = [c for c in all_checks if c != "anatomical_views"]
    elif round_name == "cci":
        skip_checks = [c for c in all_checks if c != "cci"]
    elif round_name == "before_after_cci":
        skip_checks = [c for c in all_checks if c != "before_after_cci"]
    elif round_name == "atlas_views":
        # For atlas views, we'll generate them once for all subjects
        # We also generate subject MNI views here for atlas comparison
        skip_checks = all_checks  # Skip all other checks (handled separately)
    elif round_name == "shape_similarity":
        skip_checks = [c for c in all_checks if c != "shape_similarity"]
    elif round_name == "afq_profile":
        skip_checks = [c for c in all_checks if c != "afq_profile"]
    elif round_name == "bundle_assignment":
        skip_checks = [c for c in all_checks if c != "bundle_assignment"]
    else:
        raise ValueError(f"Unknown round name: {round_name}")

    # Prepare data structures
    subjects_original_space = config["subjects_original_space"]
    subjects_mni_space = config.get("subjects_mni_space")
    atlas_files = config.get("atlas_files")
    metric_files = config.get("metric_files")
    atlas_ref_img = config.get("atlas_ref_img")
    ref_img = config.get("ref_img")
    flip_lr = config.get("flip_lr", False)

    # Filter subjects by provided list first (if any)
    # If subjects are explicitly provided, skip batch filtering
    subject_list = config.get("subject_list")
    has_explicit_subjects = subject_list is not None

    if subject_list:
        logger.info("Filtering subjects by provided list (%d subjects)", len(subject_list))
        subjects_original_space = filter_subjects_by_list(
            subjects_original_space,
            subject_list,
        )
        logger.info("Processing %d subjects from list", len(subjects_original_space))

    # Filter subjects by batch if running in batch mode
    # This automatically infers which subjects belong to this batch from the config
    if batch_index is not None and num_batches is not None:
        if has_explicit_subjects:
            # If explicit subjects provided, filter those by batch
            logger.info(
                "Filtering provided subjects for batch %d of %d (start index: %d)",
                batch_index,
                num_batches,
                batch_start_index,
            )
            subjects_original_space = filter_subjects_by_batch(
                subjects_original_space,
                batch_index,
                num_batches,
                batch_start_index,
            )
        else:
            # Automatically infer subjects for this batch from config
            logger.info(
                "Automatically inferring subjects for batch %d of %d from config file (start index: %d)",
                batch_index,
                num_batches,
                batch_start_index,
            )
            total_subjects = len(subjects_original_space)
            logger.info("Total subjects in config: %d", total_subjects)
            subjects_original_space = filter_subjects_by_batch(
                subjects_original_space,
                batch_index,
                num_batches,
                batch_start_index,
            )

        # Log which subjects are in this batch
        subject_ids = sorted(subjects_original_space.keys())
        logger.info("Processing %d subjects in batch %d: %s", len(subject_ids), batch_index, ", ".join(subject_ids))

    # Also filter subjects_mni_space and metric_files if they exist
    if subjects_mni_space is not None:
        subjects_mni_space = {
            sid: tracts for sid, tracts in subjects_mni_space.items() if sid in subjects_original_space
        }

    if metric_files is not None:
        metric_files = {sid: metrics for sid, metrics in metric_files.items() if sid in subjects_original_space}

    # Filter ref_img if it's a dictionary
    if isinstance(ref_img, dict):
        ref_img = {sid: path for sid, path in ref_img.items() if sid in subjects_original_space}

    # Handle reference image - can be single path or dict mapping subject_id -> path
    # Convert string paths to Path objects, keep dict as-is (workflow handles it)
    if isinstance(ref_img, str):
        # Single reference image for all subjects
        ref_img_path: str | Path | dict[str, str | Path] | None = Path(ref_img)
    elif isinstance(ref_img, dict):
        # Per-subject reference images - convert values to Path objects
        ref_img_path = {subject_id: Path(path) for subject_id, path in ref_img.items()}
    else:
        ref_img_path = None

    # Special handling for atlas_views round - generate once for all subjects
    if round_name == "atlas_views":
        if atlas_files is None:
            logger.warning("No atlas_files provided, skipping atlas_views round")
            return

        # Create a shared atlas output directory
        atlas_output_dir = output_dir / "atlas_views"
        atlas_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate atlas views once for each tract
        atlas_results: dict[str, dict[str, dict[str, str]]] = {}
        for tract_name, atlas_file in atlas_files.items():
            logger.info("Generating atlas views for tract: %s", tract_name)
            try:
                atlas_views = visualizer.generate_atlas_views(
                    atlas_file,
                    atlas_ref_img=atlas_ref_img,
                    flip_lr=flip_lr,
                    output_dir=atlas_output_dir,
                    **config.get("atlas_kwargs", {}),
                )

                # Add atlas views to results for all subjects that have this tract
                for subject_id, tracts in subjects_original_space.items():
                    if tract_name in tracts:
                        if subject_id not in atlas_results:
                            atlas_results[subject_id] = {}
                        if tract_name not in atlas_results[subject_id]:
                            atlas_results[subject_id][tract_name] = {}
                        # Add atlas views with the same keys as in the workflow
                        for view_name, view_path in atlas_views.items():
                            atlas_results[subject_id][tract_name][f"atlas_{view_name}"] = str(view_path)

                # Clean up after each atlas
                del atlas_views
                gc.collect()
            except Exception as e:
                logger.exception("Failed to generate atlas views for %s: %s", tract_name, e)

        # Also generate subject MNI views if subjects_mni_space is provided
        # These are needed for atlas comparison even though atlas views are generated once
        if subjects_mni_space is not None:
            logger.info("Generating subject MNI views for atlas comparison")
            for subject_id, tracts in subjects_mni_space.items():
                subject_output_dir = output_dir / subject_id
                for tract_name, tract_file_mni in tracts.items():
                    if tract_name in atlas_files:  # Only generate if atlas exists
                        tract_output_dir = subject_output_dir / tract_name
                        tract_output_dir.mkdir(parents=True, exist_ok=True)
                        try:
                            subject_mni_views = visualizer.generate_anatomical_views(
                                tract_file_mni,
                                ref_img=atlas_ref_img,  # Use atlas ref image for MNI space
                                output_dir=tract_output_dir,
                                **config.get("subject_kwargs", {}),
                            )
                            # Add subject MNI views to results
                            if subject_id not in atlas_results:
                                atlas_results[subject_id] = {}
                            if tract_name not in atlas_results[subject_id]:
                                atlas_results[subject_id][tract_name] = {}
                            for view_name, view_path in subject_mni_views.items():
                                atlas_results[subject_id][tract_name][f"subject_mni_{view_name}"] = str(view_path)
                            del subject_mni_views
                            gc.collect()
                        except Exception as e:
                            logger.exception(
                                "Failed to generate subject MNI views for %s/%s: %s",
                                subject_id,
                                tract_name,
                                e,
                            )

        # Merge atlas results into existing results
        save_and_merge_results(atlas_results, results_file)
        # existing_results = merge_results(existing_results,atlas_results)
        # save_results(existing_results, results_file)
        logger.info("Atlas views round completed")
        return

    # For other rounds, run the normal workflow with skip_checks
    try:
        round_results = visualizer.run_quality_check_workflow(
            subjects_original_space=subjects_original_space,
            ref_img=ref_img_path,
            subjects_mni_space=subjects_mni_space,
            atlas_files=atlas_files,
            metric_files=metric_files,
            atlas_ref_img=atlas_ref_img,
            flip_lr=flip_lr,
            output_dir=output_dir,
            skip_checks=skip_checks,
            html_output=None,  # Don't generate HTML in individual rounds
            subject_kwargs=config.get("subject_kwargs"),
            atlas_kwargs=config.get("atlas_kwargs"),
            **config.get("kwargs", {}),
        )

        # Merge results
        # existing_results = merge_results(existing_results, round_results)
        # save_results(existing_results, results_file)
        save_and_merge_results(round_results, results_file)
        logger.info("Round %s completed successfully", round_name)
    except Exception as e:
        logger.exception("Error in round %s: %s", round_name, e)
        raise
    finally:
        # Clean up visualizer
        del visualizer
        gc.collect()


def generate_html(config: dict, results_file: Path, output_dir: Path) -> None:
    """Generate HTML report from accumulated results."""
    logger.info("=" * 80)
    logger.info("Generating HTML report")
    logger.info("=" * 80)

    # Load all results
    results = load_results(results_file)

    if not results:
        logger.warning("No results found, cannot generate HTML report")
        return

    # Convert string paths back to Path objects for HTML generation
    results_for_html: dict[str, dict[str, dict[str, str]]] = {}
    for subject_id, subject_tracts in results.items():
        results_for_html[subject_id] = {}
        if isinstance(subject_tracts, dict):
            for tract_name, media_dict in subject_tracts.items():
                results_for_html[subject_id][tract_name] = {}
                if isinstance(media_dict, dict):
                    for media_type, file_path in media_dict.items():
                        results_for_html[subject_id][tract_name][media_type] = str(file_path)

    # Generate HTML
    html_output = config.get("html_output")
    if html_output is None:
        html_output = output_dir / "quality_check_report.html"
    else:
        html_output = Path(html_output)

    create_quality_check_html(
        results_for_html,
        str(html_output),
        title="Tractography Quality Check Report",
    )
    logger.info("HTML report generated: %s", html_output)


def run_all_rounds(
    config: dict,
    results_file: Path,
    output_dir: Path,
    skip_rounds: list[str] | None = None,
    batch_index: int | None = None,
    num_batches: int | None = None,
    batch_start_index: int = 0,
) -> None:
    """Run all rounds sequentially.

    Parameters
    ----------
    config : dict
        Configuration dictionary.
    results_file : Path
        Path to results JSON file.
    output_dir : Path
        Output directory.
    skip_rounds : list[str] | None, optional
        List of rounds to skip.
    batch_index : int | None, optional
        Batch index (1-indexed) if running in batch mode.
    num_batches : int | None, optional
        Total number of batches. Required if batch_index is provided.
    batch_start_index : int, optional
        Starting index for batch numbering (0 or 1). Default is 0.
    """
    if skip_rounds is None:
        skip_rounds = []

    # Define rounds in order
    rounds = [
        "anatomical",
        "cci",
        "before_after_cci",
        "atlas_views",
        "shape_similarity",
        "afq_profile",
        "bundle_assignment",
    ]

    logger.info("=" * 80)
    logger.info("Running quality check workflow in rounds")
    logger.info("=" * 80)
    logger.info("Config file: %s", config.get("_config_path", "N/A"))
    logger.info("Output directory: %s", output_dir)
    logger.info("Results file: %s", results_file)
    logger.info("")

    # Run each round
    for round_name in rounds:
        if round_name in skip_rounds:
            logger.info("Skipping round: %s", round_name)
            continue

        logger.info("")
        logger.info("=" * 80)
        logger.info("Running round: %s", round_name)
        logger.info("=" * 80)

        try:
            run_round(
                round_name,
                config,
                results_file,
                output_dir,
                batch_index,
                num_batches,
                batch_start_index,
            )
            logger.info("Round %s completed successfully", round_name)
        except Exception as e:
            logger.exception("ERROR: Round %s failed: %s", round_name, e)
            raise

        # Force garbage collection and memory clearing between rounds
        logger.debug("Clearing memory between rounds...")
        gc.collect()

    # Generate HTML report at the end (only if not in batch mode or if it's the last batch)
    if batch_index is None or (num_batches is not None and batch_index == num_batches):
        logger.info("")
        logger.info("=" * 80)
        logger.info("Generating HTML report")
        logger.info("=" * 80)

        try:
            generate_html(config, results_file, output_dir)
            logger.info("HTML report generated successfully")
        except Exception:
            logger.exception("ERROR: HTML generation failed")
            raise

    logger.info("")
    logger.info("=" * 80)
    logger.info("All rounds completed successfully!")
    logger.info("=" * 80)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run quality check workflow in separate rounds for memory management",
    )
    parser.add_argument(
        "round",
        nargs="?",
        choices=[
            "anatomical",
            "cci",
            "before_after_cci",
            "atlas_views",
            "shape_similarity",
            "afq_profile",
            "bundle_assignment",
            "html",
            "all",
        ],
        default="all",
        help="Round to run (default: 'all' to run all rounds sequentially)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to JSON configuration file",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=None,
        help="Path to JSON file for accumulating results (default: <output_dir>/results.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (overrides config)",
    )
    parser.add_argument(
        "--skip",
        action="append",
        help="Skip specific rounds (can be used multiple times)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--batch-index",
        type=int,
        default=None,
        help="Batch index (1-indexed) for SLURM array jobs. "
        "If not provided, will check SLURM_ARRAY_TASK_ID environment variable.",
    )
    parser.add_argument(
        "--num-batches",
        type=int,
        default=None,
        help="Total number of batches. Required when using --batch-index or SLURM arrays.",
    )
    parser.add_argument(
        "--subjects",
        nargs="+",
        default=None,
        help="List of subject IDs to process (overrides config and batch filtering)",
    )
    parser.add_argument(
        "--subjects-file",
        type=Path,
        default=None,
        help="File containing subject IDs to process (one per line, # for comments)",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load config
    config = load_config(args.config)
    # Store config path for logging
    config["_config_path"] = str(args.config)

    # Handle subject filtering from command line (optional - batch mode will auto-infer from config)
    if args.subjects_file is not None:
        subject_list = load_subject_list(args.subjects_file)
        logger.info("Loaded %d subjects from file: %s", len(subject_list), args.subjects_file)
        config["subject_list"] = subject_list
    elif args.subjects is not None:
        logger.info("Using %d subjects from command line", len(args.subjects))
        config["subject_list"] = args.subjects
    else:
        # No explicit subjects provided - will auto-infer from config and batch
        logger.info("No explicit subject list provided - will infer from config and SLURM array")

    # Determine output directory
    output_dir = args.output_dir
    if output_dir is None:
        output_dir = Path(config.get("output_dir", "output"))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine results file
    results_file = args.results_file
    if results_file is None:
        results_file = output_dir / "results.json"
    results_file = Path(results_file)

    # Determine skip rounds
    skip_rounds = args.skip if args.skip else []

    # Handle batch mode (SLURM array jobs)
    batch_index = args.batch_index
    num_batches = args.num_batches

    # Determine if batches are 0-indexed or 1-indexed
    # Check SLURM_ARRAY_TASK_MIN to determine indexing
    batch_start_index = 0  # Default to 0-indexed
    array_task_min = os.environ.get("SLURM_ARRAY_TASK_MIN")
    if array_task_min is not None:
        try:
            min_id = int(array_task_min)
            batch_start_index = min_id
            logger.debug("Detected batch start index: %d", batch_start_index)
        except ValueError:
            pass

    # Also check config for batch_start_index
    if "batch_start_index" in config:
        batch_start_index = config["batch_start_index"]
        logger.info("Using batch_start_index from config: %d", batch_start_index)

    # If batch_index not provided, check SLURM_ARRAY_TASK_ID
    if batch_index is None:
        batch_index = get_slurm_array_task_id()
        if batch_index is not None:
            logger.info("Detected SLURM array job with task ID: %d (start index: %d)", batch_index, batch_start_index)
            # Also try to get num_batches from SLURM if not provided
            if num_batches is None:
                num_batches = get_slurm_array_task_count()
                if num_batches is not None:
                    logger.info("Detected SLURM array job with %d total tasks", num_batches)

    # If we have batch info, log which subjects will be processed
    if batch_index is not None and num_batches is not None:
        subjects_in_config = config.get("subjects_original_space", {})
        if subjects_in_config:
            try:
                batch_subjects = get_subjects_for_batch(
                    subjects_in_config,
                    batch_index,
                    num_batches,
                    batch_start_index,
                )
                logger.info(
                    "Batch %d/%d (start: %d) will process %d subjects: %s",
                    batch_index,
                    num_batches,
                    batch_start_index,
                    len(batch_subjects),
                    ", ".join(batch_subjects) if batch_subjects else "(none)",
                )
            except Exception as e:
                logger.debug("Could not determine batch subjects: %s", e)

    # Check if num_batches is in config (only if not already set)
    if num_batches is None:
        num_batches = config.get("num_batches")

    # If we have a batch_index, we need num_batches
    if batch_index is not None and num_batches is None:
        logger.error(
            "Batch index provided but num_batches is missing. "
            "Please provide --num-batches, set it in the config file, "
            "or run this script as part of a SLURM array job.",
        )
        return 1

    # If we have batch_index, validate it
    if batch_index is not None:
        if num_batches is None:
            logger.error("num_batches must be provided when using batch mode")
            return 1
        max_batch_index = batch_start_index + num_batches - 1
        if batch_index < batch_start_index or batch_index > max_batch_index:
            logger.error(
                "Batch index %d is out of range (%d-%d)",
                batch_index,
                batch_start_index,
                max_batch_index,
            )
            return 1

    try:
        if args.round == "generate-slurm":
            logger.error("generate-slurm is not implemented")
            return 1
        if args.round == "all":
            run_all_rounds(
                config,
                results_file,
                output_dir,
                skip_rounds=skip_rounds,
                batch_index=batch_index,
                num_batches=num_batches,
                batch_start_index=batch_start_index,
            )
        elif args.round == "html":
            generate_html(config, results_file, output_dir)
        else:
            run_round(
                args.round,
                config,
                results_file,
                output_dir,
                batch_index=batch_index,
                num_batches=num_batches,
                batch_start_index=batch_start_index,
            )
    except Exception:
        logger.exception("Fatal error")
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
