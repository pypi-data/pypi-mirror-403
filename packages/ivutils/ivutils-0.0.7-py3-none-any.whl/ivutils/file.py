import re
import os

def reindex_file_sequence(src_dir: str, file_pattern: str, precision: int = 1, init_seq_val: int = 0):
    """
    Analyses all the files of a directory to filter on a sequence pattern. Then iterates over the pattern to find any missing values and re-indexes the files to form a continious sequence

    :param src_dir:
    :param file_pattern:
    :param precision:
    :param init_seq_val:
    :return:
    """

    def sequence_generator():
        seq_id = init_seq_val
        seq_id_pattern = re.compile(file_pattern).pattern
        seq_id_pattern = seq_id_pattern.replace("^", "").replace("$", "").replace("__", "_")
        while True:
            file_name = seq_id_pattern.replace("(?P<seq_id>\\d{6})", f"{seq_id:0{precision}d}").replace("\\", "")
            yield file_name
            seq_id += 1

    files = [f for f in os.listdir(src_dir) if re.search(file_pattern, f)]
    seq_gen = sequence_generator()
    for actual in files:
        expected = next(seq_gen)
        print(f"expected: {expected}")
        if actual != expected:
            print(f"rename {actual} to {expected}")
            os.rename(os.path.join(src_dir, actual), os.path.join(src_dir, expected))
