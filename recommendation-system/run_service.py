"""启动推荐服务（强制重新训练）"""
from app import RecommendationSystem
import logging
logging.basicConfig(level=logging.INFO)

rec_sys = RecommendationSystem()
rec_sys.connect_database()
rec_sys.connect_redis()
rec_sys.train(force=True)
logger = logging.getLogger(__name__)
logger.info(f"训练后用户数: {len(rec_sys.user_ids) if rec_sys.user_ids else 0}")
logger.info(f"训练后资源数: {len(rec_sys.resource_ids) if rec_sys.resource_ids else 0}")
rec_sys.app.run(host='0.0.0.0', port=5000, debug=False)
