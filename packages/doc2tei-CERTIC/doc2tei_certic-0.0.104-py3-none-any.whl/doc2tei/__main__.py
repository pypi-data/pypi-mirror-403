import logging
import sys

import argh
from doc2tei import _process_doc
import os
import shutil
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def _convert_file(
    input_file_path: str,
    keep_transient_files: bool = False,
    schema: str = "metopes",
    out_dir: str = None,
    verbose: bool = False,
):
    """
    Converts a *.docx file to XML TEI.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    destination_folder = os.path.dirname(os.path.abspath(input_file_path))
    if out_dir:
        out_dir = os.path.abspath(out_dir)
        if (
            out_dir == destination_folder
        ):  # when out_dir is the directory of input_file_path...
            out_dir = None  # ...this is effectively the same as not specifying out_dir
        else:
            os.makedirs(out_dir, exist_ok=True)
            copy_dest = os.path.join(out_dir, os.path.basename(input_file_path))
            shutil.copy(input_file_path, copy_dest)
            input_file_path = copy_dest
            destination_folder = out_dir
    if not os.path.exists(input_file_path):
        sys.exit(f"no such file: {input_file_path}")
    success, output = _process_doc(
        input_file_path,
        destination_folder,
        logger,
        keep_transient_files,
        schema,
    )
    if not success:
        sys.exit(output)


def run_cli():
    argh.dispatch_command(_convert_file)


if __name__ == "__main__":
    run_cli()
