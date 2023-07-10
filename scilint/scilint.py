# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/scilint.ipynb.

# %% auto 0
__all__ = ['indicator_funcs', 'run_nbqa_cmd', 'tidy', 'is_nbdev_project', 'get_func_defs', 'count_func_calls',
           'replace_ipython_magics', 'safe_div', 'get_cell_code', 'calls_per_func', 'mean_cpf', 'median_cpf', 'afr',
           'count_inline_asserts', 'iaf', 'mean_iaf', 'median_iaf', 'calc_ifp', 'ifp', 'mcp', 'tcl',
           'loc_per_md_section', 'lint_nb', 'get_excluded_paths', 'lint_nbs', 'display_warning_report', 'scilint_tidy',
           'scilint_lint', 'scilint_build', 'scilint_ci']

# %% ../nbs/scilint.ipynb 2
import ast
import json
import operator
import os
import re
import shutil
import sys
import warnings
from collections import Counter
from configparser import InterpolationMissingOptionError
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Tuple

import nbformat
import numpy as np
import pandas as pd
import yaml
from execnb.nbio import read_nb
from fastcore.script import call_parse
from nbdev.clean import nbdev_clean
from nbdev.config import get_config
from nbdev.doclinks import nbdev_export, nbglob
from nbdev.quarto import nbdev_docs, nbdev_readme
from nbdev.test import nbdev_test
from nbqa.__main__ import _get_configs, _main
from nbqa.cmdline import CLIArgs
from nbqa.find_root import find_project_root

# %% ../nbs/scilint.ipynb 7
def run_nbqa_cmd(cmd):
    print(f"Running {cmd}")
    project_root: Path = find_project_root(tuple([str(Path(".").resolve())]))
    args = CLIArgs.parse_args([cmd, str(project_root)])
    configs = _get_configs(args, project_root)
    output_code = _main(args, configs)
    return output_code

# %% ../nbs/scilint.ipynb 9
def tidy():
    tidy_tools = ["black", "isort", "autoflake"]
    [run_nbqa_cmd(c) for c in tidy_tools]

# %% ../nbs/scilint.ipynb 11
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

# %% ../nbs/scilint.ipynb 14
def get_func_defs(code, ignore_private_prefix=True):
    func_names = []
    for stmt in ast.walk(ast.parse(code)):
        if isinstance(stmt, ast.FunctionDef):
            inner_cond = (
                False if ignore_private_prefix and stmt.name.startswith("_") else True
            )
            if inner_cond:
                func_names.append(stmt.name)
    return func_names

# %% ../nbs/scilint.ipynb 16
def count_func_calls(code, func_defs):
    func_calls = Counter({k: 0 for k in func_defs})
    for stmt in ast.walk(ast.parse(code)):
        if isinstance(stmt, ast.Call):
            if type(stmt.func) == ast.Subscript:
                func_name = stmt.func.value.id
            else:
                func_name = (
                    stmt.func.id if "id" in stmt.func.__dict__ else stmt.func.attr
                )
            if func_name in func_defs:
                if func_name in func_calls:
                    func_calls[func_name] += 1
    return func_calls

# %% ../nbs/scilint.ipynb 20
def replace_ipython_magics(code):
    # Replace Ipython magic and shell command symbol with comment
    code = code.replace("%", "#")
    code = re.sub(r"^!", "#", code)
    return re.sub(r"\n\W?!", "\n#", code)

# %% ../nbs/scilint.ipynb 22
def safe_div(numer, denom):
    return 0 if denom == 0 else numer / denom

# %% ../nbs/scilint.ipynb 24
def get_cell_code(nb):
    pnb = nbformat.from_dict(nb)
    nb_cell_code = "\n".join(
        [
            replace_ipython_magics(c["source"])
            for c in pnb.cells
            if c["cell_type"] == "code"
        ]
    )
    return nb_cell_code

# %% ../nbs/scilint.ipynb 27
def calls_per_func(nb):
    nb_cell_code = get_cell_code(nb)
    func_defs = get_func_defs(nb_cell_code)
    func_calls = count_func_calls(nb_cell_code, func_defs)
    return func_calls

# %% ../nbs/scilint.ipynb 28
def mean_cpf(nb):
    return pd.Series(calls_per_func(nb)).mean()

# %% ../nbs/scilint.ipynb 29
def median_cpf(nb):
    with warnings.catch_warnings():
        warnings.filterwarnings(action="ignore", message="Mean of empty slice")
        return pd.Series(calls_per_func(nb)).median()

# %% ../nbs/scilint.ipynb 37
def afr(nb):
    nb_cell_code = get_cell_code(nb)
    if nb_cell_code == "":  # no code cells - metric is not well defined
        return np.nan
    func_defs = get_func_defs(nb_cell_code)
    num_funcs = len(func_defs)

    assert_count = 0
    for stmt in ast.walk(ast.parse(nb_cell_code)):
        if isinstance(stmt, ast.Assert):
            assert_count += 1

    return safe_div(assert_count, num_funcs)

# %% ../nbs/scilint.ipynb 40
def count_inline_asserts(code, func_defs):
    inline_func_asserts = Counter({k: 0 for k in func_defs})

    for stmt in ast.walk(ast.parse(code)):
        if isinstance(stmt, ast.Assert):
            for assert_st in ast.walk(stmt):
                if isinstance(assert_st, ast.Call):
                    func_name = (
                        assert_st.func.id
                        if "id" in assert_st.func.__dict__
                        else assert_st.func.attr
                    )
                    if func_name in inline_func_asserts:
                        inline_func_asserts[func_name] += 1
    return inline_func_asserts

# %% ../nbs/scilint.ipynb 41
def iaf(nb):
    nb_cell_code = get_cell_code(nb)
    if nb_cell_code == "":
        return np.nan
    func_defs = get_func_defs(nb_cell_code)
    return count_inline_asserts(nb_cell_code, func_defs)

# %% ../nbs/scilint.ipynb 48
def mean_iaf(nb):
    return pd.Series(iaf(nb)).mean()

# %% ../nbs/scilint.ipynb 49
def median_iaf(nb):
    with warnings.catch_warnings():
        warnings.filterwarnings(action="ignore", message="Mean of empty slice")
        return pd.Series(iaf(nb)).median()

# %% ../nbs/scilint.ipynb 52
def calc_ifp(nb_cell_code):
    stmts_in_func = 0
    stmts_outside_func = 0
    for stmt in ast.walk(ast.parse(replace_ipython_magics(nb_cell_code))):
        if isinstance(stmt, ast.FunctionDef) and not stmt.name.startswith("_"):
            for body_item in stmt.body:
                stmts_in_func += 1
        elif isinstance(stmt, ast.Module):
            for body_item in stmt.body:
                if not isinstance(body_item, ast.FunctionDef):
                    stmts_outside_func += 1
    return (
        0
        if stmts_outside_func + stmts_in_func == 0
        else (stmts_in_func / (stmts_outside_func + stmts_in_func)) * 100
    )

# %% ../nbs/scilint.ipynb 54
def ifp(nb):
    nb_cell_code = "\n".join(
        [
            replace_ipython_magics(c["source"])
            for c in nb.cells
            if c["cell_type"] == "code"
        ]
    )
    if nb_cell_code == "":
        return np.nan
    return calc_ifp(nb_cell_code)

# %% ../nbs/scilint.ipynb 57
def mcp(nb):
    md_cells = [c for c in nb.cells if c["cell_type"] == "markdown"]
    code_cells = [c for c in nb.cells if c["cell_type"] == "code"]
    num_code_cells = len(code_cells)
    if num_code_cells == 0:
        return np.nan
    num_md_cells = len(md_cells)
    return (
        100
        if num_code_cells == 0
        else (num_md_cells / (num_md_cells + num_code_cells)) * 100
    )

# %% ../nbs/scilint.ipynb 60
def tcl(nb):
    return sum([len(c["source"]) for c in nb.cells if c["cell_type"] == "code"])

# %% ../nbs/scilint.ipynb 63
def loc_per_md_section(nb):
    num_md_sections = len(
        [
            c["source"]
            for c in nb.cells
            if c["cell_type"] == "markdown" and c["source"].strip().startswith("#")
        ]
    )
    total_code_len = tcl(nb)
    if total_code_len == 0 or num_md_sections == 0:
        result = np.nan
    else:
        result = tcl(nb) / num_md_sections
    return result

# %% ../nbs/scilint.ipynb 66
indicator_funcs = {
    "calls_per_func_mean": mean_cpf,
    "calls_per_func_median": median_cpf,
    "asserts_func_ratio": afr,
    "inline_asserts_per_func_mean": mean_iaf,
    "inline_asserts_per_func_median": median_iaf,
    "in_func_pct": ifp,
    "markdown_code_pct": mcp,
    "loc_per_md_section": loc_per_md_section,
    "total_code_len": tcl,
}

# %% ../nbs/scilint.ipynb 69
def lint_nb(
    nb_path: Path,
    conf: Dict[str, Any],
    indicators: Dict[str, Callable],
    include_in_scoring: bool,
) -> Tuple[float]:
    nb = read_nb(nb_path)

    has_syntax_error = False
    indic_vals = list(np.repeat(np.nan, len(indicators)))
    try:
        for i, indic_name in enumerate(indicators):
            indic_vals[i] = round(indicators[indic_name](nb), conf["precision"])
    except SyntaxError as se:
        if conf["print_syntax_errors"]:
            print(f"Syntax error in notebook: {nb_path} reason: ", se)
        has_syntax_error = True
    indic_vals.append(has_syntax_error)
    indic_vals.append(include_in_scoring)

    return tuple(indic_vals)

# %% ../nbs/scilint.ipynb 70
def get_excluded_paths(paths: Iterable[Path], exclude_pattern: str) -> Iterable[Path]:
    excl_paths = []
    for ex_pattern in exclude_pattern.split(","):
        ex_path = Path(ex_pattern)
        if ex_path.exists():
            excl_paths.extend([p for p in paths if ex_pattern in str(p)])
        elif not ex_path.exists():
            raise ValueError(f"Path component: {ex_path} does not exist")
        else:
            raise ValueError(
                f"Invalid exclusion pattern: {ex_path} pattern is comma separrated list of 'dir/' for directories and 'name.ipynb' for specific notebook"
            )
    return excl_paths

# %% ../nbs/scilint.ipynb 73
def lint_nbs(conf: Dict[str, Any], indicators: Dict[str, Callable]):
    nb_paths = [Path(p) for p in nbglob(Path("."))]

    excluded_paths = None
    exclusions = conf["exclusions"]
    if exclusions is not None:
        excluded_paths = get_excluded_paths(nb_paths, exclude_pattern=exclusions)

    results = []
    nb_names = []
    for nb_path in nb_paths:
        include_in_scoring = True
        if exclusions is not None:
            include_in_scoring = False if nb_path in excluded_paths else True

        nb_names.append(nb_path.stem)
        lint_result = lint_nb(nb_path, conf, indicators, include_in_scoring)
        results.append(lint_result)

    lint_report = pd.DataFrame.from_records(
        data=results,
        index=nb_names,
        columns=list(indicators.keys()) + ["has_syntax_error", "include_in_scoring"],
    ).sort_values(["in_func_pct", "markdown_code_pct"], ascending=False)

    scoring_report = lint_report[lint_report.include_in_scoring].copy()
    all_warns, num_warnings = _calculate_warnings(scoring_report, conf)
    _persist_results(lint_report, all_warns, conf)

    if num_warnings > 0:
        display_warning_report(all_warns)
    else:
        print("No issues found during linting")

    return lint_report, all_warns, num_warnings

# %% ../nbs/scilint.ipynb 75
def display_warning_report(all_warns: pd.DataFrame):
    print(
        "\n*********************************Begin Scilint Warning Report********************************"
    )
    print(all_warns.to_markdown(tablefmt="grid", index=False))
    print(
        "\n*********************************End Scilint Warning Report**********************************\n"
    )

# %% ../nbs/scilint.ipynb 78
def _persist_results(
    lint_report: pd.DataFrame, all_warns: pd.DataFrame, conf: Dict[str, Any]
):
    out_dir = Path(conf["out_dir"])
    conf_to_persist = {k: v for k, v in conf.items() if k != "indicators"}
    if not out_dir.exists():
        Path(out_dir).mkdir()
    with open(Path(out_dir, "scilint_config.json"), "w") as outfile:
        json.dump(conf_to_persist, outfile)
    all_warns.to_csv(Path(out_dir, "scilint_warnings.csv"), index=False)
    lint_report.to_csv(Path(out_dir, "scilint_report.csv"))

# %% ../nbs/scilint.ipynb 81
def _calculate_warnings(
    scoring_report: pd.DataFrame, conf: Dict[str, Any], include_missing: bool = False
) -> Tuple[Dict[str, Any], int]:
    warning_details = []
    for op_text in list(conf["warnings"].keys()):
        for indic in conf["warnings"][op_text]:
            metric_series = scoring_report[indic]
            or_exp = pd.isnull(metric_series) if include_missing else False
            op = (
                operator.lt
                if op_text == "lt"
                else operator.gt
                if op_text == "gt"
                else operator.eq
            )
            warning_data = metric_series[
                (op(metric_series, conf["warnings"][op_text][indic])) | (or_exp)
            ]
            warning_dict = warning_data.to_dict()
            for key, val in warning_dict.items():
                warning_dict[key] = (
                    indic,
                    val,
                    op_text,
                    conf["warnings"][op_text][indic],
                )
            warning_details.append(warning_dict)

    all_warns = _reshape_warnings(scoring_report, warning_details)
    num_warnings = len(all_warns)
    return all_warns, num_warnings

# %% ../nbs/scilint.ipynb 83
def _reshape_warnings(
    scoring_report: pd.DataFrame, warning_details: Iterable[Any]
) -> Dict[str, Iterable[Tuple]]:
    warnings_by_nb = {nb: [] for nb in scoring_report.index}
    for nb in scoring_report.index:
        for wd in warning_details:
            if nb in wd:
                warnings_by_nb[nb].append(tuple([nb] + list(wd[nb])))
    warnings_by_nb = {key: val for key, val in warnings_by_nb.items() if len(val) > 0}
    flattened_warns = [item for sublist in warnings_by_nb.values() for item in sublist]
    return pd.DataFrame.from_records(
        data=flattened_warns,
        columns=["notebook", "indicator", "value", "operator", "threshold"],
    )

# %% ../nbs/scilint.ipynb 90
def _lint(conf: Dict[str, Any]):
    _, _, num_warnings = lint_nbs(conf, indicator_funcs)
    fail_over = conf["fail_over"]
    if fail_over == -1:
        print("Linting outcome ignored as fail_over set to -1")
    elif num_warnings > fail_over:
        print(
            f"Linting failed: total warnings ({num_warnings}) exceeded threshold ({fail_over})"
        )
        sys.exit(num_warnings)
    else:
        print("Linting succeeded")

# %% ../nbs/scilint.ipynb 92
def _build(conf: Dict[str, Any]):
    print("Tidying notebooks..")
    tidy()
    if is_nbdev_project():
        nbdev_export.__wrapped__()
        print("Converted notebooks to modules")
        print("Testing notebooks..")
        nbdev_test.__wrapped__()
    print("Running notebook linter..")
    _lint(conf)
    if is_nbdev_project():
        nbdev_clean.__wrapped__()
        print("Cleaned notebooks")

# %% ../nbs/scilint.ipynb 94
def _load_conf(
    conf_path: str = None,
    exclusions: str = None,
    fail_over: int = None,
    out_dir: int = None,
    precision: int = None,
    print_syntax_errors: bool = None,
):
    if conf_path is None:
        project_root = find_project_root(tuple([str(Path(".").resolve())]))
        conf_path = Path(project_root, "nbs", "scilint-default.yaml")
        print(f"Loading default lint config: {conf_path}")
    else:
        conf_path = Path(conf_path)

    conf = yaml.safe_load(conf_path.read_text())
    override_names = (
        "exclusions",
        "fail_over",
        "out_dir",
        "precision",
        "print_syntax_errors",
    )
    overrides = (exclusions, fail_over, out_dir, precision, print_syntax_errors)
    for override in zip(override_names, overrides):
        if override[1] is not None:
            conf[override[0]] = override[1]
    return conf

# %% ../nbs/scilint.ipynb 97
@call_parse
def scilint_tidy():
    tidy()

# %% ../nbs/scilint.ipynb 99
@call_parse
def scilint_lint(
    conf_path: str = None,
    exclusions: str = None,
    fail_over: int = None,
    out_dir: int = None,
    precision: int = None,
    print_syntax_errors: bool = None,
):
    conf = _load_conf(
        conf_path, exclusions, fail_over, out_dir, precision, print_syntax_errors
    )
    _lint(conf)

# %% ../nbs/scilint.ipynb 101
@call_parse
def scilint_build(
    conf_path: str = None,
    exclusions: str = None,
    fail_over: int = None,
    out_dir: int = None,
    precision: int = None,
    print_syntax_errors: bool = None,
):
    conf = _load_conf(
        conf_path, exclusions, fail_over, out_dir, precision, print_syntax_errors
    )
    _build(conf)

# %% ../nbs/scilint.ipynb 103
@call_parse
def scilint_ci(
    conf_path: str = None,
    exclusions: str = None,
    fail_over: int = None,
    out_dir: int = None,
    precision: int = None,
    print_syntax_errors: bool = None,
):
    if not is_nbdev_project():
        print("scilint_ci feature is only available for nbdev projects")
        return

    conf = _load_conf(
        conf_path, exclusions, fail_over, out_dir, precision, print_syntax_errors
    )

    _build(conf)

    if not shutil.which("quarto"):
        print(
            "Quarto is not installed. A working quarto install is required for the CI build"
        )
        sys.exit(-1)
    nbdev_readme.__wrapped__()
    nbdev_docs.__wrapped__()
