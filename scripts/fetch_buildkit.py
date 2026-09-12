#!/usr/bin/env python3
"""
下载 Minecraft 26.2 的 client jar 与编译期依赖库, 生成 classpath。
供无外网的构建环境(javac 直编)使用。

用法: python3 fetch_buildkit.py [MC版本] [输出目录]
"""
import json
import os
import shutil
import sys
import urllib.request

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
UA = {"User-Agent": "buildkit-fetcher/1.0 (github-actions)"}


def get(url, dest, timeout=600):
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    return dest


def main():
    target_ver = sys.argv[1] if len(sys.argv) > 1 else "26.2"
    out = sys.argv[2] if len(sys.argv) > 2 else "buildkit"
    os.makedirs(out, exist_ok=True)

    # --- 版本清单 ---
    print("[1/4] 获取版本清单...")
    vm = json.load(open(get(MANIFEST, f"{out}/version_manifest_v2.json")))
    target = None
    for v in vm["versions"]:
        if v["id"] == target_ver:
            target = v
            break
    if target is None:
        cands = [v["id"] for v in vm["versions"] if v["id"].startswith(target_ver)]
        if cands:
            target = next(v for v in vm["versions"] if v["id"] == cands[0])
        else:
            raise SystemExit(f"未找到 MC {target_ver}")
    print(f"      目标: {target['id']}")

    # --- version json ---
    print("[2/4] 获取 version json...")
    vj = json.load(open(get(target["url"], f"{out}/version.json")))
    print(f"      id={vj['id']}  java={vj.get('javaVersion', {}).get('majorVersion')}")
    print(f"      assetIndex={vj.get('assetIndex', {}).get('id')}")

    # --- client jar ---
    client = vj["downloads"]["client"]
    print(f"[3/4] 下载 client jar ({client['size'] / 1e6:.1f} MB)...")
    get(client["url"], f"{out}/minecraft-{vj['id']}-client.jar")

    # --- libraries (编译期依赖) ---
    print("[4/4] 下载 libraries...")
    total = len(vj.get("libraries", []))
    ok = 0
    failed = []
    for i, lib in enumerate(vj.get("libraries", []), 1):
        art = lib.get("downloads", {}).get("artifact")
        if not art:
            continue
        url = art.get("url")
        path = art.get("path")
        if not url or not path:
            continue
        dest = os.path.join(out, "libs", os.path.basename(path))
        if os.path.exists(dest):
            ok += 1
            continue
        try:
            get(url, dest, timeout=300)
            ok += 1
        except Exception as e:
            failed.append(f"{lib.get('name')}: {e}")
        if i % 10 == 0:
            print(f"      {i}/{total}")
    print(f"      libraries: {ok} 成功, {len(failed)} 失败")
    for f in failed:
        print(f"      ! {f}")

    # --- classpath ---
    jars = [f"{out}/minecraft-{vj['id']}-client.jar"]
    libs_dir = os.path.join(out, "libs")
    if os.path.isdir(libs_dir):
        for f in sorted(os.listdir(libs_dir)):
            if f.endswith(".jar"):
                jars.append(os.path.join(libs_dir, f))
    with open(f"{out}/classpath.txt", "w") as f:
        f.write(os.pathsep.join(jars))
    print(f"\nclasspath 条目: {len(jars)}")
    print("完成。")


if __name__ == "__main__":
    main()
