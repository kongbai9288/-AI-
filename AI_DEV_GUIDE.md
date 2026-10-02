# AI 开发 Fabric Mod 速查（26.2 / 26.3 实战版）

> 本文件**已按 Minecraft 26.2 实测校准，并已补入 26.3**（Wilderness Bound，2026-09-15）。
> 旧版内容（1.21.x / Yarn 时代）大量失效，若你来自旧教程，请以本文件为准。
> **版本基线唯一真相是各版本目录下的 `gradle.properties`**，README 只是说明。

---

## 〇、先选版本目录

| 目录 | 状态 | 什么时候用 |
|---|---|---|
| [`26.3/`](26.3/) | ✅ 当前 | 新项目、升级项目。基线见 `26.3/gradle.properties`，制品校验见 `26.3/versions.json` |
| [`26.2/`](26.2/) | 📦 归档 | 维护 26.2 旧 mod、对照 26.2→26.3 差异 |

每个目录里都有一套可直接跑的 `gradle.properties` + `build.gradle` + `settings.gradle` + `fabric.mod.json`，
以及记录 sha256 的 `versions.json`。**别跨目录混用版本值。**

### 本仓库工具链能干什么、不能干什么

| 文件 | 状态 | 说明 |
|---|---|---|
| `toolchain/jdk-25-linux-x64.tar.gz.part-*` | ✅ 可用 | `cat *.part-* > jdk.tar.gz` 后解压，Java 25 |
| `toolchain/fabric-loader-0.19.5.jar` | ✅ 可用 | 运行时 loader，26.2 / 26.3 通用 |
| `toolchain/fabric-installer-1.1.2.jar` | ✅ 可用 | 生成服务端 |
| `26.3/fabric-api-0.161.0+26.3.jar` | ✅ 可用 | 44 个子模块，`META-INF/jars/` 里是 jar-in-jar |
| `26.2/fabric-api-0.160.0+26.2.jar` | ✅ 可用（归档） | 43 个子模块 |
| `toolchain/yarn-1.21.11+build.6.jar` | ❌ **对 26.x 无效** | 这是 **1.21.11** 的映射，26.1 起用不上 |

> 按版本区分的 Fabric API 已归入 `26.2/` 与 `26.3/`；
> 与版本无关的公共组件（JDK / loader / installer）仍留在 `toolchain/`。
> 版本与 sha256 以 `toolchain/manifest.json` + 各目录 `versions.json` 为准。

### ⚠️ 头号大坑：不要再给 26.x 找 mappings

- Minecraft 到 **1.21.11 为止是混淆的**，需要 Yarn / Mojang 映射。
- **26.1 起官方发布未混淆版本**，Fabric 已停止维护第三方映射。
- 所以 26.2 / 26.3 项目里 **`dependencies` 里不要写 `mappings` 那一行**，写了反而会报：
  `The mappings (...) were not built for Minecraft version 26.x, proceed with caution.`
- 源码里直接用 **Mojang 官方命名**（`Level`、`ServerLevel`、`ItemStack`、`ResourceKey`、`Identifier`）。

---

## 一、版本矩阵

| 组件 | 26.2 | 26.3 |
|---|---|---|
| Minecraft | `26.2` | `26.3` |
| Java | **25**（class 主版本 69） | **25** |
| Fabric Loader | `0.19.5`（API 要求 `>=0.18.4`） | `0.19.5`（API 要求 `>=0.19.3`） |
| Fabric Loom | `1.17-SNAPSHOT`；实测 `1.18.0-alpha.21` 也可用 | `1.18-SNAPSHOT`（develop 页当前推荐） |
| Gradle | `9.7.0` | `9.7.0`（公告中配 Loom 1.17 时写的是 9.6.0） |
| Fabric API | `0.160.0+26.2` | `0.161.0+26.3` |
| mappings | 无 | 无 |

> 26 = 年份，2/3 = 第几个 drop，不是 1.21.x 的延续。

### Loom / Gradle 是个隐藏雷

- Loom 1.18.0-alpha 系列的 `runtimeElements` 变体带属性 `org.gradle.plugin.api-version`。
  用低版本 Gradle 会报 `No matching variant ... required '9.x.y'`。
- 反过来 **Gradle 8.14.3 + JDK 25** 会死在另一处：
  `BUG! exception in phase 'semantic analysis' ... Unsupported class file major version 69`
  （Gradle 8 的 Groovy 不认 Java 25 字节码）。**别试图靠降 JDK 绕开**，Loom 自己要求 JVM 25。
- 结论：**JDK 25 + Gradle 9.7.0**，别自作聪明乱配。
- 26.3 官方公告写作时推荐的是 **Loom 1.17 + Gradle 9.6.0**，develop 页面现在给的是 **1.18-SNAPSHOT**。
  两套都能用，选 1.18 就把 Gradle 顶到 9.7.0；若 1.18 报变体不匹配，回退 1.17 + 9.6.0。

---

## 二、构建脚本模板（26.1+ 通用）

完整文件直接取 `26.3/build.gradle` / `26.2/build.gradle`，要点如下：

```gradle
plugins {
    id 'net.fabricmc.fabric-loom' version "${loom_version}"   // ① 插件 id 带 net.fabricmc. 前缀
}

dependencies {
    minecraft "com.mojang:minecraft:${minecraft_version}"
    // ② 26.1 起：不写 mappings

    // ③ 26.1 起：modImplementation / modCompileOnly → implementation / compileOnly
    implementation "net.fabricmc:fabric-loader:${loader_version}"
    implementation "net.fabricmc.fabric-api:fabric-api:${fabric_api_version}"
}

loom {
    noIntermediateMappings()   // ④ 26.1 起无 intermediary 命名空间
}

java {
    sourceCompatibility = JavaVersion.VERSION_25
    targetCompatibility = JavaVersion.VERSION_25
    // 不要 withSourcesJar()：无 intermediary，remapSourcesJar 无法工作
}
tasks.withType(JavaCompile).configureEach { it.options.release = 25 }
```

`gradle.properties`（26.3 版，详见 `26.3/gradle.properties`）：

```properties
minecraft_version=26.3
java_version=25
loader_version=0.19.5
loom_version=1.18-SNAPSHOT
gradle_version=9.7.0
fabric_api_version=0.161.0+26.3
```

26.2 项目取 `26.2/gradle.properties`（`minecraft_version=26.2`、`fabric_api_version=0.160.0+26.2`、
`loom_version=1.17-SNAPSHOT`），其余键相同。两个目录的 `build.gradle` 写法一致，只是值不同。

**26.1 起必须改的四件事**（漏一件就编不过）：
1. 插件 id `fabric-loom` → `net.fabricmc.fabric-loom`
2. 删掉 `mappings` 依赖
3. `modImplementation` / `modCompileOnly` → `implementation` / `compileOnly`
4. 产物用 `jar` 任务，**不再有 `remapJar`**

---

## 二之二、版本 API 表（两个目录各一份，逐条实测）

| 目录 | 表 | 重跑命令 |
|---|---|---|
| `26.3/` | `26.3/API_TABLE.md` + `26.3/api_table.json` | `python3 scripts/verify_api_table.py 26.3` |
| `26.2/` | `26.2/API_TABLE.md` + `26.2/api_table.json` | `python3 scripts/verify_api_table.py 26.2` |

每份 43 条，三条实验通道：
1. **Fabric API**（25 条）：`javap` 读 jar-in-jar 子模块的真实签名
2. **MC 本体**（13 条）：`javap -v` 从 Fabric 的 mixin 注解
   （`target="Lnet/minecraft/...;method()Desc"`）取真实 MC 签名 —— mixin 目标写错就注入失败，是硬证据
3. **符号探测**（5 条）：在子模块 class 常量池里搜字节串（只能证明"被引用"，不能证明"不存在"）

当前结果：两版本均 **37 PASS / 1 UNPROVEN / 5 INFO**。

### 实测纠错的旧教程写法（这张表最大的用处）

| 旧教程写法 | 实测真实情况（26.2 与 26.3 均如此） |
|---|---|
| `ItemGroupEvents.modifyEntriesEvent(...)` | 类**不存在** → `CreativeModeTabEvents.modifyOutputEvent(ResourceKey<CreativeModeTab>)` |
| `ServerTickEvents.END_WORLD_TICK` | 实际是 `END_LEVEL_TICK`（还有 `END_SERVER_TICK`） |
| `PayloadTypeRegistry.playS2C()` | 实际是 `clientboundPlay()` / `serverboundPlay()` |
| `RegistryAttributeHolder.getAttribute(...)` | 实际是 `addAttribute(...)` / `hasAttribute(...)` |
| `ItemStack.hurtAndBreak(int, LivingEntity, EquipmentSlot)` | 26.3 已被 Fabric 重定向到 `hurtAndBreak(int, ServerLevel, ServerPlayer, Consumer)` |

### 26.2 → 26.3 实测差异（脚本 diff 出来的）

| API | 26.2 | 26.3 |
|---|---|---|
| `FuelValueEvents` | present | **absent** |
| `CompostableRegistry` | present | **absent** |
| `FabricPotionBrewingBuilder` | present | **absent** |
| `FabricBrewingProvider`（datagen） | **absent** | present |
| `Strippable/Tillable/FlattenableBlockRegistry` | present | **absent** |
| `FluidVariantAttributes` | `enableColoredVanillaFluidNames()` | `getColoredName()` + `getAssociatedColor()` |
| `FluidFlowEvents.ALLOW` | present | present（**两版都有**，别信"26.3 才新增"的说法） |
| 子模块数 | 43 | 44 |

> 唯一 UNPROVEN：`Entity.hurt` —— 本仓库没有 MC 本体 jar，且 Fabric 的 mixin 没触及它，
> 所以拿不到证据。写伤害代码前请在有 MC jar 的环境跑 `javap -cp <mc-jar> net.minecraft.world.entity.Entity`。

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
- 已核验：`ItemGroupEvents` 在 26.2 / 26.3 的 API jar 里都**不存在**

### 实体

```java
// 拿世界：直接访问字段 world（26.2 已移除 getWorld()）
Level level = this.level();      // Mojang 命名下是 level()
World world = this.world;        // Yarn 命名下是字段 world

// 伤害：26.2 签名带 ServerWorld 且是 final
public final void hurt(DamageSource, float);              // Mojang
public final boolean hurtServer(ServerLevel, DamageSource, float);

// 伤害源
level.damageSources().thrown(this, owner);   // Mojang

// 运动
Vec3 vel = this.getDeltaMovement();   // Mojang / getVelocity() Yarn
this.onGround();                       // Mojang / isOnGround() Yarn

// 生成实体（客户端 World 上没有，只有 ServerLevel 有）
((ServerLevel) level).addFreshEntity(entity);

// 范围查询
List<LivingEntity> hits = level.getEntitiesOfClass(LivingEntity.class, box, pred);
```

**26.x 实体必须实现的抽象方法**：`defineSynchedData(SynchedEntityData.Builder)`
（旧版叫 `initDataTracker`），不实现编译直接报错 `is not abstract and does not override`。

### 物品使用

```java
public InteractionResult use(Level level, Player player, InteractionHand hand)
```
返回值：`InteractionResult.SUCCESS` / `CONSUME` / `PASS` / `FAIL`

### 命令

```java
CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
    dispatcher.register(CommandManager.literal("mycmd")
        .requires(src -> src.hasPermissionLevel(2))
        .executes(ctx -> { ctx.getSource().sendMessage(Text.literal("hi")); return 1; }));
});
```

### 客户端渲染（26.x 架构变了）

```java
// 26.x 用 RenderState 模式，旧的 getTexture() 已移除
public class MyRenderer extends EntityRenderer<RollingLogEntity, EntityRenderState> {
    public MyRenderer(EntityRendererFactory.Context ctx) { super(ctx); }
    @Override public EntityRenderState createRenderState() { return new EntityRenderState(); }
}
EntityRendererRegistry.<RollingLogEntity>register(TYPE, MyRenderer::new);
```

---

## 三之二、26.2 → 26.3 迁移（新增）

构建写法不用改（同为 26.1+ 规则），改的是**被移除的 API**。
下表是把两个 Fabric API jar 解开后按类名比对的结果，与官方公告一致：

| 26.2 有 | 26.3 | 26.3 怎么替代 |
|---|---|---|
| `FuelValueEvents` / `FuelRegistry` | ❌ 移除 | 物品组件 `DataComponents.COOKING_FUEL` |
| `CompostableRegistry` | ❌ 移除 | 物品组件 `DataComponents.COMPOSTABLE`（可用 `DefaultItemComponentEvents.MODIFY`） |
| `FabricPotionBrewingBuilder` | ❌ 移除 | `FabricBrewingProvider`（酿造配方改用 provider） |
| `StrippableBlockRegistry` | ❌ 移除 | 数据驱动的 block transformer |
| `TillableBlockRegistry` | ❌ 移除 | 同上 |
| `FlattenableBlockRegistry` | ❌ 移除 | 同上 |
| `FluidVariantAttributes`（实验性流体 API） | ✅ 转正 | 新增 `isInFluid` / `onFluidEntered` / `onFluidExited` |
| — | 🆕 `FluidFlowEvents` | 流体流动回调（扩散 / 放置 / 邻居更新） |
| `CreativeModeTabEvents` | ✅ 保留 | 写法不变 |

其它 26.3 新增点（来自官方公告，未在本仓库 jar 上逐条实测）：
- `TooltipFlag#shouldDisplayAllInformation`：给配方查看类 mod 索引 tooltip 用
- 方块可覆写 `Block#getProvidedEnchantmentPower` 提供附魔威力
- 子模块数：26.2 = 43，26.3 = 44
- 客户端侧 GLFW → SDL 迁移（社区迁移笔记提及）：鼠标按键别再用魔法数字比较，
  改用 `InputConstants` 字段 —— 此条未在本次 jar 比对中验证，写客户端输入代码时注意

---

## 四、Yarn 命名 vs Mojang 命名 对照

本仓库的 yarn jar 是 1.21.11 的，**26.x 请用 Mojang 官方命名**。混用会编译失败：

| Yarn（旧） | Mojang（26.x） |
|---|---|
| `World` | `Level`（`ServerWorld` → `ServerLevel`） |
| `getVelocity()` / `setVelocity()` | `getDeltaMovement()` / `setDeltaMovement()` |
| `isOnGround()` | `onGround()` |
| `isClient()` | `isClientSide()` |
| `damage(src, amt)` | `hurt(src, amt)` |
| `spawnEntity()` | `addFreshEntity()`（仅 `ServerLevel`） |
| `Vec3d` | `Vec3` |
| `RegistryKey` | `ResourceKey` |
| `ItemStack` / `BlockPos` / `BuiltInRegistries` | 同名 |

---

## 五、fabric.mod.json 版本约束（血泪）

```json
"depends": {
  "fabricloader": ">=0.19.5",
  "minecraft": ">=26.3",      // ⚠️ 不要写 "~26.3"
  "java": ">=25",
  "fabric-api": "*"           // 硬依赖：没装就拒绝加载
}
```

- **`~26.3` 等价于 `>=26.3.0 <26.4.0`**。版本字符串带 hotfix 后缀或格式不符时，
  会误判成"旧版本"拒绝加载 —— 症状是"我版本明明是对的，它非说我旧"。
- `*` 表示"必须存在，任意版本"，放在 `depends` 里就是**硬依赖**，缺了直接崩。
  只想做成可选就放 `suggests`。
- **运行时真正用到的库，必须在 `depends` 里**；只编译不运行用 `compileOnly` 即可。

### 配套纪律
- **版本基线唯一真相是 `gradle.properties`**（26.3 项目看 `26.3/gradle.properties`）。
- `processResources` 里 `expand` 了哪些变量，`fabric.mod.json` 里才能用哪些 `${}`。

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

1. **先确认 MC 版本再动手**，并先翻对应目录（`26.3/` 或 `26.2/`）的 `gradle.properties`。
2. **不要凭记忆写 API** —— 用 `javap` 核对。
3. **别给 26.x 找 mappings** —— 游戏不混淆，`mappings` 依赖是多余的。
4. **JDK 25 + Gradle 9.7.0**，别乱配；Loom 1.18 需要 Gradle 9.7.0。
5. **实体要实现 `defineSynchedData`**，渲染要按 RenderState 模式写。
6. **`fabric.mod.json` 别用 `~`** 锁版本。
7. **26.3 起别再用 `FuelRegistry` / `CompostableRegistry` / `FabricPotionBrewingBuilder` /
   Strippable / Tillable / Flattenable**，改物品组件与新 API。
8. **每加一个功能就编一次**，别堆到最后。

---

## 八、本次核验记录（2026-10-02）

| 项目 | 方法 | 结果 |
|---|---|---|
| `fabric-api-0.161.0+26.3.jar` | 从仓库重新下载后算 sha256，与 `toolchain/manifest.json` 比对 | ✅ 一致（`86f16178…b657a6`） |
| `fabric-loader-0.19.5.jar` | 同上 | ✅ 一致 |
| `fabric-installer-1.1.2.jar` | 同上 | ✅ 一致 |
| `yarn-1.21.11+build.6.jar` | 同上 | ✅ 一致（但对 26.x 无用） |
| `fabric-api-0.160.0+26.2.jar` | 同上（manifest 无此条目，为补记录） | ✅ `5f3dff88…ea05e`，已写入 `26.2/versions.json` |
| 26.3 版本基线 | 核对 fabricmc.net/develop、Fabric 26.3 公告、Modrinth | ✅ loader 0.19.5 / API 0.161.0+26.3 / Java 25 |
| API 增删 | 解开两个 API jar 的 jar-in-jar 子模块按类名比对 | ✅ 与 26.3 公告的移除清单一致 |
| 版本 API 表（26.2） | `javap` 25 读 fabric-api jar + mixin 注解 | ✅ 43 条：37 PASS / 1 UNPROVEN / 5 INFO |
| 版本 API 表（26.3） | 同上 | ✅ 43 条：37 PASS / 1 UNPROVEN / 5 INFO |
| 真实 Gradle 构建 | 本环境无法访问 maven.fabricmc.net / piston-meta | ⚠️ 未执行，需在有外网的机器或 GitHub Actions 上跑 |

> 说明：`loom_version` / `gradle_version` 属于"官方公告值 + 本仓库历史实测值"的组合，
> 若新环境下 Loom 报 `No matching variant`，按第一节的回退方案处理。

---

## 九、参考

- Fabric 开发文档：https://docs.fabricmc.net/
- 26.3 公告（Wilderness Bound）：https://fabricmc.net/2026/09/15/263.html
- 26.2 公告：https://fabricmc.net/2026/06/15/262.html
- 组件推荐版本：https://fabricmc.net/develop
- Fabric API（Modrinth，含 sha）：https://modrinth.com/mod/fabric-api
- 映射查询（1.21.11 及更早）：https://mapping.dev/
