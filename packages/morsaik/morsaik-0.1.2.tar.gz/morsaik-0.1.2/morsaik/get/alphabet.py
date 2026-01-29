def alphabet(strand_trajectory_id : str) -> list:
    from ..read.strand_reactor_nucleotides import strand_reactor_nucleotides as read_strand_reactor_nucleotides
    from ..utils.manage_strand_reactor_files import _create_typical_alphabet_filepath
    filepath = _create_typical_alphabet_filepath(strand_trajectory_id)
    return read_strand_reactor_nucleotides(filepath)
