import subprocess

glibc_path = "/home/cip/2014/aj46ezos/BA/glibc/glibc-install/lib"
glibc_path_notc = "/home/cip/2014/aj46ezos/BA/glibc/glibc-install-notc/lib"

library_path = ""
p = subprocess.run(["ldconfig", "-v"], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True)

for l in p.stdout.splitlines():
    if not l.startswith('\t'):
        library_path += l

common_targets = {
                  "glibc" :    {
                                "cmd_prefix"    : "",
                                "binary_suffix" : "",
                                "LD_PRELOAD"    : "",
                                "color"         : "C1"
                               },
                  "tcmalloc" : {
                                "cmd_prefix"    : "",
                                "binary_suffix" : "",
                                "LD_PRELOAD"    : "targets/libtcmalloc.so",
                                "color"         : "C2"
                               },
                  "jemalloc" : {
                                "cmd_prefix"    : "",
                                "binary_suffix" : "",
                                "LD_PRELOAD"    : "targets/libjemalloc.so",
                                "color"         : "C3"
                               },
                  "hoard"    : {
                                "cmd_prefix"    : "",
                                "binary_suffix" : "",
                                "LD_PRELOAD"    : "targets/libhoard.so",
                                "color"         : "C4"
                               },
                  "glibc-notc" :    {
                                "cmd_prefix"    : glibc_path+"/ld-2.28.9000.so "
                                                    + "--library-path "
                                                    + glibc_path + ":"
                                                    + library_path,
                                "binary_suffix" : "-glibc-notc",
                                "LD_PRELOAD"    : "/usr/lib/libstdc++.so /usr/lib/libgcc_s.so.1",
                                "color"         : "C5"
                               },
                  }
