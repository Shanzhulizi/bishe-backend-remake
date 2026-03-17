from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime

from app.db.session import SessionLocal
from app.services.popularity_service import PopularityService
from app.models.character import Character
from sqlalchemy import func

logger = logging.getLogger(__name__)

# 创建调度器
scheduler = BackgroundScheduler()

# 后台自动运行，不需要写接口
def update_popularity_job():
    """定时更新角色热度"""
    db = SessionLocal()
    try:
        service = PopularityService(db)

        # 根据当前小时决定更新哪个分片
        current_hour = datetime.now().hour
        shard_id = current_hour % 4

        characters = db.query(Character).filter(
            Character.is_active == True,
            func.mod(Character.id, 4) == shard_id
        ).all()

        logger.info(f"分片 {shard_id}: 开始更新 {len(characters)} 个角色")

        for char in characters:
            new_score = service.calculate_score(char.id)
            if abs(char.popularity_score - new_score) > 0.01:
                char.popularity_score = new_score

        db.commit()
        logger.info(f"分片 {shard_id} 更新完成")

    except Exception as e:
        logger.error(f"更新失败: {e}")


        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """启动调度器"""
    global scheduler
    # 每小时执行一次
    scheduler.add_job(
        update_popularity_job,
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