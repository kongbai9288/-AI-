# AI 开发 Fabric Mod 速查（MC 26.2 实战版）

> 本文件**已按 Minecraft 26.2 实测校准**。旧版内容（1.21.x / Yarn 时代）大量失效，
> 若你来自旧教程，请以本文件为准。版本真相永远以 `gradle.properties` 为准。

---

## 〇、先看清这个仓库的工具链能干什么、不能干什么

| 文件 | 状态 | 说明 |
|---|---|---|
| `toolchain/jdk-25-linux-x64.tar.gz.part-*` | ✅ 可用 | `cat *.part-* > jdk.tar.gz` 后解压，Java 25 |
| `toolchain/fabric-loader-0.19.5.jar` | ✅ 可用 | 运行时 loader |
| `toolchain/fabric-api-0.160.0+26.2.jar` | ✅ 可用 | 44 个子模块，`META-INF/jars/` 里是 jar-in-jar |
| `toolchain/fabric-installer-1.1.2.jar` | ✅ 可用 | 生成服务端 |
| `toolchain/yarn-1.21.11+build.6.jar` | ❌ **对 26.2 无效** | 这是 **1.21.11** 的映射，不是 26.2 的 |

### ⚠️ 头号大坑：不要再给 26.2 找 mappings

- Minecraft 到 **1.21.11 为止是混淆的**，需要 Yarn / Mojang 映射。
- **26.1 起官方发布未混淆版本**，Fabric 已停止维护第三方映射。
- 所以 26.2 项目里 **`dependencies` 里不要写 `mappings` 那一行**，写了反而会报：
  `The mappings (...) were not built for Minecraft version 26.2, proceed with caution.`
- 源码里直接用 **Mojang 官方命名**（`ServerWorld`、`ItemStack`、`ResourceKey`、`Identifier`）。

---

## 一、版本矩阵（26.2 实测）

| 组件 | 值 | 踩过的坑 |
|---|---|---|
| Minecraft | `26.2` | 26 是年份、2 是第 2 个 drop，不是 1.21.x 的延续 |
| Java | **25**（class 主版本 69） | 不可降级；MC 26.1+ 强制 |
| Fabric Loader | `0.19.3` 起 | 26.2 推荐 0.19.5 |
| Fabric Loom | **1.17+** | 插件 id 是 `net.fabricmc.fabric-loom`（不是 `fabric-loom`） |
| Gradle | **9.7.0** | ⚠️ 见下 |

### Gradle 版本是个隐藏雷

Loom 1.18.0-alpha.21 的 `runtimeElements` 变体带属性 `org.gradle.plugin.api-version = 9.7.0`。
用 Gradle **9.1.0** 会报 `No matching variant ... required '9.1.0'`。
实测 **Gradle 9.7.0 + JDK 25** 组合可用。

反过来，用 **Gradle 8.14.3 + JDK 25** 会死在另一处：
`BUG! exception in phase 'semantic analysis' ... Unsupported class file major version 69`
（Gradle 8 的 Groovy 不认 Java 25 字节码）。**别试图靠降 JDK 绕开**，Loom 自己要求 JVM 25。

结论：**JDK 25 + Gradle 9.7.0**，别自作聪明乱配。

---

## 二、26.2 构建脚本模板（实测可编译）

```gradle
plugins {
    id 'net.fabricmc.fabric-loom' version "${loom_version}"
}

dependencies {
    minecraft "com.mojang:minecraft:${minecraft_version}"
    // 26.1 起：不写 mappings

    // 26.1 起：modImplementation / modCompileOnly → implementation / compileOnly
    implementation "net.fabricmc:fabric-loader:${loader_version}"
    implementation "net.fabricmc.fabric-api:fabric-api:${fabric_api_version}"
}

loom {
    noIntermediateMappings()   // 26.1 起无 intermediary 命名空间
}

java {
    sourceCompatibility = JavaVersion.VERSION_25
    targetCompatibility = JavaVersion.VERSION_25
    // 不要 withSourcesJar()：无 intermediary，remapSourcesJar 无法工作
}
tasks.withType(JavaCompile).configureEach { it.options.release = 25 }
```

`gradle.properties`：

```properties
minecraft_version=26.2
loader_version=0.19.3
loom_version=1.17-SNAPSHOT      # 想锁死可用 1.18.0-alpha.21
fabric_api_version=0.160.0+26.2
```

**26.1 起必须改的三件事**（漏一件就编不过）：
1. 插件 id `fabric-loom` → `net.fabricmc.fabric-loom`
2. 删掉 `mappings` 依赖
3. `modImplementation` / `modCompileOnly` → `implementation` / `compileOnly`
4. 产物用 `jar` 任务，**不再有 `remapJar`**

---

## 三、26.2 API 速查（javap 实测签名，非记忆）

> 以下均从 `minecraft-26.2-client.jar` + `fabric-api-0.160.0+26.2.jar` 反编译核对过。
> **不要凭旧教程写 API。** 用 `javap -cp <classpath> <类名>` 自查。

### 注册

```java
// 物品
Registry.register(BuiltInRegistries.ITEM,
    ResourceKey.create(Registries.ITEM, Identifier.fromNamespaceAndPath(MOD_ID, "name")),
    new Item(new Item.Properties().stacksTo(16)));

// 实体类型：26.x 用 ResourceKey + Builder.build(key)
ResourceKey<EntityType<?>> KEY = ResourceKey.create(Registries.ENTITY_TYPE,
        Identifier.fromNamespaceAndPath(MOD_ID, "rolling_log"));
EntityType<RollingLogEntity> TYPE = Registry.register(
        BuiltInRegistries.ENTITY_TYPE, KEY,
        EntityType.Builder.<RollingLogEntity>of(RollingLogEntity::new, MobCategory.MISC)
                .sized(0.9f, 0.9f)
                .clientTrackingRange(10)
                .updateInterval(4)
                .build(KEY));
```

- `Identifier.of(ns, path)` / `fromNamespaceAndPath` / `withDefaultNamespace` —— 不再是 `new Identifier`
- `Registry.register(Registry, ResourceKey, V)` 或 `(Registry, Identifier, V)`

### 创造模式物品栏（26.2 改名了！）

```java
// ❌ 旧：ItemGroupEvents.modifyEntriesEvent(ItemGroups.COMBAT)
// ✅ 新：CreativeModeTabs 的 key 常量是 private，需自己构造 ResourceKey
private static final ResourceKey<CreativeModeTab> COMBAT =
        ResourceKey.create(Registries.CREATIVE_MODE_TAB,
                Identifier.withDefaultNamespace("combat"));

CreativeModeTabEvents.modifyOutputEvent(COMBAT)
        .register((FabricCreativeModeTabOutput output) -> output.accept(MY_ITEM));
```

- `net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents`（不是 `itemgroup.v1.ItemGroupEvents`）
- `modifyOutputEvent(ResourceKey<CreativeModeTab>)` → `Event<ModifyOutput>`
- `ModifyOutput.modifyOutput(FabricCreativeModeTabOutput)`
- `FabricCreativeModeTabOutput.accept(ItemStack)` / `accept(ItemStack, TabVisibility)` / `prepend(...)`

### 实体（26.2 关键差异）

```java
// 拿世界：直接访问字段 world（26.2 已移除 getWorld()）
Level level = this.level();      // Mojang 命名下是 level()
World world = this.world;        // Yarn 命名下是字段 world

// 伤害：26.2 签名带 ServerWorld 且是 final
public final void hurt(DamageSource, float);              // Mojang
public final boolean hurtServer(ServerLevel, DamageSource, float);
target.hurt(source, DAMAGE);
// Yarn 侧：target.damage(ServerWorld, DamageSource, float)

// 伤害源
level.damageSources().thrown(this, owner);   // Mojang
world.getDamageSources().generic();          // Yarn

// 运动
Vec3 vel = this.getDeltaMovement();   // Mojang / getVelocity() Yarn
this.setDeltaMovement(vx, vy, vz);
this.onGround();                       // Mojang / isOnGround() Yarn

// 生成实体（客户端 World 上没有，只有 ServerLevel 有）
((ServerLevel) level).addFreshEntity(entity);      // Mojang
((ServerWorld) world).spawnNewEntityAndPassengers(entity);  // Yarn

// 范围查询
List<LivingEntity> hits = level.getEntitiesOfClass(LivingEntity.class, box, pred);  // Mojang
world.collectEntitiesByType(TypeFilter.instanceOf(LivingEntity.class), box, pred, list); // Yarn
```

**26.2 实体必须实现的抽象方法**：`defineSynchedData(SynchedEntityData.Builder)`
（旧版叫 `initDataTracker`），不实现编译直接报错 `is not abstract and does not override`。

### 物品使用

```java
// Mojang 命名
public InteractionResult use(Level level, Player player, InteractionHand hand)
// Yarn 命名
public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand)
```
返回值：`InteractionResult.SUCCESS` / `CONSUME` / `PASS` / `FAIL`（Yarn：`TypedActionResult.success/pass/consume`）

### 命令

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
回调三参：`(CommandDispatcher<CommandSourceStack>, CommandBuildContext, Commands.CommandSelection)`

### 客户端渲染（26.2 架构变了）

```java
// 26.2 用 RenderState 模式，旧的 getTexture() 已移除
public class MyRenderer extends EntityRenderer<RollingLogEntity, EntityRenderState> {
    public MyRenderer(EntityRendererFactory.Context ctx) { super(ctx); }
    @Override public EntityRenderState createRenderState() { return new EntityRenderState(); }
}
// 注册
EntityRendererRegistry.<RollingLogEntity>register(TYPE, MyRenderer::new);
// 投掷物可复用：ThrownItemRenderer::new
```

---

## 四、Yarn 命名 vs Mojang 命名 对照

本仓库的 yarn jar 是 1.21.11 的，**26.2 请用 Mojang 官方命名**。混用会编译失败：

| Yarn（旧） | Mojang（26.x） |
|---|---|
| `World` | `Level`（`ServerWorld` → `ServerLevel`） |
| `ItemStack` | `ItemStack` |
| `getVelocity()` / `setVelocity()` | `getDeltaMovement()` / `setDeltaMovement()` |
| `isOnGround()` | `onGround()` |
| `isClient()` | `isClientSide()` |
| `damage(src, amt)` | `hurt(src, amt)` |
| `spawnEntity()` | `addFreshEntity()`（仅 `ServerLevel`） |
| `BlockPos` | `BlockPos` |
| `Vec3d` | `Vec3` |
| `Registry`/`BuiltInRegistries` | 同名 |
| `RegistryKey` | `ResourceKey` |

---

## 五、fabric.mod.json 版本约束（血泪）

```json
"depends": {
  "fabricloader": ">=0.19.3",
  "minecraft": ">=26.2",      // ⚠️ 不要写 "~26.2"
  "java": ">=25",
  "carpet": "*"               // 硬依赖：没装就拒绝加载
}
```

- **`~26.2` 等价于 `>=26.2.0 <26.3.0`**。版本字符串带 hotfix 后缀或格式不符时，
  会误判成"旧版本"拒绝加载 —— 症状是"我版本明明是对的，它非说我旧"。
- `*` 表示"必须存在，任意版本"，放在 `depends` 里就是**硬依赖**，缺了直接崩。
- 只想做成可选就放 `suggests`。
- **运行时真正用到的库，必须在 `depends` 里**；只编译不运行用 `compileOnly` 即可，
  别把它塞 `depends` 造成误拒。

### 配套纪律
- **版本基线唯一真相是 `gradle.properties`**，README 只是说明。两处冲突时以 properties 为准 —— 
  不一致是"加载器版本不对"这类玄学报错的高发来源。
- `processResources` 里 `expand` 了哪些变量，`fabric.mod.json` 里才能用哪些 `${}`，
  没 expand 的写成硬编码，改 properties 不会同步。

---

## 六、构建与自查命令

```bash
export JAVA_HOME=/path/to/jdk25
./gradlew build            # 产物 build/libs/
./gradlew genSources       # 反编译源码，查 API 用

# 无 Gradle 时用 javac 直编（本仓库 JDK 25 可直接用）
javac --release 25 -cp "$(cat full_cp.txt)" -d build/classes $(find src -name '*.java')
javap -cp "$CP" net.minecraft.world.entity.Entity   # 核对签名
```

**验证 class 版本**：`javap -v` 看 `major version`，**69 = Java 25**。

---

## 七、给下一个 AI 的防坑清单

1. **先确认 MC 版本再动手**。26.1+ 和 1.21.x 是两套世界，API 几乎全变。
2. **不要凭记忆写 API** —— 用 `javap` 核对（本仓库有现成 `jap.sh`）。
3. **别给 26.2 找 mappings** —— 游戏不混淆，`mappings` 依赖是多余的。
4. **Gradle 9.7.0 + JDK 25**，别乱配，8.x 和 9.1 都有坑。
5. **实体要实现 `defineSynchedData`**，渲染要按 RenderState 模式写。
6. **`fabric.mod.json` 别用 `~`** 锁版本。
7. **版本表只信 `gradle.properties`**。
8. **每加一个功能就编一次**，别堆到最后。

## 八、参考

- Fabric 开发文档：https://docs.fabricmc.net/
- 26.2 迁移：https://docs.fabricmc.net/develop/porting/
- Fabric 26.2 公告：https://fabricmc.net/2026/06/15/262.html
- 组件推荐版本：https://fabricmc.net/develop
- 映射查询（1.21.11 及更早）：https://mapping.dev/
