# Fabric + JDK 工具链自动仓库

用 GitHub Actions 自动把 **JDK** 和 **Fabric 开发工具链** 抓进仓库，供 AI / 自动化流程离线取用。

---

## 一、30 秒上手

1. **新建公开仓库**（例如 `你的用户名/fabric-toolchain`），把本目录内容全部放进去
2. **触发工作流**：仓库页面 → Actions → `Fetch Toolchain (JDK + Fabric)` → Run workflow
   - `jdk_major`：默认 `25`
   - `mc_version`：留空自动取最新稳定版，或填 `1.21.4`
3. **等待完成**，产物落在 `toolchain/` 目录并自动 commit

之后每周一会自动检查上游新版本，有更新才提交。

---

## 二、目录结构

```
.github/workflows/fetch-toolchain.yml   # 主工作流(手动/定时/清单变更触发)
scripts/
  resolve_versions.py                   # 从 meta.fabricmc.net 解析最新版本
  build-toolchain.sh                    # 下载 + 分卷 + 生成 manifest
  sync-gradle-props.py                  # 把 manifest 版本同步进 mod 模板
templates/fabric-mod/                   # 给 AI 用的 mod 项目骨架
  build.gradle / settings.gradle / gradle.properties
  src/main/resources/fabric.mod.json
toolchain/                              # ← 工作流产出(首次运行后生成)
  manifest.json                         # 版本 + SHA256 + 分卷清单
  jdk-25-linux-x64.tar.gz.part-*        # JDK(大文件已分卷)
  fabric-loader-*.jar
  fabric-installer-*.jar
  yarn-*.jar                            # Yarn 反混淆映射
  fabric-api-*.jar
```

---

## 三、取用（AI / 自动化）

**下载整个仓库**（GitHub Actions 环境下 codeload 域名通常可达）：

```bash
curl -L "https://codeload.github.com/<用户名>/<仓库>/zip/refs/heads/main" -o repo.zip
unzip repo.zip
```

**重组分卷文件**：

```bash
cd toolchain
cat jdk-25-linux-x64.tar.gz.part-* > jdk.tar.gz
tar -xzf jdk.tar.gz
export JAVA_HOME=$PWD/jdk-25+*/      # 按实际目录名调整
$JAVA_HOME/bin/java -version
```

**校验完整性**：对照 `manifest.json` 里的 `sha256`。

---

## 四、给 AI 开发 mod（模板用法）

```bash
cp -r templates/fabric-mod my-mod
cd my-mod

# 让模板版本与仓库工具链一致
python3 ../scripts/sync-gradle-props.py

# 构建（Loom 会自动下载 Minecraft 本体）
export JAVA_HOME=<对应 MC 版本要求的 JDK>   # 见下方"版本选择"
./gradlew build
```

产物在 `build/libs/`。开发速查见 [`AI_DEV_GUIDE.md`](AI_DEV_GUIDE.md)。

---

## 五、版本选择：别踩这个坑 ⚠️

**JDK 25 ≠ 编译 Minecraft 的 JDK。** 两件事要分清：

| 用途 | 用什么 |
|---|---|
| 仓库里的 JDK 25 | 通用 Java 任务、新版工具链、未来 MC 版本 |
| 编译 Fabric mod | **按 MC 版本定**，当前 MC 1.21.x 需要 **Java 21** |

`templates/fabric-mod/gradle.properties` 里的 `java_version` 由 `sync-gradle-props.py` 按 MC 版本自动推导（1.21→21、1.18~1.20→17）。Gradle 的 toolchain 会去找对应版本的 JDK，所以**编译环境仍需准备 Java 21**，仓库里的 JDK 25 是额外工具，不直接用于旧版 MC 编译。

---

## 六、合规说明

- ✅ **仓库内只含开源工具链**：JDK（开源许可）、Fabric Loader / Installer / Yarn / Fabric API（均为开源许可）
- ❌ **不含 Minecraft 客户端或服务端 jar**。Minecraft 是 Mojang/微软的商业作品，其 EULA 禁止分发游戏文件。本体由 Fabric Loom 在构建时从 Mojang 官方服务器自动拉取——这部分请自行确保遵守 EULA 与正版要求。
- 下载源均为官方：Adoptium / Microsoft OpenJDK、maven.fabricmc.net、meta.fabricmc.net

---

## 七、维护提醒

- **仓库体积**：JDK 分卷后约 200MB/版本。建议只保留最新版本，定期清理旧版避免仓库膨胀（GitHub 建议仓库 < 1GB，单文件硬上限 100MB，所以脚本按 90MB 分卷）。
- **不要用 Git LFS**：LFS 实际文件存在独立存储域名，codeload 拉下来只会得到指针文件，**拿不到真实内容**。分卷方案更可靠。
- **公开仓库**的 Actions 免费额度充足；私有仓库有分钟数限制。
- 上游版本解析失败时，工作流会保留上一次成功产物并报错退出，不会写入半成品。

---

## 八、可调参数

编辑 `.github/workflows/fetch-toolchain.yml`：

| 项 | 位置 | 说明 |
|---|---|---|
| JDK 版本 | inputs 默认 `25` | 换成 21/17 等 |
| 分卷大小 | `build-toolchain.sh` 第 4 参 `90m` | 建议不超过 95m |
| 定时频率 | `schedule.cron` | 默认每周一 03:00 UTC |
| 强制重下 | 环境变量 `FORCE=1` | 版本未变也重下 |
