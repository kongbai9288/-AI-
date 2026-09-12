package com.kongbai.rollinglog.client;

import com.kongbai.rollinglog.RollingLogMod;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;

public class RollingLogClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        RollingLogMod.LOGGER.info("[{}] 客户端初始化", RollingLogMod.MOD_ID);
        EntityRendererRegistry.register(RollingLogMod.ROLLING_LOG_ENTITY, RollingLogRenderer::new);
    }
}
