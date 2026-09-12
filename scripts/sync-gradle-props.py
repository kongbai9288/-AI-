#!/usr/bin/env python3
"""
把 toolchain/manifest.json 里的实际版本同步进 templates/fabric-mod/gradle.properties
保证 AI 用的 mod 模板与仓库工具链版本一致

用法: python3 scripts/sync-gradle-props.py [manifest路径] [gradle.properties路径]
"""
import json
import re
import sys

MANIFEST = sys.argv[1] if len(sys.argv) > 1 else "toolchain/manifest.json"
PROPS = sys.argv[2] if len(sys.argv) > 2 else "templates/fabric-mod/gradle.properties"


def java_for(mc: str) -> int:
    """根据 MC 版本推断所需 Java 版本"""
    try:
        parts = mc.split(".")
        minor = int(parts[1]) if len(parts) > 1 else 21
    except (IndexError, ValueError):
        return 21
    if minor >= 21:
        return 21      # MC 1.21.x -> Java 21
    if minor >= 18:
        return 17      # MC 1.18~1.20 -> Java 17
    if minor >= 17:
        return 16      # MC 1.17 -> Java 16
    return 8


def main():
    with open(MANIFEST) as f:
        man = json.load(f)
    fab = man["fabric"]
    mc = fab["minecraft"]

    updates = {
        "minecraft_version": mc,
        "yarn_mappings":     fab["yarn"]["version"],
        "loader_version":    fab["loader"]["version"],
        "java_version":      str(java_for(mc)),
    }
    if "api" in fab and fab["api"]:
        updates["fabric_api_version"] = fab["api"]["version"]

    with open(PROPS) as f:
        text = f.read()

    changed = []
    for key, val in updates.items():
        new_text, n = re.subn(rf"(?m)^{re.escape(key)}=.*$", f"{key}={val}", text)
        if n:
            if new_text != text:
                changed.append(f"{key}={val}")
            text = new_text
        else:
            text += f"\n{key}={val}\n"
            changed.append(f"{key}={val} (新增)")

    with open(PROPS, "w") as f:
        f.write(text)

    print(f"已从 {MANIFEST} 同步到 {PROPS}:")
    for c in changed:
        print(f"  {c}")
    if not changed:
        print("  无变化")
    print()
    print("提示: loom_version 与 MC 版本强相关, 未自动改动, 如有构建问题请手动核对")
    print("      (loom 版本对照见 https://fabricmc.net/develop )")


if __name__ == "__main__":
    main()
