package com.kongbai.rollinglog;

import com.mojang.brigadier.CommandDispatcher;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroups;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 滚木学 (The Art of Rolling Logs) —— Fabric 26.2
 *
 * 一门关于"让木头滚起来"的学问。
 */
public class RollingLogMod implements ModInitializer {

    public static final String MOD_ID = "rollinglog";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static Item ROLLING_LOG;
    public static Item ROLLING_STUDIES;
    public static EntityType<RollingLogEntity> ROLLING_LOG_ENTITY;

    /** 滚木学箴言 —— 一门严肃学问的严肃结论 */
    public static final String[] VERSES = {
        "§6§l《滚木学》卷一§r：万物皆可滚，只欠一脚。",
        "§6§l《滚木学》卷二§r：木头不会自己滚，但被踢之后会。",
        "§6§l《滚木学》卷三§r：滚动的木头不长苔，正如奔跑的你不长胖。",
        "§6§l《滚木学》卷四§r：斜坡是木头的伯乐，平地是木头的归宿。",
        "§6§l《滚木学》卷五§r：当木头撞上怪物，那不是事故，那是学术成果。",
        "§6§l《滚木学》卷六§r：一根本头能滚多远，取决于你踹得多狠。",
        "§6§l《滚木学》卷七§r：圆者，滚也；方者，卡也。此乃滚木学第一公理。",
        "§6§l《滚木学》卷八§r：若木头停止滚动，请检查它是否变成了箱子。",
        "§6§l《滚木学》卷九§r：滚木不争先，它只是顺着坡，顺便碾过你。",
        "§6§l《滚木学》卷十§r：天下木友一家，滚木学派永存。"
    };

    @Override
    public void onInitialize() {
        LOGGER.info("[{}] 滚木学 · 开课", MOD_ID);

        // ---- 物品 ----
        ROLLING_LOG = registerItem("rolling_log",
                new RollingLogItem(new Item.Settings().maxCount(16)));
        ROLLING_STUDIES = registerItem("rolling_studies",
                new RollingStudiesItem(new Item.Settings().maxCount(1)));

        // ---- 实体 ----
        Identifier entityId = Identifier.of(MOD_ID, "rolling_log");
        ROLLING_LOG_ENTITY = Registry.register(
                Registries.ENTITY_TYPE,
                entityId,
                EntityType.Builder.create(RollingLogEntity::new, SpawnGroup.field_6302)
                        .dimensions(0.98f, 0.98f)
                        .maxTrackingRange(8)
                        .trackingTickInterval(1)
                        .build(RegistryKey.of(RegistryKeys.ENTITY_TYPE, entityId)));

        // ---- 创造模式物品栏 (26.2: CreativeModeTabEvents, 单参回调) ----
        CreativeModeTabEvents.modifyOutputEvent(ItemGroups.NATURAL).register(output -> {
            output.prepend(new ItemStack(ROLLING_LOG));
            output.prepend(new ItemStack(ROLLING_STUDIES));
        });

        // ---- 命令 ----
        CommandRegistrationCallback.EVENT.register(RollingLogMod::registerCommands);

        LOGGER.info("[{}] 滚木学 · 已就绪，共 {} 条箴言", MOD_ID, VERSES.length);
    }

    private static void registerCommands(CommandDispatcher<ServerCommandSource> dispatcher,
                                         Object registryAccess, Object environment) {
        dispatcher.register(CommandManager.literal("gunmu")
                .executes(ctx -> {
                    int i = (int) (Math.random() * VERSES.length);
                    ctx.getSource().sendMessage(Text.literal(VERSES[i]));
                    return 1;
                }));
        dispatcher.register(CommandManager.literal("rollinglog")
                .executes(ctx -> {
                    ctx.getSource().getPlayerOrThrow()
                            .giveItemStack(new ItemStack(ROLLING_LOG, 8));
                    ctx.getSource().sendMessage(Text.literal("§6§l《滚木学》§r：拿去，八根。"));
                    return 1;
                }));
    }

    private static Item registerItem(String name, Item item) {
        return Registry.register(Registries.ITEM, Identifier.of(MOD_ID, name), item);
    }
}
