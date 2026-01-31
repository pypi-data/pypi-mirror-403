import subprocess
import os
import pandas as pd
from rich.console import Console
from rich.panel import Panel

console = Console()


def run_methyldackel(bam_path, configs):

    # Create covs directory to store coverage files
    cov_dir = os.path.join(configs.outdir, "covs")
    os.makedirs(cov_dir, exist_ok=True)

    # Compute number of reads
    cmd = ["samtools", "view", "-c", bam_path]
    # Run command
    num_reads = subprocess.run(
        cmd, capture_output=True, text=True, check=True
    ).stdout.strip()

    # Use the BAM filename (without directories) as prefix
    bam_name = os.path.basename(bam_path)
    prefix = os.path.join(cov_dir, os.path.splitext(bam_name)[0])
    cmd = [
        "MethylDackel",
        "extract",
        "-@",
        str(configs.threads),
        "-o",
        str(prefix),
        configs.fasta,
        bam_path,
    ]

    # Add RRBS-specific argument if config.rrbs is True
    if configs.rrbs:
        cmd.append("--keepDupes")

    # Run command
    subprocess.run(cmd)

    # Read the file dumped by MethylDackel
    file = prefix + "_CpG.bedGraph"

    # Check if file has data (more than just header)
    try:
        df = pd.read_csv(file, sep="\t", header=None, skiprows=1)
        if df.empty:
            raise pd.errors.EmptyDataError("MethylDackel output file is empty")
    except pd.errors.EmptyDataError:
        warning_message = (
            f"[bold red]⚠ MethylDackel Error[/bold red]\n\n"
            f"MethylDackel produced no data for:\n"
            f"[yellow]{bam_path}[/yellow]\n\n"
            f"[dim]This may be due to chromosome mismatch with reference genome.[/dim]\n"
            f"[bold]Skipping sample: {os.path.basename(bam_path)}[/bold]"
        )
        console.print(Panel(warning_message, border_style="red", expand=False))

    # gzip the file and return the stats
    subprocess.run(["gzip", "-f", f"{prefix}_CpG.bedGraph"])

    return file + ".gz", num_reads
