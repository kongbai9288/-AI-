package com.example.aimod;

import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroups;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;

/**
 * 集中注册物品/方块。
 *
 * 注意: Yarn 映射与 Fabric API 会随 MC 小版本变动,
 * 若编译报错请以实际版本的 Yarn 名称为准(用 IDE 补全核对)。
 */
public final class ModContent {

    // ---- 物品 ----
    public static final Item EXAMPLE_ITEM = registerItem(
            "example_item",
            new Item(new Item.Settings()));

    // ---- 方块(同时注册对应的方块物品) ----
    public static final Block EXAMPLE_BLOCK = registerBlock(
            "example_block",
            new Block(AbstractBlock.Settings.create().strength(4.0f).requiresTool()));

    private ModContent() {}

    public static void register() {
        // 加入创造模式物品栏(需要 fabric-api)
        ItemGroupEvents.modifyEntriesEvent(ItemGroups.INGREDIENTS).register(entries -> {
            entries.add(EXAMPLE_ITEM);
            entries.add(EXAMPLE_BLOCK);
        });

        AIMod.LOGGER.info("[{}] 内容注册完成", AIMod.MOD_ID);
    }

    private static <T extends Item> T registerItem(String name, T item) {
        return Registry.register(Registries.ITEM, Identifier.of(AIMod.MOD_ID, name), item);
    }

    private static <T extends Block> T registerBlock(String name, T block) {
        Identifier id = Identifier.of(AIMod.MOD_ID, name);
        T registered = Registry.register(Registries.BLOCK, id, block);
        Registry.register(Registries.ITEM, id, new BlockItem(registered, new Item.Settings()));
        return registered;
    }
}
