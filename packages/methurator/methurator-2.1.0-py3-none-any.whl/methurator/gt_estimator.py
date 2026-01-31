import rich_click as click
from rich.console import Console
from rich.panel import Panel
import importlib.metadata
from methurator.gt_utils.run_estimator import run_estimator
from methurator.gt_utils.config_validator import GTConfig
from methurator.gt_utils.yaml_summary import generate_yaml_summary
from methurator.config_utils.bam_utils import bam_to_list
from methurator.gt_utils.methyldackel import run_methyldackel
from methurator.config_utils.validation_utils import (
    validate_dependencies,
    validate_reference,
    mincoverage_checker,
)
from methurator.config_utils.config_validator import available_cpus
import shutil
import os

console = Console()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument(
    "bams",
    type=click.Path(),
    required=True,
    nargs=-1,
    help="Path to a single .bam file or to multiple ones (e.g. files/*.bam).",
)
@click.option(
    "--minimum-coverage",
    "-mc",
    default="1",
    help="CpG coverage to estimate sequencing saturation. "
    "It can be either a single integer or a list of integers (e.g 1,3,5). Default: 3",
)
@click.option(
    "--t-step",
    default=0.05,
    help="Step size taken when predicting future unique CpGs at increasing depth. Default: 0.05",
)
@click.option(
    "--t-max",
    type=click.FloatRange(min=2.0, max=1000.0),
    default=10.0,
    help="Maximum value of t for prediction. Default: 10.0",
)
@click.option(
    "--compute_ci",
    is_flag=True,
    help="Compute confidence intervals. Default: False",
)
@click.option(
    "--bootstrap-replicates",
    "-b",
    type=click.IntRange(min=10, max=100),
    default=30,
    help="Number of bootstrap replicates. Default: 30",
)
@click.option(
    "--conf",
    type=click.FloatRange(min=0.1, max=0.99),
    default=0.95,
    help="Confidence level for the bootstrap confidence intervals. Default: 0.95",
)
@click.option(
    "--mu",
    type=float,
    default=0.5,
    help="Initial value for the mu parameter in the negative binomial distribution for the EM algorithm. Default: 0.5",
)
@click.option(
    "--size",
    type=float,
    default=1.0,
    help="A positive double, the initial value of the parameter size in the negative binomial distribution for the EM algorithm. Default value is 1.",
)
@click.option(
    "--mt",
    type=int,
    default=20,
    help="An positive integer constraining possible rational function approximations. Default is 20.",
)
@click.option(
    "--rrbs",
    is_flag=True,
    help="If set to True, MethylDackel extract will consider the RRBS nature of the data "
    "adding the --keepDupes flag. Default: False",
)
@click.option(
    "--threads",
    "-@",
    type=int,
    default=lambda: max(1, available_cpus() - 2),
    help="Number of threads to use. Default: all available threads - 2.",
)
@click.option(
    "--fasta",
    type=click.Path(exists=True),
    help="Fasta file of the reference genome used to align the samples. "
    "If not provided, it will download it according to the specified genome.",
)
@click.option(
    "--genome",
    type=click.Choice(["hg19", "hg38", "GRCh37", "GRCh38", "mm10", "mm39"]),
    default=None,
    help="Genome used to align the samples.",
)
@click.option(
    "--keep-temporary-files",
    "-k",
    is_flag=True,
    help="If set to True, temporary files will be kept after the analysis. Default: False",
)
@click.option(
    "--outdir",
    "-o",
    type=click.Path(),
    default="output",
    help="Default output directory.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging.")
@click.version_option(importlib.metadata.version("methurator"))
def gt_estimator(bams, **kwargs):
    """Fit the Chao estimator."""

    # Import and validate params
    configs = GTConfig(bams, **kwargs)
    validate_reference(configs)
    mincoverage_checker(configs.minimum_coverage)
    # Check that required external tools are installed
    validate_dependencies()

    params_text = ""

    # ── Input / Output ─────────────────────────────────────────────
    params_text += "[bold underline]Input / Output[/bold underline]\n"
    params_text += (
        f"[purple]Input BAM files:[/purple] [blue]{', '.join(configs.bam)}[/blue]\n"
    )
    if configs.fasta is not None:
        params_text += (
            f"[purple]Reference FASTA:[/purple] [blue]{configs.fasta}[/blue]\n"
        )
    if configs.genome is not None:
        params_text += f"[purple]Genome:[/purple] [blue]{configs.genome}[/blue]\n"
    params_text += f"[purple]Output directory:[/purple] [blue]{configs.outdir}[/blue]\n"
    params_text += f"[purple]Minimum coverage:[/purple] [blue]{configs.minimum_coverage}[/blue]\n\n"

    # ── Model parameters ───────────────────────────────────────────
    params_text += "[bold underline]Model parameters[/bold underline]\n"
    params_text += f"[purple]mu:[/purple] [blue]{configs.mu}[/blue]\n"
    params_text += f"[purple]size:[/purple] [blue]{configs.size}[/blue]\n"
    params_text += f"[purple]mt:[/purple] [blue]{configs.mt}[/blue]\n"
    params_text += f"[purple]t step size:[/purple] [blue]{configs.t_step}[/blue]\n"
    params_text += f"[purple]t max:[/purple] [blue]{configs.t_max}[/blue]\n\n"

    # ── Confidence Intervals ───────────────────────────────────────
    params_text += "[bold underline]Confidence intervals[/bold underline]\n"
    params_text += f"[purple]Compute confidence intervals:[/purple] [blue]{configs.compute_ci}[/blue]\n"
    if configs.compute_ci:
        params_text += (
            f"[purple]Confidence level:[/purple] [blue]{configs.conf}[/blue]\n"
        )
        params_text += f"[purple]Bootstrap replicates:[/purple] [blue]{configs.bootstrap_replicates}[/blue]\n"
    params_text += "\n"

    # ── Other options ────────────────────────────────────────
    params_text += "[bold underline]Other options[/bold underline]\n"
    params_text += f"[purple]Threads:[/purple] [blue]{configs.threads}[/blue]\n"
    params_text += f"[purple]Verbose:[/purple] [blue]{configs.verbose}[/blue]\n"
    params_text += f"[purple]Keep temporary files:[/purple] [blue]{configs.keep_temporary_files}[/blue]"

    console.print(
        Panel(
            params_text,
            title="📌 [bold cyan]Run configuration[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )

    # Sanity checks on the bams
    csorted_bams = bam_to_list(configs)

    # Generate the .COV files
    covs = {}
    for bam in csorted_bams:
        cov, reads = run_methyldackel(bam, configs)
        covs[cov] = reads
    configs.covs = covs

    # Run the estimator
    df = run_estimator(configs)

    # Generate the .YAML summary
    generate_yaml_summary(df, configs)

    # Clean-up
    if not configs.keep_temporary_files:
        shutil.rmtree(os.path.join(configs.outdir, "covs"))
        if os.path.exists(os.path.join(configs.outdir, "bams")):
            shutil.rmtree(os.path.join(configs.outdir, "bams"))
