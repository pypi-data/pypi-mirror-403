def strand_reactor_nucleotides(filepath : str) -> list:
    file1 = open(filepath, 'r')
    lines = file1.readlines()[0].rstrip('\n')
    return list(lines)
