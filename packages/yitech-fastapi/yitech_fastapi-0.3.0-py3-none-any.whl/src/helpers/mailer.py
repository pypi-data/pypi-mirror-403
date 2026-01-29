from typing import List, Optional, Any


class YiBaseMailer:
    """邮件服务基类"""

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """发送邮件

        Args:
            to: 收件人列表
            subject: 邮件主题
            body: 邮件正文
            is_html: 是否为HTML邮件
            cc: 抄送列表
            bcc: 密送列表
            attachments: 附件列表

        Returns:
            bool: 发送成功返回True，失败返回False

        """
        raise NotImplementedError


class YiConsoleMailer(YiBaseMailer):
    """控制台邮件服务，用于开发环境，将邮件内容输出到控制台"""

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """将邮件内容输出到控制台"""
        print("\n=== 邮件模拟发送 ===")
        print(f"收件人: {', '.join(to)}")
        if cc:
            print(f"抄送: {', '.join(cc)}")
        if bcc:
            print(f"密送: {', '.join(bcc)}")
        print(f"主题: {subject}")
        print(f"类型: {'HTML' if is_html else '纯文本'}")
        print(f"正文: {body}")
        if attachments:
            print(f"附件: {', '.join(attachments)}")
        print("=== 邮件模拟发送结束 ===\n")
        return True


class YiSESMailer(YiBaseMailer):
    """AWS SES邮件服务实现"""

    def __init__(self, aws_access_key: str, aws_secret_key: str, region: str):
        """初始化SES邮件服务

        Args:
            aws_access_key: AWS访问密钥
            aws_secret_key: AWS秘密密钥
            region: AWS区域

        """
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region
        # 这里可以初始化SES客户端

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """使用SES发送邮件"""
        # TODO: 实现SES邮件发送逻辑
        print(f"[SES] 发送邮件到: {', '.join(to)}，主题: {subject}")
        return True


# 邮件服务工厂函数
def yi_create_mailer(mailer_type: str = "console", **kwargs: Any) -> YiBaseMailer:
    """创建邮件服务实例

    Args:
        mailer_type: 邮件服务类型，可选值：console, ses
        **kwargs: 邮件服务的配置参数

    Returns:
        YiBaseMailer: 邮件服务实例

    """
    if mailer_type == "console":
        return YiConsoleMailer()
    elif mailer_type == "ses":
        return YiSESMailer(**kwargs)
    else:
        raise ValueError(f"不支持的邮件服务类型: {mailer_type}")


# 默认邮件服务实例
yi_mailer = yi_create_mailer()
