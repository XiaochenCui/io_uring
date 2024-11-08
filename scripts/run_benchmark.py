#!/usr/bin/env python3

import os
import xiaochen_py
import signal

CODE_DIR = "/home/xiaochen/code"


# io_uring vs epoll
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

        os.chdir(CODE_DIR)
        echo_server_dir = os.path.join(CODE_DIR, "io_uring-echo-server")
        if not os.path.exists(echo_server_dir):
            xiaochen_py.run_command(
                "git clone https://github.com/frevib/io_uring-echo-server.git"
            )
            os.chdir(echo_server_dir)
            # make CCFLAGS="-Wall -O2 -D_GNU_SOURCE -luring -I/home/xiaochen/lib/liburing/include -L/home/xiaochen/lib/liburing/lib"
            INCLUDE_DIR = "/home/xiaochen/lib/liburing/include"
            LIB_DIR = "/home/xiaochen/lib/liburing/lib"
            xiaochen_py.run_command(
                f'make CCFLAGS="-Wall -O2 -D_GNU_SOURCE -luring -I{INCLUDE_DIR} -L{LIB_DIR}"'
            )

    setup()

    PORT = 8080
    CLIENTS_NUMBER = 300
    DURATION_SECONDS = 30
    MESSAGE_LENGTH = 128

    ECHO_CLIENT_DIR = os.path.join(CODE_DIR, "rust_echo_bench")

    io_uring_echo_server = xiaochen_py.run_background(
        f"./io_uring_echo_server {PORT}",
        log_path="io_uring_echo_server.log",
        work_dir=os.path.join(CODE_DIR, "io_uring-echo-server"),
    )

    # bind io_uring_echo_server to CPU 0
    xiaochen_py.run_command(
        f"taskset -cp 0 {io_uring_echo_server.pid}",
    )

    xiaochen_py.run_command(
        f"cargo run --release -- --address 'localhost:{PORT}' --number {CLIENTS_NUMBER} --duration {DURATION_SECONDS} --length {MESSAGE_LENGTH}",
        work_dir=ECHO_CLIENT_DIR,
    )
    io_uring_echo_server.exit()

    epoll_echo_server = xiaochen_py.run_background(
        f"./epoll_echo_server {PORT}",
        log_path="epoll_echo_server.log",
        work_dir=os.path.join(CODE_DIR, "epoll-echo-server"),
    )
    # bind epoll_echo_server to CPU 1
    xiaochen_py.run_command(
        f"taskset -cp 1 {epoll_echo_server.pid}",
    )
    xiaochen_py.run_command(
        f"cargo run --release -- --address 'localhost:{PORT}' --number {CLIENTS_NUMBER} --duration {DURATION_SECONDS} --length {MESSAGE_LENGTH}",
        work_dir=ECHO_CLIENT_DIR,
    )
    epoll_echo_server.exit()


if __name__ == "__main__":
    bench_a()
