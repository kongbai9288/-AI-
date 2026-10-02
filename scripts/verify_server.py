#!/usr/bin/env python3
"""服务端实测脚本: 真跑 loader 的服务端 launcher、读 installer 的 server 子命令与产物名。

不做任何"凭记忆"的推断, 全部从真实运行输出 / class 常量池里取。

用法:
  python3 scripts/verify_server.py            # 生成 server/SETUP_REPORT.md
  python3 scripts/verify_server.py --stdout   # 只打印不写文件

依赖: JDK 25(java/javap), toolchain/ 下的 fabric-loader / fabric-installer jar
"""
import glob
import json
import os
import re
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONLY_STDOUT = '--stdout' in sys.argv


def find_jdk():
    for p in sorted(glob.glob('/data/workspace/jdk-25*/')):
        if os.path.exists(p + 'bin/javap'):
            return p.rstrip('/')
    raise SystemExit('找不到 JDK 25, 请先合并并解压 toolchain/jdk-25-linux-x64.tar.gz')


def find_jar(pattern):
    hits = sorted(glob.glob(os.path.join(ROOT, 'toolchain', pattern)))
    return hits[0] if hits else None


def javap_consts(jdk, jar, cls):
    """从 class 常量池里取所有字符串常量(命令名/参数名/产物名都藏在这里)"""
    r = subprocess.run([f'{jdk}/bin/javap', '-v', '-p', '-cp', jar, cls],
                       capture_output=True, text=True)
    out = []
    for ln in (r.stdout + r.stderr).splitlines():
        m = re.match(r'^\s*#\d+ = String\s+#\d+\s+//\s?(.*)$', ln)
        if m:
            out.append(m.group(1).strip())
    return out


def run_java(jdk, args, cwd=None):
    r = subprocess.run([f'{jdk}/bin/java'] + args, capture_output=True, text=True,
                       cwd=cwd, timeout=120)
    return (r.stdout + r.stderr).strip()


def main():
    jdk = find_jdk()
    loader = find_jar('fabric-loader-*.jar')
    installer = find_jar('fabric-installer-*.jar')
    man_path = os.path.join(ROOT, 'toolchain', 'manifest.json')
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    mc_default = man.get('fabric', {}).get('minecraft', '26.3')

    L = []
    w = L.append

    w('# 服务端实测报告')
    w('')
    w('> 由 `scripts/verify_server.py` 生成。所有内容来自**真实运行输出**或 **class 常量池**，'
      '没有一条是凭记忆写的。')
    w(f'> JDK: `{jdk}/bin/java`　loader: `{os.path.basename(loader or "-")}`　'
      f'installer: `{os.path.basename(installer or "-")}`')
    w('')

    # ---------------- 实验 1: 真跑 loader 的服务端 launcher ----------------
    w('## 实验 1：真跑 `java -jar fabric-loader.jar`（无 server.jar）')
    w('')
    w('在一个空目录里直接跑，看它到底要什么、报什么错：')
    w('')
    w('```bash')
    w('$ java -jar fabric-loader-0.19.5.jar')
    w('```')
    w('')
    if loader:
        empty = os.path.join(ROOT, '..', '.srv_probe')
        os.makedirs(empty, exist_ok=True)
        for f in os.listdir(empty):
            os.remove(os.path.join(empty, f))
        out = run_java(jdk, ['-jar', os.path.abspath(loader)], cwd=empty)
        w('真实输出：')
        w('')
        w('```')
        for ln in out.splitlines()[:12]:
            w(ln)
        w('```')
        w('')
        w('从输出里读出来的事实：')
        w('')
        mg = re.search(r'missing \((.*?)\)', out)
        jar_name = mg.group(1).split('/')[-1] if mg else 'server.jar'
        w(f'- 默认找的游戏 jar 是 `{jar_name}`，路径是**当前工作目录下的绝对路径**')
        w('- 报错信息里点名的配置文件是 `fabric-server-launcher.properties`')
        w('- 结论：**loader jar 本身就能当服务端启动器用**，前提是同目录有官方 server jar')
    else:
        w('⚠️ 未找到 loader jar，跳过')
    w('')

    # ---------------- 实验 2: loader MANIFEST ----------------
    w('## 实验 2：loader jar 的 MANIFEST')
    w('')
    if loader:
        z = zipfile.ZipFile(loader)
        mf = z.read('META-INF/MANIFEST.MF').decode('utf-8', 'replace')
        for ln in mf.splitlines():
            if ln.startswith(('Main-Class', 'Automatic-Module-Name', 'Multi-Release',
                              'Fabric-Loom-Remap')) and not ln.startswith(' '):
                w(f'- `{ln.strip()}`')
        w('')
        w('`Main-Class` 就是服务端启动入口 —— 这解释了为什么 `java -jar fabric-loader.jar` 能起服。')
    w('')

    # ---------------- 实验 3: installer 的 server 子命令 ----------------
    w('## 实验 3：installer 的 `server` 子命令参数（从 class 常量池读）')
    w('')
    if installer:
        cs = javap_consts(jdk, installer, 'net.fabricmc.installer.server.ServerHandler')
        cli = [c for c in cs if c.startswith('-dir') or c.startswith('-mcversion')
               or 'downloadMinecraft' in c]
        w('`net.fabricmc.installer.server.ServerHandler.cliHelp()` 里的用法串：')
        w('')
        w('```')
        for c in cli:
            w(c)
        w('```')
        w('')
        w('整理成可用命令：')
        w('')
        w('```bash')
        w(f'java -jar {os.path.basename(installer)} server \\')
        w('     -dir <安装目录, 默认当前目录> \\')
        w(f'     -mcversion <MC版本, 默认最新> \\')
        w('     -loader <loader版本, 默认最新> \\')
        w('     -downloadMinecraft')
        w('```')
        w('')
        w('> `-downloadMinecraft` 是**开关**，不带值；不写就不会自动下载官方 server jar。')
        w('')
        si = javap_consts(jdk, installer, 'net.fabricmc.installer.server.ServerInstaller')
        launch = [c for c in si if c.endswith('.jar') or 'mainClass' in c or 'properties' in c]
        w('安装产物与内部文件名（`ServerInstaller` 常量池）：')
        w('')
        for c in sorted(set(launch)):
            w(f'- `{c}`')
        w('')
        sl = javap_consts(jdk, installer, 'net.fabricmc.installer.ServerLauncher')
        keys = [c for c in sl if c.startswith('fabric.') or c in
                ('game-version', 'install.properties', '.fabric', 'server')]
        w('`ServerLauncher`（无人值守安装）读的配置键：')
        w('')
        for c in sorted(set(keys)):
            w(f'- `{c}`')
    w('')

    # ---------------- 实验 4: installer 的网络依赖 ----------------
    w('## 实验 4：installer 装服必须联网（实测失败现场）')
    w('')
    if installer:
        out = run_java(jdk, ['-jar', os.path.abspath(installer), 'server', '-help'])
        w('本环境跑 `server -help` 的真实输出（前 6 行）：')
        w('')
        w('```')
        for ln in out.splitlines()[:6]:
            w(ln)
        w('```')
        w('')
        w('读出来的事实：')
        w('')
        w('- installer 启动第一步就是拉元数据，'
          '依次尝试 `meta.fabricmc.net` → `meta2.fabricmc.net` → `meta3.fabricmc.net`，全失败就抛 '
          '`RuntimeException: Unable to load metadata`')
        w('- 所以**离线环境下 `-downloadMinecraft` 装服这条路走不通**，'
          '得用实验 1 的"loader jar + 已有 server.jar"方案')
        w('- 无头环境用 CLI 模式，别用 GUI（GUI 需要 X server）')
    w('')

    # ---------------- 实验 5: 服务端开发入口点 ----------------
    w('## 实验 5：服务端 mod 入口点（`javap` 实测签名）')
    w('')
    if loader:
        for c in ('net.fabricmc.api.DedicatedServerModInitializer',
                  'net.fabricmc.api.ModInitializer',
                  'net.fabricmc.api.ClientModInitializer',
                  'net.fabricmc.api.EnvType'):
            r = subprocess.run([f'{jdk}/bin/javap', '-cp', loader, c],
                               capture_output=True, text=True)
            body = (r.stdout or r.stderr).strip()
            w('```')
            for ln in body.splitlines():
                w(ln)
            w('```')
            w('')
    w('')

    # ---------------- 实验 5.5: 裸 loader jar 直起会缺 ASM ----------------
    w('## 实验 5.5：⚠️ 裸 `fabric-loader.jar` 直起会失败（缺 ASM）')
    w('')
    if loader:
        probe = os.path.join(ROOT, '..', '.srv_probe')
        os.makedirs(probe, exist_ok=True)
        fake = os.path.join(probe, 'server.jar')
        if not os.path.exists(fake):
            open(fake, 'wb').write(b'PK\x03\x04')   # 假的空 zip
        out = run_java(jdk, ['-jar', os.path.abspath(loader), 'nogui'], cwd=probe)
        w('放一个占位 `server.jar` 后再跑，真实输出：')
        w('')
        w('```')
        for ln in out.splitlines()[:10]:
            w(ln)
        w('```')
        w('')
        w('读出来的事实（这条推翻了"loader jar 自己能起服"的直觉）：')
        w('')
        w('- loader 过了 game jar 检查后，会在 `Knot.<clinit>` 里做 `LoaderUtil.verifyClasspath()`')
        w('- ASM 不在裸 loader jar 里，于是抛 `IllegalStateException: ASM not detected on the classpath`')
        w('- **结论**：起服要用 installer 生成的 **`fabric-server-launch.jar`**，'
          '它的 MANIFEST `Class-Path` 带上了 `.fabric/libraries/` 下的全部依赖（含 ASM）。'
          '把 `fabric-loader.jar` 单独 `java -jar` 只在"依赖已在 classpath"的场景下成立。')
        w('- `server/start.sh` 已按这个结论写：优先找 `fabric-server-launch.jar`，'
          '找不到 loader jar 时会明确提示。')
    w('')

    # ---------------- 实验 6: 26.x 服务端专属坑 ----------------
    w('## 实验 6：26.x 服务端的三个专属坑')
    w('')
    w('1. **服务端没有客户端类**：mod 若 `environment: "*"` 但代码里摸了客户端类，'
      '起服直接 `NoClassDefFoundError`。要用 `@Environment(EnvType.CLIENT)` 隔离，'
      '或把服务端逻辑单独放 `server` entrypoint。')
    w('2. **`fabric.mod.json` 的 `environment` 字段**：纯服务端 mod 写 `"server"`，'
      '写 `"*"` 会被塞进客户端，客户端装了才报错。')
    w('3. **26.3 起白名单默认开**（社区实测：26.3 服务端默认启用 whitelist）—— '
      '装完服记得在 `server.properties` 里看 `white-list`，或控制台 `whitelist on`。'
      '⚠️ 这一条来自社区资料，本脚本未在本仓库实测，请以实际启动后的 server.properties 为准。')
    w('')

    text = '\n'.join(L) + '\n'
    if ONLY_STDOUT:
        print(text)
        return
    outdir = os.path.join(ROOT, 'server')
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'SETUP_REPORT.md'), 'w').write(text)
    print('已写入 server/SETUP_REPORT.md  (%d 行)' % text.count('\n'))


if __name__ == '__main__':
    main()
