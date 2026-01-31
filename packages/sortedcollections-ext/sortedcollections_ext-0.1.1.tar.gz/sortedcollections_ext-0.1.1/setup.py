from setuptools import Extension, setup
import os


def _maybe_add_flag(flags, flag):
    if flag not in flags:
        flags.append(flag)


def _get_build_flags():
    enable_coverage = os.environ.get("SORTEDCOLLECTIONS_COVERAGE") == "1"
    enable_pgo = os.environ.get("SORTEDCOLLECTIONS_PGO") == "1"
    enable_lto = os.environ.get("SORTEDCOLLECTIONS_LTO", "1") == "1"
    cflags = []
    ldflags = []

    if enable_coverage:
        enable_pgo = False
        enable_lto = False
        _maybe_add_flag(cflags, "-O0")
        _maybe_add_flag(cflags, "-g")
        _maybe_add_flag(cflags, "-fprofile-arcs")
        _maybe_add_flag(cflags, "-ftest-coverage")
        _maybe_add_flag(ldflags, "-fprofile-arcs")
        _maybe_add_flag(ldflags, "-ftest-coverage")

    if enable_pgo:
        pgo_mode = os.environ.get("SORTEDCOLLECTIONS_PGO_MODE", "use")
        if pgo_mode == "gen":
            _maybe_add_flag(cflags, "-fprofile-generate")
            _maybe_add_flag(ldflags, "-fprofile-generate")
        else:
            _maybe_add_flag(cflags, "-fprofile-use")
            _maybe_add_flag(ldflags, "-fprofile-use")
            _maybe_add_flag(cflags, "-fprofile-correction")

    if enable_lto:
        _maybe_add_flag(cflags, "-flto")
        _maybe_add_flag(ldflags, "-flto")

    return cflags, ldflags


cflags, ldflags = _get_build_flags()

extensions = [
    Extension(
        "btree",
        sources=["src/btree.c"],
        include_dirs=["include"],
        extra_compile_args=cflags,
        extra_link_args=ldflags,
    ),
    Extension(
        "sortedcollections",
        sources=["src/sorted_collections.c"],
        include_dirs=["include"],
        extra_compile_args=cflags,
        extra_link_args=ldflags,
    ),
]

setup(ext_modules=extensions)
