#!/usr/bin/env python3

import json
import os
import sys
import time
import xiaochen_py
import signal
import matplotlib.pyplot as plt
import numpy as np
import xiaochen_py
import re

CODE_DIR = "/home/xiaochen/code"
IO_URING_RESEARCH_DIR = os.path.join(CODE_DIR, "io_uring_research")


# echo server benchmark
# - io_uring
# - epoll
# - select
def bench_a():
    def setup():
        os.chdir(CODE_DIR)
        target_dir = os.path.join(CODE_DIR, "liburing")
        if not os.path.exists(target_dir):
            xiaochen_py.run_command("git clone https://github.com/axboe/liburing")
            os.chdir(target_dir)
            xiaochen_py.run_command("./configure --prefix=/home/xiaochen/lib/liburing")
            xiaochen_py.run_command("make")
            xiaochen_py.run_command("make install")

        os.chdir(IO_URING_RESEARCH_DIR)

        # compile io_uring echo server
        INCLUDE_DIR = "/home/xiaochen/lib/liburing/include"
        LIB_DIR = "/home/xiaochen/lib/liburing/lib"
        CPP_FILE = "./benchmark/echo_server_io_uring.cpp"
        BIN_FILE = "./build/echo_server_io_uring"
        xiaochen_py.run_command(
            f"c++ {CPP_FILE} -o {BIN_FILE} -Wall -O2 -D_GNU_SOURCE -luring -I{INCLUDE_DIR} -L{LIB_DIR}"
        )

        # compile io_uring echo server (with kernel poll)
        INCLUDE_DIR = "/home/xiaochen/lib/liburing/include"
        LIB_DIR = "/home/xiaochen/lib/liburing/lib"
        CPP_FILE = "./benchmark/echo_server_io_uring_kernel_poll.cpp"
        BIN_FILE = "./build/echo_server_io_uring_kernel_poll"
        xiaochen_py.run_command(
            f"c++ {CPP_FILE} -o {BIN_FILE} -Wall -O2 -D_GNU_SOURCE -luring -I{INCLUDE_DIR} -L{LIB_DIR}"
        )

        # compile epoll echo server
        CPP_FILE = "./benchmark/echo_server_epoll.cpp"
        BIN_FILE = "./build/echo_server_epoll"
        xiaochen_py.run_command(f"c++ {CPP_FILE} -o {BIN_FILE} -Wall -O2 -D_GNU_SOURCE")

        # compile select echo server
        CPP_FILE = "./benchmark/echo_server_select.cpp"
        BIN_FILE = "./build/echo_server_select"
        xiaochen_py.run_command(f"c++ {CPP_FILE} -o {BIN_FILE} -Wall -O2 -D_GNU_SOURCE")

    setup()

    PORT = 8080
    ECHO_CLIENT_DIR = os.path.join(CODE_DIR, "rust_echo_bench")

    def run(
        target: str,
        binary: str,
        client_number: int,
        duration_seconds: int,
        message_length: int,
    ) -> xiaochen_py.BenchmarkRecord:
        # kill the previous server
        xiaochen_py.run_command(f"fuser -k {PORT}/tcp", raise_on_failure=False)
        time.sleep(1)

        server = xiaochen_py.run_background(
            f"{binary} {PORT}",
            log_path=f"./{target}_server.log",
            work_dir=IO_URING_RESEARCH_DIR,
        )

        # bind io_uring_echo_server to CPU 0
        xiaochen_py.run_command(
            f"taskset -cp 0 {server.pid}",
        )

        output, _ = xiaochen_py.run_command(
            f"cargo run --release -- --address 'localhost:{PORT}' --number {client_number} --duration {duration_seconds} --length {message_length}",
            work_dir=ECHO_CLIENT_DIR,
        )
        server.exit()
        time.sleep(2)

        # sample output: Speed: 152720 request/sec, 152720 response/sec
        speed = re.search(r"Speed: (\d+) request/sec", output.decode("utf-8")).group(1)
        print(f"Speed: {speed} request/sec")

        r = xiaochen_py.BenchmarkRecord()
        r.target_attributes = {
            "target": target,
            "client_number": client_number,
            "duration_seconds": duration_seconds,
            "message_length": message_length,
        }
        r.test_result = {
            "request_per_second": int(speed),
        }

        return r

    client_number_list = [1, 200, 400, 600, 800, 1000]
    # message_length_list = [1, 128, 1024]
    message_length_list = [1024]
    duration_seconds = 20

    records = []
    for client_number in client_number_list:
        for message_length in message_length_list:
            r = run(
                "io_uring",
                "./build/echo_server_io_uring",
                client_number,
                duration_seconds,
                message_length,
            )
            records.append(r)

            # error from client:
            # Read error! length=0
            #
            # r = run(
            #     "io_uring_kernel_poll",
            #     "./build/echo_server_io_uring_kernel_poll",
            #     client_number,
            #     duration_seconds,
            #     message_length,
            # )
            # records.append(r)

            r = run(
                "epoll",
                "./build/echo_server_epoll",
                client_number,
                duration_seconds,
                message_length,
            )
            records.append(r)
            r = run(
                "select",
                "./build/echo_server_select",
                client_number,
                duration_seconds,
                message_length,
            )
            records.append(r)

    xiaochen_py.dump_records(records, "./docs/record/echo_server/")


# disk benchmark
# - io_uring
# - aio
def bench_b():
    # fio --name=benchmark --ioengine=io_uring --direct=1 --size=1G --bs=4k --rw=randread --numjobs=1 --time_based --runtime=10s --filename=testfile
    # fio --name=benchmark --ioengine=aio --direct=1 --size=1G --bs=4k --rw=randread --numjobs=1 --time_based --runtime=10s --filename=testfile
    # fio --name=benchmark --ioengine=direct --direct=1 --size=1G --bs=4k --rw=randread --numjobs=1 --time_based --runtime=10s --filename=testfile

    # make the job run exactly 10 seconds when combined with "--time_based"
    runtime = "10s"

    # size_mb = "1024"  # total size of io, in mb
    size_mb = "10"  # total size of io, in mb

    ioengine_list = ["sync", "psync", "io_uring", "libaio", "mmap", "pvsync"]

    readwrite_options = [
        "read",
        "write",
        "randread",
        "randwrite",
        "readwrite",
        "randrw",
    ]

    # linux libaio only support queued behavior with non-buffered I/O (direct=1 or buffered=0)
    direct_options = [0, 1]

    DATA_DIR = "/media/xiaochen/large/cs_data/io_uring_test"

    records = []
    for ioengine in ioengine_list:
        for readwrite in readwrite_options:
            for direct in direct_options:
                fio_command = f"fio --name=benchmark --ioengine={ioengine} --direct={direct} --size={size_mb}M --bs=4k --rw={readwrite} --numjobs=1 --filename=testfile"
                output, _ = xiaochen_py.run_command(fio_command, work_dir=DATA_DIR)

                # sample output:
                # - bw=840.2MiB/s
                # - bw=840MiB/s
                # - bw=123.4KiB/s
                # - bw=123KiB/s
                groups = re.search(
                    r"bw=(\d+\.?\d*)([KMG]iB/s)", output.decode("utf-8")
                ).groups()
                number = float(groups[0])
                unit = groups[1]

                bandwidth_mb = 0
                if unit == "KiB/s":
                    bandwidth_mb = number / 1024
                if unit == "MiB/s":
                    bandwidth_mb = number
                if unit == "GiB/s":
                    bandwidth_mb = number * 1024

                r = xiaochen_py.BenchmarkRecord()
                r.target_attributes = {
                    "target": ioengine,
                    "readwrite": readwrite,
                    "size_mb": size_mb,  # total size of io, in mb
                    "direct": direct,
                }
                r.test_result = {
                    "bandwidth_mb": bandwidth_mb,
                }
                records.append(r)
    os.chdir(IO_URING_RESEARCH_DIR)
    xiaochen_py.dump_records(records, "./docs/record/disk/")


if __name__ == "__main__":
    # bench_a()
    bench_b()
