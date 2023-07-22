# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/indicators.ipynb.

# %% auto 0
__all__ = ['indicator_funcs', 'get_project_root', 'remove_ipython_special_directives', 'safe_div', 'calls_per_func',
           'calls_per_func_mean', 'calls_per_func_median', 'iaf', 'tests_per_function', 'tests_per_func_mean',
           'tests_func_coverage_pct', 'calc_ifp', 'in_func_pct', 'markdown_code_pct', 'total_code_len',
           'loc_per_md_section']

# %% ../nbs/indicators.ipynb 2
import ast
import warnings
from collections import Counter
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
from execnb.nbio import read_nb

# %% ../nbs/indicators.ipynb 7
def get_project_root(path: Path = Path(".").resolve()):
    return find_project_root(tuple([str()]))

# %% ../nbs/indicators.ipynb 9
def _count_func_calls(code, func_defs):
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

# %% ../nbs/indicators.ipynb 13
def remove_ipython_special_directives(code):
    lines = code.split("\n")
    lines = [
        line
        for line in lines
        if not line.strip().startswith("%") and not line.strip().startswith("!")
    ]
    return "\n".join(lines)

# %% ../nbs/indicators.ipynb 15
def safe_div(numer, denom):
    return 0 if denom == 0 else numer / denom

# %% ../nbs/indicators.ipynb 18
def _get_cell_code(nb):
    pnb = nbformat.from_dict(nb)
    nb_cell_code = "\n".join(
        [
            remove_ipython_special_directives(c["source"])
            for c in pnb.cells
            if c["cell_type"] == "code"
        ]
    )
    return nb_cell_code

# %% ../nbs/indicators.ipynb 20
def _get_func_defs(code, ignore_private_prefix=True):
    func_names = []
    for stmt in ast.walk(ast.parse(code)):
        if isinstance(stmt, ast.FunctionDef):
            inner_cond = (
                False if ignore_private_prefix and stmt.name.startswith("_") else True
            )
            if inner_cond:
                func_names.append(stmt.name)
    return func_names

# %% ../nbs/indicators.ipynb 24
def calls_per_func(nb):
    nb_cell_code = _get_cell_code(nb)
    func_defs = _get_func_defs(nb_cell_code)
    func_calls = _count_func_calls(nb_cell_code, func_defs)
    return func_calls

# %% ../nbs/indicators.ipynb 26
def calls_per_func_mean(nb):
    return pd.Series(calls_per_func(nb)).mean()

# %% ../nbs/indicators.ipynb 28
def calls_per_func_median(nb):
    with warnings.catch_warnings():
        warnings.filterwarnings(action="ignore", message="Mean of empty slice")
        return pd.Series(calls_per_func(nb)).median()

# %% ../nbs/indicators.ipynb 37
def _count_inline_asserts(code, func_defs):
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

# %% ../nbs/indicators.ipynb 38
def iaf(nb):
    nb_cell_code = _get_cell_code(nb)
    if nb_cell_code == "":
        return np.nan
    func_defs = _get_func_defs(nb_cell_code)
    return _count_inline_asserts(nb_cell_code, func_defs)

# %% ../nbs/indicators.ipynb 44
def _count_func_ret_asserts(nb_cell_code):
    ret_vals = {}
    func_defs = _get_func_defs(nb_cell_code)
    func_ret_asserts = Counter({k: 0 for k in func_defs})
    assert_func_counts = {}
    for stmt in ast.walk(ast.parse(nb_cell_code)):
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
            _update_ret_vals(stmt, ret_vals)

        if isinstance(stmt, ast.Assert):
            assert_func_counts[id(stmt)] = []
            _check_for_function_asserts(
                stmt, ret_vals, func_ret_asserts, assert_func_counts
            )

    return func_ret_asserts

# %% ../nbs/indicators.ipynb 45
def _check_for_function_asserts(
    stmt: ast.AST, ret_vals, func_ret_asserts, assert_func_counts
):
    if hasattr(stmt.test, "left"):
        if hasattr(stmt.test.left, "id"):
            _incr_assert_count(
                id(stmt),
                ret_vals,
                func_ret_asserts,
                assert_func_counts,
                stmt.test.left.id,
            )
        for comp in stmt.test.comparators:
            if hasattr(comp, "id"):
                _incr_assert_count(
                    id(stmt), ret_vals, func_ret_asserts, assert_func_counts, comp.id
                )
    elif isinstance(stmt.test, ast.Name):
        if hasattr(stmt.test, "id"):
            _incr_assert_count(
                id(stmt), ret_vals, func_ret_asserts, assert_func_counts, stmt.test.id
            )
    elif isinstance(stmt.test, ast.BoolOp):
        for val in stmt.test.values:
            if hasattr(val, "left"):
                if hasattr(val.left, "id"):
                    _incr_assert_count(
                        id(stmt),
                        ret_vals,
                        func_ret_asserts,
                        assert_func_counts,
                        val.left.id,
                    )
                for comp in val.comparators:
                    if hasattr(comp, "id"):
                        _incr_assert_count(
                            id(stmt),
                            ret_vals,
                            func_ret_asserts,
                            assert_func_counts,
                            comp.id,
                        )

# %% ../nbs/indicators.ipynb 46
def _incr_assert_count(
    assert_id, ret_vals, func_ret_asserts, assert_func_counts, return_var
):
    if (
        return_var in ret_vals
        and ret_vals[return_var] not in assert_func_counts[assert_id]
    ):
        assert_func_counts[assert_id].append(ret_vals[return_var])
        if return_var in ret_vals:
            func_ret_asserts[ret_vals[return_var]] += 1

# %% ../nbs/indicators.ipynb 47
def _update_ret_vals(stmt, ret_vals):
    if isinstance(stmt.value.func, ast.Subscript):
        func_name = stmt.func.value.id
    elif isinstance(stmt.value.func, ast.Attribute):
        func_name = stmt.value.func.attr
    else:
        func_name = (
            stmt.value.func.id if hasattr(stmt.value.func, "id") else stmt.func.attr
        )

    if isinstance(stmt.targets[0], ast.Name):
        ret_vals[stmt.targets[0].id] = func_name
    elif isinstance(stmt.targets[0], ast.Tuple):
        for elts in stmt.targets[0].elts:
            ret_vals[elts.id] = func_name

# %% ../nbs/indicators.ipynb 49
def tests_per_function(nb):
    nb_cell_code = "\n".join(
        [
            remove_ipython_special_directives(c["source"])
            for c in nb.cells
            if c["cell_type"] == "code"
        ]
    )
    return _tests_per_function_code(nb_cell_code)


def _tests_per_function_code(nb_cell_code):
    func_ret_asserts = _count_func_ret_asserts(nb_cell_code)
    inline_asserts = _count_inline_asserts(nb_cell_code, _get_func_defs(nb_cell_code))

    func_ret_asserts.update(inline_asserts)
    return pd.Series(func_ret_asserts)

# %% ../nbs/indicators.ipynb 52
def tests_per_func_mean(nb):
    return tests_per_function(nb).mean()

# %% ../nbs/indicators.ipynb 54
def tests_func_coverage_pct(nb):
    return tests_per_function(nb).clip(upper=1).mean() * 100

# %% ../nbs/indicators.ipynb 59
def calc_ifp(nb_cell_code):
    stmts_in_func = 0
    stmts_outside_func = 0
    for stmt in ast.walk(ast.parse(remove_ipython_special_directives(nb_cell_code))):
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

# %% ../nbs/indicators.ipynb 62
def in_func_pct(nb):
    nb_cell_code = "\n".join(
        [
            remove_ipython_special_directives(c["source"])
            for c in nb.cells
            if c["cell_type"] == "code"
        ]
    )
    if nb_cell_code == "":
        return np.nan
    return calc_ifp(nb_cell_code)

# %% ../nbs/indicators.ipynb 66
def markdown_code_pct(nb):
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

# %% ../nbs/indicators.ipynb 70
def total_code_len(nb):
    return sum([len(c["source"]) for c in nb.cells if c["cell_type"] == "code"])

# %% ../nbs/indicators.ipynb 74
def loc_per_md_section(nb):
    num_md_sections = len(
        [
            c["source"]
            for c in nb.cells
            if c["cell_type"] == "markdown" and c["source"].strip().startswith("#")
        ]
    )
    tcl = total_code_len(nb)
    if tcl == 0 or num_md_sections == 0:
        result = np.nan
    else:
        result = total_code_len(nb) / num_md_sections
    return result

# %% ../nbs/indicators.ipynb 77
indicator_funcs = {
    "calls_per_func_mean": calls_per_func_mean,
    "calls_per_func_median": calls_per_func_median,
    "tests_per_func_mean": tests_per_func_mean,
    "tests_func_coverage_pct": tests_func_coverage_pct,
    "in_func_pct": in_func_pct,
    "markdown_code_pct": markdown_code_pct,
    "loc_per_md_section": loc_per_md_section,
    "total_code_len": total_code_len,
}
