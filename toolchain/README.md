# toolchain/ —— 为什么这里的东西不分版本

本目录放的是**与 Minecraft 版本无关**的公共件。按版本区分的组件已经搬去
[`../26.2/`](../26.2/) 和 [`../26.3/`](../26.3/)。

## 判据：什么该分版本、什么不该

| 组件 | 位置 | 是否版本绑定 | 实测判据 |
|---|---|---|---|
| Fabric API | `26.2/` `26.3/` 各一份 | ✅ **强绑定** | jar 内 `fabric.mod.json` 写死 `minecraft: "~26.2-"` / `"~26.3-"`，版本不对加载器直接拒绝 |
| JDK 25 | `toolchain/` | ❌ | 26.2 与 26.3 的 Mojang 元数据都指定 Java 25，同一份够用 |
| Fabric Loader 0.19.5 | `toolchain/` | ❌ | 见下方实验 |
| Fabric Installer 1.1.2 | `toolchain/` | ❌ | 见下方实验 |
| Yarn 1.21.11 | `toolchain/` | ⚠️ 绑 1.21.11 | 26.1 起游戏未混淆，26.x 用不上，纯历史遗留 |

## 实验：Loader 0.19.5 对 26.2 / 26.3 是同一条代码路径

**实验 1 — 字节扫描**：`fabric-loader-0.19.5.jar` 916 个条目里，`26.2` 出现 **0 次**、`26.3` 出现 **0 次**。
唯一含版本字样的是 `McVersionLookup.class`，那是一张从 MC jar 反推版本号的**历史查找表**
（最新硬编码条目是 `26.1.1` 与 `25w14craftmine`），不是"支持列表"。

**实验 2 — 真跑 loader 的代码**（反射调用 `McVersionLookup.getRelease`，JDK 25）：

```
getRelease("26.3")   = 26.3      getRelease("26.3-rc-2") = 26.3
getRelease("26.2")   = 26.2      getRelease("26.1.1")    = 26.1.1
getRelease("1.21.11")= 1.21.11
```

**实验 3 — loader 自己的正则对不对得上**：

```
DATE_BASED_PATTERN = (\d{2}\.\d+(?:\.\d+)?)(?:-(snapshot|pre|rc)-(\d+))?
  26.3 ✅  26.2 ✅  26.1.1 ✅  1.21.11 ❌
RELEASE_PATTERN    = (1\.(\d+)(?:\.(\d+))?)...
  26.3 ❌  26.2 ❌  1.21.11 ✅
```

`26.2` 与 `26.3` 走的是**同一个 `DATE_BASED_PATTERN` 分支**，1.21.x 走的是 `RELEASE_PATTERN`。
对 loader 来说 26.2 和 26.3 没有区别，复制两份只会得到两个字节完全相同的文件。

> 附带结论：`26.3-rc-2` 会被正确归到 `26.3`，装 RC 不会认错版本。

## 实验：Installer 1.1.2 完全不含版本数据

`fabric-installer-1.1.2.jar` 133 个条目里，`26.2` / `26.3` / `26.1` / `1.21` / `1.20` / `25w`
全部 **0 次**。它内部只有这些 URL：

```
https://meta.fabricmc.net/        https://meta2.fabricmc.net/   https://meta3.fabricmc.net/
https://maven.fabricmc.net/       https://maven2.fabricmc.net/  https://maven3.fabricmc.net/
https://launchermeta.mojang.com/mc/game/version_manifest_v2.json
https://maven.fabricmc.net/net/minecraft/experimental_versions.json
```

版本列表是**运行时从网络拉取**的，装哪个 MC 版本由你在界面上选。分版本归档毫无意义。

## 想要"某个版本目录里工具链齐全"怎么办

不要复制（会产生两个字节相同、升级时要改两处的文件）。用组装脚本：

```bash
python3 scripts/use_version.py 26.3          # 软链公共件到 26.3/toolchain/, 打印 JAVA_HOME / classpath
python3 scripts/use_version.py 26.3 --copy   # 真的复制一份(离线/打包时用)
python3 scripts/use_version.py 26.3 --jdk    # 顺带 cat 分卷 + 解压 JDK
```

## 什么时候才真的需要分开

出现以下任一情况时再来拆：

1. **Loader 开始按 MC 版本分叉** —— 比如某天 26.4 要求 loader `>=0.20`，而 26.3 仍停在 0.19.x，
   那就按 `applies_to` 各自归档（判据：jar 内出现版本专属代码路径）。
2. **JDK 主版本变了** —— 26.x 若升到 Java 26，就要新增 `jdk-26-*` 并归到对应目录。
3. **Installer 出现破坏性变更** —— 新旧版本装法不同。

目前三条都不成立，所以 `toolchain/` 保持公共。
