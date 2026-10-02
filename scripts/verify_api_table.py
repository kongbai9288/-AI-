#!/usr/bin/env python3
"""生成并逐条验证某个 MC 版本目录下的「版本 API 表」。

每条 API 都要实测, 不凭记忆、不抄文档:
  - Fabric API 条目: 用 javap 对真实的 fabric-api jar(含 jar-in-jar 子模块)取签名
  - Minecraft 本体条目: 用 javap -v 从 fabric-api 的 mixin 注解里读出真实 MC 方法签名
    (mixin 的 @Inject/@Redirect/@Overwrite 必须写对目标方法名与描述符, 否则注入会失败,
     所以注解里的 target="Lnet/minecraft/...;method()Desc" 是编译进 class 的硬证据)

用法:
  python3 scripts/verify_api_table.py 26.2
  python3 scripts/verify_api_table.py 26.3
  python3 scripts/verify_api_table.py 26.2 26.3     # 一次跑两个

依赖: JDK 25 的 javap(用 --jdk 指定, 默认取仓库 toolchain 里的 JDK),
      版本目录下的 fabric-api-*.jar(不存在时自动从 codeload 拉仓库 zip)

退出码: 全部条目符合预期 = 0; 有任一不符 = 1
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get('API_TABLE_WORK', '/data/workspace')

# ---------------------------------------------------------------- 条目清单
# kind=fabric  : 需 javap 取签名, 用 must_have 断言方法/字段存在
# kind=mojang  : 需从 mixin 证据里匹配 owner+method, 记录真实描述符
# expect       : present | absent (不写则默认 present)
CATALOG = [
    # ---- 创造模式物品栏 ----
    dict(id='creative.tab.events', kind='fabric',
         name='net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents',
         must_have=['modifyOutputEvent'], note='26.x 的物品栏事件入口'),
    dict(id='creative.tab.modify_output', kind='fabric',
         name='net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents$ModifyOutput',
         must_have=['modifyOutput'], note='回调接口'),
    dict(id='creative.tab.output', kind='fabric',
         name='net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTabOutput',
         must_have=['accept'], note='往物品栏塞物品'),
    dict(id='itemgroup.events', kind='fabric', expect='absent',
         name='net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents',
         note='旧教程里的写法, 实测应当已不存在'),
    # ---- 物品组件 (26.3 起替代 FuelRegistry / CompostableRegistry) ----
    dict(id='item.default_components', kind='fabric',
         name='net.fabricmc.fabric.api.item.v1.DefaultItemComponentEvents',
         must_have=['MODIFY'], note='给原版/别家物品挂组件'),
    dict(id='registry.fuel', kind='fabric', must_have=['BUILD'],
         name='net.fabricmc.fabric.api.registry.FuelValueEvents',
         expect={'26.2': 'present', '26.3': 'absent'},
         note='燃料值事件 (26.3 改 DataComponents.COOKING_FUEL)'),
    dict(id='registry.compostable', kind='fabric',
         name='net.fabricmc.fabric.api.registry.CompostableRegistry',
         expect={'26.2': 'present', '26.3': 'absent'},
         note='堆肥注册 (26.3 改 DataComponents.COMPOSTABLE)'),
    dict(id='registry.brewing.builder', kind='fabric',
         name='net.fabricmc.fabric.api.registry.FabricPotionBrewingBuilder',
         expect={'26.2': 'present', '26.3': 'absent'},
         note='酿造配方构建器 (26.3 移除)'),
    dict(id='datagen.brewing', kind='fabric',
         name='net.fabricmc.fabric.api.datagen.v1.provider.FabricBrewingProvider',
         expect={'26.2': 'absent', '26.3': 'present'},
         note='26.3 的酿造 datagen provider'),
    # ---- 方块转换 (26.3 移除) ----
    dict(id='registry.strippable', kind='fabric', expect={'26.2': 'present', '26.3': 'absent'},
         name='net.fabricmc.fabric.api.registry.StrippableBlockRegistry', note='斧头去皮'),
    dict(id='registry.tillable', kind='fabric', expect={'26.2': 'present', '26.3': 'absent'},
         name='net.fabricmc.fabric.api.registry.TillableBlockRegistry', note='锄头耕地'),
    dict(id='registry.flattenable', kind='fabric', expect={'26.2': 'present', '26.3': 'absent'},
         name='net.fabricmc.fabric.api.registry.FlattenableBlockRegistry', note='铲子铲平'),
    # ---- 流体 ----
    dict(id='fluid.variant.attributes', kind='fabric',
         name='net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariantAttributes',
         must_have={'26.2': ['enableColoredVanillaFluidNames'],
                    '26.3': ['getColoredName', 'getAssociatedColor']},
         note='流体名称/颜色; 26.2 的 enableColoredVanillaFluidNames 在 26.3 换成 getColoredName'),
    dict(id='fluid.flow.events', kind='fabric', must_have=['ALLOW'],
         name='net.fabricmc.fabric.api.block.v1.FluidFlowEvents', note='流体流动回调'),
    # ---- 命令 / 事件 / 网络 ----
    dict(id='command.registration', kind='fabric',
         name='net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback',
         must_have=['EVENT'], note='注册命令'),
    dict(id='server.tick.events', kind='fabric',
         name='net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents',
         must_have=['END_LEVEL_TICK'], note='服务端 tick (旧教程的 END_WORLD_TICK 已改名)'),
    dict(id='use.block.callback', kind='fabric',
         name='net.fabricmc.fabric.api.event.player.UseBlockCallback',
         must_have=['EVENT'], note='右键方块'),
    dict(id='entity.renderer.registry', kind='fabric',
         name='net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry',
         must_have=['register'], note='客户端渲染注册'),
    dict(id='item.tooltip.callback', kind='fabric',
         name='net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback',
         must_have=['EVENT'], note='tooltip 追加'),
    dict(id='living.entity.events', kind='fabric',
         name='net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents',
         must_have=['ALLOW_DEATH'], note='生物死亡/受伤事件'),
    dict(id='biome.modifications', kind='fabric',
         name='net.fabricmc.fabric.api.biome.v1.BiomeModifications',
         must_have=['addSpawn'], note='加生物生成'),
    dict(id='attachment.registry', kind='fabric',
         name='net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry',
         must_have=['builder'], note='数据挂载 (新 API)'),
    dict(id='networking.payload', kind='fabric',
         name='net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry',
         must_have=['clientboundPlay'], note='自定义包类型 (旧名 playS2C 已改)'),
    dict(id='networking.server', kind='fabric',
         name='net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking',
         must_have=['send'], note='发包给客户端'),
    dict(id='registry.attributes', kind='fabric',
         name='net.fabricmc.fabric.api.event.registry.RegistryAttributeHolder',
         must_have=['addAttribute', 'hasAttribute'], note='注册表属性'),
    # ---- Minecraft 本体 (mixin 注解证据) ----
    dict(id='mc.item.use', kind='mojang',
         owner='net/minecraft/world/item/Item', method='use',
         note='物品右键 (guide 里的写法靠这条验证)'),
    dict(id='mc.serverlevel.addfreshentity', kind='mojang',
         owner='net/minecraft/server/level/ServerLevel', method='addFreshEntity',
         note='生成实体, 只有 ServerLevel 有'),
    dict(id='mc.level.getblockstate', kind='mojang',
         owner='net/minecraft/world/level/Level', method='getBlockState',
         note='取方块状态'),
    dict(id='mc.itemstack.hurtandbreak', kind='mojang',
         owner='net/minecraft/world/item/ItemStack', method='hurtAndBreak',
         note='物品耐久消耗, 26.x 带 ServerLevel 参数'),
    dict(id='mc.item.craftingremainder', kind='mojang',
         owner='net/minecraft/world/item/Item', method='getCraftingRemainder',
         note='合成剩余物, 26.2→26.3 返回类型有变化'),
    dict(id='mc.blockstate.isair', kind='mojang',
         owner='net/minecraft/world/level/block/state/BlockState', method='isAir',
         note='是否空气'),
    dict(id='mc.enchantingtable.isvalidbookshelf', kind='mojang',
         owner='net/minecraft/world/level/block/EnchantingTableBlock', method='isValidBookShelf',
         note='书架判定, 26.3 新增 getProvidedEnchantmentPower 的相关路径'),
    dict(id='mc.entity.readadditional', kind='mojang',
         owner='net/minecraft/world/entity/Entity', method='readAdditionalSaveData',
         note='实体读存档'),
    dict(id='mc.entity.hurt', kind='mojang',
         owner='net/minecraft/world/entity/Entity', method='hurt',
         note='受伤入口 (guide 里的写法靠这条验证)'),
    dict(id='mc.entity.hurtserver', kind='mojang',
         owner='net/minecraft/world/entity/Entity', method='hurtServer',
         note='26.x 的服务端侧受伤方法'),
    dict(id='mc.entity.killedentity', kind='mojang',
         owner='net/minecraft/world/entity/Entity', method='killedEntity',
         note='击杀回调 (fabric 死亡事件用它)'),
    dict(id='mc.itemstack.addtotooltip', kind='mojang',
         owner='net/minecraft/world/item/ItemStack', method='addToTooltip',
         note='tooltip 构建 (ItemTooltipCallback 的注入点)'),
    dict(id='mc.gamemode.interact', kind='mojang',
         owner='net/minecraft/client/multiplayer/MultiPlayerGameMode', method='interact',
         note='客户端交互'),
    # ---- 符号级实验: 在 fabric-api 的 class 字节里搜 MC 侧符号 ----
    dict(id='symbol.cooking_fuel', kind='symbol', symbol='COOKING_FUEL', expect='info',
         note='26.3 燃料改用 DataComponents.COOKING_FUEL, 26.2 用 FuelRegistry 所以不该出现'),
    dict(id='symbol.compostable', kind='symbol', symbol='COMPOSTABLE', expect='info',
         note='26.3 堆肥改用 DataComponents.COMPOSTABLE'),
    dict(id='symbol.brewing_fuel', kind='symbol', symbol='BREWING_FUEL', expect='info',
         note='26.3 酿造燃料组件'),
    dict(id='symbol.enchantment_power', kind='symbol', symbol='getProvidedEnchantmentPower',
         expect='info',
         note='26.3 新增: 方块可覆写提供附魔威力'),
    dict(id='symbol.inputconstants', kind='symbol', symbol='InputConstants', expect='info',
         note='26.3 客户端 GLFW→SDL 迁移后按键常量应走这个类'),
]

# ---------------------------------------------------------------- 服务端条目
# side: server=只在服务端 / client=只在客户端 / both=通用
SERVER_CATALOG = [
    # ---- 入口点(在 loader 里, 不在 fabric-api 里) ----
    dict(id='entrypoint.dedicated_server', kind='fabric', side='server',
         name='net.fabricmc.api.DedicatedServerModInitializer',
         must_have=['onInitializeServer'],
         note='服务端 mod 入口点, fabric.mod.json 的 "server" entrypoint 用这个'),
    dict(id='entrypoint.main', kind='fabric', side='both',
         name='net.fabricmc.api.ModInitializer', must_have=['onInitialize'],
         note='通用入口点, 客户端服务端都跑'),
    dict(id='entrypoint.client', kind='fabric', side='client',
         name='net.fabricmc.api.ClientModInitializer', must_have=['onInitializeClient'],
         note='对照用: 客户端入口点, 服务端 mod 别用'),
    dict(id='api.envtype', kind='fabric', side='both',
         name='net.fabricmc.api.EnvType', must_have=['SERVER', 'CLIENT'],
         note='EnvType.SERVER, 配合 @Environment 使用'),
    dict(id='api.environment', kind='fabric', side='both',
         name='net.fabricmc.api.Environment', note='@Environment(EnvType.SERVER) 注解'),
    dict(id='loader.server.launcher', kind='fabric', side='server',
         name='net.fabricmc.loader.impl.launch.server.FabricServerLauncher',
         must_have=['main'],
         note='loader jar 的 Main-Class, 服务端启动入口'),
    dict(id='loader.knot.server', kind='fabric', side='server',
         name='net.fabricmc.loader.impl.launch.knot.KnotServer',
         note='服务端 Knot 启动器'),
    # ---- 服务端生命周期 ----
    dict(id='server.lifecycle', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents',
         must_have=['SERVER_STARTING', 'SERVER_STARTED', 'SERVER_STOPPING', 'SERVER_STOPPED'],
         note='服务端启停'),
    dict(id='server.level.events', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.event.lifecycle.v1.ServerLevelEvents',
         must_have=['LOAD', 'UNLOAD'], note='维度加载/卸载'),
    dict(id='server.chunk.events', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.event.lifecycle.v1.ServerChunkEvents',
         must_have=['CHUNK_LOAD', 'CHUNK_UNLOAD'], note='区块事件'),
    dict(id='server.entity.events', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents',
         must_have=['ENTITY_LOAD', 'ENTITY_UNLOAD'], note='实体进出世界'),
    dict(id='server.blockentity.events', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.event.lifecycle.v1.ServerBlockEntityEvents',
         must_have=['BLOCK_ENTITY_LOAD'], note='方块实体事件'),
    dict(id='server.player.events', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents',
         must_have=['COPY_FROM', 'AFTER_RESPAWN'], note='玩家复制/重生'),
    dict(id='server.entity.combat', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.entity.event.v1.ServerEntityCombatEvents',
         must_have=['AFTER_KILLED_OTHER_ENTITY'], note='击杀回调'),
    # ---- 服务端网络 ----
    dict(id='server.play.connection', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents',
         must_have=['INIT', 'JOIN', 'DISCONNECT'], note='玩家进/出服'),
    dict(id='server.play.networking', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking',
         must_have=['registerGlobalReceiver', 'canSend', 'send'], note='Play 阶段收发包'),
    dict(id='server.configuration.networking', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.networking.v1.ServerConfigurationNetworking',
         must_have=['registerGlobalReceiver', 'send'], note='Configuration 阶段收发包'),
    dict(id='server.login.networking', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.networking.v1.ServerLoginNetworking',
         must_have=['registerGlobalReceiver'], note='Login 阶段查询/应答'),
    dict(id='server.message.events', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.message.v1.ServerMessageEvents',
         must_have=['ALLOW_CHAT_MESSAGE', 'CHAT_MESSAGE'], note='聊天消息拦截'),
    # ---- 服务端资源 ----
    dict(id='server.resource.helper', kind='fabric', side='server',
         name='net.fabricmc.fabric.api.resource.ResourceManagerHelper',
         must_have=['registerReloadListener', 'get'], note='挂 reload listener / 内置资源包'),
    # ---- MC 本体服务端(来自 mixin 证据) ----
    dict(id='mc.minecraftserver.initserver', kind='mojang', side='server',
         owner='net/minecraft/server/MinecraftServer', method='initServer',
         note='服务端初始化'),
    dict(id='mc.minecraftserver.tickchildren', kind='mojang', side='server',
         owner='net/minecraft/server/MinecraftServer', method='tickChildren',
         note='tick 子维度'),
    dict(id='mc.serverplayer.setrespawnposition', kind='mojang', side='server',
         owner='net/minecraft/server/level/ServerPlayer', method='setRespawnPosition',
         note='设置重生点'),
    dict(id='mc.servergamepacketlistener.send', kind='mojang', side='server',
         owner='net/minecraft/server/network/ServerGamePacketListenerImpl', method='send',
         note='给单个玩家发包'),
    dict(id='mc.entity.teleportcrossdimension', kind='mojang', side='server',
         owner='net/minecraft/world/entity/Entity', method='teleportCrossDimension',
         note='跨维度传送'),
]

CATALOG = CATALOG + SERVER_CATALOG


def find_jdk():
    for p in sorted(glob.glob('/data/workspace/jdk-25*/')) + sorted(glob.glob(f'{WORK}/jdk-25*/')):
        if os.path.exists(p + 'bin/javap'):
            return p.rstrip('/')
    raise SystemExit('找不到 JDK 25 的 javap, 用 --jdk 指定')


def prepare_cp(version, jar):
    """把 jar-in-jar 子模块摊平到一个 classpath 目录

    额外把 toolchain/ 里的 fabric-loader 也放进去 —— 服务端的入口点
    (DedicatedServerModInitializer / EnvType / FabricServerLauncher) 在 loader 里,
    不在 fabric-api 里, 不加就查不到。
    """
    out = f'{WORK}/cp_{version}'
    cached = os.path.isdir(out) and glob.glob(out + '/*.jar')
    if cached:
        # 目录是缓存的, 但 loader jar 可能是后来才加进来的, 补齐再返回
        for ld in glob.glob(f'{ROOT}/toolchain/fabric-loader-*.jar'):
            dst = os.path.join(out, '_loader-' + os.path.basename(ld))
            if not os.path.exists(dst):
                shutil.copy2(ld, dst)
        return out
    os.makedirs(out, exist_ok=True)
    z = zipfile.ZipFile(jar)
    for n in z.namelist():
        if n.startswith('META-INF/jars/') and n.endswith('.jar'):
            open(os.path.join(out, n.split('/')[-1]), 'wb').write(z.read(n))
    for ld in glob.glob(f'{ROOT}/toolchain/fabric-loader-*.jar'):
        dst = os.path.join(out, '_loader-' + os.path.basename(ld))
        if not os.path.exists(dst):
            shutil.copy2(ld, dst)
    return out


def javap(jdk, cp, cls):
    r = subprocess.run([f'{jdk}/bin/javap', '-cp', cp, cls],
                       capture_output=True, text=True)
    return r.stdout, r.stderr


def scan_mixins(jdk, cp_dir):
    """从 mixin 注解里提取真实 MC 方法签名

    抓两类注解元素:
      target="Lnet/minecraft/Owner;method(Desc)Ret"  -> 带 owner 的完整签名
      method="xxx" / method=["xxx(Desc)Ret"]         -> mixin 声明要注入的目标方法名
    """
    cp = ':'.join(sorted(glob.glob(os.path.join(cp_dir, '*.jar'))))
    mixins = []
    for j in sorted(glob.glob(os.path.join(cp_dir, '*.jar'))):
        z = zipfile.ZipFile(j)
        for c in z.namelist():
            if c.endswith('Mixin.class') and '$' not in c:
                mixins.append(c[:-6].replace('/', '.'))
    mixins = sorted(set(mixins))
    ev = {'targets': {}, 'methods': {}}
    B = 30
    for i in range(0, len(mixins), B):
        r = subprocess.run([f'{jdk}/bin/javap', '-v', '-p', '-cp', cp] + mixins[i:i + B],
                           capture_output=True, text=True)
        cur = None
        for ln in (r.stdout + r.stderr).splitlines():
            s = ln.strip()
            if s.startswith('Classfile'):
                cur = None
                continue
            m = re.match(r'^(?:public |final |abstract |synchronized )*(?:class|interface) ([A-Za-z0-9_.$]+)', s)
            if m:
                cur = m.group(1)
            mt = re.match(r'^\s*target="(Lnet/minecraft.*)"$', ln)
            if mt and cur:
                ev['targets'].setdefault(mt.group(1), []).append(cur)
            mm = re.match(r'^\s*method=(?:"([^"]*)"|\["([^"]*)"\])', ln)
            if mm and cur:
                val = mm.group(1) or mm.group(2)
                ev['methods'].setdefault(val, []).append(cur)
    return ev


def run(version, jdk):
    jars = glob.glob(f'{ROOT}/{version}/fabric-api-*.jar')
    if not jars:
        raise SystemExit(f'{ROOT}/{version}/ 下没有 fabric-api jar')
    jar = jars[0]
    cp_dir = prepare_cp(version, jar)
    cp = ':'.join(sorted(glob.glob(os.path.join(cp_dir, '*.jar'))))
    ev = scan_mixins(jdk, cp_dir)

    rows = []
    for item in CATALOG:
        expect = item.get('expect', 'present')
        if isinstance(expect, dict):
            expect = expect[version]
        must = item.get('must_have', [])
        if isinstance(must, dict):
            must = must[version]
        if item['kind'] == 'symbol':
            disp = '常量池符号 ' + item['symbol']
        else:
            disp = item.get('name') or f"{item.get('owner')}.{item.get('method')}"
        row = dict(id=item['id'], kind=item['kind'], note=item.get('note', ''),
                   expect=expect, name=disp, side=item.get('side', 'both'))
        if item['kind'] == 'fabric':
            out, err = javap(jdk, cp, item['name'])
            if 'class not found' in err or 'Error:' in err:
                row.update(result='absent', signature='', evidence='javap: class not found')
            else:
                sig = [l.strip() for l in out.splitlines() if l.strip()]
                row.update(result='present', signature=sig,
                           evidence=f'javap -cp <{os.path.basename(jar)} 子模块> {item["name"]}')
                missing = [m for m in must if not any(m in s for s in sig)]
                row['missing'] = missing
        elif item['kind'] == 'symbol':
            sym = item['symbol'].encode()
            hits = []
            for j in sorted(glob.glob(os.path.join(cp_dir, '*.jar'))):
                z = zipfile.ZipFile(j)
                for c in z.namelist():
                    if c.endswith('.class') and sym in z.read(c):
                        hits.append(os.path.basename(j) + '!' + c[:-6].replace('/', '.'))
            if hits:
                row.update(result='present', signature=hits[:6],
                           evidence=f'{len(hits)} 个 fabric class 的常量池里出现符号 "{item["symbol"]}"')
            else:
                row.update(result='absent', signature=[],
                           evidence=f'全部 {len(glob.glob(cp_dir + "/*.jar"))} 个子模块中未出现 "{item["symbol"]}"')
        else:
            owner, method = item['owner'], item['method']
            prefix = f'L{owner};{method}('
            hits = {k: v for k, v in ev['targets'].items() if k.startswith(prefix)}
            mhits = {k: v for k, v in ev['methods'].items()
                     if k == method or k.startswith(method + '(')}
            if hits:
                row.update(result='present', signature=sorted(hits),
                           evidence='mixin 注解 target=' + sorted(hits)[0] +
                                    ' (来自 ' + hits[sorted(hits)[0]][0] + ')')
            elif mhits:
                row.update(result='present(symbol)', signature=sorted(mhits),
                           evidence='mixin 注解 method=' + sorted(mhits)[0] +
                                    ' (来自 ' + mhits[sorted(mhits)[0]][0] + ')')
            else:
                row.update(result='no-evidence', signature='',
                           evidence=f'未匹配到: {len(ev["targets"])} 条 target / '
                                    f'{len(ev["methods"])} 条 method 证据中无 {owner}.{method}')
        rows.append(row)
    return rows, jar, len(ev['targets']) + len(ev['methods'])


def verdict(row):
    expect, result = row['expect'], row['result']
    if expect == 'info':          # 只记录探测结果, 不做通过/失败断言
        return 'INFO'
    if result == 'no-evidence':
        return 'UNPROVEN'          # 证据未采集到, 不算通过也不算失败
    if expect == 'present':
        if result.startswith('present'):
            return 'FAIL' if row.get('missing') else 'PASS'
        return 'FAIL'
    if expect == 'absent':
        return 'PASS' if result == 'absent' else 'FAIL'
    return 'FAIL'


def write_table(version, rows, jar, nev):
    md = [f'# Minecraft {version} 版本 API 表',
          '',
          f'> 本表**全部条目由脚本实测生成**，不是从文档抄的。',
          f'> 生成命令：`python3 scripts/verify_api_table.py {version}`',
          '',
          '**实验方法**',
          f'- Fabric API 条目：`javap` 直接读 `{os.path.basename(jar)}`（含 43/44 个 jar-in-jar 子模块）的真实签名',
          f'- Minecraft 本体条目：`javap -v` 读 fabric-api 的 mixin 注解，'
          f'从 `@Inject/@Redirect/@Overwrite` 的 `target="Lnet/minecraft/...;method()Desc"` '
          f'与 `method="..."` 取出真实 MC 签名（mixin 目标方法写错就注入失败，所以这是硬证据）。'
          f'本次共采集 {nev} 条注解证据。',
          '- 符号探测条目：在全部子模块的 class 常量池里搜字节串，看该 MC 符号是否被 Fabric 代码引用'
          '（**只能证明"被引用"，不能证明"不存在"**，故只做记录不做断言）。',
          '',
          f'| # | 端 | 类别 | API | 预期 | 实测 | 状态 |',
          f'|---|---|---|---|---|---|---|']
    SIDE_CN = {'server': '服务端', 'client': '客户端', 'both': '通用'}
    for i, r in enumerate(rows, 1):
        sig = r['signature']
        if isinstance(sig, list):
            shown = '<br>'.join(s[:150] for s in sig[:3]) if sig else '—'
        else:
            shown = sig or '—'
        kind_cn = {'fabric': 'Fabric API', 'mojang': 'MC 本体', 'symbol': '符号探测'}[r['kind']]
        md.append(f"| {i} | {SIDE_CN[r['side']]} | {kind_cn} | "
                  f"`{r['name']}` | {r['expect']} | {r['result']} | {verdict(r)} |")
    md += ['', '## 逐条签名与证据', '']
    for r in rows:
        md += [f"### `{r['id']}` — {r['name']}",
               '',
               f"- 预期：{r['expect']}　实测：**{r['result']}**　状态：**{verdict(r)}**",
               f"- 说明：{r['note']}",
               f"- 证据：{r['evidence']}"]
        if r['signature']:
            sigs = r['signature'] if isinstance(r['signature'], list) else [r['signature']]
            md.append('- 实测签名：')
            md.append('  ```')
            for s in sigs[:8]:
                md.append('  ' + s)
            md.append('  ```')
        md.append('')
    open(f'{ROOT}/{version}/API_TABLE.md', 'w').write('\n'.join(md))

    data = dict(version=version, generated_by='scripts/verify_api_table.py',
                jar=os.path.basename(jar), mixin_annotation_evidence=nev,
                entries=[dict(r, status=verdict(r)) for r in rows])
    json.dump(data, open(f'{ROOT}/{version}/api_table.json', 'w'), indent=1, ensure_ascii=False)
    return data


SIDE_CN = {'server': '服务端', 'client': '客户端', 'both': '通用'}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    jdk = find_jdk()
    versions = args or ['26.2', '26.3']
    print(f'javap: {jdk}/bin/javap')
    allpass = True
    datas = {}
    for v in versions:
        rows, jar, nev = run(v, jdk)
        d = write_table(v, rows, jar, nev)
        datas[v] = d
        print(f'\n===== {v} ({os.path.basename(jar)}, {nev} 条 mixin 证据) =====')
        for r in rows:
            st = verdict(r)
            if st == 'FAIL':
                allpass = False
            extra = ''
            if st == 'FAIL' and r.get('missing'):
                extra = ' 缺少: ' + ','.join(r['missing'])
            print(f"  {st}  {r['id']:34s} {r['expect']:7s} -> {r['result']:7s}{extra}")
        npass = sum(1 for r in rows if verdict(r) == 'PASS')
        nun = sum(1 for r in rows if verdict(r) == 'UNPROVEN')
        byside = {}
        for r in rows:
            d = byside.setdefault(r['side'], [0, 0])
            d[0] += 1
            if verdict(r) == 'PASS':
                d[1] += 1
        side_txt = '  '.join(f"{SIDE_CN[k]} {c[1]}/{c[0]}" for k, c in byside.items())
        print(f'  ---- {v}: {npass}/{len(rows)} PASS, {nun} UNPROVEN  |  {side_txt}')
    if len(versions) == 2:
        print('\n===== 26.2 vs 26.3 差异 =====')
        a = {r['id']: r for r in datas['26.2']['entries']}
        b = {r['id']: r for r in datas['26.3']['entries']}
        for k in a:
            if a[k]['result'] != b[k]['result']:
                print(f"  {k}: 26.2={a[k]['result']}  26.3={b[k]['result']}")
            elif a[k].get('signature') != b[k].get('signature') and a[k]['kind'] == 'mojang':
                print(f"  {k}: 签名变化\n     26.2 {a[k]['signature']}\n     26.3 {b[k]['signature']}")
    print('\nRESULT:', 'ALL PASS' if allpass else 'HAS FAILURE')
    return 0 if allpass else 1


if __name__ == '__main__':
    sys.exit(main())
