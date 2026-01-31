import subprocess
import os
import yaml


def test_methurator_downsample_withci(tmp_path):
    """Test the 'methurator downsample' CLI command."""

    # Define the command as a list (like in subprocess)
    cmd = [
        "methurator",
        "gt-estimator",
        "tests/data/Ecoli.csorted.bam",
        "--fasta",
        "tests/data/genome.fa",
        "-mc",
        "1,3",
        "--compute_ci",
        "--outdir",
        str(tmp_path),
    ]

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Paths of the expected outputs
    yaml_summary = os.path.join(tmp_path, "methurator_summary.yml")

    # Assert that output files exist
    error_info = f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert os.path.exists(yaml_summary), f"{yaml_summary} not found{error_info}"

    # Validate YAML structure
    with open(yaml_summary) as f:
        yaml_data = yaml.safe_load(f)

    assert "methurator_summary" in yaml_data
    summary = yaml_data["methurator_summary"]

    # Check metadata fields
    assert "metadata" in summary
    metadata = summary["metadata"]
    assert "date_generated" in metadata
    assert "methurator_version" in metadata
    assert "command" in metadata
    assert metadata["command"] == "methurator gt_estimator"
    assert "options" in metadata

    # Check options
    options = metadata["options"]
    assert "cov_files" in options
    assert "outdir" in options
    assert "minimum_coverage" in options
    assert "t_step" in options
    assert "t_max" in options

    # Validate gt_summary structure
    # Format: [{sample_name: [{minimum_coverage: X, data: [[t, saturation, total_cpgs, ci_low, ci_high], ...]}, ...]}, ...]
    assert "gt_summary" in summary
    gt_summary = summary["gt_summary"]
    assert isinstance(gt_summary, list)
    assert len(gt_summary) > 0

    # Check first sample entry
    first_sample_entry = gt_summary[0]
    assert isinstance(first_sample_entry, dict)
    sample_name = list(first_sample_entry.keys())[0]
    sample_data = first_sample_entry[sample_name]
    assert isinstance(sample_data, list)
    assert len(sample_data) >= 1

    # Check first coverage entry (minimum_coverage == 1)
    first_coverage_entry = sample_data[0]
    assert isinstance(first_coverage_entry, dict)
    assert "minimum_coverage" in first_coverage_entry
    assert "data" in first_coverage_entry
    assert first_coverage_entry["minimum_coverage"] == 1

    # Each data entry should be [t, extrapolated, total_cpgs, ci_low, ci_high]
    data_points = first_coverage_entry["data"]
    assert isinstance(data_points, list)
    assert len(data_points) > 0
    first_data_point = data_points[0]
    assert len(first_data_point) == 5
    assert isinstance(first_data_point[0], (int, float))  # t value
    assert isinstance(first_data_point[1], float)  # saturation
    assert isinstance(first_data_point[2], int)  # total_cpgs

    # Check second coverage entry if it exists (minimum_coverage == 3)
    if len(sample_data) >= 2:
        second_coverage_entry = sample_data[1]
        assert isinstance(second_coverage_entry, dict)
        assert "minimum_coverage" in second_coverage_entry
        assert "data" in second_coverage_entry
        assert second_coverage_entry["minimum_coverage"] == 3
        assert len(second_coverage_entry["data"]) > 0


def test_methurator_downsample(tmp_path):
    """Test the 'methurator downsample' CLI command."""

    # Define the command as a list (like in subprocess)
    cmd = [
        "methurator",
        "gt-estimator",
        "tests/data/Ecoli.csorted.bam",
        "--fasta",
        "tests/data/genome.fa",
        "-mc",
        "1,3",
        "--outdir",
        str(tmp_path),
    ]

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Paths of the expected outputs
    yaml_summary = os.path.join(tmp_path, "methurator_summary.yml")

    # Assert that output files exist
    error_info = f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert os.path.exists(yaml_summary), f"{yaml_summary} not found{error_info}"

    # Validate YAML structure
    with open(yaml_summary) as f:
        yaml_data = yaml.safe_load(f)

    assert "methurator_summary" in yaml_data
    summary = yaml_data["methurator_summary"]

    # Check metadata fields
    assert "metadata" in summary
    metadata = summary["metadata"]
    assert "date_generated" in metadata
    assert "methurator_version" in metadata
    assert "command" in metadata
    assert metadata["command"] == "methurator gt_estimator"
    assert "options" in metadata

    # Check options
    options = metadata["options"]
    assert "cov_files" in options
    assert "outdir" in options
    assert "minimum_coverage" in options
    assert "t_step" in options
    assert "t_max" in options

    # Validate gt_summary structure
    # Format: [{sample_name: [{minimum_coverage: X, data: [[t, extrapolated, total_cpgs, ci_low, ci_high], ...]}, ...]}, ...]
    assert "gt_summary" in summary
    gt_summary = summary["gt_summary"]
    assert isinstance(gt_summary, list)
    assert len(gt_summary) > 0

    # Check first sample entry
    first_sample_entry = gt_summary[0]
    assert isinstance(first_sample_entry, dict)
    sample_name = list(first_sample_entry.keys())[0]
    sample_data = first_sample_entry[sample_name]
    assert isinstance(sample_data, list)
    assert len(sample_data) >= 1

    # Check first coverage entry (minimum_coverage == 1)
    first_coverage_entry = sample_data[0]
    assert isinstance(first_coverage_entry, dict)
    assert "minimum_coverage" in first_coverage_entry
    assert "data" in first_coverage_entry
    assert first_coverage_entry["minimum_coverage"] == 1

    # Each data entry should be [t, extrapolated, total_cpgs, ci_low, ci_high]
    data_points = first_coverage_entry["data"]
    assert isinstance(data_points, list)
    assert len(data_points) > 0
    first_data_point = data_points[0]
    assert len(first_data_point) == 5
    assert isinstance(first_data_point[0], (int, float))  # t value
    assert isinstance(first_data_point[1], float)  # saturation
    assert isinstance(first_data_point[2], int)  # total_cpgs

    # Check second coverage entry if it exists (minimum_coverage == 3)
    if len(sample_data) >= 2:
        second_coverage_entry = sample_data[1]
        assert isinstance(second_coverage_entry, dict)
        assert "minimum_coverage" in second_coverage_entry
        assert "data" in second_coverage_entry
        assert second_coverage_entry["minimum_coverage"] == 3
        assert len(second_coverage_entry["data"]) > 0
