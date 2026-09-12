package com.example.aimod;

import net.fabricmc.api.ModInitializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Mod 主入口。
 * fabric.mod.json 中 entrypoints.main 指向本类。
 */
public class AIMod implements ModInitializer {
    public static final String MOD_ID = "aimod";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    @Override
    public void onInitialize() {
        LOGGER.info("[{}] 初始化", MOD_ID);

        // 注册内容（物品/方块/配方…）
        ModContent.register();

        // 在此注册服务器事件、命令、网络包等
        // 示例见 AI_DEV_GUIDE.md
    }
}
