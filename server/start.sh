#!/usr/bin/env bash
# 起 Fabric 服务端
#
# 实测依据(见 server/SETUP_REPORT.md):
#   - 正确的启动目标是 installer 生成的 fabric-server-launch.jar,
#     它的 MANIFEST Class-Path 带上了 .fabric/libraries/ 下全部依赖(含 ASM)
#   - 直接 java -jar fabric-loader-*.jar 会在 Knot.<clinit> 里报
#     "ASM not detected on the classpath" (实验 5.5), 因为裸 loader jar 不含 ASM
#   - 两种 jar 都要求当前目录有官方 server.jar
#     (路径可用 fabric-server-launcher.properties 改)
#
# 用法:
#   ./start.sh                 # 前台起服
#   ./start.sh nogui           # 参数原样透传给服务端
#   JAVA_HOME=/path/to/jdk25 ./start.sh
#   GAME_JAR=/path/to/server.jar ./start.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"

# ---------- 1. 找 JDK 25 ----------
if [ -z "${JAVA_HOME:-}" ]; then
  for d in "$REPO_ROOT"/toolchain/jdk-25*/ "$REPO_ROOT"/jdk-25*/; do
    if [ -x "${d}bin/java" ]; then JAVA_HOME="${d%/}"; break; fi
  done
fi
if [ -z "${JAVA_HOME:-}" ] || [ ! -x "$JAVA_HOME/bin/java" ]; then
  echo "✗ 找不到 JDK 25。先准备 JDK:" >&2
  echo "    cd $REPO_ROOT/toolchain && cat jdk-25-linux-x64.tar.gz.part-* > jdk.tar.gz && tar -xzf jdk.tar.gz" >&2
  echo "  或: export JAVA_HOME=/path/to/jdk25" >&2
  exit 1
fi
"$JAVA_HOME/bin/java" -version 2>&1 | head -1

# ---------- 2. 找启动 jar: 优先 installer 产物 ----------
LAUNCH=""
for c in "$PWD/fabric-server-launch.jar" "$REPO_ROOT/server/fabric-server-launch.jar"; do
  [ -f "$c" ] && LAUNCH="$c" && break
done
if [ -z "$LAUNCH" ]; then
  # 没有 installer 产物, 退回 loader jar(但要提醒 ASM 问题)
  LAUNCH="$(ls "$REPO_ROOT"/toolchain/fabric-loader-*.jar 2>/dev/null | sort -V | tail -1 || true)"
  if [ -n "${LAUNCH:-}" ]; then
    echo "⚠️  用的是裸 loader jar, 启动可能报 'ASM not detected on the classpath'" >&2
    echo "   推荐先跑 installer 生成 fabric-server-launch.jar:" >&2
    echo "     java -jar $REPO_ROOT/toolchain/fabric-installer-*.jar \\" >&2
    echo "          server -dir . -mcversion 26.3 -downloadMinecraft" >&2
  fi
fi
if [ -z "${LAUNCH:-}" ] || [ ! -f "$LAUNCH" ]; then
  echo "✗ 没找到 fabric-server-launch.jar 或 toolchain/fabric-loader-*.jar" >&2
  exit 1
fi
echo "launch jar: $LAUNCH"

# ---------- 3. 检查官方 server.jar ----------
GAME_JAR="${GAME_JAR:-server.jar}"
if [ ! -f "$GAME_JAR" ]; then
  echo "✗ 缺少官方 Minecraft server.jar (当前目录: $PWD/$GAME_JAR)" >&2
  echo "  有外网: java -jar $REPO_ROOT/toolchain/fabric-installer-*.jar \\" >&2
  echo "              server -dir . -mcversion 26.3 -downloadMinecraft" >&2
  echo "  无外网: 手动把官方 server.jar 放到本目录, 或设置 GAME_JAR=/path/to/server.jar" >&2
  exit 1
fi
echo "game jar: $PWD/$GAME_JAR"

# ---------- 4. 起服 ----------
MEM="${MEM:--Xms1G -Xmx4G}"
echo "启动: java $MEM -jar $(basename "$LAUNCH") $*"
exec "$JAVA_HOME/bin/java" $MEM -jar "$LAUNCH" "$@"
