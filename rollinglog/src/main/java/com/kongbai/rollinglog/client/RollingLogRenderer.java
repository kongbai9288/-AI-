package com.kongbai.rollinglog.client;

import com.kongbai.rollinglog.RollingLogEntity;
import net.minecraft.client.render.entity.EntityRenderer;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.entity.state.EntityRenderState;

/**
 * 26.2 渲染架构已重构为 RenderState 模式, 旧的 getTexture() 已移除。
 * 这里用最小实现: 只提供 RenderState, 具体模型留待后续扩展。
 */
public class RollingLogRenderer extends EntityRenderer<RollingLogEntity, EntityRenderState> {

    public RollingLogRenderer(EntityRendererFactory.Context ctx) {
        super(ctx);
    }

    @Override
    public EntityRenderState createRenderState() {
        return new EntityRenderState();
    }
}
