#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 ReSukiSU Manual Hook 的接线错误：sucompat 挂在 ksu_handle_execve() 上，
只调 ksu_handle_execveat_ksud() 会导致 su 永远不生效。3.18 无 execveat，
execve/compat_execve 都汇聚到 do_execve_common()，改这一处即可。
"""
import io
import os
import re
import sys

KSRC = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
TARGET = os.path.join(KSRC, "fs/exec.c")
MARK = "KSU_EXEC_HOOK_V2"

HOOK_BLOCK = """#ifdef CONFIG_KSU
\t/* --- KSU_EXEC_HOOK_V2 ---
\t * 必须调用 ksu_handle_execve()：sucompat（把 /system/bin/su 重定向到
\t * /data/adb/ksud）挂在它内部的 do_ksu_handle_execveat_sucompat()，
\t * 只调 ksu_handle_execveat_ksud() 不含任何 su 逻辑。
\t * 3.18 恒为 AT_FDCWD + flags=0。
\t */
\t{
\t\textern void ksu_handle_execveat_ksud(const char *filename,
\t\t\tstruct user_arg_ptr *argv, struct user_arg_ptr *envp, int *flags);
\t\textern int ksu_handle_execve(int *fd, const char *filename,
\t\t\tvoid *argv, void *envp, int *flags);

\t\tint ksu_fd = AT_FDCWD;
\t\tint ksu_flags = 0;

\t\tksu_handle_execveat_ksud(filename->name, &argv, &envp, NULL);
\t\tksu_handle_execve(&ksu_fd, filename->name, &argv, &envp, &ksu_flags);
\t}
\t/* --- end KSU_EXEC_HOOK_V2 --- */
#endif
"""

POST_BLOCK = """\t/* execve succeeded */
#ifdef CONFIG_KSU
\t/* KSU_EXEC_HOOK_V2: exec 成功后安装 su 会话 fd */
\t{
\t\textern int ksu_handle_post_execve(int *fd, const char *filename,
\t\t\tvoid *argv, void *envp, int *flags, int *retval);
\t\tint ksu_fd = AT_FDCWD;
\t\tint ksu_flags = 0;
\t\tksu_handle_post_execve(&ksu_fd, filename->name, &argv, &envp,
\t\t\t\t       &ksu_flags, &retval);
\t}
#endif
"""


def fail(msg):
    sys.stderr.write("[exec_hook_fix] ERROR: %s\n" % msg)
    sys.exit(1)


def main():
    if not os.path.isfile(TARGET):
        fail("找不到 %s" % TARGET)

    with io.open(TARGET, "r", encoding="utf-8", errors="surrogateescape") as f:
        src = f.read()

    if MARK in src:
        print("[exec_hook_fix] 已打过补丁，跳过")
        return

    pat = re.compile(
        r"#ifdef CONFIG_KSU\n"
        r"(?:[^\n]*\n)*?"
        r"[^\n]*ksu_handle_execveat_ksud\(filename->name[^\n]*\n"
        r"#endif\n"
    )
    m = pat.search(src)
    if not m:
        fail("找不到原 ksu_handle_execveat_ksud 钩子块")
    src = src[:m.start()] + HOOK_BLOCK + src[m.end():]
    print("[exec_hook_fix] 已替换 execve 主钩子")

    anchor = "\t/* execve succeeded */\n"
    n = src.count(anchor)
    if n != 1:
        fail("'/* execve succeeded */' 出现 %d 次（期望 1 次）" % n)
    src = src.replace(anchor, POST_BLOCK, 1)
    print("[exec_hook_fix] 已插入 ksu_handle_post_execve")

    with io.open(TARGET, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(src)
    print("[exec_hook_fix] 完成")


if __name__ == "__main__":
    main()
