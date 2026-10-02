# 26.2（已归档）

> 26.2 之后官方发布了 26.3（Wilderness Bound，2026-09-15），新项目请直接用 [`../26.3/`](../26.3/)。
> 本目录保留 26.2 的完整基线，供维护旧 mod / 对照差异使用。

## 版本基线

| 组件 | 值 | 说明 |
|---|---|---|
| Minecraft | `26.2` | 26 = 年份，2 = 第 2 个 drop |
| Java | `25` | class 主版本 69，26.1+ 强制，不可降级 |
| Fabric Loader | `0.19.5` | API 侧最低要求 `>=0.18.4` |
| Fabric Loom | `1.17-SNAPSHOT` | 实测 `1.18.0-alpha.21` 也可用，但要求 Gradle 9.7.0 |
| Gradle | `9.7.0` | Gradle 8.x 死在 `Unsupported class file major version 69` |
| Fabric API | `0.160.0+26.2` | 43 个 jar-in-jar 子模块 |
| mappings | 无 | 26.1 起未混淆，写了 mappings 依赖会报错 |

## 本目录文件

| 文件 | 用途 |
|---|---|
| `gradle.properties` | 版本基线，唯一真相 |
| `build.gradle` / `settings.gradle` | 26.1+ 写法的构建脚本（可直接跑） |
| `fabric.mod.json` | 依赖约束模板（不含 `~` 锁版本） |
| `versions.json` | 版本清单 + 制品 sha256 + 校验记录 |
| `fabric-api-0.160.0+26.2.jar` | Fabric API 本体（jar-in-jar） |

## 26.2 的坑（与旧教程冲突的地方）

1. 不写 `mappings` / `yarn` 依赖 —— 26.1 起游戏未混淆，直接用 Mojang 命名。
2. 插件 id 是 `net.fabricmc.fabric-loom`，不是 `fabric-loom`。
3. `modImplementation` / `modCompileOnly` → `implementation` / `compileOnly`。
4. `loom { noIntermediateMappings() }`，产物用 `jar` 任务，不再有 `remapJar`。
5. 创造模式物品栏是 `CreativeModeTabEvents`（`net.fabricmc.fabric.api.creativetab.v1`），`ItemGroupEvents` 已不存在（已在本目录 jar 中核验）。
6. `fabric.mod.json` 里 minecraft 写 `>=26.2`，不要写 `~26.2`。

## 已核验

- `fabric-api-0.160.0+26.2.jar` sha256 = `5f3dff88…ea05e`（2026-10-02 重新下载比对）
- jar 内 `fabric.mod.json` 声明 `minecraft ~26.2-`、`fabricloader >=0.18.4`、`java >=25`
- jar 内存在：`CreativeModeTabEvents`、`StrippableBlockRegistry`、`TillableBlockRegistry`、`FlattenableBlockRegistry`、`FabricPotionBrewingBuilder`、`CompostableRegistry`、`FuelValueEvents`
- jar 内不存在：`ItemGroupEvents`

详见 `versions.json` 与仓库根目录 `AI_DEV_GUIDE.md`。
