# Minecraft 26.3 版本 API 表

> 本表**全部条目由脚本实测生成**，不是从文档抄的。
> 生成命令：`python3 scripts/verify_api_table.py 26.3`

**实验方法**
- Fabric API 条目：`javap` 直接读 `fabric-api-0.161.0+26.3.jar`（含 43/44 个 jar-in-jar 子模块）的真实签名
- Minecraft 本体条目：`javap -v` 读 fabric-api 的 mixin 注解，从 `@Inject/@Redirect/@Overwrite` 的 `target="Lnet/minecraft/...;method()Desc"` 与 `method="..."` 取出真实 MC 签名（mixin 目标方法写错就注入失败，所以这是硬证据）。本次共采集 626 条注解证据。
- 符号探测条目：在全部子模块的 class 常量池里搜字节串，看该 MC 符号是否被 Fabric 代码引用（**只能证明"被引用"，不能证明"不存在"**，故只做记录不做断言）。

| # | 类别 | API | 预期 | 实测 | 状态 |
|---|---|---|---|---|---|
| 1 | Fabric API | `net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents` | present | present | PASS |
| 2 | Fabric API | `net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents$ModifyOutput` | present | present | PASS |
| 3 | Fabric API | `net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTabOutput` | present | present | PASS |
| 4 | Fabric API | `net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents` | absent | absent | PASS |
| 5 | Fabric API | `net.fabricmc.fabric.api.item.v1.DefaultItemComponentEvents` | present | present | PASS |
| 6 | Fabric API | `net.fabricmc.fabric.api.registry.FuelValueEvents` | absent | absent | PASS |
| 7 | Fabric API | `net.fabricmc.fabric.api.registry.CompostableRegistry` | absent | absent | PASS |
| 8 | Fabric API | `net.fabricmc.fabric.api.registry.FabricPotionBrewingBuilder` | absent | absent | PASS |
| 9 | Fabric API | `net.fabricmc.fabric.api.datagen.v1.provider.FabricBrewingProvider` | present | present | PASS |
| 10 | Fabric API | `net.fabricmc.fabric.api.registry.StrippableBlockRegistry` | absent | absent | PASS |
| 11 | Fabric API | `net.fabricmc.fabric.api.registry.TillableBlockRegistry` | absent | absent | PASS |
| 12 | Fabric API | `net.fabricmc.fabric.api.registry.FlattenableBlockRegistry` | absent | absent | PASS |
| 13 | Fabric API | `net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariantAttributes` | present | present | PASS |
| 14 | Fabric API | `net.fabricmc.fabric.api.block.v1.FluidFlowEvents` | present | present | PASS |
| 15 | Fabric API | `net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback` | present | present | PASS |
| 16 | Fabric API | `net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents` | present | present | PASS |
| 17 | Fabric API | `net.fabricmc.fabric.api.event.player.UseBlockCallback` | present | present | PASS |
| 18 | Fabric API | `net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry` | present | present | PASS |
| 19 | Fabric API | `net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback` | present | present | PASS |
| 20 | Fabric API | `net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents` | present | present | PASS |
| 21 | Fabric API | `net.fabricmc.fabric.api.biome.v1.BiomeModifications` | present | present | PASS |
| 22 | Fabric API | `net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry` | present | present | PASS |
| 23 | Fabric API | `net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry` | present | present | PASS |
| 24 | Fabric API | `net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking` | present | present | PASS |
| 25 | Fabric API | `net.fabricmc.fabric.api.event.registry.RegistryAttributeHolder` | present | present | PASS |
| 26 | MC 本体 | `net/minecraft/world/item/Item.use` | present | present | PASS |
| 27 | MC 本体 | `net/minecraft/server/level/ServerLevel.addFreshEntity` | present | present | PASS |
| 28 | MC 本体 | `net/minecraft/world/level/Level.getBlockState` | present | present | PASS |
| 29 | MC 本体 | `net/minecraft/world/item/ItemStack.hurtAndBreak` | present | present | PASS |
| 30 | MC 本体 | `net/minecraft/world/item/Item.getCraftingRemainder` | present | present | PASS |
| 31 | MC 本体 | `net/minecraft/world/level/block/state/BlockState.isAir` | present | present | PASS |
| 32 | MC 本体 | `net/minecraft/world/level/block/EnchantingTableBlock.isValidBookShelf` | present | present | PASS |
| 33 | MC 本体 | `net/minecraft/world/entity/Entity.readAdditionalSaveData` | present | present | PASS |
| 34 | MC 本体 | `net/minecraft/world/entity/Entity.hurt` | present | no-evidence | UNPROVEN |
| 35 | MC 本体 | `net/minecraft/world/entity/Entity.hurtServer` | present | present(symbol) | PASS |
| 36 | MC 本体 | `net/minecraft/world/entity/Entity.killedEntity` | present | present | PASS |
| 37 | MC 本体 | `net/minecraft/world/item/ItemStack.addToTooltip` | present | present | PASS |
| 38 | MC 本体 | `net/minecraft/client/multiplayer/MultiPlayerGameMode.interact` | present | present | PASS |
| 39 | 符号探测 | `常量池符号 COOKING_FUEL` | info | absent | INFO |
| 40 | 符号探测 | `常量池符号 COMPOSTABLE` | info | present | INFO |
| 41 | 符号探测 | `常量池符号 BREWING_FUEL` | info | absent | INFO |
| 42 | 符号探测 | `常量池符号 getProvidedEnchantmentPower` | info | present | INFO |
| 43 | 符号探测 | `常量池符号 InputConstants` | info | present | INFO |

## 逐条签名与证据

### `creative.tab.events` — net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents

- 预期：present　实测：**present**　状态：**PASS**
- 说明：26.x 的物品栏事件入口
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents
- 实测签名：
  ```
  Compiled from "CreativeModeTabEvents.java"
  public final class net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents {
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents$ModifyOutputAll> MODIFY_OUTPUT_ALL;
  public static net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents$ModifyOutput> modifyOutputEvent(net.minecraft.resources.ResourceKey<net.minecraft.world.item.CreativeModeTab>);
  static {};
  }
  ```

### `creative.tab.modify_output` — net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents$ModifyOutput

- 预期：present　实测：**present**　状态：**PASS**
- 说明：回调接口
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents$ModifyOutput
- 实测签名：
  ```
  Compiled from "CreativeModeTabEvents.java"
  public interface net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents$ModifyOutput {
  public abstract void modifyOutput(net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTabOutput);
  }
  ```

### `creative.tab.output` — net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTabOutput

- 预期：present　实测：**present**　状态：**PASS**
- 说明：往物品栏塞物品
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTabOutput
- 实测签名：
  ```
  Compiled from "FabricCreativeModeTabOutput.java"
  public class net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTabOutput implements net.minecraft.world.item.CreativeModeTab$Output {
  public net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTabOutput(net.minecraft.world.item.CreativeModeTab$ItemDisplayParameters, java.util.List<net.minecraft.world.item.ItemStack>, java.util.List<net.minecraft.world.item.ItemStack>);
  public net.minecraft.world.item.CreativeModeTab$ItemDisplayParameters getContext();
  public net.minecraft.world.flag.FeatureFlagSet getEnabledFeatures();
  public boolean shouldShowOpRestrictedItems();
  public java.util.List<net.minecraft.world.item.ItemStack> getDisplayStacks();
  public java.util.List<net.minecraft.world.item.ItemStack> getSearchTabStacks();
  ```

### `itemgroup.events` — net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents

- 预期：absent　实测：**absent**　状态：**PASS**
- 说明：旧教程里的写法, 实测应当已不存在
- 证据：javap: class not found

### `item.default_components` — net.fabricmc.fabric.api.item.v1.DefaultItemComponentEvents

- 预期：present　实测：**present**　状态：**PASS**
- 说明：给原版/别家物品挂组件
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.item.v1.DefaultItemComponentEvents
- 实测签名：
  ```
  Compiled from "DefaultItemComponentEvents.java"
  public final class net.fabricmc.fabric.api.item.v1.DefaultItemComponentEvents {
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.item.v1.DefaultItemComponentEvents$ModifyCallback> MODIFY;
  static {};
  }
  ```

### `registry.fuel` — net.fabricmc.fabric.api.registry.FuelValueEvents

- 预期：absent　实测：**absent**　状态：**PASS**
- 说明：燃料值事件 (26.3 改 DataComponents.COOKING_FUEL)
- 证据：javap: class not found

### `registry.compostable` — net.fabricmc.fabric.api.registry.CompostableRegistry

- 预期：absent　实测：**absent**　状态：**PASS**
- 说明：堆肥注册 (26.3 改 DataComponents.COMPOSTABLE)
- 证据：javap: class not found

### `registry.brewing.builder` — net.fabricmc.fabric.api.registry.FabricPotionBrewingBuilder

- 预期：absent　实测：**absent**　状态：**PASS**
- 说明：酿造配方构建器 (26.3 移除)
- 证据：javap: class not found

### `datagen.brewing` — net.fabricmc.fabric.api.datagen.v1.provider.FabricBrewingProvider

- 预期：present　实测：**present**　状态：**PASS**
- 说明：26.3 的酿造 datagen provider
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.datagen.v1.provider.FabricBrewingProvider
- 实测签名：
  ```
  Compiled from "FabricBrewingProvider.java"
  public abstract class net.fabricmc.fabric.api.datagen.v1.provider.FabricBrewingProvider extends net.minecraft.data.recipes.BrewingProvider {
  protected net.fabricmc.fabric.api.datagen.v1.provider.FabricBrewingProvider(net.minecraft.data.recipes.RecipeOutput);
  protected void addContainers();
  protected void addContainerTransformations();
  }
  ```

### `registry.strippable` — net.fabricmc.fabric.api.registry.StrippableBlockRegistry

- 预期：absent　实测：**absent**　状态：**PASS**
- 说明：斧头去皮
- 证据：javap: class not found

### `registry.tillable` — net.fabricmc.fabric.api.registry.TillableBlockRegistry

- 预期：absent　实测：**absent**　状态：**PASS**
- 说明：锄头耕地
- 证据：javap: class not found

### `registry.flattenable` — net.fabricmc.fabric.api.registry.FlattenableBlockRegistry

- 预期：absent　实测：**absent**　状态：**PASS**
- 说明：铲子铲平
- 证据：javap: class not found

### `fluid.variant.attributes` — net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariantAttributes

- 预期：present　实测：**present**　状态：**PASS**
- 说明：流体名称/颜色; 26.2 的 enableColoredVanillaFluidNames 在 26.3 换成 getColoredName
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariantAttributes
- 实测签名：
  ```
  Compiled from "FluidVariantAttributes.java"
  public final class net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariantAttributes {
  public static void register(net.minecraft.world.level.material.Fluid, net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariantAttributeHandler);
  public static net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariantAttributeHandler getHandler(net.minecraft.world.level.material.Fluid);
  public static net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariantAttributeHandler getHandlerOrDefault(net.minecraft.world.level.material.Fluid);
  public static net.minecraft.network.chat.Component getName(net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant);
  public static net.minecraft.network.chat.Component getColoredName(net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant);
  public static int getAssociatedColor(net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant);
  ```

### `fluid.flow.events` — net.fabricmc.fabric.api.block.v1.FluidFlowEvents

- 预期：present　实测：**present**　状态：**PASS**
- 说明：流体流动回调
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.block.v1.FluidFlowEvents
- 实测签名：
  ```
  Compiled from "FluidFlowEvents.java"
  public final class net.fabricmc.fabric.api.block.v1.FluidFlowEvents {
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.block.v1.FluidFlowEvents$Allow> ALLOW;
  static {};
  }
  ```

### `command.registration` — net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback

- 预期：present　实测：**present**　状态：**PASS**
- 说明：注册命令
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback
- 实测签名：
  ```
  Compiled from "CommandRegistrationCallback.java"
  public interface net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback {
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback> EVENT;
  public abstract void register(com.mojang.brigadier.CommandDispatcher<net.minecraft.commands.CommandSourceStack>, net.minecraft.commands.CommandBuildContext, net.minecraft.commands.Commands$CommandSelection);
  static {};
  }
  ```

### `server.tick.events` — net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents

- 预期：present　实测：**present**　状态：**PASS**
- 说明：服务端 tick (旧教程的 END_WORLD_TICK 已改名)
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents
- 实测签名：
  ```
  Compiled from "ServerTickEvents.java"
  public final class net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents {
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents$StartTick> START_SERVER_TICK;
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents$EndTick> END_SERVER_TICK;
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents$StartLevelTick> START_LEVEL_TICK;
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents$EndLevelTick> END_LEVEL_TICK;
  static {};
  }
  ```

### `use.block.callback` — net.fabricmc.fabric.api.event.player.UseBlockCallback

- 预期：present　实测：**present**　状态：**PASS**
- 说明：右键方块
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.event.player.UseBlockCallback
- 实测签名：
  ```
  Compiled from "UseBlockCallback.java"
  public interface net.fabricmc.fabric.api.event.player.UseBlockCallback {
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.event.player.UseBlockCallback> EVENT;
  public abstract net.minecraft.world.InteractionResult interact(net.minecraft.world.entity.player.Player, net.minecraft.world.level.Level, net.minecraft.world.InteractionHand, net.minecraft.world.phys.BlockHitResult);
  static {};
  }
  ```

### `entity.renderer.registry` — net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry

- 预期：present　实测：**present**　状态：**PASS**
- 说明：客户端渲染注册
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry
- 实测签名：
  ```
  Compiled from "EntityRendererRegistry.java"
  public final class net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry {
  public static <E extends net.minecraft.world.entity.Entity> void register(net.minecraft.world.entity.EntityType<? extends E>, net.minecraft.client.renderer.entity.EntityRendererProvider<E>);
  }
  ```

### `item.tooltip.callback` — net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback

- 预期：present　实测：**present**　状态：**PASS**
- 说明：tooltip 追加
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback
- 实测签名：
  ```
  Compiled from "ItemTooltipCallback.java"
  public interface net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback {
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback> EVENT;
  public abstract void getTooltip(net.minecraft.world.item.ItemStack, net.minecraft.world.item.Item$TooltipContext, net.minecraft.world.item.TooltipFlag, java.util.List<net.minecraft.network.chat.Component>);
  static {};
  }
  ```

### `living.entity.events` — net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents

- 预期：present　实测：**present**　状态：**PASS**
- 说明：生物死亡/受伤事件
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents
- 实测签名：
  ```
  Compiled from "ServerLivingEntityEvents.java"
  public final class net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents {
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents$AllowDamage> ALLOW_DAMAGE;
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents$AfterDamage> AFTER_DAMAGE;
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents$AllowDeath> ALLOW_DEATH;
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents$AfterDeath> AFTER_DEATH;
  public static final net.fabricmc.fabric.api.event.Event<net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents$MobConversion> MOB_CONVERSION;
  static {};
  ```

### `biome.modifications` — net.fabricmc.fabric.api.biome.v1.BiomeModifications

- 预期：present　实测：**present**　状态：**PASS**
- 说明：加生物生成
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.biome.v1.BiomeModifications
- 实测签名：
  ```
  Compiled from "BiomeModifications.java"
  public final class net.fabricmc.fabric.api.biome.v1.BiomeModifications {
  public static void addFeature(java.util.function.Predicate<net.fabricmc.fabric.api.biome.v1.BiomeSelectionContext>, net.minecraft.world.level.levelgen.GenerationStep$Decoration, net.minecraft.resources.ResourceKey<net.minecraft.world.level.levelgen.placement.PlacedFeature>);
  public static void addCarver(java.util.function.Predicate<net.fabricmc.fabric.api.biome.v1.BiomeSelectionContext>, net.minecraft.resources.ResourceKey<net.minecraft.world.level.levelgen.carver.WorldCarver>);
  public static void addSpawn(java.util.function.Predicate<net.fabricmc.fabric.api.biome.v1.BiomeSelectionContext>, net.minecraft.world.entity.MobCategory, net.minecraft.world.entity.EntityType<?>, int, int, int);
  public static net.fabricmc.fabric.api.biome.v1.BiomeModification create(net.minecraft.resources.Identifier);
  }
  ```

### `attachment.registry` — net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry

- 预期：present　实测：**present**　状态：**PASS**
- 说明：数据挂载 (新 API)
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry
- 实测签名：
  ```
  Compiled from "AttachmentRegistry.java"
  public final class net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry {
  public static <A> net.fabricmc.fabric.api.attachment.v1.AttachmentType<A> create(net.minecraft.resources.Identifier, java.util.function.Consumer<net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry$Builder<A>>);
  public static <A> net.fabricmc.fabric.api.attachment.v1.AttachmentType<A> create(net.minecraft.resources.Identifier);
  public static <A> net.fabricmc.fabric.api.attachment.v1.AttachmentType<A> createDefaulted(net.minecraft.resources.Identifier, java.util.function.Supplier<A>);
  public static <A> net.fabricmc.fabric.api.attachment.v1.AttachmentType<A> createPersistent(net.minecraft.resources.Identifier, com.mojang.serialization.Codec<A>);
  public static <A> net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry$Builder<A> builder();
  }
  ```

### `networking.payload` — net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry

- 预期：present　实测：**present**　状态：**PASS**
- 说明：自定义包类型 (旧名 playS2C 已改)
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry
- 实测签名：
  ```
  Compiled from "PayloadTypeRegistry.java"
  public interface net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry<B extends net.minecraft.network.FriendlyByteBuf> {
  public abstract <T extends net.minecraft.network.protocol.common.custom.CustomPacketPayload> net.minecraft.network.protocol.common.custom.CustomPacketPayload$TypeAndCodec<? super B, T> register(net.minecraft.network.protocol.common.custom.CustomPacketPayload$Type<T>, net.minecraft.network.codec.StreamCodec<? super B, T>);
  public abstract <T extends net.minecraft.network.protocol.common.custom.CustomPacketPayload> net.minecraft.network.protocol.common.custom.CustomPacketPayload$TypeAndCodec<? super B, T> registerLarge(net.minecraft.network.protocol.common.custom.CustomPacketPayload$Type<T>, net.minecraft.network.codec.StreamCodec<? super B, T>, int);
  public abstract <T extends net.minecraft.network.protocol.common.custom.CustomPacketPayload> net.minecraft.network.protocol.common.custom.CustomPacketPayload$TypeAndCodec<? super B, T> registerLarge(net.minecraft.network.protocol.common.custom.CustomPacketPayload$Type<T>, net.minecraft.network.codec.StreamCodec<? super B, T>, java.util.function.IntSupplier);
  public static net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry<net.minecraft.network.FriendlyByteBuf> serverboundConfiguration();
  public static net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry<net.minecraft.network.FriendlyByteBuf> clientboundConfiguration();
  public static net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry<net.minecraft.network.RegistryFriendlyByteBuf> serverboundPlay();
  ```

### `networking.server` — net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking

- 预期：present　实测：**present**　状态：**PASS**
- 说明：发包给客户端
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking
- 实测签名：
  ```
  Compiled from "ServerPlayNetworking.java"
  public final class net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking {
  public static <T extends net.minecraft.network.protocol.common.custom.CustomPacketPayload> boolean registerGlobalReceiver(net.minecraft.network.protocol.common.custom.CustomPacketPayload$Type<T>, net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking$PlayPayloadHandler<T>);
  public static net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking$PlayPayloadHandler<?> unregisterGlobalReceiver(net.minecraft.resources.Identifier);
  public static java.util.Set<net.minecraft.resources.Identifier> getGlobalReceivers();
  public static <T extends net.minecraft.network.protocol.common.custom.CustomPacketPayload> boolean registerReceiver(net.minecraft.server.network.ServerGamePacketListenerImpl, net.minecraft.network.protocol.common.custom.CustomPacketPayload$Type<T>, net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking$PlayPayloadHandler<T>);
  public static net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking$PlayPayloadHandler<?> unregisterReceiver(net.minecraft.server.network.ServerGamePacketListenerImpl, net.minecraft.resources.Identifier);
  public static java.util.Set<net.minecraft.resources.Identifier> getReceived(net.minecraft.server.level.ServerPlayer);
  ```

### `registry.attributes` — net.fabricmc.fabric.api.event.registry.RegistryAttributeHolder

- 预期：present　实测：**present**　状态：**PASS**
- 说明：注册表属性
- 证据：javap -cp <fabric-api-0.161.0+26.3.jar 子模块> net.fabricmc.fabric.api.event.registry.RegistryAttributeHolder
- 实测签名：
  ```
  Compiled from "RegistryAttributeHolder.java"
  public interface net.fabricmc.fabric.api.event.registry.RegistryAttributeHolder {
  public static net.fabricmc.fabric.api.event.registry.RegistryAttributeHolder get(net.minecraft.resources.ResourceKey<?>);
  public static net.fabricmc.fabric.api.event.registry.RegistryAttributeHolder get(net.minecraft.core.Registry<?>);
  public abstract net.fabricmc.fabric.api.event.registry.RegistryAttributeHolder addAttribute(net.fabricmc.fabric.api.event.registry.RegistryAttribute);
  public abstract boolean hasAttribute(net.fabricmc.fabric.api.event.registry.RegistryAttribute);
  }
  ```

### `mc.item.use` — net/minecraft/world/item/Item.use

- 预期：present　实测：**present**　状态：**PASS**
- 说明：物品右键 (guide 里的写法靠这条验证)
- 证据：mixin 注解 target=Lnet/minecraft/world/item/Item;use(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/InteractionResult; (来自 net.fabricmc.fabric.mixin.event.interaction.ItemStackMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/item/Item;use(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/InteractionResult;
  ```

### `mc.serverlevel.addfreshentity` — net/minecraft/server/level/ServerLevel.addFreshEntity

- 预期：present　实测：**present**　状态：**PASS**
- 说明：生成实体, 只有 ServerLevel 有
- 证据：mixin 注解 target=Lnet/minecraft/server/level/ServerLevel;addFreshEntity(Lnet/minecraft/world/entity/Entity;)Z (来自 net.fabricmc.fabric.mixin.entity.event.MobMixin)
- 实测签名：
  ```
  Lnet/minecraft/server/level/ServerLevel;addFreshEntity(Lnet/minecraft/world/entity/Entity;)Z
  ```

### `mc.level.getblockstate` — net/minecraft/world/level/Level.getBlockState

- 预期：present　实测：**present**　状态：**PASS**
- 说明：取方块状态
- 证据：mixin 注解 target=Lnet/minecraft/world/level/Level;getBlockState(Lnet/minecraft/core/BlockPos;)Lnet/minecraft/world/level/block/state/BlockState; (来自 net.fabricmc.fabric.mixin.block.LivingEntityMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/level/Level;getBlockState(Lnet/minecraft/core/BlockPos;)Lnet/minecraft/world/level/block/state/BlockState;
  ```

### `mc.itemstack.hurtandbreak` — net/minecraft/world/item/ItemStack.hurtAndBreak

- 预期：present　实测：**present**　状态：**PASS**
- 说明：物品耐久消耗, 26.x 带 ServerLevel 参数
- 证据：mixin 注解 target=Lnet/minecraft/world/item/ItemStack;hurtAndBreak(ILnet/minecraft/server/level/ServerLevel;Lnet/minecraft/server/level/ServerPlayer;Ljava/util/function/Consumer;)V (来自 net.fabricmc.fabric.mixin.item.ItemStackMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/item/ItemStack;hurtAndBreak(ILnet/minecraft/server/level/ServerLevel;Lnet/minecraft/server/level/ServerPlayer;Ljava/util/function/Consumer;)V
  ```

### `mc.item.craftingremainder` — net/minecraft/world/item/Item.getCraftingRemainder

- 预期：present　实测：**present**　状态：**PASS**
- 说明：合成剩余物, 26.2→26.3 返回类型有变化
- 证据：mixin 注解 target=Lnet/minecraft/world/item/Item;getCraftingRemainder()Lnet/minecraft/world/item/ItemStackTemplate; (来自 net.fabricmc.fabric.mixin.item.AbstractFurnaceBlockEntityMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/item/Item;getCraftingRemainder()Lnet/minecraft/world/item/ItemStackTemplate;
  ```

### `mc.blockstate.isair` — net/minecraft/world/level/block/state/BlockState.isAir

- 预期：present　实测：**present**　状态：**PASS**
- 说明：是否空气
- 证据：mixin 注解 target=Lnet/minecraft/world/level/block/state/BlockState;isAir()Z (来自 net.fabricmc.fabric.mixin.block.ChunkSectionBlockStateCounterMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/level/block/state/BlockState;isAir()Z
  ```

### `mc.enchantingtable.isvalidbookshelf` — net/minecraft/world/level/block/EnchantingTableBlock.isValidBookShelf

- 预期：present　实测：**present**　状态：**PASS**
- 说明：书架判定, 26.3 新增 getProvidedEnchantmentPower 的相关路径
- 证据：mixin 注解 target=Lnet/minecraft/world/level/block/EnchantingTableBlock;isValidBookShelf(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/core/BlockPos;)Z (来自 net.fabricmc.fabric.mixin.block.EnchantmentMenuMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/level/block/EnchantingTableBlock;isValidBookShelf(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/core/BlockPos;)Z
  ```

### `mc.entity.readadditional` — net/minecraft/world/entity/Entity.readAdditionalSaveData

- 预期：present　实测：**present**　状态：**PASS**
- 说明：实体读存档
- 证据：mixin 注解 target=Lnet/minecraft/world/entity/Entity;readAdditionalSaveData(Lnet/minecraft/world/level/storage/ValueInput;)V (来自 net.fabricmc.fabric.mixin.attachment.EntityMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/entity/Entity;readAdditionalSaveData(Lnet/minecraft/world/level/storage/ValueInput;)V
  ```

### `mc.entity.hurt` — net/minecraft/world/entity/Entity.hurt

- 预期：present　实测：**no-evidence**　状态：**UNPROVEN**
- 说明：受伤入口 (guide 里的写法靠这条验证)
- 证据：未匹配到: 231 条 target / 395 条 method 证据中无 net/minecraft/world/entity/Entity.hurt

### `mc.entity.hurtserver` — net/minecraft/world/entity/Entity.hurtServer

- 预期：present　实测：**present(symbol)**　状态：**PASS**
- 说明：26.x 的服务端侧受伤方法
- 证据：mixin 注解 method=hurtServer (来自 net.fabricmc.fabric.mixin.entity.event.LivingEntityMixin)
- 实测签名：
  ```
  hurtServer
  ```

### `mc.entity.killedentity` — net/minecraft/world/entity/Entity.killedEntity

- 预期：present　实测：**present**　状态：**PASS**
- 说明：击杀回调 (fabric 死亡事件用它)
- 证据：mixin 注解 target=Lnet/minecraft/world/entity/Entity;killedEntity(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/damagesource/DamageSource;)Z (来自 net.fabricmc.fabric.mixin.entity.event.LivingEntityMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/entity/Entity;killedEntity(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/damagesource/DamageSource;)Z
  ```

### `mc.itemstack.addtotooltip` — net/minecraft/world/item/ItemStack.addToTooltip

- 预期：present　实测：**present**　状态：**PASS**
- 说明：tooltip 构建 (ItemTooltipCallback 的注入点)
- 证据：mixin 注解 target=Lnet/minecraft/world/item/ItemStack;addToTooltip(Lnet/minecraft/core/component/DataComponentType;Lnet/minecraft/world/item/Item$TooltipContext;Lnet/minecraft/world/item/component/TooltipDisplay;Ljava/util/function/Consumer;Lnet/minecraft/world/item/TooltipFlag;)V (来自 net.fabricmc.fabric.mixin.item.ItemStackMixin)
- 实测签名：
  ```
  Lnet/minecraft/world/item/ItemStack;addToTooltip(Lnet/minecraft/core/component/DataComponentType;Lnet/minecraft/world/item/Item$TooltipContext;Lnet/minecraft/world/item/component/TooltipDisplay;Ljava/util/function/Consumer;Lnet/minecraft/world/item/TooltipFlag;)V
  ```

### `mc.gamemode.interact` — net/minecraft/client/multiplayer/MultiPlayerGameMode.interact

- 预期：present　实测：**present**　状态：**PASS**
- 说明：客户端交互
- 证据：mixin 注解 target=Lnet/minecraft/client/multiplayer/MultiPlayerGameMode;interact(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/phys/EntityHitResult;Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/InteractionResult; (来自 net.fabricmc.fabric.mixin.event.interaction.client.MinecraftMixin)
- 实测签名：
  ```
  Lnet/minecraft/client/multiplayer/MultiPlayerGameMode;interact(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/phys/EntityHitResult;Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/InteractionResult;
  ```

### `symbol.cooking_fuel` — 常量池符号 COOKING_FUEL

- 预期：info　实测：**absent**　状态：**INFO**
- 说明：26.3 燃料改用 DataComponents.COOKING_FUEL, 26.2 用 FuelRegistry 所以不该出现
- 证据：全部 44 个子模块中未出现 "COOKING_FUEL"

### `symbol.compostable` — 常量池符号 COMPOSTABLE

- 预期：info　实测：**present**　状态：**INFO**
- 说明：26.3 堆肥改用 DataComponents.COMPOSTABLE
- 证据：2 个 fabric class 的常量池里出现符号 "COMPOSTABLE"
- 实测签名：
  ```
  fabric-content-registries-v0-15.0.4+74ed1ea55d.jar!net.fabricmc.fabric.mixin.content.registry.WorkAtComposterAccessor
  fabric-transfer-api-v1-8.0.25+fcdff87f5d.jar!net.fabricmc.fabric.impl.transfer.item.ComposterWrapper$TopStorage
  ```

### `symbol.brewing_fuel` — 常量池符号 BREWING_FUEL

- 预期：info　实测：**absent**　状态：**INFO**
- 说明：26.3 酿造燃料组件
- 证据：全部 44 个子模块中未出现 "BREWING_FUEL"

### `symbol.enchantment_power` — 常量池符号 getProvidedEnchantmentPower

- 预期：info　实测：**present**　状态：**INFO**
- 说明：26.3 新增: 方块可覆写提供附魔威力
- 证据：3 个 fabric class 的常量池里出现符号 "getProvidedEnchantmentPower"
- 实测签名：
  ```
  fabric-block-api-v1-3.1.0+0ae6f9115d.jar!net.fabricmc.fabric.api.block.v1.FabricBlock
  fabric-block-api-v1-3.1.0+0ae6f9115d.jar!net.fabricmc.fabric.api.block.v1.FabricBlockState
  fabric-block-api-v1-3.1.0+0ae6f9115d.jar!net.fabricmc.fabric.mixin.block.EnchantmentMenuMixin
  ```

### `symbol.inputconstants` — 常量池符号 InputConstants

- 预期：info　实测：**present**　状态：**INFO**
- 说明：26.3 客户端 GLFW→SDL 迁移后按键常量应走这个类
- 证据：3 个 fabric class 的常量池里出现符号 "InputConstants"
- 实测签名：
  ```
  fabric-creative-tab-api-v1-5.0.21+fcdff87f5d.jar!net.fabricmc.fabric.mixin.creativetab.client.CreativeModeInventoryScreenMixin
  fabric-key-mapping-api-v1-2.0.8+3434d6d95d.jar!net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper
  fabric-key-mapping-api-v1-2.0.8+3434d6d95d.jar!net.fabricmc.fabric.mixin.client.keymapping.KeyMappingAccessor
  ```
