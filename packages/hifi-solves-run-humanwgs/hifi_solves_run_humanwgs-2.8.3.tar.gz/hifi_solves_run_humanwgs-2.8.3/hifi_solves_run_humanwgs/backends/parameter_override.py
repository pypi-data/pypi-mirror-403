"""
A set of common functions across all cloud platforms
to override parameters to generate inputs.
"""

# Memory override input keys - these are excluded from the inputs hash
# when determining run identity, since they represent resource configuration
# rather than changes to the actual analysis being performed.
MEMORY_OVERRIDE_KEYS = {
    "HumanWGS_wrapper.hiphase_override_mem_gb",
    "HumanWGS_wrapper.merge_bam_stats_override_mem_gb",
    "HumanWGS_wrapper.pbmm2_align_wgs_override_mem_gb",
    "HumanWGS_wrapper.pbstarphase_diplotype_override_mem_gb",
    "HumanWGS_wrapper.pbsv_discover_override_mem_gb",
    "HumanWGS_wrapper.pbsv_call_mem_gb",
}


def generate_memory_override_inputs(overrides) -> dict:
    """
    Generate a dictionary containing key values pairs for memory
    overrides from the command line.

    Arguments:
        overrides (dict): A dictionary of memory override keys and associated values

    Returns:
        overrides (dict): A set of input arguments for memory overrides
    """
    # check for memory overrides
    mem_override_inputs = {}

    if overrides['hiphase_override_mem_gb'] is not None:
        mem_override_inputs.update({
            "HumanWGS_wrapper.hiphase_override_mem_gb": overrides['hiphase_override_mem_gb']
        })
    if overrides['merge_bam_stats_override_mem_gb'] is not None:
        mem_override_inputs.update({
            "HumanWGS_wrapper.merge_bam_stats_override_mem_gb": overrides['merge_bam_stats_override_mem_gb']
        })
    if overrides['pbmm2_align_wgs_override_mem_gb'] is not None:
        mem_override_inputs.update({
            "HumanWGS_wrapper.pbmm2_align_wgs_override_mem_gb": overrides['pbmm2_align_wgs_override_mem_gb']
        })
    if overrides['pbstarphase_diplotype_override_mem_gb'] is not None:
        mem_override_inputs.update({
            "HumanWGS_wrapper.pbstarphase_diplotype_override_mem_gb": overrides['pbstarphase_diplotype_override_mem_gb']
        })
    if overrides['pbsv_discover_override_mem_gb'] is not None:
        mem_override_inputs.update({
            "HumanWGS_wrapper.pbsv_discover_override_mem_gb": overrides['pbsv_discover_override_mem_gb']
        })
    if overrides['pbsv_call_mem_gb'] is not None:
        mem_override_inputs.update({
            "HumanWGS_wrapper.pbsv_call_mem_gb": overrides['pbsv_call_mem_gb']
        })

    return mem_override_inputs
