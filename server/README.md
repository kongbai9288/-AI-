# server/ —— 服务端资料

这里放的是**与 Minecraft 版本无关**的服务端通用资料（装服、起服、服务端 mod 骨架）。
跟版本绑定的服务端 API 在 [`26.2/API_TABLE.md`](../26.2/API_TABLE.md) 与
[`26.3/API_TABLE.md`](../26.3/API_TABLE.md) 里，已经按"端"分好类（服务端 21 条、客户端 1 条、通用 46 条）。

## 一、本目录怎么分类的

| 类别 | 文件 | 解决什么问题 |
|---|---|---|
| **部署**（装服 / 起服） | [`SETUP_REPORT.md`](SETUP_REPORT.md) | installer 的 `server` 子命令参数、产物名、离线替代方案 |
| **起服脚本** | [`start.sh`](start.sh) | 一条命令起服，自动找仓库里的 JDK 25 |
| **mod 骨架** | [`fabric.mod.json`](fabric.mod.json) | 纯服务端 mod 的 `environment` 与 `server` entrypoint 该怎么写 |

服务端**开发 API** 不在这里 —— 那属于版本基线，跟着 MC 版本走，所以放在 `26.2/` `26.3/`
的 API 表里，用「端」这一列区分：

| 端 | 条目数（每个版本） | 例子 |
|---|---|---|
| 服务端 | 21 | `DedicatedServerModInitializer`、`ServerLifecycleEvents`、`ServerPlayNetworking`、`ServerTickEvents` |
| 客户端 | 1 | `ClientModInitializer`（对照用，服务端别碰） |
| 通用 | 46 | `ModInitializer`、`EnvType`、`CommandRegistrationCallback`、物品/方块注册 |

## 二、服务端三条路，选哪条

| 方案 | 命令 | 要不要联网 | 适用场景 |
|---|---|---|---|
| **A. installer CLI** | `java -jar fabric-installer-1.1.2.jar server -dir . -mcversion 26.3 -loader 0.19.5 -downloadMinecraft` | ✅ 必须（拉 meta + MC server jar） | 全新装服，有外网 |
| **B. 起已有的 launch jar** | `./start.sh`（起 `fabric-server-launch.jar`） | ❌ 不需要（产物已装好） | 日常起服 / CI |
| **C. 官方 server launcher** | 下载 `fabric-server.jar` 后 `java -jar fabric-server.jar` | 首次需要 | 官方推荐的新流程 |

**实测纠错（重要）**：直觉上"loader jar 的 `Main-Class` 就是
`FabricServerLauncher`，所以 `java -jar fabric-loader.jar` 能起服"——**这是错的**。
实测过了 game jar 检查后会在 `Knot.<clinit>` 抛
`IllegalStateException: ASM not detected on the classpath`（报告实验 5.5），
因为 ASM 不在裸 loader jar 里。真正该起的是 installer 生成的
**`fabric-server-launch.jar`**，它的 MANIFEST `Class-Path` 带上了
`.fabric/libraries/` 下的全部依赖。`server/start.sh` 已按这个结论写。

## 三、实测出来的关键事实

（全部来自 [`SETUP_REPORT.md`](SETUP_REPORT.md)，跑 `python3 scripts/verify_server.py` 可复现）

- installer 的 `server` 子命令参数是
  `-dir <目录> -mcversion <MC版本> -loader <loader版本> -downloadMinecraft`，
  `-downloadMinecraft` 是**开关不带值**
- 装完的产物是 `fabric-server-launch.jar` + `fabric-server-launch.properties`，
  vanilla server jar 叫 `server.jar`，运行时数据在 `.fabric/server/`
- 无人值守安装读 `install.properties`，键是 `fabric-loader-version` / `game-version`；
  loader 侧另有 `fabric-server-launcher.properties`，键是 `launch.mainClass` / `serverJar`
  ⚠️ 两个 properties 名字只差一个 `-launcher`，别写错
- 裸 loader jar 直起会在 `Knot.<clinit>` 报 `ASM not detected on the classpath`；
  起服目标应是 `fabric-server-launch.jar`
- installer 一启动就拉元数据，依次试 `meta.fabricmc.net` → `meta2` → `meta3`，
  全挂就抛 `Unable to load metadata` —— **离线装不了服，只能起已装好的**
- 服务端 mod 入口点：`DedicatedServerModInitializer.onInitializeServer()`
  （在 loader 里，不在 fabric-api 里，所以 classpath 要带 loader）

## 四、26.x 服务端专属坑

1. **服务端没有客户端类**：`environment: "*"` 的 mod 里摸了客户端类，起服就 `NoClassDefFoundError`。
   用 `@Environment(EnvType.CLIENT)` 隔离，或把服务端逻辑单独放 `server` entrypoint。
2. **纯服务端 mod 写 `"environment": "server"`**：写 `"*"` 会被塞进客户端。
3. **26.3 起白名单默认开**：装完看 `server.properties` 的 `white-list`。
   ⚠️ 这条来自社区资料，本仓库未实测，以实际启动后的配置为准。
4. **26.1 起未混淆**：服务端同样不写 `mappings`，直接用 Mojang 命名
   （`ServerLevel` 不是 `ServerWorld`）。
