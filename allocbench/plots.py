# Copyright 2018-2020 Florian Fischer <florian.fl.fischer@fau.de>
#
# This file is part of allocbench.
#
# allocbench is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# allocbench is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with allocbench.  If not, see <http://www.gnu.org/licenses/>.
"""Plot different graphs from allocbench results"""

import ast
import copy
import itertools
import operator
import os
import re
import traceback
from typing import Dict, List, Tuple, NamedTuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats

import allocbench.facter as facter
from allocbench.util import get_logger

logger = get_logger(__file__)

# This is useful when evaluating strings in the plot functions. str(np.NaN) == "nan"
nan = np.NaN  # pylint: disable=invalid-name

SUMMARY_FILE_EXT = "svg"

LATEX_CUSTOM_PREAMBLE = ""

DEFAULT_PLOT_OPTIONS = {
    'plot': {
        'marker': '.',
        'linestyle': '-',
    },
    'errorbar': {
        'marker': '.',
        'linestyle': '-',
        'yerr': True,
    },
    'bar': {
        'yerr': True,
    }
}

DEFAULT_FIG_OPTIONS = {
    'plot': {
        'legend': True,
        'legend_pos': 'best',
        'autoticks': True,
    },
    'errorbar': {
        'legend': True,
        'legend_pos': 'best',
        'autoticks': True,
    },
    'bar': {
        'legend': True,
        'legend_pos': 'lower center',
        'autoticks': False,
    }
}

FIGURES = {}


def _set_all_alloc_colors(allocators):
    """Populate all not set allocator colors with matplotlib 'C' colors"""
    explicit_colors = [
        v["color"] for v in allocators.values() if v["color"] is not None
    ]
    matplotlib_c_colors = ["C" + str(i) for i in range(0, 10)]
    avail_colors = [c for c in matplotlib_c_colors if c not in explicit_colors]

    i = 0
    for alloc in allocators.values():
        if alloc["color"] is None:
            alloc["color"] = avail_colors[i]
            i = (i + 1) % len(avail_colors)


def get_alloc_color(bench, alloc):
    """Retrieve color of an allocator"""
    if isinstance(alloc, str):
        alloc = bench.results["allocators"][alloc]
    if alloc["color"] is None:
        _set_all_alloc_colors(bench.results["allocators"])

    return alloc["color"]


#https://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string
def _eval_with_stat(bench, evaluation, alloc, perm, stat):
    """Helper to evaluate a datapoint description string as arithmetic operation"""
    def _eval(node):
        """evaluate a arithmetic ast node"""

        # supported operators
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.BitXor: operator.xor,
            ast.USub: operator.neg
        }

        if isinstance(node, ast.Num):  # <number>
            return node.n
        if isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return operators[type(node.op)](_eval(node.left),
                                            _eval(node.right))
        if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return operators[type(node.op)](_eval(node.operand))

        raise TypeError(node)

    try:
        expr = evaluation.format(**bench.results["stats"][alloc][perm][stat])
    except KeyError:
        logger.debug("%s", traceback.format_exc())
        logger.warning("KeyError while expanding %s for %s and %s", evaluation,
                       alloc, perm)
        return nan

    node = ast.parse(expr, mode='eval')

    try:
        return _eval(node.body)
    except TypeError:
        logger.debug("%s", traceback.format_exc())
        logger.warning("%s could not be evaluated as arithmetic operation",
                       expr)
        return nan


def get_y_data(bench,
               expression,
               allocator,
               perms,
               stat="mean",
               scale=None) -> List[float]:
    """Helper to get the y data of an allocator for given permutations"""

    y_data: List[float] = []

    if isinstance(perms, bench.Perm):
        perms = [perms]

    for perm in perms:
        if scale:
            if scale == allocator:
                y_data.append(1)
            else:
                val = _eval_with_stat(bench, expression, allocator, perm, stat)
                norm_val = _eval_with_stat(bench, expression, scale, perm,
                                           stat)
                y_data.append(val / norm_val)
        else:
            y_data.append(
                _eval_with_stat(bench, expression, allocator, perm, stat))

    return y_data


def _create_plot_options(plot_type, **kwargs):
    """
    Create a plot options dictionary.

    Parameters
    ----------
    plot_type : str
        The plot type for which the options should be created.
        Possible values: {'bar', 'errorbar', 'plot'}

    **kwargs : plot properties, optional
        *kwargs* are used to specify properties like a line label (for
        auto legends), linewidth, antialiasing, marker face color.

    Returns
    -------
    options : dict
        Dict holding the specified options and all default values for plot type
    """

    options = copy.deepcopy(DEFAULT_PLOT_OPTIONS[plot_type])
    for key, value in kwargs.items():
        options[key] = value

    return options


def _create_figure_options(plot_type, fig_label, **kwargs):
    """
    Create a figure options dictionary

    Parameters
    ----------
    plot_type : str
        The plot type for which the options should be created.
        Possible values: {'bar', 'errorbar', 'plot'}

    **kwargs : figure properties, optional
        *kwargs* are used to specify properties like legends, legend position,
        x-/ and ylabel, and title.

    Returns
    -------
    options : dict
        Dict holding the specified options and all default values for plot type
    """

    options = copy.deepcopy(DEFAULT_FIG_OPTIONS[plot_type])

    options['fig_label'] = fig_label

    for key, value in kwargs.items():
        options[key] = value

    return options


def _plot(bench,
          allocators,
          y_expression,
          x_data,
          perms,
          plot_type,
          plot_options,
          fig_options,
          scale=None,
          sumdir="",
          file_ext=SUMMARY_FILE_EXT):
    """
    Create a plot for a given expression

    Parameters
    ----------

    Returns
    -------
    figure : :rc:`~matplotlib.figure.Figure`
        The new :rc:`.Figure` instance wrapping our plot.

    Notes
    -----
    If you are creating many figures, make sure you explicitly call
    :rc:`.pyplot.close` on the figures you are not using, because this will
    enable pyplot to properly clean up the memory.
    """
    fig = plt.figure(fig_options['fig_label'])
    FIGURES[fig_options['fig_label']] = fig
    if plot_type == 'bar' and 'width' not in plot_options:
        n_allocators = len(allocators)
        width = 1 / (n_allocators + 1)
        plot_options['width'] = width
    for i, allocator in enumerate(allocators):
        y_data = get_y_data(bench,
                            y_expression,
                            allocator,
                            perms,
                            stat='mean',
                            scale=scale)

        if plot_options.get('yerr', False):
            plot_options['yerr'] = get_y_data(bench,
                                              y_expression,
                                              allocator,
                                              perms,
                                              stat='std')
        try:
            plot_func = getattr(plt, plot_type)
        except AttributeError:
            logger.debug('Unknown plot type: %s', plot_type)
            raise

        _x_data = x_data
        if not fig_options['autoticks']:
            _x_data = np.arange(1, len(x_data) + 1)
            if plot_type == 'bar':
                _x_data = _x_data + width / 2 + (i * plot_options['width'])

        plot_func(_x_data,
                  y_data,
                  label=allocator,
                  color=get_alloc_color(bench, allocator),
                  **plot_options)

    if fig_options['legend']:
        plt.legend(loc=fig_options['legend_pos'])

    if not fig_options['autoticks']:
        plt.xticks(_x_data - (len(allocators) / 2 * plot_options['width']),
                   x_data)

    plt.xlabel(fig_options['xlabel'])
    plt.ylabel(fig_options['ylabel'])
    plt.title(fig_options['title'])

    fig_path = os.path.join(sumdir, f'{fig_options["fig_label"]}.{file_ext}')
    if file_ext == 'tex':
        import tikzplotlib  # pylint: disable=import-outside-toplevel
        tikzplotlib.save(fig_path)
    else:
        fig.savefig(fig_path)

    return fig


def plot(bench,
         y_expression,
         plot_type='errorbar',
         x_args=None,
         scale=None,
         plot_options=None,
         fig_options=None,
         file_postfix="",
         sumdir="",
         file_ext=SUMMARY_FILE_EXT):
    """
    Create plots for a given expression for the y axis.

    Parameters
    ----------

    y_expression : str

    plot_type : str, optional, default='errorbar'
        The plot type for which the options should be created.
        Possible values: {'bar', 'errorbar', 'plot'}

    x_args : [str], optional, default=None
        The benchmark arguments for which a plot should be created.
        If not provided, defaults to :rc:`bench.arguments.keys()`

    scale : str, optional, default=None
        Name of the allocator which should be used to normalize the results.

    plot_options : dict, optional, default None
        Dictionary containing plot options which should be passed to the plot
        type function. If not provided the default plot type options are used.
        Possible options:
            * yerr: bool - Plot the standard deviation as errorbars
            * marker: str - Style of the used markers
            * line: str - Style of the drawn lines

    fig_options : dict, optional, default None
        Dictionary containing figure options.
        If not provided the default plot type options are used.
        Possible options:
            * ylabel : str - The label of the y axis.
            * xlabel : str - The label of the x axis.
            * title : str - The title of the plot.
            * legend : bool - Should the plot have a legend.
            * legend_pos : str - Location of the legend.
                For possible values see :rc:`help(matplotlib.pyploy.legend)`.
            * autoticks : bool - Let matplotlib set the xticks automatically.

    file_postfix: str, optional, default=""
        Postfix which is appended to the plot's file name.

    sumdir : path or str, optional, default=""
        Directory where the plot should be saved. If not provided defaults
        to the current working directory.

    file_ext : str, optional, default=:rc:`allocbench.plots.SUMMARY_FILE_EXT`
        File extension of the saved plot. If not provided defaults to the
        value of :rc:`allocbench.plots.SUMMARY_FILE_EXT`

    """

    args = bench.results["args"]
    allocators = bench.results["allocators"]

    x_args = x_args or args

    # create plots for benchmarks without arguments
    if not x_args:
        fig_label = f'{bench.name}.{file_postfix}'
        karg_plot_option = plot_options or {}
        cur_plot_options = _create_plot_options(plot_type, **karg_plot_option)

        cur_fig_options = {}

        substitutions = vars()
        substitutions.update(vars(bench))
        for option, value in (fig_options or {}).items():
            if isinstance(value, str):
                cur_fig_options[option] = value.format(**substitutions)

        cur_fig_options = _create_figure_options(plot_type, fig_label,
                                                 **cur_fig_options)

        # plot specific defaults
        cur_fig_options.setdefault("ylabel", y_expression)
        cur_fig_options.setdefault("xlabel", "")
        cur_fig_options.setdefault("titel", fig_label)

        _plot(bench,
              allocators,
              y_expression, [""],
              list(bench.iterate_args(args=args)),
              plot_type,
              cur_plot_options,
              cur_fig_options,
              scale=scale,
              sumdir=sumdir,
              file_ext=file_ext)

    for loose_arg in x_args:
        x_data = args[loose_arg]

        fixed_args = [[(k, v) for v in args[k]] for k in args
                      if k != loose_arg]
        for fixed_part_tuple in itertools.product(*fixed_args):
            fixed_part = dict(fixed_part_tuple)

            fixed_part_str = ".".join(
                [f'{k}={v}' for k, v in fixed_part.items()])
            fig_label = f'{bench.name}.{fixed_part_str}.{file_postfix}'

            karg_plot_option = plot_options or {}
            cur_plot_options = _create_plot_options(plot_type,
                                                    **karg_plot_option)

            cur_fig_options = {}

            substitutions = vars()
            substitutions.update(vars(bench))
            for option, value in (fig_options or {}).items():
                if isinstance(value, str):
                    cur_fig_options[option] = value.format(**substitutions)

            cur_fig_options = _create_figure_options(plot_type, fig_label,
                                                     **cur_fig_options)

            # plot specific defaults
            cur_fig_options.setdefault("ylabel", y_expression)
            cur_fig_options.setdefault("xlabel", loose_arg)
            cur_fig_options.setdefault("titel", fig_label)

            _plot(bench,
                  allocators,
                  y_expression,
                  x_data,
                  list(bench.iterate_args(args=args, fixed=fixed_part)),
                  plot_type,
                  cur_plot_options,
                  cur_fig_options,
                  scale=scale,
                  sumdir=sumdir,
                  file_ext=file_ext)


def print_common_facts(comment_symbol="", file=None):
    """Print the facts about the used system common to all benchmarks"""
    print(comment_symbol, "Common facts:", file=file)
    for fact, value in facter.FACTS.items():
        print(f"{comment_symbol}  {fact}: {value}", file=file)
    print(file=file)


def print_facts(bench,
                comment_symbol="",
                print_common=True,
                print_allocators=False,
                file=None):
    """Write collected facts about used system and benchmark to file"""
    print(comment_symbol, bench.name, file=file)
    print(file=file)

    if print_common:
        print_common_facts(comment_symbol=comment_symbol, file=file)

    print(comment_symbol, "Benchmark facts:", file=file)
    for fact, value in bench.results["facts"].items():
        print(comment_symbol, f"{fact}: {value}", file=file)

    if print_allocators:
        print(comment_symbol,
              f'allocators: {" ".join(bench.results["allocators"])}',
              file=file)

    print(file=file)


def export_stats_to_csv(bench, datapoint, path=None):
    """Write descriptive statistics about datapoint to csv file"""
    allocators = bench.results["allocators"]
    args = bench.results["args"]
    stats = bench.results["stats"]

    if path is None:
        path = datapoint

    path = path + ".csv"

    stats_fields = list(stats[list(allocators)[0]][list(
        bench.iterate_args(args=args))[0]])
    fieldnames = ["allocator", *args, *stats_fields]
    widths = []
    for fieldname in fieldnames:
        widths.append(len(fieldname) + 2)

    # collect rows
    rows = {}
    for alloc in allocators:
        rows[alloc] = {}
        for perm in bench.iterate_args(args=args):
            row = []
            row.append(alloc)
            row += list(perm._asdict().values())
            row += [
                stats[alloc][perm][stat].get(datapoint, nan)
                for stat in stats[alloc][perm]
            ]
            if row[-1] is not nan:
                row[-1] = (",".join([str(x) for x in row[-1]]))
            else:
                row[-1] = ""

            rows[alloc][perm] = row

    # calc widths
    for i in range(0, len(fieldnames)):
        for alloc in allocators:
            for perm in bench.iterate_args(args=args):
                field_len = len(str(rows[alloc][perm][i])) + 2
                if field_len > widths[i]:
                    widths[i] = field_len

    with open(path, "w") as csv_file:
        headerline = ""
        for i, name in enumerate(fieldnames):
            headerline += name.capitalize().ljust(widths[i]).replace("_", "-")
        print(headerline, file=csv_file)

        for alloc in allocators:
            for perm in bench.iterate_args(args=args):
                line = ""
                for i, row in enumerate(rows[alloc][perm]):
                    line += str(row).ljust(widths[i])
                print(line.replace("_", "-"), file=csv_file)


def get_ordered_results_for_perm(bench,
                                 datapoint: str,
                                 perm: NamedTuple,
                                 order='>') -> List[Tuple[float, List[str]]]:
    """Return a ordered list of the allocator and their results for a specific perm"""
    data: Dict[float, List[str]] = {}
    for allocator in bench.results["allocators"]:
        value = _eval_with_stat(bench, datapoint, allocator, perm, "mean")
        if value in data:
            data[value].append(allocator)
        else:
            data[value] = [allocator]

    return sorted(data.items(), reverse=order == ">")


def get_ordered_results(bench, datapoint, order='>'):
    """Return a ordered list of the allocator and their results"""
    results = {}
    for perm in bench.iterate_args(args=bench.results["args"]):
        results[perm] = get_ordered_results_for_perm(bench,
                                                     datapoint,
                                                     perm,
                                                     order=order)

    return results


def create_ascii_leaderboards(bench, datapoints: List[Tuple[str, str]]):
    """Return a dictionary containing ordered list of allocators according to their results"""

    res = ""
    leaderboards = {
        datapoint: get_ordered_results(bench, datapoint, order=order)
        for datapoint, order in datapoints
    }
    # combined = []

    for datapoint, leaderboard in leaderboards.items():
        res += f'leaderboard for "{datapoint}":\n'
        for perm in leaderboard:
            res += f'{perm}:\n'
            doubles = 0
            for i, (val, allocators) in enumerate(leaderboard[perm]):
                doubles += len(allocators) - 1
                allocs_str = ','.join(allocators)
                res += f'{i + 1}. {allocs_str}: {val}\n'
            res += '\n'

    return res[:-1]


def calc_ttests_for_alloc_pair(bench, alloc1, alloc2, datapoint: str) -> Dict:
    """Calculate independent t-test between two allocators for each argument permutation"""
    ttest_results = {}
    for perm in bench.iterate_args():
        data1 = [float(m[datapoint]) for m in bench.results[alloc1][perm]]
        data2 = [float(m[datapoint]) for m in bench.results[alloc2][perm]]

        ttest_results[perm] = scipy.stats.ttest_ind(data1, data2)

    return ttest_results


# https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates#25875504
def tex_escape(text: str) -> str:
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(
        re.escape(str(key))
        for key in sorted(conv.keys(), key=lambda item: -len(item))))
    return regex.sub(lambda match: conv[match.group()], text)


def export_stats_to_dataref(bench, datapoint, path=None):
    """Write descriptive statistics about datapoint to dataref file"""
    stats = bench.results["stats"]

    if path is None:
        path = datapoint

    path = path + ".dataref"

    # Example: \drefset{/mysql/glibc/40/Lower-whisker}{71552.0}
    line = "\\drefset{{/{}/{}/{}/{}}}{{{}}}"

    with open(path, "w") as dataref_file:
        # Write facts to file
        print_facts(bench, comment_symbol="%", file=dataref_file)

        for alloc in bench.results["allocators"]:
            for perm in bench.iterate_args(args=bench.results["args"]):
                for statistic, values in stats[alloc][perm].items():
                    cur_line = line.format(
                        bench.name, alloc,
                        "/".join([str(p) for p in list(perm)]), statistic,
                        values.get(datapoint, nan))
                    # Replace empty outliers
                    cur_line.replace("[]", "")
                    # Replace underscores
                    cur_line.replace("_", "-")
                    print(cur_line, file=dataref_file)


def write_best_doublearg_tex_table(bench,
                                   expr,
                                   sort=">",
                                   file_postfix="",
                                   sumdir=""):
    """create a colored standalone tex table"""
    args = bench.results["args"]
    keys = list(args.keys())
    allocators = bench.results["allocators"]

    header_arg = keys[0] if len(args[keys[0]]) < len(
        args[keys[1]]) else keys[1]
    row_arg = [arg for arg in args if arg != header_arg][0]

    headers = args[header_arg]
    rows = args[row_arg]

    cell_text = []
    for arg_value in rows:
        row = []
        for perm in bench.iterate_args(args=args, fixed={row_arg: arg_value}):
            best = []
            best_val = None
            for allocator in allocators:
                mean = _eval_with_stat(bench, expr, allocator, perm, "mean")

                if not best_val:
                    best = [allocator]
                    best_val = mean
                elif ((sort == ">" and mean > best_val)
                      or (sort == "<" and mean < best_val)):
                    best = [allocator]
                    best_val = mean
                elif mean == best_val:
                    best.append(allocator)

            if isinstance(best_val, float):
                val_str = f"{best_val:.3f}"
            else:
                val_str = f"{best_val}"
            val_str = tex_escape(val_str)

            row.append(f"{tex_escape(best[0])}: {val_str}")
            row_str = " & ".join(row)
        cell_text.append(f"{arg_value} & {row_str}")

    table_layout = " l |" * (len(headers) + 1)
    header_line = " & ".join([tex_escape(str(x)) for x in headers])
    cell_text = "\\\\\n".join(cell_text)

    tex =\
f"""\\documentclass{{standalone}}
\\begin{{document}}
\\begin{{tabular}}{{|{table_layout}}}
{header_arg}/{row_arg} & {header_line} \\\\
{cell_text}
\\end{{tabular}}
\\end{{document}}
"""

    fname = os.path.join(sumdir, f"{bench.name}.{file_postfix}.tex")
    with open(fname, "w") as tex_file:
        print(tex, file=tex_file)


def write_tex_table(bench, entries, file_postfix="", sumdir=""):
    """generate a latex standalone table from an list of entries dictionaries

    Entries must have at least the two keys: "label" and "expression".
    The optional "sort" key specifies the direction of the order:
        ">" : bigger is better.
        "<" : smaller is better.

    Table layout:

    |    alloc1     |    alloc2    | ....
    ---------------------------------------
    | name1  name2  | ...
    ---------------------------------------
    perm1 | eavl1  eval2  | ...
    perm2 | eval1  eval2  | ...
    """
    args = bench.results["args"]
    allocators = bench.results["allocators"]
    nallocators = len(allocators)
    nentries = len(entries)
    perm_fields = bench.Perm._fields
    nperm_fields = len(perm_fields)

    alloc_header_line = f"\\multicolumn{{{nperm_fields}}}{{c|}}{{}} &"
    for alloc in allocators:
        alloc_esc = tex_escape(alloc)
        alloc_header_line += f"\\multicolumn{{{nentries}}}{{c|}}{{{alloc_esc}}} &"
    alloc_header_line = alloc_header_line[:-1] + "\\\\"

    perm_fields_header = ""
    for field in bench.Perm._fields:
        field_esc = tex_escape(field)
        perm_fields_header += f'{field_esc} &'
    entry_header_line = ""
    for entry in entries:
        entry_header_line += f'{entry["label"]} &'
    entry_header_line = perm_fields_header + entry_header_line * nallocators
    entry_header_line = entry_header_line[:-1] + "\\\\"

    fname = os.path.join(sumdir, ".".join([bench.name, file_postfix, "tex"]))
    with open(fname, "w") as tex_file:
        print("\\documentclass{standalone}", file=tex_file)
        print("\\usepackage{booktabs}", file=tex_file)
        print("\\usepackage{xcolor}", file=tex_file)
        print("\\begin{document}", file=tex_file)
        print("\\begin{tabular}{|",
              f"{'c|'*nperm_fields}",
              f"{'c'*nentries}|" * nallocators,
              "}",
              file=tex_file)
        print("\\toprule", file=tex_file)

        print(alloc_header_line, file=tex_file)
        print("\\hline", file=tex_file)
        print(entry_header_line, file=tex_file)
        print("\\hline", file=tex_file)

        for perm in bench.iterate_args(args=args):
            values = [[] for _ in entries]
            maxs = [None for _ in entries]
            mins = [None for _ in entries]
            for allocator in allocators:
                for i, entry in enumerate(entries):
                    expr = entry["expression"]
                    values[i].append(
                        _eval_with_stat(bench, expr, allocator, perm, "mean"))

            # get max and min for each entry
            for i, entry in enumerate(entries):
                if not "sort" in entry:
                    continue
                # bigger is better
                if entry["sort"] == ">":
                    maxs[i] = max(values[i])
                    mins[i] = min(values[i])
                # smaller is better
                elif entry["sort"] == "<":
                    mins[i] = max(values[i])
                    maxs[i] = min(values[i])

            # build row
            row = ""
            perm_dict = perm._asdict()
            for field in perm_fields:
                row += str(perm_dict[field]) + "&"

            for i, _ in enumerate(allocators):
                for j, entry_vals in enumerate(values):
                    val = entry_vals[i]

                    # format
                    if isinstance(val, float):
                        val_str = f"{val:.2f}"
                    # escape latex symbols
                    val_str = tex_escape(val_str)

                    # colorize
                    if val == maxs[j]:
                        val_str = f"\\textcolor{{green}}{{{val_str}}}"
                    elif val == mins[j]:
                        val_str = f"\\textcolor{{red}}{{{val_str}}}"
                    row += f"{val_str} &"
            print(row[:-1], "\\\\", file=tex_file)

        print("\\end{tabular}", file=tex_file)
        print("\\end{document}", file=tex_file)


def pgfplot_legend(bench,
                   sumdir="",
                   file_name="pgfplot_legend",
                   colors=True,
                   columns=3):
    """create a standalone pgfplot legend"""

    allocators = bench.results["allocators"]
    color_definitions = ""
    legend_entries = ""
    for alloc_name, alloc_dict in allocators.items():
        alloc_name = tex_escape(alloc_name)
        if colors:
            # define color
            rgb = matplotlib.colors.to_rgb(get_alloc_color(bench, alloc_dict))
            color_definitions += (f"\\providecolor{{{alloc_name}-color}}"
                                  f"{{rgb}}{{{rgb[0]},{rgb[1]},{rgb[2]}}}\n")
            color_definitions += (f"\\pgfplotsset{{{alloc_name}/"
                                  f".style={{color={alloc_name}-color}}}}\n\n")

        alloc_color = ""
        if colors:
            alloc_color = f"{alloc_name}-color"
        legend_entries += f"\t\\addplot+ [{alloc_color}] coordinates {{(0,0)}};\n"
        legend_entries += f"\t\\addlegendentry{{{alloc_name}}}\n\n"

    tex =\
f"""
\\documentclass{{standalone}}
\\usepackage{{pgfplots}}

\\usepackage{{xcolor}}

{color_definitions}
{LATEX_CUSTOM_PREAMBLE}
\\begin{{document}}
\\begin{{tikzpicture}}
\\begin{{axis}} [
\tlegend columns={columns},
\thide axis,
\tscale only axis, width=5mm, % make axis really small (smaller than legend)
]

{legend_entries}
\\end{{axis}}
\\end{{tikzpicture}}
\\end{{document}}"""

    with open(os.path.join(sumdir, f"{file_name}.tex"), "w") as legend_file:
        print(tex, file=legend_file)


def pgfplot(bench,
            perms,
            xexpr,
            yexpr,
            axis_attr="",
            bar=False,
            ylabel="y-label",
            xlabel="x-label",
            title="default title",
            postfix="",
            sumdir="",
            scale=None,
            error_bars=True,
            colors=True):
    """Create a pgf plot for a given expression"""

    allocators = bench.results["allocators"]
    perms = list(perms)

    label_substitutions = vars()
    label_substitutions.update(vars(bench))
    xlabel = xlabel.format(**label_substitutions)
    ylabel = ylabel.format(**label_substitutions)
    title = title.format(**label_substitutions)

    if bar:
        axis_attr = f"\tybar,\n{axis_attr}"

    color_definitions = ""
    style_definitions = ""
    plots = ""
    for alloc_name, alloc_dict in allocators.items():
        if colors:
            # define color
            rgb = matplotlib.colors.to_rgb(get_alloc_color(bench, alloc_dict))  # pylint: disable=unused-variable
            color_definitions += (f"\\providecolor{{{alloc_name}-color}}"
                                  "{{rgb}}{{{rgb[0]},{rgb[1]},{rgb[2]}}}\n")
            style_definitions += (f"\\pgfplotsset{{{alloc_name}/"
                                  ".style={{color={alloc_name}-color}}}}\n\n")

        eb = ""
        ebt = ""
        edp = ""
        if error_bars:
            eb = ",\n\terror bars/.cd, y dir=both, y explicit,\n"
            ebt += "[y error=error]"
            edp = " error"
        alloc_color = ""
        if colors:
            alloc_color = f"{alloc_name}"
        plots += f"\\addplot+[{alloc_color}{eb}] table {ebt}"

        plots += f" {{\n\tx y{edp}\n"

        for perm in perms:
            xval = _eval_with_stat(bench, xexpr, alloc_name, perm, "mean")
            yval = get_y_data(bench,
                              yexpr,
                              alloc_name,
                              perm,
                              "mean",
                              scale=scale)
            error = ""
            if error_bars:
                error = f" {_eval_with_stat(bench, yexpr, alloc_name, perm, 'std')}"
            plots += f"\t{xval} {yval}{error}\n"

        plots += "};\n"

    #pylint: disable=line-too-long
    tex =\
f"""\\documentclass{{standalone}}
\\usepackage{{pgfplots}}
\\usepackage{{xcolor}}
{style_definitions}
% include commont.tex if found to override styles
% see https://tex.stackexchange.com/questions/377295/how-to-prevent-input-from-failing-if-the-file-is-missing/377312#377312
\\InputIfFileExists{{common.tex}}{{}}{{}}
{color_definitions}
\\begin{{document}}
\\begin{{tikzpicture}}
\\begin{{axis}}[
\ttitle={{{title}}},
\txlabel={{{xlabel}}},
\tylabel={{{ylabel}}},
{axis_attr}]

{plots}
\\end{{axis}}
\\end{{tikzpicture}}
\\end{{document}}"""
    #pylint: enable=line-too-long

    with open(os.path.join(sumdir, f"{bench.name}.{postfix}.tex"),
              "w") as plot_file:
        print(tex, file=plot_file)
