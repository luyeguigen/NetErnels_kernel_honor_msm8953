#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""3.18 没有 kmemdup_nul（4.x 才有），KSU 的 selinux_hide.c 用了它 -> 补本地实现."""
import os
import re
import sys

KSRC = os.getcwd()
TGT = os.path.join(KSRC, "drivers/kernelsu/feature/selinux_hide.c")

if not os.path.isfile(TGT):
    sys.stderr.write("[selinux_hide_fix] 找不到 %s\n" % TGT)
    sys.exit(1)

s = open(TGT, encoding="utf-8", errors="replace").read()

if "ksu_kmemdup_nul" not in s:
    s = re.sub(r"\bkmemdup_nul\b", "ksu_kmemdup_nul", s)
    s = s.replace(
        '#include "compat/kernel_compat.h"',
        '#include "compat/kernel_compat.h"\n'
        "\n"
        "/* Local kmemdup_nul fallback for pre-3.18.9 kernels */\n"
        "static inline char *ksu_kmemdup_nul(const char *s, size_t len, gfp_t gfp)\n"
        "{\n"
        "\tchar *buf;\n"
        "\n"
        "\tif (!s)\n"
        "\t\treturn NULL;\n"
        "\n"
        "\tbuf = kmalloc(len + 1, gfp);\n"
        "\tif (buf) {\n"
        "\t\tmemcpy(buf, s, len);\n"
        "\t\tbuf[len] = 0;\n"
        "\t}\n"
        "\treturn buf;\n"
        "}",
        1,
    )
    open(TGT, "w", encoding="utf-8").write(s)
    print("[selinux_hide_fix] 已注入 ksu_kmemdup_nul")
else:
    print("[selinux_hide_fix] 已存在，跳过")
