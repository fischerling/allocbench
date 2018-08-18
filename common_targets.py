common_targets = {"klmalloc" : {
                                "cmd_prefix"    : "",
                                "binary_suffix" : "",
                                "LD_PRELOAD"    : "targets/libklmalloc.so",
                                "color"         : "C0"
                               },
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
                  }

analyse_targets = {"chattymalloc" : {"LD_PRELOAD" : "build/chattymalloc.so"}}
