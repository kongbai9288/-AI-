#!/usr/bin/env bash
# 拉取 JDK + Fabric 开发工具链到仓库
# 用法: ./build-toolchain.sh [JDK主版本] [MC版本] [输出目录] [分卷大小]
# 例:   ./build-toolchain.sh 25 1.21.4 toolchain 90m
set -euo pipefail

JDK_MAJOR="${1:-25}"
MC_WANTED="${2:-}"
OUT_DIR="${3:-toolchain}"
SPLIT_SIZE="${4:-90m}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MB_LIMIT=95            # 超过此大小(MB)就分卷, GitHub 单文件硬上限 100MB
TMP="$(mktemp -d)"
mkdir -p "$OUT_DIR"

echo "=============================================="
echo " 工具链拉取  JDK=${JDK_MAJOR}  MC=${MC_WANTED:-自动}"
echo "=============================================="

# ---------- 0. 解析 Fabric 各组件版本 ----------
echo
echo "[1/5] 解析 Fabric 组件版本..."
if ! VERSIONS="$(python3 "$SCRIPT_DIR/resolve_versions.py" "$MC_WANTED")"; then
  echo "版本解析失败"; exit 1
fi
eval "$VERSIONS"
echo "  MC        : $MC_VERSION"
echo "  Loader    : $LOADER_VERSION"
echo "  Installer : $INSTALLER_VERSION"
echo "  Yarn      : $YARN_VERSION"
echo "  Fabric API: ${API_VERSION:-<解析失败,跳过>}"

# 若核心组件版本与现有 manifest 完全一致, 可直接复用(省带宽)
if [ -f "$OUT_DIR/manifest.json" ]; then
  OLD_MC=$(python3 -c "import json;print(json.load(open('$OUT_DIR/manifest.json'))['fabric']['minecraft'])" 2>/dev/null || echo "")
  OLD_JDK=$(python3 -c "import json;print(json.load(open('$OUT_DIR/manifest.json'))['jdk']['major'])" 2>/dev/null || echo "")
  if [ "$OLD_MC" = "$MC_VERSION" ] && [ "$OLD_JDK" = "$JDK_MAJOR" ] && [ "${FORCE:-0}" != "1" ]; then
    echo
    echo "  与现有 manifest 一致 (MC=$OLD_MC, JDK=$OLD_JDK), 无更新。设 FORCE=1 可强制重下。"
    exit 0
  fi
fi

# ---------- 1. 下载 JDK ----------
echo
echo "[2/5] 下载 JDK $JDK_MAJOR (Linux x64)..."
JDK_FILE="$OUT_DIR/jdk-${JDK_MAJOR}-linux-x64.tar.gz"
JDK_VENDOR=""
fetch() {  # url, dest
  echo "  尝试: $1"
  if curl -fsSL --retry 3 --retry-delay 5 --max-time 900 "$1" -o "$2" 2>/dev/null && gzip -t "$2" 2>/dev/null; then
    return 0
  fi
  return 1
}
if fetch "https://api.adoptium.net/v3/binary/latest/${JDK_MAJOR}/ga/linux/x64/jdk/hotspot/normal/eclipse" "$JDK_FILE"; then
  JDK_VENDOR="eclipse-temurin"
elif fetch "https://aka.ms/download-jdk/microsoft-jdk-${JDK_MAJOR}-linux-x64.tar.gz" "$JDK_FILE"; then
  JDK_VENDOR="microsoft-openjdk"
elif fetch "https://download.java.net/java/GA/jdk${JDK_MAJOR}/linux-x64_bin.tar.gz" "$JDK_FILE"; then
  JDK_VENDOR="openjdk-jdk.java.net"
else
  echo "  ✗ 所有 JDK 源均失败"; rm -f "$JDK_FILE"; exit 1
fi
echo "  ✓ $JDK_VENDOR  ($(du -h "$JDK_FILE" | cut -f1))"

# ---------- 2. 下载 Fabric 组件 ----------
echo
echo "[3/5] 下载 Fabric 组件..."
dl() {  # 名称, url, 目标文件
  local name="$1" url="$2" dest="$3"
  if curl -fsSL --retry 3 --retry-delay 3 --max-time 300 "$url" -o "$dest" 2>/dev/null; then
    local sz; sz=$(du -h "$dest" | cut -f1)
    echo "  ✓ $name  ($sz)"
    return 0
  fi
  echo "  ✗ $name 下载失败: $url"
  rm -f "$dest"
  return 1
}
FAILED=0
dl "fabric-loader"   "https://maven.fabricmc.net/net/fabricmc/fabric-loader/${LOADER_VERSION}/fabric-loader-${LOADER_VERSION}.jar" \
   "$OUT_DIR/fabric-loader-${LOADER_VERSION}.jar" || FAILED=1
dl "fabric-installer" "https://maven.fabricmc.net/net/fabricmc/fabric-installer/${INSTALLER_VERSION}/fabric-installer-${INSTALLER_VERSION}.jar" \
   "$OUT_DIR/fabric-installer-${INSTALLER_VERSION}.jar" || FAILED=1
dl "yarn-mappings"   "https://maven.fabricmc.net/net/fabricmc/yarn/${YARN_VERSION}/yarn-${YARN_VERSION}.jar" \
   "$OUT_DIR/yarn-${YARN_VERSION}.jar" || FAILED=1
if [ -n "${API_VERSION:-}" ]; then
  dl "fabric-api"   "https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/${API_VERSION}/fabric-api-${API_VERSION}.jar" \
     "$OUT_DIR/fabric-api-${API_VERSION}.jar" || true   # API 非必需, 失败不中断
fi

# ---------- 3. 大文件分卷 ----------
echo
echo "[4/5] 检查体积并分卷 (GitHub 单文件上限 100MB)..."
split_if_needed() {
  local f="$1"
  [ -f "$f" ] || return 0
  local size_mb; size_mb=$(( $(stat -c%s "$f") / 1024 / 1024 ))
  if [ "$size_mb" -ge "$MB_LIMIT" ]; then
    echo "  $f 为 ${size_mb}MB, 分卷为 ${SPLIT_SIZE}..."
    split -b "$SPLIT_SIZE" -d -a 2 "$f" "${f}.part-"
    rm -f "$f"
    echo "    -> $(ls "${f}.part-"* | wc -l) 个分卷"
  else
    echo "  $f (${size_mb}MB) 无需分卷"
  fi
}
for f in "$OUT_DIR"/*; do
  [ -f "$f" ] || continue
  case "$f" in *.part-*|*manifest.json) continue;; esac
  split_if_needed "$f"
done

# ---------- 4. 生成 manifest ----------
echo
echo "[5/5] 生成 manifest.json..."
JDK_MAJOR="$JDK_MAJOR" JDK_VENDOR="$JDK_VENDOR" JDK_FILE="$JDK_FILE" \
MC_VERSION="$MC_VERSION" LOADER_VERSION="$LOADER_VERSION" \
INSTALLER_VERSION="$INSTALLER_VERSION" YARN_VERSION="$YARN_VERSION" \
API_VERSION="${API_VERSION:-}" OUT_DIR="$OUT_DIR" python3 <<'PY'
import hashlib, json, os, glob, datetime

out = os.environ["OUT_DIR"]
jdk_file = os.environ["JDK_FILE"]

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def entry(path):
    """返回文件条目; 若已分卷则记录 parts"""
    if os.path.exists(path):
        return {"file": os.path.basename(path),
                "sha256": sha256(path),
                "size": os.path.getsize(path)}
    parts = sorted(glob.glob(path + ".part-*"))
    if parts:
        return {"file": os.path.basename(path),
                "sha256": sha256(path + ".merged") if os.path.exists(path + ".merged") else "",
                "size": sum(os.path.getsize(p) for p in parts),
                "parts": [os.path.basename(p) for p in parts]}
    return None

jdk = entry(jdk_file)
if jdk:
    jdk.update({"major": os.environ["JDK_MAJOR"],
                "vendor": os.environ["JDK_VENDOR"],
                "platform": "linux-x64"})

fabric = {
    "minecraft": os.environ["MC_VERSION"],
    "loader":   entry(f"{out}/fabric-loader-{os.environ['LOADER_VERSION']}.jar"),
    "installer":entry(f"{out}/fabric-installer-{os.environ['INSTALLER_VERSION']}.jar"),
    "yarn":     entry(f"{out}/yarn-{os.environ['YARN_VERSION']}.jar"),
}
fabric["loader"]["version"]   = os.environ["LOADER_VERSION"]
fabric["installer"]["version"]= os.environ["INSTALLER_VERSION"]
fabric["yarn"]["version"]     = os.environ["YARN_VERSION"]

api = entry(f"{out}/fabric-api-{os.environ['API_VERSION']}.jar") if os.environ.get("API_VERSION") else None
if api:
    api["version"] = os.environ["API_VERSION"]
    fabric["api"] = api

manifest = {
    "schema": 1,
    "generated_at": datetime.datetime.now(datetime.timezone.utc)
                    .isoformat(timespec="seconds"),
    "jdk": jdk,
    "fabric": fabric,
    "reassemble": {
        "note": "分卷文件用 cat 合并: cat <file>.part-* > <file>",
        "example": "cat jdk-25-linux-x64.tar.gz.part-* > jdk-25-linux-x64.tar.gz"
    },
    "legal": {
        "minecraft_jar": "本仓库不含 Minecraft 客户端/服务端 jar。"
                         "Fabric Loom 在构建时会自动从 Mojang 官方服务器拉取, "
                         "请遵守 Mojang/Microsoft EULA。",
        "included": "仅含开源工具链: JDK(开源许可) + Fabric loader/installer/yarn/API(开源许可)"
    }
}
with open(f"{out}/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
print("  ✓ manifest.json 已生成")
PY

rm -rf "$TMP"
echo
echo "=============================================="
echo " 完成。产物在 $(realpath "$OUT_DIR")/"
echo "=============================================="
ls -lh "$OUT_DIR/"
