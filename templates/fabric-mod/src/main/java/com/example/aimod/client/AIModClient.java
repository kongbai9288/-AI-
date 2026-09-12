package com.example.aimod.client;

import com.example.aimod.AIMod;
import net.fabricmc.api.ClientModInitializer;

/**
 * 客户端入口。
 * fabric.mod.json 中 entrypoints.client 指向本类。
 * 只放渲染、按键绑定、GUI 等客户端专属逻辑。
 */
public class AIModClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {
        AIMod.LOGGER.info("[{}] 客户端初始化", AIMod.MOD_ID);

        // 渲染注册、按键绑定等
        // 注意: 不要在此引用服务端专属类(如 MinecraftServer 的实体逻辑)
    }
}
