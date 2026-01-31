import pandas as pd
import os
import yaml
from methurator.plot_utils.plot_gtestimator import plot_gtestimator
from methurator.plot_utils.plot_functions import plot_fitted_data, plot_fallback


class PlotObject:
    def __init__(self, output_path=None):
        self.x_data = []
        self.y_data = []
        self.observed_y = []
        self.asymptote = str
        self.saturations = []
        self.is_predicted = []
        self.params = []
        self.title = str
        self.reads = int
        self.error_msg = None
        self.output_path = output_path

    @staticmethod
    def reads_to_df(reads_summary):
        """
        Convert the reads summary section from YAML into a pandas DataFrame.
        """
        rows = []
        for sample_block in reads_summary:
            for sample, values in sample_block.items():
                for percentage, reads in values:
                    rows.append(
                        {
                            "Sample": sample,
                            "Percentage": percentage,
                            "Read_Count": reads,
                        }
                    )

        return pd.DataFrame(rows)

    @staticmethod
    def cpgs_to_df(cpgs_summary):
        """
        Convert the CpGs summary section from YAML into a pandas DataFrame.
        """
        rows = []
        for sample_block in cpgs_summary:
            for sample, coverages in sample_block.items():
                for cov_block in coverages:
                    cov = cov_block["minimum_coverage"]

                    for percentage, cpgs in cov_block["data"]:
                        rows.append(
                            {
                                "Sample": sample,
                                "Coverage": cov,
                                "Percentage": percentage,
                                "CpG_Count": cpgs,
                            }
                        )

        return pd.DataFrame(rows)

    @staticmethod
    def build_saturation_lookup(saturation_summary):
        """
        Build a lookup dictionary for saturation model parameters,
        indexed by (sample, minimum_coverage).
        """
        lookup = {}
        for sample_block in saturation_summary:
            for sample, coverages in sample_block.items():
                for cov_block in coverages:
                    cov = cov_block["minimum_coverage"]

                    lookup[(sample, cov)] = {
                        "fit_success": cov_block.get("fit_success"),
                        "beta0": cov_block.get("beta0"),
                        "beta1": cov_block.get("beta1"),
                        "asymptote": cov_block.get("asymptote"),
                        "fit_error": cov_block.get("fit_error"),
                        "data": cov_block.get("data"),
                    }

        return lookup


class PlotGTEstObject:
    def __init__(self):
        self.t_data = []
        self.saturations = []
        self.cpgs_data = []
        self.ci_low = []
        self.ci_high = []
        self.asymptote = int
        self.min_cov = int
        self.sample_name = str
        self.output_path = str

    @staticmethod
    def build_saturation_lookup(saturation_summary):
        """
        Build a lookup dictionary for GT estimator,
        indexed by (sample, minimum_coverage).
        """
        lookup = {}
        for sample_block in saturation_summary:
            for sample, coverages in sample_block.items():
                for cov_block in coverages:
                    cov = cov_block["minimum_coverage"]

                    lookup[(sample, cov)] = {
                        "asymptote": cov_block.get("asymptote(1000t)"),
                        "reads": cov_block.get("reads"),
                        "data": cov_block.get("data"),
                    }

        return lookup


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def plot_curve(configs):
    """
    Main plotting function.
    Reads summary statistics, merges data, and generates saturation plots
    per sample and coverage level.
    """

    # Load YAML summary
    summary = load_yaml(configs.summary)["methurator_summary"]
    # Create output directory for plots if it does not exist
    plot_dir = os.path.join(configs.outdir, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    # If command was run without gt_estimator
    if "gt_summary" in summary:
        plot_gtobject = PlotGTEstObject()
        sat_lookup = PlotGTEstObject.build_saturation_lookup(summary["gt_summary"])

        # Iterate over samples and coverage levels
        for (sample, min_cov), info in sat_lookup.items():
            data_points = info.get("data", [])
            asymptote = info.get("asymptote", [])
            reads = info.get("reads", [])
            plot_gtobject.output_path = f"{plot_dir}/{sample}_{min_cov}x_plot.html"
            plot_gtobject.sample_name = sample
            plot_gtobject.min_cov = min_cov
            plot_gtobject.asymptote = asymptote
            plot_gtobject.reads = reads
            plot_gtobject.t_data = [x[0] for x in data_points]
            plot_gtobject.saturations = [x[1] for x in data_points]
            plot_gtobject.cpgs_data = [x[2] for x in data_points]
            plot_gtobject.ci_low = [x[3] for x in data_points]
            plot_gtobject.ci_high = [x[4] for x in data_points]
            plot_gtestimator(plot_gtobject)

    else:
        # Convert YAML summaries to DataFrames and merge them
        reads_df = PlotObject.reads_to_df(summary["reads_summary"])
        cpgs_df = PlotObject.cpgs_to_df(summary["cpgs_summary"])
        data = pd.merge(cpgs_df, reads_df, on=["Sample", "Percentage"])

        # Build saturation model lookup table
        sat_lookup = PlotObject.build_saturation_lookup(summary["saturation_analysis"])

        # Iterate over samples
        for sample in data["Sample"].unique():
            sample_data = data[data["Sample"] == sample]

            # Iterate over coverage values
            for min_val in sample_data["Coverage"].unique():

                # Subset data for the current sample and coverage
                subset = sample_data[sample_data["Coverage"] == min_val].sort_values(
                    by="Percentage"
                )

                # Retrieve saturation fit information from methurator_summary.yml
                # saturation_analysis section
                sat_info = sat_lookup.get((sample, min_val), {})
                fit_success = sat_info.get("fit_success")
                data_points = sat_info.get("data")
                if fit_success:
                    beta0 = sat_info["beta0"]
                    beta1 = sat_info["beta1"]
                    asymptote = sat_info["asymptote"]
                    fit_error = None
                else:
                    beta0 = beta1 = asymptote = None
                    fit_error = sat_info["fit_error"]

                # Define output plot path
                plot_path = f"{plot_dir}/{sample}_{min_val}x_plot.html"

                # Initialize PlotObject and populate it with data
                plot_obj = PlotObject(plot_path)
                plot_obj.x_data = [x[0] for x in data_points]
                plot_obj.y_data = [y[1] for y in data_points]
                # observed_y contains only the observed CpG counts
                # while y_data contains predicted CpG counts for all points
                # even the observed ones
                plot_obj.observed_y = [0] + subset.CpG_Count.tolist()
                plot_obj.saturations = [sat[2] for sat in data_points]
                plot_obj.is_predicted = [pred[3] for pred in data_points]
                plot_obj.params = beta0, beta1
                plot_obj.asymptote = asymptote
                plot_obj.error_msg = fit_error
                plot_obj.title = sample
                # Total number of reads at 0% downsampling (raw bam file)
                plot_obj.reads = int(subset["Read_Count"].iloc[-1])

                # Generate plot depending on fit success
                if fit_success:
                    plot_fitted_data(plot_obj)
                else:
                    plot_fallback(plot_obj)
