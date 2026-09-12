package com.kongbai.rollinglog;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

/**
 * 滚木 —— 右键释放一根滚动的原木。
 */
public class RollingLogItem extends Item {

    public RollingLogItem(Settings settings) {
        super(settings);
    }

    @Override
    public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
        ItemStack stack = user.getStackInHand(hand);
        if (world.isClient()) {
            return TypedActionResult.success(stack);
        }

        // 朝向: 玩家视线水平方向
        Vec3d look = user.getRotationVector();
        Vec3d dir = new Vec3d(look.x, 0.0, look.z);
        if (dir.lengthSquared() < 0.0001) {
            dir = new Vec3d(1.0, 0.0, 0.0);
        }
        dir = dir.normalize();

        Vec3d spawnAt = user.getPos()
                .add(dir.multiply(1.1))
                .add(0.0, 0.6, 0.0);

        RollingLogEntity log = new RollingLogEntity(RollingLogMod.ROLLING_LOG_ENTITY, world);
        log.setPos(spawnAt.x, spawnAt.y, spawnAt.z);
        log.launch(dir, 0.92);

        ((ServerWorld) world).spawnNewEntityAndPassengers(log);

        if (!user.isCreative()) {
            stack.decrement(1);
        }
        return TypedActionResult.consume(stack);
    }
}
