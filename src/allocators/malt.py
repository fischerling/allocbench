from src.allocator import Allocator

# result_dir and perm are substituted during Benchmark.run
cmd = "malt -q -o output:name={{result_dir}}/malt.{{perm}}.%3"

malt = Allocator("malt", cmd_prefix=cmd)
