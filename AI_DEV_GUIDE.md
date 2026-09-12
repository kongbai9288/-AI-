# AI 开发 Fabric Mod 速查

给 AI / 自动化流程用的 Fabric 开发备忘。版本以 `gradle.properties`（由 `sync-gradle-props.py` 从 manifest 同步）为准。

---

## 一、先确认 Java 版本 ⚠️

**这是最常见的翻车点。** Java 版本由 Minecraft 版本决定，不是越新越好：

| Minecraft | 需要 Java |
|---|---|
| 1.21.x | **21** |
| 1.20.5 / 1.20.6 | 21 |
| 1.18 ~ 1.20.4 | 17 |
| 1.17 | 16 |
| ≤ 1.16 | 8 |

`sync-gradle-props.py` 会按 MC 版本自动写入 `java_version`。若报错
`Unsupported class file major version XX`，就是 Java 版本不对——换对应 JDK，不要改 `java_version` 硬编。

---

## 二、项目结构

```
build.gradle              依赖 / Loom 配置(不要手改版本, 用 gradle.properties)
gradle.properties         版本集中处 ← 改这里
settings.gradle           仓库源(Fabric Maven 必须)
src/main/java/...         代码
src/main/resources/
  fabric.mod.json         mod 元数据 + 入口声明
  aimod.mixins.json       mixin 配置
build/libs/               产物 jar
```

---

## 三、常用任务片段

> 以下以 MC 1.21.x + Yarn 为准。跨版本时类名/方法名可能变，
> **先让 IDE 补全或查 Yarn 映射**，不要凭记忆写。

### 注册物品 / 方块

见 `ModContent.java` 模板。要点：
- 用 `Identifier.of(MOD_ID, name)`（1.21 起，不再是 `new Identifier`）
- 方块要**同时注册 Block 和 BlockItem**，否则背包里没有
- 加进创造物品栏：`ItemGroupEvents.modifyEntriesEvent(ItemGroups.XXX)`

### 服务端 Tick 事件

```java
ServerTickEvents.END_SERVER_TICK.register(server -> {
    // 每 tick 执行。别在这里做重活
});
```

### 玩家交互

```java
UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
    if (!world.isClient) { /* 服务端逻辑 */ }
    return ActionResult.PASS;   // PASS=放行, SUCCESS=拦截
});
```

### 注册命令

```java
CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
    dispatcher.register(CommandManager.literal("mycmd")
        .requires(src -> src.hasPermissionLevel(2))
        .executes(ctx -> {
            ctx.getSource().sendMessage(Text.literal("hi"));
            return 1;
        }));
});
```

### 网络包（1.20.5+ 新 API）

1.20.5 起旧 `PacketByteBufs` 方式改了，用自定义 payload：

```java
public record MyPayload(String data) implements CustomPayload {
    public static final Id<MyPayload> ID =
        new CustomPayload.Id<>(Identifier.of("aimod", "my"));
    public static final PacketCodec<RegistryByteBuf, MyPayload> CODEC =
        PacketCodec.tuple(PacketCodecs.STRING, MyPayload::data, MyPayload::new);

    @Override public Id<? extends CustomPayload> getId() { return ID; }
}
// 注册: PayloadTypeRegistry.playC2S().register(MyPayload.ID, MyPayload.CODEC);
// 发送: ServerPlayNetworking.send(player, new MyPayload("hi"));
```

### Mixin（改原版行为）

1. 在 `aimod.mixins.json` 的 `mixins` / `client` 数组里加类名
2. 写 mixin 类：

```java
@Mixin(PlayerEntity.class)
public class PlayerEntityMixin {
    @Inject(method = "tick", at = @At("HEAD"))
    private void onTick(CallbackInfo ci) {
        // 注入逻辑
    }
}
```

⚠️ 方法名/签名来自 **Yarn 映射**，MC 小版本更新常变动。失效时典型症状：
`Mixin apply failed`，此时重新反混淆确认目标方法名。

---

## 四、构建与调试

```bash
export JAVA_HOME=/path/to/jdk21     # 按 MC 版本选
./gradlew build                     # 产物 build/libs/
./gradlew runClient                 # 启动测试客户端(需图形环境)
./gradlew genSources                # 生成反混淆源码, 便于查 API
```

`genSources` 对 AI 特别有用——能直接搜原版代码，确认类名和方法签名，避免凭记忆写错。

---

## 五、常见报错排查

| 报错 | 原因 / 处理 |
|---|---|
| `Unsupported class file major version` | Java 版本与 MC 不匹配 |
| `Could not resolve net.fabricmc:fabric-loom` | settings.gradle 缺 Fabric Maven 源 |
| Minecraft 本体下载失败 | 网络问题；Loom 从 Mojang 官方拉，需遵守 EULA |
| `Mixin apply failed` | 目标方法签名变了，重新 genSources 核对 |
| `fabric.mod.json` 校验失败 | schemaVersion 或 depends 格式错，对照官方 schema |
| 注册了但游戏里没有 | 忘了注册 BlockItem / 忘了加物品组 |

---

## 六、给 AI 的工作建议

1. **不要凭记忆写 API**——先 `genSources` 或直接读仓库里的 Yarn 映射 jar
2. **版本先同步**：跑 `sync-gradle-props.py`，再动手写
3. **小步验证**：每加一个功能就 `./gradlew build` 一次，别堆到最后
4. **跨版本谨慎**：1.20.5 / 1.21 都有 API 断裂式改动（尤其网络包和注册 API）

---

## 七、参考

- Fabric 开发文档：https://fabricmc.net/wiki/
- Loom 版本对照：https://fabricmc.net/develop
- Yarn 映射查询：https://mapping.dev/ （或本地 genSources）
- Fabric API 源码：https://github.com/FabricMC/fabric
