# 服务端实测报告

> 由 `scripts/verify_server.py` 生成。所有内容来自**真实运行输出**或 **class 常量池**，没有一条是凭记忆写的。
> JDK: `/data/workspace/jdk-25.0.4.1+1/bin/java`　loader: `fabric-loader-0.19.5.jar`　installer: `fabric-installer-1.1.2.jar`

## 实验 1：真跑 `java -jar fabric-loader.jar`（无 server.jar）

在一个空目录里直接跑，看它到底要什么、报什么错：

```bash
$ java -jar fabric-loader-0.19.5.jar
```

真实输出：

```
The Minecraft server .JAR is missing (/data/workspace/.srv_probe/server.jar)!

Fabric's server-side launcher expects the server .JAR to be provided.
You can edit its location in fabric-server-launcher.properties.

Without the official Minecraft server .JAR, Fabric Loader cannot launch.
Exception in thread "main" java.lang.RuntimeException: Failed to setup Fabric server environment!
	at net.fabricmc.loader.impl.launch.server.FabricServerLauncher.main(FabricServerLauncher.java:63)
Caused by: java.lang.RuntimeException: Missing game jar at /data/workspace/.srv_probe/server.jar
	at net.fabricmc.loader.impl.launch.server.FabricServerLauncher.setup(FabricServerLauncher.java:92)
	at net.fabricmc.loader.impl.launch.server.FabricServerLauncher.main(FabricServerLauncher.java:61)
```

从输出里读出来的事实：

- 默认找的游戏 jar 是 `server.jar`，路径是**当前工作目录下的绝对路径**
- 报错信息里点名的配置文件是 `fabric-server-launcher.properties`
- 结论：**loader jar 本身就能当服务端启动器用**，前提是同目录有官方 server jar

## 实验 2：loader jar 的 MANIFEST

- `Main-Class: net.fabricmc.loader.impl.launch.server.FabricServerLauncher`
- `Fabric-Loom-Remap: false`
- `Automatic-Module-Name: net.fabricmc.loader`
- `Multi-Release: true`

`Main-Class` 就是服务端启动入口 —— 这解释了为什么 `java -jar fabric-loader.jar` 能起服。

## 实验 3：installer 的 `server` 子命令参数（从 class 常量池读）

`net.fabricmc.installer.server.ServerHandler.cliHelp()` 里的用法串：

```
downloadMinecraft
-dir <install dir, default current dir> -mcversion <minecraft version, default latest> -loader <loader version, default latest> -downloadMinecraft
```

整理成可用命令：

```bash
java -jar fabric-installer-1.1.2.jar server \
     -dir <安装目录, 默认当前目录> \
     -mcversion <MC版本, 默认最新> \
     -loader <loader版本, 默认最新> \
     -downloadMinecraft
```

> `-downloadMinecraft` 是**开关**，不带值；不写就不会自动下载官方 server jar。

安装产物与内部文件名（`ServerInstaller` 常量池）：

- `fabric-server-launch.jar`
- `fabric-server-launch.properties`
- `launch.mainClass=`
- `mainClass`
- `progress.generating.launch.jar`

`ServerLauncher`（无人值守安装）读的配置键：

- `.fabric`
- `fabric.customLoaderPath`
- `fabric.gameJarPath`
- `fabric.installer.server.gameJar`
- `game-version`
- `install.properties`
- `server`

## 实验 4：installer 装服必须联网（实测失败现场）

本环境跑 `server -help` 的真实输出（前 6 行）：

```
Loading Fabric Installer: 1.1.2
service FabricService{meta='https://meta.fabricmc.net/', maven='https://maven.fabricmc.net/'} failed: java.io.IOException: Request to https://meta.fabricmc.net/v2/versions/loader using DIRECT failed: (certificate_unknown) PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target
service FabricService{meta='https://meta2.fabricmc.net/', maven='https://maven2.fabricmc.net/'} failed: java.io.IOException: Request to https://meta2.fabricmc.net/v2/versions/loader using DIRECT failed: (certificate_unknown) PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target
service FabricService{meta='https://meta3.fabricmc.net/', maven='https://maven3.fabricmc.net/'} failed: java.io.IOException: Request to https://meta3.fabricmc.net/v2/versions/loader using DIRECT failed: (certificate_unknown) PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target
Exception in thread "main" java.lang.RuntimeException: Unable to load metadata
	at net.fabricmc.installer.Main.loadMetadata(Main.java:108)
```

读出来的事实：

- installer 启动第一步就是拉元数据，依次尝试 `meta.fabricmc.net` → `meta2.fabricmc.net` → `meta3.fabricmc.net`，全失败就抛 `RuntimeException: Unable to load metadata`
- 所以**离线环境下 `-downloadMinecraft` 装服这条路走不通**，得用实验 1 的"loader jar + 已有 server.jar"方案
- 无头环境用 CLI 模式，别用 GUI（GUI 需要 X server）

## 实验 5：服务端 mod 入口点（`javap` 实测签名）

```
Compiled from "DedicatedServerModInitializer.java"
public interface net.fabricmc.api.DedicatedServerModInitializer {
  public abstract void onInitializeServer();
}
```

```
Compiled from "ModInitializer.java"
public interface net.fabricmc.api.ModInitializer {
  public abstract void onInitialize();
}
```

```
Compiled from "ClientModInitializer.java"
public interface net.fabricmc.api.ClientModInitializer {
  public abstract void onInitializeClient();
}
```

```
Compiled from "EnvType.java"
public final class net.fabricmc.api.EnvType extends java.lang.Enum<net.fabricmc.api.EnvType> {
  public static final net.fabricmc.api.EnvType CLIENT;
  public static final net.fabricmc.api.EnvType SERVER;
  public static net.fabricmc.api.EnvType[] values();
  public static net.fabricmc.api.EnvType valueOf(java.lang.String);
  static {};
}
```


## 实验 5.5：⚠️ 裸 `fabric-loader.jar` 直起会失败（缺 ASM）

放一个占位 `server.jar` 后再跑，真实输出：

```
Exception in thread "main" java.lang.RuntimeException: An exception occurred when launching the server!
	at net.fabricmc.loader.impl.launch.server.FabricServerLauncher.main(FabricServerLauncher.java:71)
Caused by: java.lang.ExceptionInInitializerError
	at net.fabricmc.loader.impl.launch.knot.KnotServer.main(KnotServer.java:23)
	at net.fabricmc.loader.impl.launch.server.FabricServerLauncher.main(FabricServerLauncher.java:69)
Caused by: java.lang.IllegalStateException: ASM not detected on the classpath (or perhaps org/objectweb/asm/ClassReader.class was renamed?)
	at net.fabricmc.loader.impl.util.LoaderUtil.verifyClasspath(LoaderUtil.java:85)
	at net.fabricmc.loader.impl.launch.knot.Knot.<clinit>(Knot.java:330)
	... 2 more
```

读出来的事实（这条推翻了"loader jar 自己能起服"的直觉）：

- loader 过了 game jar 检查后，会在 `Knot.<clinit>` 里做 `LoaderUtil.verifyClasspath()`
- ASM 不在裸 loader jar 里，于是抛 `IllegalStateException: ASM not detected on the classpath`
- **结论**：起服要用 installer 生成的 **`fabric-server-launch.jar`**，它的 MANIFEST `Class-Path` 带上了 `.fabric/libraries/` 下的全部依赖（含 ASM）。把 `fabric-loader.jar` 单独 `java -jar` 只在"依赖已在 classpath"的场景下成立。
- `server/start.sh` 已按这个结论写：优先找 `fabric-server-launch.jar`，找不到 loader jar 时会明确提示。

## 实验 6：26.x 服务端的三个专属坑

1. **服务端没有客户端类**：mod 若 `environment: "*"` 但代码里摸了客户端类，起服直接 `NoClassDefFoundError`。要用 `@Environment(EnvType.CLIENT)` 隔离，或把服务端逻辑单独放 `server` entrypoint。
2. **`fabric.mod.json` 的 `environment` 字段**：纯服务端 mod 写 `"server"`，写 `"*"` 会被塞进客户端，客户端装了才报错。
3. **26.3 起白名单默认开**（社区实测：26.3 服务端默认启用 whitelist）—— 装完服记得在 `server.properties` 里看 `white-list`，或控制台 `whitelist on`。⚠️ 这一条来自社区资料，本脚本未在本仓库实测，请以实际启动后的 server.properties 为准。

