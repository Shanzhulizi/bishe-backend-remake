import asyncio
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, func

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.character import Character
from app.services.popularity_service import PopularityService

logger = get_logger(__name__)

# 创建调度器
scheduler = BackgroundScheduler()

# 后台自动运行，不需要写接口
# def update_popularity_job():
#     """定时更新角色热度"""
#     db = AsyncSessionLocal()
#     try:
#         service = PopularityService(db)
#
#         # 根据当前小时决定更新哪个分片
#         current_hour = datetime.now().hour
#         shard_id = current_hour % 4
#
#         characters = db.query(Character).filter(
#             Character.is_active == True,
#             func.mod(Character.id, 4) == shard_id
#         ).all()
#
#         logger.info(f"分片 {shard_id}: 开始更新 {len(characters)} 个角色")
#
#         for char in characters:
#             new_score = service.calculate_score(char.id)
#             if abs(char.popularity_score - new_score) > 0.01:
#                 char.popularity_score = new_score
#
#         db.commit()
#         logger.info(f"分片 {shard_id} 更新完成")
#
#     except Exception as e:
#         logger.error(f"更新失败: {e}")
#
#
#         db.rollback()
#     finally:
#         db.close()

async def update_popularity_job_async():
    """异步定时更新角色热度"""
    async with AsyncSessionLocal() as db:
        try:
            service = PopularityService(db)

            # 根据当前小时决定更新哪个分片
            current_hour = datetime.now().hour
            shard_id = current_hour % 4

            # 查询需要更新的角色
            stmt = select(Character).where(
                Character.is_active == True,
                func.mod(Character.id, 4) == shard_id
            )
            result = await db.execute(stmt)
            characters = result.scalars().all()

            logger.info(f"分片 {shard_id}: 开始更新 {len(characters)} 个角色")

            for char in characters:
                new_score = await service.calculate_score(char.id)
                if abs((char.popularity_score or 0) - new_score) > 0.01:
                    char.popularity_score = new_score

            await db.commit()
            logger.info(f"分片 {shard_id} 更新完成")

        except Exception as e:
            logger.error(f"更新失败: {e}")
            await db.rollback()

def update_popularity_job():
    """同步包装器（供 APScheduler 调用）"""
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果循环正在运行，创建任务
            asyncio.run(update_popularity_job_async())
        else:
            # 否则运行直到完成
            loop.run_until_complete(update_popularity_job_async())
    except RuntimeError:
        # 没有事件循环，创建一个新的
        asyncio.run(update_popularity_job_async())
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}")
def start_scheduler():
    """启动调度器"""
    global scheduler
    # 每小时执行一次
    scheduler.add_job(
        update_popularity_job,  # ✅ 调用同步包装器，而不是异步函数
        trigger=IntervalTrigger(hours=1),
        id='update_popularity',
        name='更新角色热度',
        replace_existing=True
    )
    scheduler.start()
    logger.info("定时任务调度器已启动")


def stop_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        print("✅ 定时任务已关闭")