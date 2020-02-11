import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import tikzplotlib

from src.benchmark import Benchmark
import src.globalvars
from src.util import print_warn

# This is useful when evaluating strings in the plot functions. str(np.NaN) == "nan"
nan = np.NaN


###### Summary helpers ######
def _eval_with_stat(bench, evaluation, alloc, perm, stat):
    try:
        s = evaluation.format(**bench.results["stats"][alloc][perm][stat])
    except KeyError as e:
        import traceback
        print_warn(traceback.format_exc())
        print_warn(f"For {alloc} in {perm}")
        return nan
    return eval(s)

def plot_single_arg(bench, yval, ylabel="'y-label'", xlabel="'x-label'",
                    autoticks=True, title="'default title'", filepostfix="",
                    sumdir="", arg="", scale=None, file_ext=src.globalvars.summary_file_ext):

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
                 label=allocator, color=allocators[allocator]["color"])

    plt.legend(loc="best")
    if not autoticks:
        plt.xticks(x_vals, args[arg])
    plt.xlabel(eval(xlabel))
    plt.ylabel(eval(ylabel))
    plt.title(eval(title))
    figname = os.path.join(sumdir, f"{bench.name}.{filepostfix}.{file_ext}")
    if figname.endswith(".tex"):
        tikzplotlib.save(figname)
    else:
        plt.savefig(figname)
    plt.clf()

def barplot_single_arg(bench, yval, ylabel="'y-label'", xlabel="'x-label'",
                       title="'default title'", filepostfix="", sumdir="",
                       arg="", scale=None, file_ext=src.globalvars.summary_file_ext, yerr=True):

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
                color=allocators[allocator]["color"])

    plt.legend(loc="best")
    plt.xticks(list(range(int(np.floor(nallocators/2)), narg*(nallocators+1), nallocators+1)), arg)
    plt.xlabel(eval(xlabel))
    plt.ylabel(eval(ylabel))
    plt.title(eval(title))
    figname = os.path.join(sumdir, f"{bench.name}.{filepostfix}.{file_ext}")
    if figname.endswith(".tex"):
        import tikzplotlib
        tikzplotlib.save(figname)
    else:
        plt.savefig(figname)
    plt.clf()

def plot_fixed_arg(bench, yval, ylabel="'y-label'", xlabel="loose_arg",
                   autoticks=True, title="'default title'", filepostfix="",
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
                         label=allocator, color=allocators[allocator]["color"])

            plt.legend(loc="best")
            if not autoticks:
                plt.xticks(x_vals, args[loose_arg])
            plt.xlabel(eval(xlabel))
            plt.ylabel(eval(ylabel))
            plt.title(eval(title))
            figname = os.path.join(sumdir,
                                   f"{bench.name}.{arg}.{arg_value}.{filepostfix}.{file_ext}")
            if figname.endswith(".tex"):
                import tikzplotlib
                tikzplotlib.save(figname)
            else:
                plt.savefig(figname)
            plt.clf()

def export_facts_to_file(bench, comment_symbol, f):
    """Write collected facts about used system and benchmark to file"""
    print(comment_symbol, bench.name, file=f)
    print(file=f)
    print(comment_symbol, "Common facts:", file=f)
    for k, v in src.facter.FACTS.items():
        print(comment_symbol, k + ":", v, file=f)
    print(file=f)
    print(comment_symbol, "Benchmark facts:", file=f)
    for k, v in bench.results["facts"].items():
        print(comment_symbol, k + ":", v, file=f)
    print(file=f)

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
            d = []
            d.append(alloc)
            d += list(perm._asdict().values())
            d += [stats[alloc][perm][s][datapoint] for s in stats[alloc][perm]]
            d[-1] = (",".join([str(x) for x in d[-1]]))
            rows[alloc][perm] = d

    # calc widths
    for i in range(0, len(fieldnames)):
        for alloc in allocators:
            for perm in bench.iterate_args(args=args):
                field_len = len(str(rows[alloc][perm][i])) + 2
                if field_len > widths[i]:
                    widths[i] = field_len

    with open(path, "w") as f:
        headerline = ""
        for i, h in enumerate(fieldnames):
            headerline += h.capitalize().ljust(widths[i]).replace("_", "-")
        print(headerline, file=f)

        for alloc in allocators:
            for perm in bench.iterate_args(args=args):
                line = ""
                for i, x in enumerate(rows[alloc][perm]):
                    line += str(x).ljust(widths[i])
                print(line.replace("_", "-"), file=f)

def export_stats_to_dataref(bench, datapoint, path=None):
    """Write descriptive statistics about datapoint to dataref file"""
    stats = bench.results["stats"]

    if path is None:
        path = datapoint

    path = path + ".dataref"

    # Example: \drefset{/mysql/glibc/40/Lower-whisker}{71552.0}
    line = "\\drefset{{/{}/{}/{}/{}}}{{{}}}"

    with open(path, "w") as f:
        # Write facts to file
        export_facts_to_file(bench, "%", f)

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
                    print(cur_line, file=f)

def write_best_doublearg_tex_table(bench, evaluation, sort=">",
                                   filepostfix="", sumdir="", std=False):
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
                d = []
                for m in bench.results[allocator][perm]:
                    d.append(eval(evaluation.format(**m)))
                mean = np.mean(d)
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
    with open(fname, "w") as f:
        print("\\documentclass{standalone}", file=f)
        print("\\begin{document}", file=f)
        print("\\begin{tabular}{|", end="", file=f)
        print(" l |" * len(headers), "}", file=f)

        print(header_arg+"/"+row_arg, end=" & ", file=f)
        for header in headers[:-1]:
            print(header, end="& ", file=f)
        print(headers[-1], "\\\\", file=f)

        for i, row in enumerate(cell_text):
            print(rows[i], end=" & ", file=f)
            for e in row[:-1]:
                print(e, end=" & ", file=f)
            print(row[-1], "\\\\", file=f)
        print("\\end{tabular}", file=f)
        print("\\end{document}", file=f)

def write_tex_table(bench, entries, sort=">",
                    filepostfix="", sumdir="", std=False):
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
    with open(fname, "w") as f:
        print("\\documentclass{standalone}", file=f)
        print("\\usepackage{booktabs}", file=f)
        print("\\usepackage{xcolor}", file=f)
        print("\\begin{document}", file=f)
        print("\\begin{tabular}{|", f"{'c|'*nperm_fields}", f"{'c'*nentries}|"*nallocators, "}", file=f)
        print("\\toprule", file=f)

        print(alloc_header_line, file=f)
        print("\\hline", file=f)
        print(entry_header_line, file=f)
        print("\\hline", file=f)

        for perm in bench.iterate_args(args=args):
            values = [[] for _ in entries]
            maxs = [None for _ in entries]
            mins = [None for _ in entries]
            for allocator in allocators:
                for i, entry in enumerate(entries):
                    expr = entry["expression"]
                    values[i].append(eval(expr.format(**bench.results["stats"][allocator][perm]["mean"])))

            # get max and min for each entry
            for i, entry in enumerate(entries):
                if not "sort" in entry:
                    continue
                # bigger is better
                elif entry["sort"] == ">":
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
                for y, entry_vals in enumerate(values):
                    val = entry_vals[i]

                    # format
                    val_str = str(val)
                    if type(val) == float:
                        val_str = f"{val:.2f}"

                    # colorize
                    if val == maxs[y]:
                        val_str = f"\\textcolor{{green}}{{{val_str}}}"
                    elif val == mins[y]:
                        val_str = f"\\textcolor{{red}}{{{val_str}}}"
                    row += f"{val_str} &"
            #escape _ for latex
            row = row.replace("_", "\\_")
            print(row[:-1], "\\\\", file=f)

        print("\\end{tabular}", file=f)
        print("\\end{document}", file=f)

def pgfplot_legend(bench, sumdir=""):

    allocators = bench.results["allocators"]
    s =\
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
        rgb = matplotlib.colors.to_rgb(alloc_dict["color"])
        s += f"\\providecolor{{{alloc_name}-color}}{{rgb}}{{{rgb[0]},{rgb[1]},{rgb[2]}}}\n"

    s +=\
"""
\\begin{document}
\\begin{tikzpicture}
\\begin{customlegend}[
\tlegend entries={"""

    alloc_list = ""
    addlegendimage_list = ""
    for alloc_name in allocators:
        alloc_list += f"{alloc_name}, "
        addlegendimage_list += "\t\\addlegendimage{}\n"

    s += alloc_list[:-2] + "},\n]"
    s += addlegendimage_list
    s +=\
"""
\\end{customlegend}
\\end{tikzpicture}
\\end{document}"""

    with open(os.path.join(sumdir, "legend.tex"), "w") as legend_file:
        print(s, file=legend_file)

def pgfplot_linear(bench, perms, xval, yval, ylabel="'y-label'", xlabel="'x-label'",
                   title="'default title'", postfix="", sumdir="", scale=None):

    allocators = bench.results["allocators"]
    perms = list(perms)
    title = eval(title)
    s =\
"""\\documentclass{standalone}
\\usepackage{pgfplots}
\\usepackage{xcolor}
"""

    for alloc_name, alloc_dict in allocators.items():
        s += f"\\begin{{filecontents*}}{{{alloc_name}.dat}}\n"
        for i, perm in enumerate(perms):
            x = _eval_with_stat(bench, xval, alloc_name, perm, "mean")
            y = _eval_with_stat(bench, yval, alloc_name, perm, "mean")
            s += f"{x} {y}\n"
        s += "\\end{filecontents*}\n"

        # define color
        rgb = matplotlib.colors.to_rgb(alloc_dict["color"])
        s += f"\\providecolor{{{alloc_name}-color}}{{rgb}}{{{rgb[0]},{rgb[1]},{rgb[2]}}}\n"

    s +=\
f"""
\\begin{{document}}
\\begin{{tikzpicture}}
\\begin{{axis}}[
\ttitle={{{title}}},
\txlabel={{{eval(xlabel)}}},
\tylabel={{{eval(ylabel)}}},
]
"""

    for alloc_name in allocators:
        s += f"\\addplot [{alloc_name}-color] table {{{alloc_name}.dat}};\n"
        # s += f"\t\\addplot table {{{alloc_name}.dat}};\n"

    s +=\
"""\\end{axis}
\\end{tikzpicture}
\\end{document}"""

    with open(os.path.join(sumdir, f"{bench.name}.{postfix}.tex"), "w") as plot_file:
        print(s, file=plot_file)
