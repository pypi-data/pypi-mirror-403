class GTConfig:

    def __init__(self, bams, **kwargs):
        self.bam = bams
        self.covs = {}
        self.outdir = kwargs.get("outdir")
        self.minimum_coverage = kwargs.get("minimum_coverage")
        self.t_step = kwargs.get("t_step")
        self.t_max = kwargs.get("t_max")
        self.mu = kwargs.get("mu")
        self.size = kwargs.get("size")
        self.mt = kwargs.get("mt")
        self.compute_ci = kwargs.get("compute_ci")
        self.bootstrap_replicates = kwargs.get("bootstrap_replicates")
        self.conf = kwargs.get("conf")
        self.fasta = kwargs.get("fasta")
        self.genome = kwargs.get("genome")
        self.rrbs = kwargs.get("rrbs")
        self.threads = kwargs.get("threads")
        self.keep_temporary_files = kwargs.get("keep_temporary_files")
        self.verbose = kwargs.get("verbose")
