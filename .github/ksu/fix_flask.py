#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""3.18: flask.h 只在 objtree 生成，KSU 的 Kbuild 需要补 -I$(objtree)/security/selinux."""
import os
import sys

KSRC = os.getcwd()
KBUILD = os.path.join(KSRC, "KernelSU/kernel/Kbuild")

if not os.path.isfile(KBUILD):
    sys.stderr.write("[fix_flask] 找不到 %s\n" % KBUILD)
    sys.exit(1)

s = open(KBUILD, encoding="utf-8", errors="replace").read()

if "-I$(objtree)/security/selinux" in s:
    print("[fix_flask] 已包含，跳过")
    sys.exit(0)

ANCHOR = ("ccflags-y += -I$(srctree)/security/selinux "
          "-I$(srctree)/security/selinux/include\n")
if ANCHOR not in s:
    sys.stderr.write("[fix_flask] 找不到锚点行，实际内容：\n")
    for line in s.splitlines():
        if "ccflags" in line or "selinux" in line:
            sys.stderr.write("   %s\n" % line)
    sys.exit(1)

s = s.replace(
    ANCHOR,
    ANCHOR
    + "# flask.h / av_permissions.h 由构建时生成，只在 objtree\n"
    + "ccflags-y += -I$(objtree)/security/selinux "
      "-I$(objtree)/security/selinux/include\n",
    1,
)
open(KBUILD, "w", encoding="utf-8").write(s)
print("[fix_flask] 已修补 Kbuild")
