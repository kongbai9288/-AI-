package com.kongbai.rollinglog;

import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.MovementType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.TypeFilter;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

import java.util.ArrayList;
import java.util.List;

/**
 * 滚动的原木。
 *
 * 26.2 注意点:
 *  - 拿世界用字段 this.world (26.2 已无 getWorld())
 *  - 伤害 API 变了: damage(ServerWorld, DamageSource, float)
 *  - 实体查询用 collectEntitiesByType(TypeFilter, Box, Predicate, List)
 */
public class RollingLogEntity extends Entity {

    private static final double GRAVITY = 0.045;
    private static final double FRICTION = 0.985;
    private static final float DAMAGE = 6.0f;
    private static final int MAX_LIFE = 240;

    private int life = 0;
    private int spinAccum = 0;

    public RollingLogEntity(EntityType<? extends RollingLogEntity> type, World world) {
        super(type, world);
    }

    /** 由物品调用: 设定初始速度 */
    public void launch(Vec3d dir, double speed) {
        this.setVelocity(dir.x * speed, 0.28, dir.z * speed);
    }

    @Override
    public void tick() {
        super.tick();
        if (this.world.isClient()) {
            return;
        }
        if (++life > MAX_LIFE) {
            this.discard();
            return;
        }

        Vec3d v = this.getVelocity();

        // 重力
        double vy = v.y - GRAVITY;
        if (this.isOnGround()) {
            vy = v.y < -0.12 ? -v.y * 0.32 : 0.0;   // 弹跳并衰减
        }
        double vx = v.x * FRICTION;
        double vz = v.z * FRICTION;

        this.setVelocity(vx, vy, vz);
        this.move(MovementType.field_6308, this.getVelocity());

        // 滚得多快就转得多快(纯视觉, 服务端也算一份以保证同步)
        this.spinAccum += (int) (Math.hypot(vx, vz) * 42);

        // 撞击生物
        Box hitBox = this.getBoundingBox().expand(0.18);
        List<LivingEntity> hits = new ArrayList<>();
        this.world.collectEntitiesByType(
                TypeFilter.instanceOf(LivingEntity.class),
                hitBox,
                e -> e != this && e.isAlive(),
                hits);

        for (LivingEntity target : hits) {
            double dx = target.getX() - this.getX();
            double dz = target.getZ() - this.getZ();
            double len = Math.hypot(dx, dz);
            if (len < 0.0001) {
                dx = 0.01;
                dz = 0.01;
                len = Math.hypot(dx, dz);
            }
            double kx = (dx / len) * 1.35 + vx * 0.55;
            double kz = (dz / len) * 1.35 + vz * 0.55;

            target.damage((ServerWorld) this.world,
                    this.world.getDamageSources().generic(), DAMAGE);
            Vec3d cur = target.getVelocity();
            target.setVelocity(cur.x + kx, Math.max(cur.y, 0.42), cur.z + kz);
        }

        // 停下或掉出世界就消失
        BlockPos pos = BlockPos.ofFloored(this.getX(), this.getY(), this.getZ());
        if (this.getY() < this.world.getBottomY() - 8) {
            this.discard();
            return;
        }
        if (this.isOnGround() && Math.hypot(vx, vz) < 0.045) {
            this.discard();
        }
    }

    public int getSpin() {
        return spinAccum;
    }

    @Override
    protected void initDataTracker(net.minecraft.entity.data.DataTracker.Builder builder) {
        // 无需同步数据
    }

    @Override
    protected void readCustomDataFromNbt(net.minecraft.nbt.NbtCompound nbt,
                                         net.minecraft.registry.RegistryWrapper.WrapperLookup lookup) {
        this.life = nbt.getInt("RollingLife");
    }

    @Override
    protected void writeCustomDataToNbt(net.minecraft.nbt.NbtCompound nbt,
                                        net.minecraft.registry.RegistryWrapper.WrapperLookup lookup) {
        nbt.putInt("RollingLife", this.life);
    }
}
