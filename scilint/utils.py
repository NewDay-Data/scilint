# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/utils.ipynb.

# %% auto 0
__all__ = ['logger', 'get_project_root', 'configure_logging', 'run_nbqa_cmd', 'is_nbdev_project', 'resolve_nbs',
           'find_common_root', 'get_excluded_paths', 'remove_ipython_special_directives', 'safe_div', 'get_cell_code']

# %% ../nbs/utils.ipynb 2
import ast
import logging
import sys
from configparser import InterpolationMissingOptionError
from importlib import reload
from pathlib import Path
from typing import Iterable

import nbformat
import pandas as pd
from fastcore.xtras import globtastic
from nbdev.config import get_config
from nbdev.doclinks import nbglob
from nbqa.__main__ import _get_configs, _main
from nbqa.cmdline import CLIArgs
from nbqa.find_root import find_project_root

reload(logging)
logger = logging.getLogger(__name__)

# %% ../nbs/utils.ipynb 5
def get_project_root(path: Path = Path(".").resolve()):
    return find_project_root(tuple([str()]))

# %% ../nbs/utils.ipynb 7
def configure_logging(level_text: str == "warn"):
    if level_text.lower() == "warn":
        level = logging.WARN
    elif level_text.lower() == "info":
        level = logging.INFO
    elif level_text.lower() == "error":
        level = logging.ERROR
    elif level_text.lower() == "debug":
        level = logging.DEBUG
    else:
        raise ValueError(f"Unrecognised log level: {level_text}")

    logFormatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    rootLogger = logging.getLogger()

    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    rootLogger.setLevel(level)

# %% ../nbs/utils.ipynb 9
def run_nbqa_cmd(cmd: str, root_dir: Path = None):
    logger.info(f"Running {cmd}")
    if root_dir is None:
        root_dir: Path = find_project_root(tuple([str(Path(".").resolve())]))
    args = CLIArgs.parse_args([cmd, str(root_dir)])
    logger.debug(f"Running command: {cmd} with args: {args} via nbQA toolchain")
    configs = _get_configs(args, root_dir)
    output_code = _main(args, configs)
    return output_code

# %% ../nbs/utils.ipynb 12
def is_nbdev_project(project_path: Path = Path(".")):
    is_nbdev = True
    project_root = find_project_root(tuple([str(project_path.resolve())]))

    if not Path(project_root, "settings.ini").exists():
        is_nbdev = False
    try:
        get_config().lib_name
    except InterpolationMissingOptionError:
        is_nbdev = False

    return is_nbdev

# %% ../nbs/utils.ipynb 16
def resolve_nbs(nb_glob: str = None):
    if is_nbdev_project():
        nbs = nbglob(nb_glob)
    else:
        nb_glob = Path(".") if nb_glob is None else nb_glob
        nbs = [
            p.absolute()
            for p in globtastic(
                path=nb_glob,
                skip_folder_re="^[_.]",
                file_glob="*.ipynb",
                skip_file_re="^[_.]",
            ).map(Path)
        ]
        nbs = [str(p) for p in nbs]
    logger.debug(f"Resolved notebook paths: {nbs}")
    return nbs

# %% ../nbs/utils.ipynb 19
def find_common_root(nb_glob: str = None) -> Path:
    """Expand a glob expression then find the common root directory"""
    nb_paths = resolve_nbs(nb_glob)
    path_parts_coll = [p.parts for p in [Path(_) for _ in nb_paths]]
    common_part_len = min([len(x) for x in path_parts_coll])
    path_parts = pd.DataFrame.from_records(
        [x[:common_part_len] for x in path_parts_coll]
    )
    for i in range(common_part_len):
        if path_parts[i].nunique() > 1:
            common_root = Path(*path_parts_coll[0][:i]).absolute()
            break
    return common_root

# %% ../nbs/utils.ipynb 21
def get_project_root(path: Path = Path(".").resolve()) -> Path:
    return find_project_root(tuple([str()]))

# %% ../nbs/utils.ipynb 23
def get_excluded_paths(paths: Iterable[Path], exclude_pattern: str) -> Iterable[Path]:
    """Excluded paths should either be absolute paths or paths rooted at the project root directory"""
    excl_paths = []
    paths = [p.absolute() for p in paths]

    for ex_pattern in exclude_pattern.split(","):
        if Path(ex_pattern).is_absolute():
            ex_path = Path(ex_pattern)
        else:
            ex_path = Path(get_project_root(), ex_pattern)

        if ex_path.exists():
            excl_paths.extend([p for p in paths if ex_pattern in str(p)])
        elif not ex_path.exists():
            raise ValueError(f"Path component: {ex_path} does not exist")
        else:
            raise ValueError(
                f"Invalid exclusion pattern: {ex_path} pattern is comma separrated list of 'dir/' for directories and 'name.ipynb' for specific notebook"
            )
    return excl_paths

# %% ../nbs/utils.ipynb 25
def remove_ipython_special_directives(code):
    lines = code.split("\n")
    lines = [
        line
        for line in lines
        if not line.strip().startswith("%") and not line.strip().startswith("!")
    ]
    return "\n".join(lines)

# %% ../nbs/utils.ipynb 28
def safe_div(numer, denom):
    return 0 if denom == 0 else numer / denom

# %% ../nbs/utils.ipynb 31
def get_cell_code(nb):
    pnb = nbformat.from_dict(nb)
    nb_cell_code = "\n".join(
        [
            remove_ipython_special_directives(c["source"])
            for c in pnb.cells
            if c["cell_type"] == "code"
        ]
    )
    return nb_cell_code
