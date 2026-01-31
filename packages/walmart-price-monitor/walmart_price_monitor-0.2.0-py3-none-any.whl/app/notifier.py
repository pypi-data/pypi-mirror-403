import logging
from typing import List, Optional
from .config import settings
from dingtalkchatbot.chatbot import DingtalkChatbot

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    def __init__(self):
        webhook = settings.DINGTALK_WEBHOOK
        secret = settings.DINGTALK_SECRET
        if webhook and secret:
            self.bot = DingtalkChatbot(webhook, secret=secret)
            logger.info("✅ 钉钉通知器初始化成功")
        else:
            self.bot = None
            logger.warning("⚠️ 钉钉通知器未初始化: Webhook 或 Secret 未配置")
            logger.warning("请在 .env 文件中配置 DINGTALK_WEBHOOK 和 DINGTALK_SECRET")

        # 解析 @ 指定人员手机号
        self.at_mobiles: List[str] = []
        if settings.DINGTALK_AT_MOBILES:
            self.at_mobiles = [m.strip() for m in settings.DINGTALK_AT_MOBILES.split(",") if m.strip()]
            logger.info(f"配置了 @ 指定人员: {len(self.at_mobiles)} 人")

    def send_markdown(self, title: str, text: str, is_at_all: bool = False, at_mobiles: Optional[List[str]] = None):
        """
        发送 Markdown 消息

        Args:
            title: 消息标题
            text: 消息内容
            is_at_all: 是否 @所有人（当配置了 at_mobiles 时会被覆盖）
            at_mobiles: 指定 @ 的手机号列表（优先级：参数 > 环境变量配置）
        """
        if not self.bot:
            logger.warning("⚠️ 钉钉通知器未初始化，跳过发送消息")
            logger.warning(f"消息标题: {title}")
            logger.info("💡 提示: 请在 .env 文件中配置 DINGTALK_WEBHOOK 和 DINGTALK_SECRET")
            return

        try:
            # 确定 @ 的目标
            mobiles = at_mobiles or self.at_mobiles

            logger.info(f"📤 发送钉钉通知: {title}")

            if mobiles:
                # @ 指定人员
                result = self.bot.send_markdown(title=title, text=text, at_mobiles=mobiles, is_at_all=False)
                logger.info(f"✅ 钉钉通知发送成功 (@ {len(mobiles)} 人)")
            elif is_at_all:
                # @所有人
                result = self.bot.send_markdown(title=title, text=text, is_at_all=True)
                logger.info("✅ 钉钉通知发送成功 (@所有人)")
            else:
                # 不 @ 任何人
                result = self.bot.send_markdown(title=title, text=text, is_at_all=False)
                logger.info("✅ 钉钉通知发送成功")

            # 记录返回结果
            if result and hasattr(result, 'get'):
                if result.get('errcode') != 0:
                    logger.warning(f"⚠️ 钉钉 API 返回错误: {result}")
        except Exception as e:
            logger.error(f"❌ 钉钉通知发送失败: {e}")
            logger.error(f"标题: {title}")
            logger.error(f"错误详情: {type(e).__name__}: {str(e)}")


ding_talk_notifier = DingTalkNotifier()
