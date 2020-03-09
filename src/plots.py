# Copyright 2018-2019 Florian Fischer <florian.fl.fischer@fau.de>
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

import os
import traceback

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import src.globalvars
from src.util import print_debug, print_warn

# This is useful when evaluating strings in the plot functions. str(np.NaN) == "nan"
nan = np.NaN


def _get_alloc_color(bench, alloc):
    """Populate all not set allocator colors with matplotlib 'C' colors"""
    if isinstance(alloc, str):
        alloc = bench.results["allocators"][alloc]
    if alloc["color"] is None:
        allocs = bench.results["allocators"]
        explicit_colors = [v["color"] for v in allocs.values() if v["color"] is not None]
        matplotlib_c_colors = ["C" + str(i) for i in range(0,10)]
        avail_colors = [c for c in matplotlib_c_colors if c not in explicit_colors]

        for alloc in allocs.values():
            if alloc["color"] is None:
                alloc["color"] = avail_colors.pop()

    return alloc["color"]

def _eval_with_stat(bench, evaluation, alloc, perm, stat):
    """Helper to evaluate a datapoint description string"""
    try:
        res = evaluation.format(**bench.results["stats"][alloc][perm][stat])
    except KeyError:
        print_debug(traceback.format_exc())
        print_warn(f"KeyError while expanding {evaluation} for {alloc} and {perm}")
        return nan
    return eval(res)

def _get_y_data(bench, expression, allocator, perms, stat="mean", scale=None):
    """Helper to get the y data of an allocator for given permutations"""
    y_data = []
    for perm in perms:
        if scale:
            if scale == allocator:
                y_data.append(1)
            else:
                val = _eval_with_stat(bench, expression, allocator, perm, stat)
                norm_val = _eval_with_stat(bench, expression, scale, perm, stat)
                y_data.append(val / norm_val)
        else:
            y_data.append(_eval_with_stat(bench, expression, allocator, perm, stat))

    return y_data

def _save_figure(bench, fig, sumdir='', file_postfix='', file_ext=src.globalvars.summary_file_ext):
    figname = os.path.join(sumdir, f"{bench.name}.{file_postfix}.{file_ext}")
    if figname.endswith(".tex"):
        import tikzplotlib
        tikzplotlib.save(figname)
    else:
        fig.savefig(figname)

def plot_single_arg(bench, yval, ylabel="y-label", xlabel="x-label",
                    autoticks=True, title="default title", file_postfix="",
                    sumdir="", arg="", scale=None, file_ext=src.globalvars.summary_file_ext):
    """plot line graphs for each permutation of the benchmark's command arguments"""

    args = bench.results["args"]
    allocators = bench.results["allocators"]

    arg = arg or list(args.keys())[0]

    fig = plt.figure()

    if not autoticks:
        x_vals = list(range(1, len(args[arg]) + 1))
    else:
        x_vals = args[arg]

    for allocator in allocators:
        y_vals = _get_y_data(bench, yval, allocator, bench.iterate_args(args=args), stat='mean', scale=scale)
        plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                 label=allocator, color=_get_alloc_color(bench, allocator))

    plt.legend(loc="best")
    if not autoticks:
        plt.xticks(x_vals, args[arg])
    label_substitutions = vars()
    label_substitutions.update(vars(bench))
    plt.xlabel(xlabel.format(**label_substitutions))
    plt.ylabel(ylabel.format(**label_substitutions))
    plt.title(title.format(**label_substitutions))

    _save_figure(bench, fig, sumdir, file_postfix, file_ext)
    fig.close()

    return fig

def barplot_single_arg(bench, yval, ylabel="y-label", xlabel="x-label",
                       title="default title", file_postfix="", sumdir="",
                       arg="", scale=None, file_ext=src.globalvars.summary_file_ext, yerr=True):
    """plot bar plots for each permutation of the benchmark's command arguments"""

    args = bench.results["args"]
    allocators = bench.results["allocators"]
    nallocators = len(allocators)

    if arg:
        arg = args[arg]
    elif args.keys():
        arg = args[list(args.keys())[0]]
    else:
        arg = [""]

    narg = len(arg)

    fig = plt.figure()

    for i, allocator in enumerate(allocators):
        x_vals = list(range(i, narg * (nallocators+1), nallocators+1))
        y_vals = _get_y_data(bench, yval, allocator, bench.iterate_args(args=args), stat='mean', scale=scale)
        y_errs = None
        if yerr:
            y_vals = _get_y_data(bench, yval, allocator, bench.iterate_args(args=args), stat='std')

        plt.bar(x_vals, y_vals, width=1, label=allocator, yerr=y_errs,
                color=_get_alloc_color(bench, allocator))

    plt.legend(loc="best")
    plt.xticks(list(range(int(np.floor(nallocators/2)), narg*(nallocators+1), nallocators+1)), arg)

    label_substitutions = vars()
    label_substitutions.update(vars(bench))
    plt.xlabel(xlabel.format(**label_substitutions))
    plt.ylabel(ylabel.format(**label_substitutions))
    plt.title(title.format(**label_substitutions))

    _save_figure(bench, fig, sumdir, file_postfix, file_ext)
    fig.close()

def plot_fixed_arg(bench, yval, ylabel="y-label", xlabel="{loose_arg}",
                   autoticks=True, title="default title", file_postfix="",
                   sumdir="", fixed=None, file_ext=src.globalvars.summary_file_ext, scale=None):

    args = bench.results["args"]
    allocators = bench.results["allocators"]

    for arg in fixed or args:
        loose_arg = [a for a in args if a != arg][0]

        if not autoticks:
            x_vals = list(range(1, len(args[loose_arg]) + 1))
        else:
            x_vals = args[loose_arg]

        for arg_value in args[arg]:
            fig = plt.figure()

            for allocator in allocators:
                y_vals = _get_y_data(bench, yval, allocator, bench.iterate_args_fixed({arg: arg_value}, args=args), stat='mean', scale=scale)

                plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                         label=allocator, color=_get_alloc_color(bench, allocator))

            plt.legend(loc="best")
            if not autoticks:
                plt.xticks(x_vals, args[loose_arg])

            label_substitutions = vars()
            label_substitutions.update(vars(bench))
            plt.xlabel(xlabel.format(**label_substitutions))
            plt.ylabel(ylabel.format(**label_substitutions))
            plt.title(title.format(**label_substitutions))

            _save_figure(bench, fig, sumdir, file_postfix, file_ext)
            fig.close()

def export_facts_to_file(bench, comment_symbol, output_file):
    """Write collected facts about used system and benchmark to file"""
    print(comment_symbol, bench.name, file=output_file)
    print(file=output_file)
    print(comment_symbol, "Common facts:", file=output_file)
    for fact, value in src.facter.FACTS.items():
        print("f{comment_symbol}  {fact}: {value}", file=output_file)
    print(file=output_file)
    print(comment_symbol, "Benchmark facts:", file=output_file)
    for fact, value in bench.results["facts"].items():
        print(f"{comment_symbol} {fact}: {value}", file=output_file)
    print(file=output_file)

def export_stats_to_csv(bench, datapoint, path=None):
    """Write descriptive statistics about datapoint to csv file"""
    allocators = bench.results["allocators"]
    args = bench.results["args"]
    stats = bench.results["stats"]

    if path is None:
        path = datapoint

    path = path + ".csv"

    stats_fields = list(stats[list(allocators)[0]][list(bench.iterate_args(args=args))[0]])
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
            row += [stats[alloc][perm][stat][datapoint] for stat in stats[alloc][perm]]
            row[-1] = (",".join([str(x) for x in row[-1]]))
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
        export_facts_to_file(bench, "%", dataref_file)

        for alloc in bench.results["allocators"]:
            for perm in bench.iterate_args(args=bench.results["args"]):
                for statistic, values in stats[alloc][perm].items():
                    cur_line = line.format(bench.name,
                                            alloc,
                                           "/".join([str(p) for p in list(perm)]),
                                           statistic,
                                          values.get(datapoint, nan))
                    # Replace empty outliers
                    cur_line.replace("[]", "")
                    # Replace underscores
                    cur_line.replace("_", "-")
                    print(cur_line, file=dataref_file)

def write_best_doublearg_tex_table(bench, expr, sort=">", file_postfix="", sumdir=""):
    args = bench.results["args"]
    keys = list(args.keys())
    allocators = bench.results["allocators"]

    header_arg = keys[0] if len(args[keys[0]]) < len(args[keys[1]]) else keys[1]
    row_arg = [arg for arg in args if arg != header_arg][0]

    headers = args[header_arg]
    rows = args[row_arg]

    cell_text = []
    for av in rows:
        row = []
        for perm in bench.iterate_args_fixed({row_arg: av}, args=args):
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

            row.append("{}: {:.3f}".format(best[0], best_val))
        cell_text.append(row)

    fname = os.path.join(sumdir, ".".join([bench.name, filepostfix, "tex"]))
    with open(fname, "w") as tex_file:
        print("\\documentclass{standalone}", file=tex_file)
        print("\\begin{document}", file=tex_file)
        print("\\begin{tabular}{|", end="", file=tex_file)
        print(" l |" * len(headers), "}", file=tex_file)

        print(header_arg+"/"+row_arg, end=" & ", file=tex_file)
        for header in headers[:-1]:
            print(header, end="& ", file=tex_file)
        print(headers[-1], "\\\\", file=tex_file)

        for i, row in enumerate(cell_text):
            print(rows[i], end=" & ", file=tex_file)
            for entry in row[:-1]:
                print(entry, end=" & ", file=tex_file)
            print(row[-1], "\\\\", file=tex_file)
        print("\\end{tabular}", file=tex_file)
        print("\\end{document}", file=tex_file)

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
        alloc_header_line += f"\\multicolumn{{{nentries}}}{{c|}}{{{alloc}}} &"
    alloc_header_line = alloc_header_line[:-1] + "\\\\"

    perm_fields_header = ""
    for field in bench.Perm._fields:
        perm_fields_header += f'{field} &'
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
        print("\\begin{tabular}{|", f"{'c|'*nperm_fields}", f"{'c'*nentries}|"*nallocators, "}", file=tex_file)
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
                    values[i].append(_eval_with_stat(bench, expr, allocator, perm, "mean"))

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
                    val_str = str(val)
                    if isinstance(val, float):
                        val_str = f"{val:.2f}"

                    # colorize
                    if val == maxs[j]:
                        val_str = f"\\textcolor{{green}}{{{val_str}}}"
                    elif val == mins[j]:
                        val_str = f"\\textcolor{{red}}{{{val_str}}}"
                    row += f"{val_str} &"
            #escape _ for latex
            row = row.replace("_", "\\_")
            print(row[:-1], "\\\\", file=tex_file)

        print("\\end{tabular}", file=tex_file)
        print("\\end{document}", file=tex_file)

def pgfplot_legend(bench, sumdir="", file_name="pgfplot_legend", colors=True, columns=3):
    """create a standalone pgfplot legend"""

    allocators = bench.results["allocators"]
    color_definitions = ""
    legend_entries = ""
    for alloc_name, alloc_dict in allocators.items():
        if colors:
            # define color
            rgb = matplotlib.colors.to_rgb(_get_alloc_color(bench, alloc_dict))
            color_definitions += f"\\providecolor{{{alloc_name}-color}}{{rgb}}{{{rgb[0]},{rgb[1]},{rgb[2]}}}\n"
            color_definitions += f"\\pgfplotsset{{{alloc_name}/.style={{color={alloc_name}-color}}}}\n\n"

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
{src.globalvars.latex_custom_preamble}
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

def pgfplot(bench, perms, xexpr, yexpr, axis_attr="", bar=False,
            ylabel="y-label", xlabel="x-label", title="default title",
            postfix="", sumdir="", scale=None, error_bars=True, colors=True):

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
            rgb = matplotlib.colors.to_rgb(_get_alloc_color(bench, alloc_dict))
            color_definitions += f"\\providecolor{{{alloc_name}-color}}{{rgb}}{{{rgb[0]},{rgb[1]},{rgb[2]}}}\n"
            style_definitions += f"\\pgfplotsset{{{alloc_name}/.style={{color={alloc_name}-color}}}}\n\n"

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
            yval = _eval_with_stat(bench, yexpr, alloc_name, perm, "mean")
            error = ""
            if error_bars:
                error = f" {_eval_with_stat(bench, yexpr, alloc_name, perm, 'std')}"
            plots += f"\t{xval} {yval}{error}\n"

        plots += "};\n"

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

    with open(os.path.join(sumdir, f"{bench.name}.{postfix}.tex"), "w") as plot_file:
        print(tex, file=plot_file)
