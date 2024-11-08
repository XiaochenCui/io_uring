#!/usr/bin/env python3

import os
import xiaochen_py


def gen_data():
    DATA_FILE = "/media/xiaochen/large/cs_data/io_uring_test/test_file"
    if os.path.exists(DATA_FILE):
        return

    xiaochen_py.run_command(
        f"fio --name=test_file --size=1G --filename={DATA_FILE} --bs=4k --rw=write --direct=1"
    )


def io_uring():
    CPP_FILE = "src/io_uring.cpp"
    BIN_FILE = "build/io_uring"
    INCLUDE_DIR = "/home/xiaochen/lib/liburing/include"
    LIB_DIR = "/home/xiaochen/lib/liburing/lib"
    xiaochen_py.run_command(
        # -Wall: enables most common warnings
        # -O2: optimization level 2 (1 is the lowest, 3 is the highest)
        # -D_GNU_SOURCE: Defines the `_GNU_SOURCE` macro, which allows access to GNU-specific features and extensions in the standard library (e.g., certain functions, macros, and constants not available in strict POSIX mode).
        f"c++ {CPP_FILE} -o {BIN_FILE} -Wall -O2 -D_GNU_SOURCE -luring -I{INCLUDE_DIR} -L{LIB_DIR}"
    )

    xiaochen_py.run_command(f"{BIN_FILE}")


if __name__ == "__main__":
    gen_data()
    io_uring()
