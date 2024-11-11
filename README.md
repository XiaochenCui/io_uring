# io_uring Research

## Environment

- linux: 6.8.0-48-generic (Ubuntu 24.04 LTS)
- gcc: (Ubuntu 13.2.0-23ubuntu4) 13.2.0
- fio: fio/noble 3.36-1build2 amd64
- liburing: 2.8

## Run

### Run Benchmark

```
bazel run //:run_benchmark
```

### Generate Benchmark Report

Generate graphs from the benchmark results.

```
bazel run //:gen_report
```

### Show Details

```
make show_details
```

