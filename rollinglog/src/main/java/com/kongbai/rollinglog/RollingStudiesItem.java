package com.kongbai.rollinglog;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.world.World;

/**
 * 《滚木学》 —— 右键朗诵一条箴言。
 */
public class RollingStudiesItem extends Item {

    public RollingStudiesItem(Settings settings) {
        super(settings);
    }

    @Override
    public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
        ItemStack stack = user.getStackInHand(hand);
        if (!world.isClient()) {
            int i = (int) (Math.random() * RollingLogMod.VERSES.length);
            user.sendMessage(Text.literal(RollingLogMod.VERSES[i]), false);
        }
        return TypedActionResult.success(stack);
    }
}
