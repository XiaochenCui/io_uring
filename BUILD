py_binary(
    name = "run_benchmark",
    srcs = ["benchmark/run_benchmark.py"],
)

py_binary(
    name = "gen_graph",
    srcs = ["benchmark/draw.py"],
)

cc_library(
    name = "liburing",
    hdrs = glob(["liburing/include/liburing.h"]),
    includes = ["liburing/include"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "echo_server_io_uring",
    srcs = ["benchmark/echo_server_io_uring.cpp"],
    deps = [":liburing"],
    copts = ["-Iliburing/include"],
    linkopts = ["-luring"],
)
