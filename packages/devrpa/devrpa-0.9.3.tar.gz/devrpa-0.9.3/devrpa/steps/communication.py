
from typing import Dict, Any, Optional
import httpx
import smtplib
from email.mime.text import MIMEText
import asyncio
from ..workflow import Step
from ..core import StepResult, ExecutionContext

class SlackStep(Step):
    def __init__(self, name: str, webhook_url: str, message: str):
        super().__init__(name)
        self.webhook_url = webhook_url
        self.message = message

    async def execute(self, context: ExecutionContext) -> StepResult:
        url = context.resolve(self.webhook_url)
        msg = context.resolve(self.message)
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json={"text": msg})
                resp.raise_for_status()
            return StepResult(name=self.name, success=True)
        except Exception as e:
            return StepResult(name=self.name, success=False, error=e)

class EmailStep(Step):
    def __init__(self, name: str, to: str, subject: str, body: str, smtp_server: str = "localhost", smtp_port: int = 25):
        super().__init__(name)
        self.to = to
        self.subject = subject
        self.body = body
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    async def execute(self, context: ExecutionContext) -> StepResult:
        to_addr = context.resolve(self.to)
        subject = context.resolve(self.subject)
        body_text = context.resolve(self.body)
        
        msg = MIMEText(body_text)
        msg['Subject'] = subject
        msg['From'] = "devrpa@bot.com" 
        msg['To'] = to_addr

        def _send():
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.send_message(msg)

        try:
            await asyncio.to_thread(_send)
            return StepResult(name=self.name, success=True)
        except Exception as e:
             return StepResult(name=self.name, success=False, error=e)
