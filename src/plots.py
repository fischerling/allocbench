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
import tikzplotlib

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
        matplotlib_c_colors = ["C" + str(i) for i in range(0,16)]
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

def plot_single_arg(bench, yval, ylabel="y-label", xlabel="x-label",
                    autoticks=True, title="default title", filepostfix="",
                    sumdir="", arg="", scale=None, file_ext=src.globalvars.summary_file_ext):
    """plot line graphs for each permutation of the benchmark's command arguments"""

    args = bench.results["args"]
    allocators = bench.results["allocators"]

    arg = arg or list(args.keys())[0]

    if not autoticks:
        x_vals = list(range(1, len(args[arg]) + 1))
    else:
        x_vals = args[arg]

    for allocator in allocators:
        y_vals = []
        for perm in bench.iterate_args(args=args):
            if scale:
                if scale == allocator:
                    y_vals = [1] * len(x_vals)
                else:
                    mean = _eval_with_stat(bench, yval, allocator, perm, "mean")
                    norm_mean = _eval_with_stat(bench, yval, scale, perm, "mean")
                    y_vals.append(mean / norm_mean)
            else:
                y_vals.append(_eval_with_stat(bench, yval, allocator, perm, "mean"))

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
    figname = os.path.join(sumdir, f"{bench.name}.{filepostfix}.{file_ext}")
    if figname.endswith(".tex"):
        tikzplotlib.save(figname)
    else:
        plt.savefig(figname)
    plt.clf()

def barplot_single_arg(bench, yval, ylabel="y-label", xlabel="x-label",
                       title="default title", filepostfix="", sumdir="",
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

    for i, allocator in enumerate(allocators):
        x_vals = list(range(i, narg * (nallocators+1), nallocators+1))
        y_vals = []
        y_errs = None
        if yerr:
            y_errs = []

        for perm in bench.iterate_args(args=args):
            if scale:
                if scale == allocator:
                    y_vals = [1] * len(x_vals)
                else:
                    mean = _eval_with_stat(bench, yval, allocator, perm, "mean")
                    norm_mean = _eval_with_stat(bench, yval, scale, perm, "mean")
                    y_vals.append(mean / norm_mean)
            else:
                y_vals.append(_eval_with_stat(bench, yval, allocator, perm, "mean"))

            if yerr:
                y_errs.append(_eval_with_stat(bench, yval, allocator, perm, "std"))

        plt.bar(x_vals, y_vals, width=1, label=allocator, yerr=y_errs,
                color=_get_alloc_color(bench, allocator))

    plt.legend(loc="best")
    plt.xticks(list(range(int(np.floor(nallocators/2)), narg*(nallocators+1), nallocators+1)), arg)

    label_substitutions = vars()
    label_substitutions.update(vars(bench))
    plt.xlabel(xlabel.format(**label_substitutions))
    plt.ylabel(ylabel.format(**label_substitutions))
    plt.title(title.format(**label_substitutions))
    figname = os.path.join(sumdir, f"{bench.name}.{filepostfix}.{file_ext}")
    if figname.endswith(".tex"):
        tikzplotlib.save(figname)
    else:
        plt.savefig(figname)
    plt.clf()

def plot_fixed_arg(bench, yval, ylabel="y-label", xlabel="{loose_arg}",
                   autoticks=True, title="default title", filepostfix="",
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
            for allocator in allocators:
                y_vals = []
                for perm in bench.iterate_args_fixed({arg: arg_value}, args=args):
                    if scale:
                        if scale == allocator:
                            y_vals = [1] * len(x_vals)
                        else:
                            mean = _eval_with_stat(bench, yval, allocator, perm, "mean")
                            norm_mean = _eval_with_stat(bench, yval, scale, perm, "mean")
                            y_vals.append(mean / norm_mean)
                    else:
                        y_vals.append(_eval_with_stat(bench, yval, allocator, perm, "mean"))

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
            figname = os.path.join(sumdir,
                                   f"{bench.name}.{arg}.{arg_value}.{filepostfix}.{file_ext}")
            if figname.endswith(".tex"):
                tikzplotlib.save(figname)
            else:
                plt.savefig(figname)
            plt.clf()

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
                    cur_line = line.format(bench.name, alloc,
                                           "/".join([str(p) for p in list(perm)]),
                                           statistic, values[datapoint])
                    # Replace empty outliers
                    cur_line.replace("[]", "")
                    # Replace underscores
                    cur_line.replace("_", "-")
                    print(cur_line, file=dataref_file)

def write_best_doublearg_tex_table(bench, expr, sort=">",
                                   filepostfix="", sumdir=""):
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

def write_tex_table(bench, entries, filepostfix="", sumdir=""):
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

    fname = os.path.join(sumdir, ".".join([bench.name, filepostfix, "tex"]))
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

def pgfplot_legend(bench, sumdir="", file_name="pgfplot_legend"):
    """create a standalone pgfplot legend"""

    allocators = bench.results["allocators"]
    tex =\
"""
\\documentclass{standalone}
\\usepackage{pgfplots}

\\usepackage{pgfkeys}

\\newenvironment{customlegend}[1][]{%
\t\\begingroup
\t\\csname pgfplots@init@cleared@structures\\endcsname
\t\\pgfplotsset{#1}%
}{%
\t\\csname pgfplots@createlegend\\endcsname
\t\\endgroup
}%
\\def\\addlegendimage{\\csname pgfplots@addlegendimage\\endcsname}

\\usepackage{xcolor}
"""

    for alloc_name, alloc_dict in allocators.items():
        # define color
        rgb = matplotlib.colors.to_rgb(_get_alloc_color(bench, alloc_dict))
        tex += f"\\providecolor{{{alloc_name}-color}}{{rgb}}{{{rgb[0]},{rgb[1]},{rgb[2]}}}\n"
        tex += f"\\pgfplotsset{{{alloc_name}/.style={{color={alloc_name}-color}}}}\n\n"

    if src.globalvars.latex_custom_preamble:
        tex += src.globalvars.latex_custom_preamble + "\n"

    tex +=\
"""
\\begin{document}
\\begin{tikzpicture}
\\begin{customlegend}[
\tlegend entries={"""

    alloc_list = ""
    addlegendimage_list = ""
    for alloc_name in allocators:
        alloc_list += f"{alloc_name}, "
        addlegendimage_list += f"\t\\addlegendimage{{{alloc_name}}}\n"

    tex += alloc_list[:-2] + "},\n]"
    tex += addlegendimage_list
    tex +=\
"""
\\end{customlegend}
\\end{tikzpicture}
\\end{document}"""

    with open(os.path.join(sumdir, f"{file_name}.tex"), "w") as legend_file:
        print(tex, file=legend_file)

def pgfplot(bench, perms, xexpr, yexpr, bar=False,
            ylabel="y-label", xlabel="x-label", title="default title",
            postfix="", sumdir="", scale=None, error_bars=True):

    allocators = bench.results["allocators"]
    perms = list(perms)
    title = title.format(**vars(), **vars(bench))
    tex =\
"""\\documentclass{standalone}
\\usepackage{pgfplots}
\\usepackage{xcolor}
"""

    for alloc_name, alloc_dict in allocators.items():
        tex += f"\\begin{{filecontents*}}{{{alloc_name}.dat}}\n"
        tex += "x y"
        if error_bars:
            tex += " error"
        tex += "\n"

        for perm in perms:
            xval = _eval_with_stat(bench, xexpr, alloc_name, perm, "mean")
            yval = _eval_with_stat(bench, yexpr, alloc_name, perm, "mean")
            tex += f"{xval} {yval}"
            if error_bars:
                error = _eval_with_stat(bench, yexpr, alloc_name, perm, "std")
                tex += f" {error}"
            tex += "\n"

        tex += "\\end{filecontents*}\n"

        # define color
        rgb = matplotlib.colors.to_rgb(_get_alloc_color(bench, alloc_dict))
        tex += f"\\providecolor{{{alloc_name}-color}}{{rgb}}{{{rgb[0]},{rgb[1]},{rgb[2]}}}\n"
        tex += f"\\pgfplotsset{{{alloc_name}/.style={{color={alloc_name}-color}}}}\n\n"

    if src.globalvars.latex_custom_preamble:
        tex += src.globalvars.latex_custom_preamble + "\n"

    label_substitutions = vars()
    label_substitutions.update(vars(bench))
    xlabel = xlabel.format(**label_substitutions)
    ylabel = ylabel.format(**label_substitutions)
    title = title.format(**label_substitutions)
    tex +=\
f"""
\\begin{{document}}
\\begin{{tikzpicture}}
\\begin{{axis}}[
\ttitle={{{title}}},
\txlabel={{{xlabel}}},
\tylabel={{{ylabel}}},"""
    if bar:
        tex += "\n\tybar,\n"
    tex += "]\n"

    for alloc_name in allocators:
        # tex += f"\\addplot [{alloc_name}-color] table {{{alloc_name}.dat}};\n"
        tex += f"\t\\addplot+[{alloc_name},"
        if error_bars:
            tex += "\n\terror bars/.cd, y dir=both, y explicit,\n\t"
        tex += f"] table"
        if error_bars:
            tex += "[y error=error]"
        tex += f" {{{alloc_name}.dat}};\n"

    tex +=\
"""\\end{axis}
\\end{tikzpicture}
\\end{document}"""

    with open(os.path.join(sumdir, f"{bench.name}.{postfix}.tex"), "w") as plot_file:
        print(tex, file=plot_file)
