import importlib.metadata
import os
from datetime import datetime
import yaml


def _represent_compact_list(dumper, data):
    """Custom YAML representer that uses flow style for numeric tuples."""
    if (
        isinstance(data, list)
        and len(data) in (2, 3, 4, 5, 6)
        and all(isinstance(x, (float, bool, int, str, type(None))) for x in data)
    ):
        return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)

    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=False)


def generate_yaml_summary(res_df, configs):
    """Generate a YAML summary file containing all results and metadata."""
    # Build the GT estimator summary data structure, grouped by sample and coverage
    # Format: [{sample_name: [{minimum_coverage: X, data: [[t, saturation, total_cpgs, ci_low, ci_high], ...]}, ...]}, ...]
    gt_estimator_by_sample = {}
    for _, row in res_df.iterrows():
        sample = row["sample"]
        min_cov = int(row["min_cov"])
        if sample not in gt_estimator_by_sample:
            gt_estimator_by_sample[sample] = {}
        if min_cov not in gt_estimator_by_sample[sample]:
            gt_estimator_by_sample[sample][min_cov] = []

        gt_estimator_by_sample[sample][min_cov].append(
            [
                round(float(row["t"]), 2),
                int(row["asymptote"]),
                float(row["saturation"]),
                int(row["total_cpgs"]),
                row["ci_low"],
                row["ci_high"],
            ]
        )

    # Restructure to list of dicts with minimum_coverage and data
    gt_estimator_data = []
    for sample, cov_dict in gt_estimator_by_sample.items():
        # Same observed num reads for the same sample
        # so I take the first occurrence
        reads = int(res_df[res_df["sample"] == sample]["reads"].iloc[0])
        sample_data = []
        for min_cov, data_list in cov_dict.items():
            # Same asymptote for each sample, so I take the first occurence
            asymptote = int(data_list[0][1])
            data_list = [
                x[:1] + x[2:] for x in data_list
            ]  # remove asymptote from the list
            sample_data.append(
                {
                    "minimum_coverage": min_cov,
                    "reads": reads,
                    "asymptote(1000t)": asymptote,
                    "data": data_list,
                }
            )

        gt_estimator_data.append({sample: sample_data})

    # Build the command and options
    command_options = {
        "cov_files": [str(cov) for cov in configs.covs],
        "outdir": str(configs.outdir),
        "minimum_coverage": configs.minimum_coverage,
        "t_step": configs.t_step,
        "t_max": configs.t_max,
        "mu": configs.mu,
        "size": configs.size,
        "mt": configs.mt,
        "compute_ci": configs.compute_ci,
        "bootstrap_replicates": configs.bootstrap_replicates,
        "conf": configs.conf,
        "verbose": configs.verbose,
    }

    # Build the full YAML structure
    yaml_data = {
        "methurator_summary": {
            "metadata": {
                "date_generated": datetime.now().isoformat(),
                "methurator_version": importlib.metadata.version("methurator"),
                "command": "methurator gt_estimator",
                "options": command_options,
            },
            "gt_summary": gt_estimator_data,
        }
    }

    # Write to YAML file with compact list formatting
    yaml_path = os.path.join(configs.outdir, "methurator_summary.yml")
    yaml.add_representer(list, _represent_compact_list)
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    return yaml_path
