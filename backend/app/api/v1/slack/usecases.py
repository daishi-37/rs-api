import requests
from app.schemas import slack, base
from app.core.logger import main_logger
from app.core.settings import SLACK_WEBHOOK_URL



def push(req: slack.ReqPush) -> slack.ResPush:
    try:
        # 受け取ったメッセージをログに記録
        main_logger.info(f"Slackメッセージを受信: \n{req.msg}")

        # Slack Webhookにメッセージを送信
        payload = {
            "text": req.msg  # 基本的なテキストメッセージ
        }
        
        # Webhookへのリクエスト送信
        response = requests.post(
            SLACK_WEBHOOK_URL, 
            json=payload,
            timeout=5  # タイムアウトを5秒に設定
        )
        
        # レスポンスのステータスコードを確認
        if response.status_code == 200:
            main_logger.info(f"Slackメッセージを送信しました: {req.msg}")
            return slack.ResPush(
                msg="スラックメッセージを送信しました",
            )
        else:
            error_msg = f"Slack APIエラー: ステータス {response.status_code}, レスポンス {response.text}"
            main_logger.error(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        main_logger.error(f"スラックメッセージ error: {e}")
        raise Exception("スラックメッセージ作成エラー")
