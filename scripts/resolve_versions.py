#!/usr/bin/env python3
"""
解析 Fabric 生态各组件的最新版本号
输出 KEY=VALUE 供 shell eval 使用

用法: python3 resolve_versions.py [mc版本]
  不传 mc 版本则自动取最新稳定版
"""
import json
import re
import sys
import urllib.request

UA = {"User-Agent": "toolchain-fetcher/1.0 (github-actions)"}
META = "https://meta.fabricmc.net/v2/versions"
MAVEN = "https://maven.fabricmc.net"


def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def jget(url):
    return json.loads(get(url))


def die(msg):
    print(f"# ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    mc_wanted = sys.argv[1].strip() if len(sys.argv) > 1 else ""

    # --- Minecraft 版本 ---
    games = jget(f"{META}/game")
    if mc_wanted:
        known = [g["version"] for g in games]
        mc = mc_wanted if mc_wanted in known else mc_wanted
        if mc_wanted not in known:
            print(f"# WARN: MC {mc_wanted} 不在官方清单, 仍按此版本尝试", file=sys.stderr)
    else:
        stable = [g for g in games if g.get("stable")]
        mc = stable[0]["version"] if stable else games[0]["version"]

    # --- Loader ---
    loaders = jget(f"{META}/loader")
    loader = loaders[0]["version"]

    # --- Installer ---
    installers = jget(f"{META}/installer")
    installer = installers[0]["version"]

    # --- Yarn mappings (按 MC 版本) ---
    yarns = jget(f"{META}/yarn")
    cand = [y for y in yarns if y.get("gameVersion") == mc]
    yarn = cand[0]["version"] if cand else yarns[0]["version"]

    # --- Fabric API (maven-metadata, 按 MC 版本) ---
    try:
        xml = get(f"{MAVEN}/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml")
        vers = re.findall(r"<version>([^<]+)</version>", xml)
        api_cand = [v for v in vers if v.endswith("+" + mc)]
        api = api_cand[-1] if api_cand else (vers[-1] if vers else "")
    except Exception as e:
        print(f"# WARN: Fabric API 版本解析失败: {e}", file=sys.stderr)
        api = ""

    print(f"MC_VERSION={mc}")
    print(f"LOADER_VERSION={loader}")
    print(f"INSTALLER_VERSION={installer}")
    print(f"YARN_VERSION={yarn}")
    print(f"API_VERSION={api}")


if __name__ == "__main__":
    main()
