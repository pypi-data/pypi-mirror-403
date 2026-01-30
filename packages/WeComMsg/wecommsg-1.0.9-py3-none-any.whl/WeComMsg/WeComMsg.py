import requests
import os
import base64
import hashlib
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type  # 新增重试依赖

# 新增：全局请求超时配置（可根据需求调整）
REQUEST_TIMEOUT = (10, 30)  # 连接超时10s，读取超时30s
# 新增：重试配置（网络波动时重试）
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),  # 最多重试3次
    "wait": wait_fixed(1),  # 每次重试间隔1s
    "retry": retry_if_exception_type((
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.ReadTimeout
    ))
}

# 创建会话对象（复用连接，提升性能）
session = requests.Session()
# 会话级超时（兜底）
session.timeout = REQUEST_TIMEOUT


class WeChatWorkSender:
    def __init__(self, corpid, corpsecret, agentid):
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agentid = agentid
        self.access_token = self.get_access_token()

    # 优化1：get_access_token 加超时+重试
    @retry(**RETRY_CONFIG)
    def get_access_token(self):
        """获取企业微信的 access_token"""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}"
        # 替换requests.get为session.get，添加显式超时
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        result = response.json()
        if 'access_token' in result:
            return result['access_token']
        else:
            raise Exception(f"Failed to get access token: {result}")

    # 优化2：upload_media 加超时+重试
    @retry(**RETRY_CONFIG)
    def upload_media(self, media_type, media_path):
        """上传文件或图片，获取 media_id"""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={self.access_token}&type={media_type}"
        files = {'media': open(media_path, 'rb')}
        response = session.post(url, files=files, timeout=REQUEST_TIMEOUT)
        result = response.json()
        if 'media_id' in result:
            return result['media_id']
        else:
            raise Exception(f"Failed to upload media: {result}")

    # 优化3：send_text 加超时+重试
    @retry(**RETRY_CONFIG)
    def send_text(self, user_ids, content):
        """发送文本消息（返回完整响应，包含msgid）"""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
        data = {
            "touser": "|".join(user_ids),
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {"content": content}
        }
        response = session.post(url, json=data, timeout=REQUEST_TIMEOUT)
        return response.json()

    # 优化4：send_image 加超时+重试
    @retry(**RETRY_CONFIG)
    def send_image(self, user_ids, image_path):
        """发送图片消息（返回完整响应，包含msgid）"""
        media_id = self.upload_media('image', image_path)
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
        data = {
            "touser": "|".join(user_ids),
            "msgtype": "image",
            "agentid": self.agentid,
            "image": {"media_id": media_id}
        }
        response = session.post(url, json=data, timeout=REQUEST_TIMEOUT)
        return response.json()

    # 优化5：send_file 加超时+重试
    @retry(**RETRY_CONFIG)
    def send_file(self, user_ids, file_path):
        """发送文件消息（返回完整响应，包含msgid）"""
        media_id = self.upload_media('file', file_path)
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
        data = {
            "touser": "|".join(user_ids),
            "msgtype": "file",
            "agentid": self.agentid,
            "file": {"media_id": media_id}
        }
        response = session.post(url, json=data, timeout=REQUEST_TIMEOUT)
        return response.json()

    # 优化6：upload_file 加超时+重试
    @retry(**RETRY_CONFIG)
    def upload_file(self, webhook_url, excel_file_path):
        """向群聊上传文件，获取 media_id"""
        webhook_key = webhook_url.split("key=")[1]
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={webhook_key}&type=file"
        with open(excel_file_path, "rb") as file:
            files = {"media": file}
            response = session.post(url, files=files, timeout=REQUEST_TIMEOUT)
        data = response.json()
        if data["errcode"] == 0:
            return data["media_id"]
        else:
            raise Exception(f"Failed to upload file to group: {data}")

    # 优化7：send_text_to_group 加超时+重试
    @retry(**RETRY_CONFIG)
    def send_text_to_group(self, webhook_url, text_message, mentioned_list=None):
        """发送群聊文本消息（返回完整响应，包含msgid）"""
        if mentioned_list is None:
            mentioned_list = ["@all"]
        text_message_dict = {
            "msgtype": "text",
            "text": {
                "content": text_message,
                "mentioned_list": mentioned_list
            }
        }
        response = session.post(webhook_url, json=text_message_dict, timeout=REQUEST_TIMEOUT)
        return response.json()

    # 优化8：send_file_to_group 加超时+重试
    @retry(**RETRY_CONFIG)
    def send_file_to_group(self, webhook_url, file_path):
        """发送群聊文件消息（返回完整响应，包含msgid）"""
        media_id = self.upload_file(webhook_url, file_path)
        file_message = {
            "msgtype": "file",
            "file": {"media_id": media_id}
        }
        response = session.post(webhook_url, json=file_message, timeout=REQUEST_TIMEOUT)
        return response.json()

    # 优化9：send_image_to_group 加超时+重试
    @retry(**RETRY_CONFIG)
    def send_image_to_group(self, webhook_url, image_path):
        """
        发送图片到群聊（Webhook）
        :param webhook_url: 群聊Webhook地址
        :param image_path: 本地图片路径（支持JPG/PNG，不超过2M）
        :return: 接口响应结果（包含msgid）
        """
        # 1. 验证图片大小（不超过2M）
        max_size = 2 * 1024 * 1024  # 2MB
        if os.path.getsize(image_path) > max_size:
            raise ValueError(f"图片大小超过2M限制，当前大小：{os.path.getsize(image_path) / 1024 / 1024:.2f}M")

        # 2. 读取图片并计算base64和md5
        with open(image_path, 'rb') as f:
            image_data = f.read()
            base64_str = base64.b64encode(image_data).decode('utf-8')
            md5_str = hashlib.md5(image_data).hexdigest()

        # 3. 构造图片消息体
        image_message = {
            "msgtype": "image",
            "image": {
                "base64": base64_str,
                "md5": md5_str
            }
        }

        # 4. 发送消息到群聊Webhook
        response = session.post(webhook_url, json=image_message, timeout=REQUEST_TIMEOUT)
        return response.json()

    # 补充到优化版的 WeChatWorkSender 类中
    @retry(**RETRY_CONFIG)
    def send_markdown(self, user_ids, content):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
        data = {
            "touser": "|".join(user_ids),
            "msgtype": "markdown",
            "agentid": self.agentid,
            "markdown": {"content": content}
        }
        response = session.post(url, json=data, timeout=REQUEST_TIMEOUT)
        return response.json()

    @retry(**RETRY_CONFIG)
    def send_markdown_to_group(self, webhook_url, content):
        markdown_message = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
        response = session.post(webhook_url, json=markdown_message, timeout=REQUEST_TIMEOUT)
        return response.json()

    # 优化10：recall_message 加超时+重试
    @retry(**RETRY_CONFIG)
    def recall_message(self, msgid):
        """
        撤回企业微信应用消息
        :param msgid: 要撤回的消息ID，从发送消息接口获取
        :return: 接口返回结果
        """
        if not msgid:
            raise ValueError("消息ID(msgid)不能为空")

        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/recall?access_token={self.access_token}"
        data = {"msgid": msgid}

        try:
            response = session.post(url, json=data, timeout=REQUEST_TIMEOUT)
            result = response.json()

            if result.get('errcode') == 0:
                print(f"消息撤回成功，msgid: {msgid}")
            else:
                print(f"消息撤回失败，错误码: {result.get('errcode')}, 错误信息: {result.get('errmsg')}")

            return result
        except Exception as e:
            raise Exception(f"撤回消息时发生错误: {str(e)}")