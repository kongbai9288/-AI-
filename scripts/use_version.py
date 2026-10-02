#!/usr/bin/env python3
"""把 toolchain/ 里的公共件组装到指定 MC 版本目录下, 让该版本自包含。

公共件(loader / installer / JDK)与 MC 版本无关, 所以仓库里只存一份;
但做离线打包、或者就想某个版本目录里东西齐全时, 用本脚本组装。

用法:
  python3 scripts/use_version.py 26.3               # 软链(默认), 打印 JAVA_HOME / classpath
  python3 scripts/use_version.py 26.3 --copy        # 复制而不是软链
  python3 scripts/use_version.py 26.3 --jdk         # 顺带合并分卷并解压 JDK
  python3 scripts/use_version.py 26.2 --copy --jdk  # 两个都做

说明:
  - 输出目录 <版本>/toolchain/ 默认应加入 .gitignore, 不提交进仓库
  - JDK 解压较耗时(141MB), 默认跳过, 加 --jdk 才做
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONS = ('26.2', '26.3')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def load_manifest():
    return json.load(open(os.path.join(ROOT, 'toolchain', 'manifest.json')))


def place(src, dst, copy):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst):
        os.remove(dst)
    if copy:
        shutil.copy2(src, dst)
        how = '复制'
    else:
        os.symlink(os.path.relpath(src, os.path.dirname(dst)), dst)
        how = '软链'
    print(f'  {how} {os.path.relpath(src, ROOT)} -> {os.path.relpath(dst, ROOT)}')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    copy = '--copy' in sys.argv
    with_jdk = '--jdk' in sys.argv
    if not args or args[0] not in VERSIONS:
        raise SystemExit(f'用法: python3 scripts/use_version.py {"|".join(VERSIONS)} [--copy] [--jdk]')
    ver = args[0]

    vj = json.load(open(os.path.join(ROOT, ver, 'versions.json')))
    man = load_manifest()
    base = vj['baseline']

    print(f'== Minecraft {ver} 工具链组装 ==')
    print(f"   基线: MC {base['minecraft_version']} / Java {base['java_version']} / "
          f"loader {base['loader_version']} / API {base['fabric_api_version']}")

    # 1) 版本专属的 API jar
    api = vj['artifacts'][0]
    src_api = os.path.join(ROOT, ver, api['file'])
    if not os.path.exists(src_api):
        print(f"  ✗ 缺少 {os.path.relpath(src_api, ROOT)}")
    else:
        got = sha256(src_api)
        print(f"  ✓ API {api['file']}  sha256 {'一致' if got == api['sha256'] else '不一致!'}")

    out = os.path.join(ROOT, ver, 'toolchain')
    os.makedirs(out, exist_ok=True)

    # 1.5) Fabric API 的 jar-in-jar 子模块摊平, 否则 javac/javap 看不到类
    mod_dir = os.path.join(out, 'api-modules')
    if os.path.exists(src_api):
        import zipfile
        z = zipfile.ZipFile(src_api)
        sub = [n for n in z.namelist()
               if n.startswith('META-INF/jars/') and n.endswith('.jar')]
        if len(sub) != len([f for f in os.listdir(mod_dir) if f.endswith('.jar')]) if os.path.isdir(mod_dir) else True:
            os.makedirs(mod_dir, exist_ok=True)
            for n in sub:
                open(os.path.join(mod_dir, n.split('/')[-1]), 'wb').write(z.read(n))
        print(f"  ✓ 摊平 {len(sub)} 个 API 子模块 -> {os.path.relpath(mod_dir, ROOT)}/")

    # 2) 公共件: loader / installer
    print('\n-- 公共件(版本无关, 见 toolchain/README.md 的实验) --')
    for key in ('loader', 'installer'):
        e = man['fabric'][key]
        src = os.path.join(ROOT, 'toolchain', e['file'])
        if not os.path.exists(src):
            print(f"  ✗ 缺少 toolchain/{e['file']}")
            continue
        got = sha256(src)
        if got != e['sha256']:
            print(f"  ✗ toolchain/{e['file']} sha256 与 manifest 不符, 跳过")
            continue
        place(src, os.path.join(out, e['file']), copy)
        print(f"      applies_to={e.get('applies_to')}  version_independent={e.get('version_independent')}")

    # 3) JDK(可选)
    jdk_dir = ''
    if with_jdk:
        print('\n-- JDK(合并分卷 + 解压) --')
        jdk = man['jdk']
        tgz = os.path.join(out, jdk['file'])
        if os.path.exists(tgz):
            print(f"  ✓ {jdk['file']} 已合并")
        else:
            parts = sorted(os.path.join(ROOT, 'toolchain', p) for p in jdk['parts'])
            if not all(os.path.exists(p) for p in parts):
                print(f"  ✗ 分卷缺失: {jdk['parts']}")
            else:
                with open(tgz, 'wb') as w:
                    for p in parts:
                        with open(p, 'rb') as r:
                            shutil.copyfileobj(r, w)
                print(f"  ✓ 合并 {len(parts)} 个分卷 -> {jdk['file']}")
        if os.path.exists(tgz):
            subprocess.run(['tar', '-xzf', tgz, '-C', out], check=False)
            cands = [d for d in os.listdir(out)
                     if d.startswith('jdk-25') and os.path.isdir(os.path.join(out, d))]
            if cands:
                jdk_dir = os.path.join(out, sorted(cands)[-1])
                print(f"  ✓ 解压 -> {os.path.relpath(jdk_dir, ROOT)}")

    # 4) 打印可用命令
    print('\n-- 组装结果 --')
    api_cp = os.path.join(ROOT, ver, api['file'])
    ld = os.path.join(out, man['fabric']['loader']['file'])
    ins = os.path.join(out, man['fabric']['installer']['file'])
    print(f"  out dir : {os.path.relpath(out, ROOT)}/")
    if jdk_dir:
        print(f"  export JAVA_HOME={jdk_dir}")
        print(f"  {jdk_dir}/bin/java -version")
    print(f"""
  # API 子模块 + loader 组成 classpath(Fabric 侧; MC 本体由 Loom 拉)
  CP="$(ls {mod_dir}/*.jar | tr '\\n' ':'){ld}"
  # 查 API 签名
  javap -cp "$CP" net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents

  # 装服务端(版本在运行时选)
  java -jar {ins} server -mcversion {base['minecraft_version']} -downloadMinecraft
""")
    print('  提示: <版本>/toolchain/ 是组装产物, 建议加进 .gitignore 不要提交')


if __name__ == '__main__':
    main()
