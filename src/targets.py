targets = {"glibc" :    {
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
          }
