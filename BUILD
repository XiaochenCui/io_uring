py_binary(
    name = "run_benchmark",
    srcs = ["benchmark/run_benchmark.py"],
)

py_binary(
    name = "gen_report",
    srcs = ["benchmark/gen_report.py"],
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
    copts = ["-Iliburing/include"],
    linkopts = ["-luring"],
    deps = [":liburing"],
)
