# 26.3（当前版本）

> 26.3 = Wilderness Bound drop，2026-09-15 发布。Fabric 侧 2026-09-18 起 stable：
> loader `0.19.5` + Fabric API `0.161.0+26.3`。

## 版本基线

| 组件 | 值 | 说明 |
|---|---|---|
| Minecraft | `26.3` | 与 26.2 同为 26.x，不是 1.21.x 的延续 |
| Java | `25` | Mojang 26.3 元数据指定，与 26.2 一致 |
| Fabric Loader | `0.19.5` | 官方公告推荐的最新稳定版；API 侧最低 `>=0.19.3` |
| Fabric Loom | `1.18-SNAPSHOT` | fabricmc.net/develop 当前推荐；26.3 公告写作时的值是 1.17 |
| Gradle | `9.7.0` | 跟 Loom 1.18 走；公告里与 Loom 1.17 搭配写的是 9.6.0 |
| Fabric API | `0.161.0+26.3` | 44 个 jar-in-jar 子模块（26.2 是 43） |
| mappings | 无 | 26.1 起未混淆，不写 mappings / yarn |

## 本目录文件

| 文件 | 用途 |
|---|---|
| `gradle.properties` | 版本基线，唯一真相 |
| `build.gradle` / `settings.gradle` | 26.1+ 写法的构建脚本（可直接跑） |
| `fabric.mod.json` | 依赖约束模板（不含 `~` 锁版本） |
| `versions.json` | 版本清单 + 制品 sha256 + 校验记录 |
| **`API_TABLE.md`** | **版本 API 表（43 条，逐条实测）** |
| `api_table.json` | 上表的机器可读版，含每条的签名与证据 |
| `fabric-api-0.161.0+26.3.jar` | Fabric API 本体（jar-in-jar） |

## 版本 API 表

`API_TABLE.md` 里 43 条全部实测，重跑命令：

```bash
python3 scripts/verify_api_table.py 26.3     # 需 JDK 25 的 javap
```

- Fabric API 条目：`javap` 读 `fabric-api-0.161.0+26.3.jar` 的 44 个 jar-in-jar 子模块
- MC 本体条目：`javap -v` 从 Fabric 的 mixin 注解里取真实 MC 签名（`@Redirect(target="Lnet/minecraft/...")`）
- 状态：`PASS` 符合预期 / `UNPROVEN` 证据未采集到 / `INFO` 仅记录不做断言

本次结果：**37 PASS、1 UNPROVEN、5 INFO**。

### 本版本实测要点（都是跑出来的，不是抄的）

- `ItemGroupEvents` **不存在**，物品栏走 `CreativeModeTabEvents.modifyOutputEvent(ResourceKey<CreativeModeTab>)`
- `ServerTickEvents` 是 `END_LEVEL_TICK`，**不是**旧教程的 `END_WORLD_TICK`
- `PayloadTypeRegistry` 是 `clientboundPlay()` / `serverboundPlay()`，**不是** `playS2C()`
- `RegistryAttributeHolder` 是 `addAttribute` / `hasAttribute`，没有 `getAttribute`
- 流体：`FluidVariantAttributes.getColoredName(FluidVariant)` + `getAssociatedColor(...)`
  （26.2 的 `enableColoredVanillaFluidNames()` 已删除）
- `ItemStack.hurtAndBreak(int, ServerLevel, ServerPlayer, Consumer)`：旧重载
  `hurtAndBreak(int, LivingEntity, EquipmentSlot)` 在 26.3 被 Fabric 直接重定向，别再写旧签名
- MC 侧真实签名：`Item.use(Level, Player, InteractionHand) → InteractionResult`、
  `ServerLevel.addFreshEntity(Entity) → boolean`、`Item.getCraftingRemainder() → ItemStackTemplate`

## 26.2 → 26.3 要改什么

构建配置不用改写法（同为 26.1+ 规则），要改的是**被移除的 API**：

| 26.2 里有 | 26.3 变成 |
|---|---|
| `FuelRegistry` / `FuelValueEvents` | 物品组件 `DataComponents.COOKING_FUEL` |
| `CompostableRegistry` | 物品组件 `DataComponents.COMPOSTABLE` |
| `FabricPotionBrewingBuilder` | `FabricBrewingProvider` |
| `StrippableBlockRegistry` / `TillableBlockRegistry` / `FlattenableBlockRegistry` | 数据驱动的 block transformer（见官方公告） |
| 流体 API（实验性） | 转正，并新增 `isInFluid` / `onFluidEntered` / `onFluidExited` 控制 |

其它新增：`FluidFlowEvents`（流体流动回调）、`TooltipFlag#shouldDisplayAllInformation`、
方块可覆写 `Block#getProvidedEnchantmentPower` 提供附魔威力。

> 以上"移除/新增"是把两个版本的 Fabric API jar 解开后按类名比对出来的，
> 与 [Fabric 26.3 公告](https://fabricmc.net/2026/09/15/263.html) 一致。
> 客户端侧另有 GLFW → SDL 迁移（社区迁移笔记提及，按键常量判断要改用 `InputConstants`），
> 这一条未在本次 jar 比对中直接验证。

## 已核验

- `fabric-api-0.161.0+26.3.jar` sha256 = `86f16178…b657a6`，与 `toolchain/manifest.json` 记录值一致
- jar 内 `fabric.mod.json` 声明 `minecraft ~26.3-`、`fabricloader >=0.19.3`、`java >=25`
- 26.2 有而 26.3 无：`StrippableBlockRegistry`、`TillableBlockRegistry`、`FlattenableBlockRegistry`、`FabricPotionBrewingBuilder`、`CompostableRegistry`、`FuelValueEvents`
- 26.3 新增/存在：`FabricBrewingProvider`、`CreativeModeTabEvents`、`DefaultItemComponentEvents`、`FluidFlowEvents`

详见 `versions.json` 与仓库根目录 `AI_DEV_GUIDE.md`。
