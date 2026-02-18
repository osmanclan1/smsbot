"""
Escalation service - handles human handoff and admin notifications.
"""
import os
import sys
import requests
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from typing import Dict, Optional
from storage.dynamodb import DynamoDBService
from datetime import datetime


class EscalationService:
    """Service for handling escalations and admin notifications."""
    
    def __init__(self):
        """Initialize escalation service."""
        self.db = DynamoDBService()
        self.admin_notification_webhook = os.getenv('ADMIN_NOTIFICATION_WEBHOOK')
        self.admin_email = os.getenv('ADMIN_EMAIL')
        self.admin_api_base_url = os.getenv('ADMIN_API_BASE_URL')  # For internal API notifications
    
    def escalate_conversation(
        self,
        conversation_id: str,
        escalation_reason: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Escalate a conversation to human review.
        
        Args:
            conversation_id: Conversation ID
            escalation_reason: Reason for escalation
            metadata: Additional escalation metadata
            
        Returns:
            True if escalation successful
        """
        # Get conversation details
        conversation = self.db.get_conversation(conversation_id)
        if not conversation:
            print(f"Error: Conversation {conversation_id} not found for escalation")
            return False
        
        phone_number = conversation.get('phone_number')
        trigger_type = conversation.get('trigger_type')
        messages = conversation.get('messages', [])
        
        # Update conversation state to ESCALATED (already done by conversation engine, but ensure it)
        self.db.transition_conversation_state(
            conversation_id,
            'ESCALATED',
            reason=escalation_reason
        )
        
        # Add system message to conversation
        escalation_message = f"[ESCALATED] {escalation_reason}. This conversation has been flagged for human review."
        self.db.add_message(
            conversation_id,
            'system',
            escalation_message
        )
        
        # Log escalation details
        escalation_data = {
            'conversation_id': conversation_id,
            'phone_number': phone_number,
            'escalation_reason': escalation_reason,
            'trigger_type': trigger_type,
            'message_count': len(messages),
            'last_messages': messages[-3:] if len(messages) >= 3 else messages,
            'metadata': metadata or {}
        }
        
        print(f"\n{'='*60}")
        print(f"🚨 CONVERSATION ESCALATED")
        print(f"{'='*60}")
        print(f"Conversation ID: {conversation_id}")
        print(f"Phone Number: {phone_number}")
        print(f"Reason: {escalation_reason}")
        print(f"Trigger Type: {trigger_type}")
        print(f"Messages: {len(messages)}")
        print(f"{'='*60}\n")
        
        # Send notifications to admins
        notification_sent = False
        if self.admin_notification_webhook:
            try:
                self._send_webhook_notification(escalation_data)
                notification_sent = True
            except Exception as e:
                print(f"Error sending webhook notification: {e}")
        
        if self.admin_api_base_url:
            try:
                self._send_api_notification(escalation_data)
                notification_sent = True
            except Exception as e:
                print(f"Error sending API notification: {e}")
        
        # Email via SES or SMTP (if configured)
        if self.admin_email:
            try:
                self._send_email_notification(escalation_data)
                notification_sent = True
            except Exception as e:
                print(f"Error sending email notification: {e}")
        
        if not notification_sent:
            print("⚠️  No notification method configured - escalation logged only")
        
        return True
    
    def _send_webhook_notification(self, escalation_data: Dict):
        """Send webhook notification to admin system."""
        payload = {
            'event_type': 'conversation_escalated',
            'timestamp': datetime.utcnow().isoformat(),
            'data': escalation_data
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'smsbot-escalation-service/1.0'
        }
        
        # Add auth header if configured
        webhook_auth_token = os.getenv('ADMIN_WEBHOOK_AUTH_TOKEN')
        if webhook_auth_token:
            headers['Authorization'] = f'Bearer {webhook_auth_token}'
        
        try:
            response = requests.post(
                self.admin_notification_webhook,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            print(f"✅ Webhook notification sent to {self.admin_notification_webhook}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send webhook notification: {e}")
            raise
    
    def _send_api_notification(self, escalation_data: Dict):
        """Send notification via internal admin API."""
        if not self.admin_api_base_url:
            return
        
        url = f"{self.admin_api_base_url.rstrip('/')}/api/admin/escalations"
        
        payload = {
            'event_type': 'conversation_escalated',
            'timestamp': datetime.utcnow().isoformat(),
            **escalation_data
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add auth header if configured
        api_auth_token = os.getenv('ADMIN_API_AUTH_TOKEN')
        if api_auth_token:
            headers['Authorization'] = f'Bearer {api_auth_token}'
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            print(f"✅ API notification sent to {url}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send API notification: {e}")
            raise
    
    def _send_email_notification(self, escalation_data: Dict):
        """Send email notification to admin via AWS SES or SMTP."""
        # Try AWS SES first (if boto3 available and configured)
        try:
            import boto3
            
            ses_region = os.getenv('AWS_SES_REGION', 'us-east-1')
            ses_client = boto3.client('ses', region_name=ses_region)
            
            # Get sender email from env or use admin email
            sender_email = os.getenv('ADMIN_SENDER_EMAIL', f'noreply@{os.getenv("DOMAIN", "oakton.edu")}')
            
            subject = f"🚨 Conversation Escalated: {escalation_data.get('conversation_id', 'Unknown')}"
            
            # Format email body
            body_text = f"""
Conversation Escalation Alert

Conversation ID: {escalation_data.get('conversation_id')}
Phone Number: {escalation_data.get('phone_number', 'N/A')}
Escalation Reason: {escalation_data.get('escalation_reason')}
Trigger Type: {escalation_data.get('trigger_type', 'N/A')}
Message Count: {escalation_data.get('message_count', 0)}

Last Messages:
{json.dumps(escalation_data.get('last_messages', []), indent=2)}

Please review this conversation in the admin dashboard.
"""
            
            body_html = f"""
<html>
<head><title>Conversation Escalation</title></head>
<body>
<h2>🚨 Conversation Escalation Alert</h2>
<table border="1" cellpadding="5">
<tr><td><strong>Conversation ID</strong></td><td>{escalation_data.get('conversation_id')}</td></tr>
<tr><td><strong>Phone Number</strong></td><td>{escalation_data.get('phone_number', 'N/A')}</td></tr>
<tr><td><strong>Escalation Reason</strong></td><td>{escalation_data.get('escalation_reason')}</td></tr>
<tr><td><strong>Trigger Type</strong></td><td>{escalation_data.get('trigger_type', 'N/A')}</td></tr>
<tr><td><strong>Message Count</strong></td><td>{escalation_data.get('message_count', 0)}</td></tr>
</table>

<h3>Last Messages:</h3>
<pre>{json.dumps(escalation_data.get('last_messages', []), indent=2)}</pre>

<p>Please review this conversation in the admin dashboard.</p>
</body>
</html>
"""
            
            response = ses_client.send_email(
                Source=sender_email,
                Destination={'ToAddresses': [self.admin_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                    }
                }
            )
            print(f"✅ Email notification sent via SES to {self.admin_email} (Message ID: {response['MessageId']})")
            return True
            
        except ImportError:
            print("⚠️  boto3 not available for SES - skipping email notification")
            return False
        except Exception as e:
            # If SES fails, fall back to SMTP if configured
            print(f"⚠️  SES email failed: {e}, trying SMTP fallback")
            return self._send_email_via_smtp(escalation_data)
    
    def _send_email_via_smtp(self, escalation_data: Dict) -> bool:
        """Send email via SMTP fallback (if SES not available)."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not smtp_user or not smtp_password:
                print("⚠️  SMTP credentials not configured - skipping email notification")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 Conversation Escalated: {escalation_data.get('conversation_id', 'Unknown')}"
            msg['From'] = smtp_user
            msg['To'] = self.admin_email
            
            text_body = f"""Conversation Escalation Alert

Conversation ID: {escalation_data.get('conversation_id')}
Phone Number: {escalation_data.get('phone_number', 'N/A')}
Escalation Reason: {escalation_data.get('escalation_reason')}
Trigger Type: {escalation_data.get('trigger_type', 'N/A')}
Message Count: {escalation_data.get('message_count', 0)}

Last Messages:
{json.dumps(escalation_data.get('last_messages', []), indent=2)}
"""
            
            msg.attach(MIMEText(text_body, 'plain'))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email notification sent via SMTP to {self.admin_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email via SMTP: {e}")
            return False
