from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.hot_recommend_service import HotRecommendService

logger = get_logger(__name__)



def update_popularity_scores():
    """
    定时任务：更新角色的热度分数
    :return:
    """

    db= SessionLocal()
    try:
        logger.info(f"[{datetime.now()}] 开始更新角色热度分数")
        HotRecommendService.refresh_hot_scores(db)
        logger.info(f"[{datetime.now()}] 角色热度分数更新完成")
    except Exception as e:
        logger.error(f"更新角色热度分数失败: {e}")
    finally:
        db.close()


# 创建调度器
scheduler = BackgroundScheduler(timezone =  'Asia/Shanghai')

# 添加定时任务
def start_scheduler():
    """
    启动定时任务
    :return:
    """
    scheduler.add_job(
        update_popularity_scores,
        CronTrigger(hour=11,minute=26),
        id='update_popularity_daily',
        replace_existing=True
    )

    scheduler.start()
    logger.info("定时任务已启动: 每天12点更新角色热度分数")



def stop_scheduler():
    """
    停止定时任务
    """
    scheduler.shutdown()
    logger.info("定时任务调度器已停止")











