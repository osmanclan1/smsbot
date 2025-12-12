"""
DynamoDB service layer for storing conversations, triggers, and results.
"""

import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json
from threading import Lock


class DynamoDBService:
    """Service for DynamoDB operations."""
    
    # In-memory fallback storage when DynamoDB is unavailable
    _memory_store: Dict[str, Dict] = {}
    _memory_lock = Lock()
    
    def __init__(self):
        """Initialize DynamoDB client."""
        # Initialize boto3 session - supports multiple credential methods:
        # 1. Direct credentials from environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        # 2. AWS profile from environment (AWS_PROFILE)
        # 3. Default credentials (~/.aws/credentials)
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Get credentials from environment
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        session_token = os.getenv('AWS_SESSION_TOKEN')  # Optional, for temporary credentials
        profile = os.getenv('AWS_PROFILE') or os.getenv('AWS_DEFAULT_PROFILE')
        
        session = None
        
        # Method 1: Try direct credentials from environment variables first
        if access_key and secret_key:
            try:
                session_kwargs = {
                    'aws_access_key_id': access_key,
                    'aws_secret_access_key': secret_key,
                    'region_name': region
                }
                if session_token:
                    session_kwargs['aws_session_token'] = session_token
                
                session = boto3.Session(**session_kwargs)
                # Test if the session works
                test_sts = session.client('sts')
                identity = test_sts.get_caller_identity()
                print(f"DynamoDB: Using credentials from environment variables - Account: {identity.get('Account')}")
            except Exception as e:
                print(f"Note: Environment credentials not valid ({e}), trying other methods...")
                session = None
        
        # Method 2: Try AWS profile if direct credentials didn't work
        if not session and profile:
            try:
                session = boto3.Session(profile_name=profile, region_name=region)
                # Test if the session works
                test_sts = session.client('sts')
                identity = test_sts.get_caller_identity()
                print(f"DynamoDB: Using profile '{profile}' - Account: {identity.get('Account')}")
            except Exception as e:
                print(f"Note: Profile '{profile}' not available ({e}), trying default credentials...")
                session = None
        
        # Method 3: Try default credentials (from ~/.aws/credentials or IAM role)
        if not session:
            try:
                session = boto3.Session(region_name=region)
                test_sts = session.client('sts')
                identity = test_sts.get_caller_identity()
                print(f"DynamoDB: Using default credentials - Account: {identity.get('Account')}")
            except Exception as e:
                error_msg = str(e)
                if 'ExpiredToken' in error_msg or 'InvalidClientTokenId' in error_msg:
                    print(f"⚠️  Warning: AWS credentials expired or invalid: {error_msg}")
                    print("💡 To fix: Update AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file")
                    print("💡 Or run: aws sso login --profile your-profile")
                    print("⚠️  Continuing without AWS (some features may not work)")
                    # Create a mock session that will fail gracefully
                    # This allows the bot to run for testing other features
                    session = None
                else:
                    print(f"Warning: Could not initialize AWS session: {e}")
                    print("Hint: Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file")
                    raise
        
        # Only create DynamoDB resource if we have a valid session
        if session:
            self.dynamodb = session.resource('dynamodb')
        else:
            # No valid session - set to None, methods will handle gracefully
            self.dynamodb = None
            print("⚠️  DynamoDB not available - running in limited mode (conversations won't be saved)")
        
        # Set table names first (before any table access)
        self.conversations_table_name = os.getenv(
            'CONVERSATIONS_TABLE',
            os.getenv('DYNAMODB_CONVERSATIONS_TABLE', 'smsbot-conversations')
        )
        self.triggers_table_name = os.getenv(
            'TRIGGERS_TABLE',
            os.getenv('DYNAMODB_TRIGGERS_TABLE', 'smsbot-triggers')
        )
        self.results_table_name = os.getenv(
            'RESULTS_TABLE',
            os.getenv('DYNAMODB_RESULTS_TABLE', 'smsbot-results')
        )
        
        # Initialize table references (will be None if DynamoDB not available)
        if self.dynamodb:
            self.conversations_table = self.dynamodb.Table(self.conversations_table_name)
            self.triggers_table = self.dynamodb.Table(self.triggers_table_name)
            self.results_table = self.dynamodb.Table(self.results_table_name)
        else:
            self.conversations_table = None
            self.triggers_table = None
            self.results_table = None
        
        # Phase 2: Additional tables
        self.students_table_name = os.getenv(
            'STUDENTS_TABLE',
            os.getenv('DYNAMODB_STUDENTS_TABLE', 'smsbot-students')
        )
        self.deadlines_table_name = os.getenv(
            'DEADLINES_TABLE',
            os.getenv('DYNAMODB_DEADLINES_TABLE', 'smsbot-deadlines')
        )
        self.followups_table_name = os.getenv(
            'FOLLOWUPS_TABLE',
            os.getenv('DYNAMODB_FOLLOWUPS_TABLE', 'smsbot-followups')
        )
        
        # Initialize Phase 2 table references (will be None if tables don't exist or DynamoDB unavailable)
        if self.dynamodb:
            try:
                self.students_table = self.dynamodb.Table(self.students_table_name)
                # Test if table exists by trying to describe it
                try:
                    self.students_table.meta.client.describe_table(TableName=self.students_table_name)
                except:
                    self.students_table = None
            except:
                self.students_table = None
        else:
            self.students_table = None
        
        if self.dynamodb:
            try:
                self.deadlines_table = self.dynamodb.Table(self.deadlines_table_name)
                try:
                    self.deadlines_table.meta.client.describe_table(TableName=self.deadlines_table_name)
                except:
                    self.deadlines_table = None
            except:
                self.deadlines_table = None
            
            try:
                self.followups_table = self.dynamodb.Table(self.followups_table_name)
                try:
                    self.followups_table.meta.client.describe_table(TableName=self.followups_table_name)
                except:
                    self.followups_table = None
            except:
                self.followups_table = None
        else:
            self.deadlines_table = None
            self.followups_table = None
    
    # Conversation methods
    def create_conversation(
        self,
        phone_number: str,
        trigger_type: Optional[str] = None,
        trigger_id: Optional[str] = None,
        initial_message: Optional[str] = None
    ) -> str:
        """
        Create a new conversation.
        
        Args:
            phone_number: Student phone number
            trigger_type: Type of trigger that started conversation
            trigger_id: ID of trigger
            initial_message: Initial message sent
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'conversation_id': conversation_id,
            'phone_number': phone_number,
            'created_at': timestamp,
            'updated_at': timestamp,
            'status': 'active',
            'messages': [],
            'trigger_type': trigger_type,
            'trigger_id': trigger_id,
            'action_items': []  # Phase 2: Track action items
        }
        
        if initial_message:
            item['messages'].append({
                'role': 'assistant',
                'content': initial_message,
                'timestamp': timestamp
            })
        
        # Try DynamoDB first
        if self.conversations_table:
            try:
                self.conversations_table.put_item(Item=item)
                return conversation_id
            except Exception as e:
                print(f"⚠️  Failed to save to DynamoDB: {e}, using in-memory storage")
        
        # Fallback to in-memory storage
        with self._memory_lock:
            self._memory_store[conversation_id] = item
            # Also index by phone number for quick lookup
            if 'phone_index' not in self._memory_store:
                self._memory_store['phone_index'] = {}
            self._memory_store['phone_index'][phone_number] = conversation_id
        print("⚠️  DynamoDB not available - using in-memory storage")
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation by ID."""
        # Try DynamoDB first
        if self.conversations_table:
            try:
                response = self.conversations_table.get_item(
                    Key={'conversation_id': conversation_id}
                )
                if 'Item' in response:
                    return response.get('Item')
            except Exception as e:
                print(f"Error getting conversation from DynamoDB: {e}, trying in-memory")
        
        # Fallback to in-memory storage
        with self._memory_lock:
            return self._memory_store.get(conversation_id)
    
    def get_conversation_by_phone(self, phone_number: str) -> Optional[Dict]:
        """Get most recent active conversation for phone number."""
        # Try DynamoDB first
        if self.conversations_table:
            try:
                response = self.conversations_table.query(
                    IndexName='PhoneNumberIndex',
                    KeyConditionExpression=Key('phone_number').eq(phone_number),
                    FilterExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'active'},
                    ScanIndexForward=False,
                    Limit=1
                )
                items = response.get('Items', [])
                if items:
                    return items[0]
            except Exception as e:
                print(f"Error getting conversation by phone from DynamoDB: {e}, trying in-memory")
        
        # Fallback to in-memory storage
        with self._memory_lock:
            phone_index = self._memory_store.get('phone_index', {})
            conv_id = phone_index.get(phone_number)
            if conv_id:
                return self._memory_store.get(conv_id)
        return None
    
    def get_conversations_by_phone(self, phone_number: str, limit: int = 50) -> List[Dict]:
        """Get all conversations for a phone number (or username for web students)."""
        # Try DynamoDB first
        if self.conversations_table:
            try:
                response = self.conversations_table.query(
                    IndexName='PhoneNumberIndex',
                    KeyConditionExpression=Key('phone_number').eq(phone_number),
                    ScanIndexForward=False,  # Most recent first
                    Limit=limit
                )
                return response.get('Items', [])
            except Exception as e:
                print(f"Error getting conversations by phone from DynamoDB: {e}, trying in-memory")
        
        # Fallback to in-memory storage
        conversations = []
        with self._memory_lock:
            for conv_id, conv_data in self._memory_store.items():
                if isinstance(conv_data, dict) and conv_data.get('phone_number') == phone_number:
                    conversations.append(conv_data)
        
        # Sort by created_at (most recent first)
        conversations.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return conversations[:limit]
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Add message to conversation.
        
        Args:
            conversation_id: Conversation ID
            role: 'user' or 'assistant'
            content: Message content
            
        Returns:
            True if successful
        """
        # Validate conversation_id
        if not conversation_id or not conversation_id.strip():
            print(f"Error: conversation_id is empty or None when adding message")
            return False
        
        timestamp = datetime.utcnow().isoformat()
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp
        }
        
        # Try DynamoDB first
        if self.conversations_table:
            try:
                # Ensure action_items list exists (Phase 2)
                self.conversations_table.update_item(
                    Key={'conversation_id': conversation_id},
                    UpdateExpression='SET #messages = list_append(if_not_exists(#messages, :empty_list), :message), updated_at = :timestamp, action_items = if_not_exists(action_items, :empty_action_items)',
                    ExpressionAttributeNames={'#messages': 'messages'},
                    ExpressionAttributeValues={
                        ':message': [message],
                        ':timestamp': timestamp,
                        ':empty_list': [],
                        ':empty_action_items': []
                    }
                )
                return True
            except Exception as e:
                print(f"Error adding message to DynamoDB: {e}, using in-memory storage")
        
        # Fallback to in-memory storage
        with self._memory_lock:
            if conversation_id in self._memory_store:
                conv = self._memory_store[conversation_id]
                if 'messages' not in conv:
                    conv['messages'] = []
                conv['messages'].append(message)
                conv['updated_at'] = timestamp
                return True
            else:
                print(f"Warning: Conversation {conversation_id} not found in memory store")
                return False
    
    def add_action_item(
        self,
        conversation_id: str,
        action: str,
        status: str = 'pending',
        due_date: Optional[str] = None
    ) -> bool:
        """
        Add an action item to a conversation (Phase 2).
        
        Args:
            conversation_id: Conversation ID
            action: Description of the action item
            status: Status (pending, in_progress, completed)
            due_date: Optional due date (ISO format)
            
        Returns:
            True if successful
        """
        if not conversation_id or not conversation_id.strip():
            return False
        
        try:
            action_item = {
                'action_id': str(uuid.uuid4()),
                'action': action,
                'status': status,
                'created_at': datetime.utcnow().isoformat()
            }
            
            if due_date:
                action_item['due_date'] = due_date
            
            self.conversations_table.update_item(
                Key={'conversation_id': conversation_id},
                UpdateExpression='SET action_items = list_append(if_not_exists(action_items, :empty_list), :action_item), updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':action_item': [action_item],
                    ':empty_list': [],
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error adding action item: {e}")
            return False
    
    def update_action_item_status(
        self,
        conversation_id: str,
        action_id: str,
        status: str
    ) -> bool:
        """Update status of an action item."""
        if not conversation_id or not conversation_id.strip():
            return False
        
        try:
            # Get conversation to find the action item
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            action_items = conversation.get('action_items', [])
            updated_items = []
            found = False
            
            for item in action_items:
                if item.get('action_id') == action_id:
                    item['status'] = status
                    item['updated_at'] = datetime.utcnow().isoformat()
                    found = True
                updated_items.append(item)
            
            if not found:
                return False
            
            # Update conversation with modified action items
            self.conversations_table.update_item(
                Key={'conversation_id': conversation_id},
                UpdateExpression='SET action_items = :items, updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':items': updated_items,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating action item: {e}")
            return False
    
    def update_conversation_status(
        self,
        conversation_id: str,
        status: str
    ) -> bool:
        """Update conversation status (e.g., 'active', 'completed', 'escalated')."""
        # Validate conversation_id
        if not conversation_id or not conversation_id.strip():
            print(f"Error: conversation_id is empty or None when updating status")
            return False
        
        try:
            self.conversations_table.update_item(
                Key={'conversation_id': conversation_id},
                UpdateExpression='SET #status = :status, updated_at = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating conversation status: {e}")
            return False
    
    def list_conversations(
        self,
        limit: int = 50,
        last_key: Optional[Dict] = None
    ) -> Dict:
        """List all conversations with pagination."""
        try:
            scan_kwargs = {'Limit': limit}
            if last_key:
                scan_kwargs['ExclusiveStartKey'] = last_key
            
            response = self.conversations_table.scan(**scan_kwargs)
            
            # Sort by updated_at descending
            items = sorted(
                response.get('Items', []),
                key=lambda x: x.get('updated_at', ''),
                reverse=True
            )
            
            return {
                'conversations': items,
                'last_key': response.get('LastEvaluatedKey')
            }
        except Exception as e:
            print(f"Error listing conversations: {e}")
            return {'conversations': [], 'last_key': None}
    
    # Trigger methods
    def create_trigger(
        self,
        phone_number: str,
        trigger_type: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a trigger record.
        
        Args:
            phone_number: Student phone number
            trigger_type: Type of trigger (overdue_balance, not_registered, etc.)
            metadata: Additional metadata
            
        Returns:
            Trigger ID
        """
        trigger_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'trigger_id': trigger_id,
            'phone_number': phone_number,
            'trigger_type': trigger_type,
            'created_at': timestamp,
            'status': 'pending',
            'metadata': metadata or {}
        }
        
        self.triggers_table.put_item(Item=item)
        return trigger_id
    
    def get_trigger(self, trigger_id: str) -> Optional[Dict]:
        """Get trigger by ID."""
        try:
            response = self.triggers_table.get_item(
                Key={'trigger_id': trigger_id}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting trigger: {e}")
            return None
    
    def update_trigger_status(
        self,
        trigger_id: str,
        status: str,
        conversation_id: Optional[str] = None
    ) -> bool:
        """Update trigger status."""
        try:
            update_expr = 'SET #status = :status'
            expr_attrs = {
                ':status': status
            }
            
            if conversation_id:
                update_expr += ', conversation_id = :conv_id'
                expr_attrs[':conv_id'] = conversation_id
            
            self.triggers_table.update_item(
                Key={'trigger_id': trigger_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expr_attrs
            )
            return True
        except Exception as e:
            print(f"Error updating trigger status: {e}")
            return False
    
    def list_triggers(
        self,
        limit: int = 50
    ) -> List[Dict]:
        """List all triggers."""
        try:
            response = self.triggers_table.scan(Limit=limit)
            items = sorted(
                response.get('Items', []),
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
            return items
        except Exception as e:
            print(f"Error listing triggers: {e}")
            return []
    
    # Result methods
    def create_result(
        self,
        conversation_id: str,
        result_type: str,
        phone_number: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a result record (called by finish() function).
        
        Args:
            conversation_id: Conversation ID
            result_type: Type of result (paid, registered, resolved, etc.)
            phone_number: Student phone number
            metadata: Additional metadata
            
        Returns:
            Result ID
        """
        result_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'result_id': result_id,
            'conversation_id': conversation_id,
            'created_at': timestamp,
            'result_type': result_type,
            'metadata': metadata or {}
        }
        
        if phone_number:
            item['phone_number'] = phone_number
        
        self.results_table.put_item(Item=item)
        return result_id
    
    def get_results_by_conversation(self, conversation_id: str) -> List[Dict]:
        """Get all results for a conversation."""
        try:
            response = self.results_table.query(
                IndexName='ConversationIndex',
                KeyConditionExpression=Key('conversation_id').eq(conversation_id)
            )
            return sorted(
                response.get('Items', []),
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
        except Exception as e:
            print(f"Error getting results: {e}")
            return []
    
    def list_results(self, limit: int = 50) -> List[Dict]:
        """List all results."""
        try:
            response = self.results_table.scan(Limit=limit)
            return sorted(
                response.get('Items', []),
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
        except Exception as e:
            print(f"Error listing results: {e}")
            return []
    
    # Phase 2: Student Profile methods
    def create_or_update_student(
        self,
        phone_number: str,
        student_id: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        program: Optional[str] = None,
        enrollment_status: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create or update a student profile.
        
        Args:
            phone_number: Student phone number (primary identifier)
            student_id: Student ID (optional)
            name: Student name (optional)
            email: Student email (optional)
            program: Program/major (optional)
            enrollment_status: Current enrollment status (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Phone number (used as key)
        """
        if not self.students_table:
            raise ValueError("Students table not initialized")
        
        # Verify table actually exists before trying to use it
        try:
            self.students_table.meta.client.describe_table(TableName=self.students_table_name)
        except Exception as e:
            # Table doesn't exist - raise a specific exception that can be caught
            error_type = type(e).__name__
            if 'ResourceNotFound' in error_type or 'ResourceNotFoundException' in str(e):
                raise ValueError("Students table does not exist in DynamoDB")
            else:
                raise
        
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'phone_number': phone_number,
            'updated_at': timestamp,
        }
        
        if student_id:
            item['student_id'] = student_id
        if name:
            item['name'] = name
        if email:
            item['email'] = email
        if program:
            item['program'] = program
        if enrollment_status:
            item['enrollment_status'] = enrollment_status
        if metadata:
            item['metadata'] = metadata
        
        # Check if student exists
        try:
            existing = self.students_table.get_item(Key={'phone_number': phone_number})
            if 'Item' in existing:
                # Update existing
                item['created_at'] = existing['Item'].get('created_at', timestamp)
                # Merge metadata if exists
                if 'metadata' in existing['Item'] and metadata:
                    existing_metadata = existing['Item']['metadata']
                    existing_metadata.update(metadata)
                    item['metadata'] = existing_metadata
            else:
                item['created_at'] = timestamp
        except:
            item['created_at'] = timestamp
        
        self.students_table.put_item(Item=item)
        return phone_number
    
    def get_student(self, phone_number: str) -> Optional[Dict]:
        """Get student profile by phone number."""
        if not self.students_table:
            return None
        
        try:
            # Verify table exists before trying to use it
            self.students_table.meta.client.describe_table(TableName=self.students_table_name)
            response = self.students_table.get_item(
                Key={'phone_number': phone_number}
            )
            return response.get('Item')
        except Exception as e:
            # Table doesn't exist or other error - return None silently
            error_type = type(e).__name__
            if 'ResourceNotFound' not in error_type and 'ResourceNotFoundException' not in str(e):
                print(f"Error getting student: {e}")
            return None
    
    # Student Authentication methods
    def create_student_account(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        name: Optional[str] = None
    ) -> str:
        """
        Create a new student account with username/password.
        Uses username-based authentication (stores username in phone_number field temporarily).
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            email: Optional email
            name: Optional name
            
        Returns:
            Student ID (UUID)
        """
        if not self.students_table:
            raise ValueError("Students table not initialized")
        
        try:
            self.students_table.meta.client.describe_table(TableName=self.students_table_name)
        except Exception as e:
            error_type = type(e).__name__
            if 'ResourceNotFound' in error_type or 'ResourceNotFoundException' in str(e):
                raise ValueError("Students table does not exist in DynamoDB")
            else:
                raise
        
        # Hash password
        try:
            import bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except ImportError:
            password_hash = password  # Plain text for dev (not secure)
        
        timestamp = datetime.utcnow().isoformat()
        student_id = str(uuid.uuid4())
        
        # Check if username already exists
        existing = self.get_student_by_username(username)
        if existing:
            raise ValueError("Username already exists")
        
        # Store with username as identifier (using phone_number field as key since it's the PK)
        # In production, consider adding a GSI on username
        item = {
            'phone_number': f"AUTH:{username}",  # Use phone_number field as key with prefix
            'username': username,
            'password_hash': password_hash,
            'student_id': student_id,
            'created_at': timestamp,
            'updated_at': timestamp,
            'account_type': 'authenticated'  # Flag to distinguish from phone-based accounts
        }
        
        if email:
            item['email'] = email
        if name:
            item['name'] = name
        
        self.students_table.put_item(Item=item)
        return student_id
    
    def get_student_by_username(self, username: str) -> Optional[Dict]:
        """Get student account by username."""
        if not self.students_table:
            return None
        
        try:
            self.students_table.meta.client.describe_table(TableName=self.students_table_name)
            
            # Try direct lookup first (faster if username format is known)
            try:
                response = self.students_table.get_item(
                    Key={'phone_number': f"AUTH:{username}"}
                )
                if 'Item' in response:
                    return response['Item']
            except:
                pass
            
            # Fallback: scan for username (inefficient but works without GSI)
            # TODO: Add GSI on username for better performance
            response = self.students_table.scan(
                FilterExpression='username = :username',
                ExpressionAttributeValues={':username': username},
                Limit=1
            )
            
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            error_type = type(e).__name__
            if 'ResourceNotFound' not in error_type and 'ResourceNotFoundException' not in str(e):
                print(f"Error getting student by username: {e}")
            return None
    
    def update_student_metadata(self, phone_number: str, metadata_updates: Dict) -> bool:
        """Update student metadata (merge with existing)."""
        if not self.students_table:
            return False
        
        try:
            # Get existing metadata
            student = self.get_student(phone_number)
            existing_metadata = student.get('metadata', {}) if student else {}
            
            # Merge updates
            existing_metadata.update(metadata_updates)
            
            # Update
            self.students_table.update_item(
                Key={'phone_number': phone_number},
                UpdateExpression='SET #metadata = :metadata, updated_at = :timestamp',
                ExpressionAttributeNames={'#metadata': 'metadata'},
                ExpressionAttributeValues={
                    ':metadata': existing_metadata,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating student metadata: {e}")
            return False
    
    # Phase 2: Deadline methods
    def store_deadline(self, deadline: Dict) -> str:
        """
        Store a deadline in the database.
        
        Args:
            deadline: Deadline dictionary with date, description, category, etc.
            
        Returns:
            Deadline ID
        """
        if not self.deadlines_table:
            raise ValueError("Deadlines table not initialized")
        
        deadline_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'deadline_id': deadline_id,
            'date': deadline.get('date'),
            'description': deadline.get('description'),
            'category': deadline.get('category', 'general'),
            'date_text': deadline.get('date_text', ''),
            'url': deadline.get('url', ''),
            'scraped_at': deadline.get('scraped_at', timestamp),
            'created_at': timestamp
        }
        
        if 'days_until' in deadline:
            item['days_until'] = deadline['days_until']
        
        self.deadlines_table.put_item(Item=item)
        return deadline_id
    
    def get_deadlines_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get deadlines by category."""
        if not self.deadlines_table:
            return []
        
        try:
            # Note: This requires a GSI on category, or we scan and filter
            response = self.deadlines_table.scan(
                FilterExpression='#category = :category',
                ExpressionAttributeNames={'#category': 'category'},
                ExpressionAttributeValues={':category': category},
                Limit=limit
            )
            return sorted(
                response.get('Items', []),
                key=lambda x: x.get('date', ''),
                reverse=False  # Oldest first
            )
        except Exception as e:
            print(f"Error getting deadlines by category: {e}")
            return []
    
    def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[Dict]:
        """Get deadlines within the next N days."""
        if not self.deadlines_table:
            return []
        
        try:
            from datetime import datetime, timedelta
            today = datetime.utcnow()
            cutoff = (today + timedelta(days=days_ahead)).isoformat()
            
            # Scan and filter (for production, add a GSI on date)
            response = self.deadlines_table.scan()
            all_deadlines = response.get('Items', [])
            
            upcoming = []
            for deadline in all_deadlines:
                deadline_date_str = deadline.get('date', '')
                if deadline_date_str and deadline_date_str <= cutoff:
                    try:
                        deadline_date = datetime.fromisoformat(deadline_date_str.replace('Z', '+00:00'))
                        if deadline_date >= today:
                            days_until = (deadline_date - today).days
                            deadline['days_until'] = days_until
                            upcoming.append(deadline)
                    except:
                        continue
            
            return sorted(upcoming, key=lambda x: x.get('date', ''))
        except Exception as e:
            print(f"Error getting upcoming deadlines: {e}")
            return []
    
    # Phase 2: Follow-up methods
    def create_followup(
        self,
        phone_number: str,
        followup_date: str,  # ISO format datetime
        trigger_type: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Schedule a follow-up for a student.
        
        Args:
            phone_number: Student phone number
            followup_date: When to follow up (ISO format)
            trigger_type: Type of trigger to send
            conversation_id: Related conversation ID (optional)
            metadata: Additional metadata
            
        Returns:
            Follow-up ID
        """
        if not self.followups_table:
            raise ValueError("Followups table not initialized")
        
        followup_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'followup_id': followup_id,
            'phone_number': phone_number,
            'followup_date': followup_date,
            'created_at': timestamp,
            'status': 'pending',
            'metadata': metadata or {}
        }
        
        if trigger_type:
            item['trigger_type'] = trigger_type
        if conversation_id:
            item['conversation_id'] = conversation_id
        
        self.followups_table.put_item(Item=item)
        return followup_id
    
    def get_due_followups(self, limit: int = 100) -> List[Dict]:
        """
        Get follow-ups that are due (followup_date <= now).
        
        Args:
            limit: Maximum number of follow-ups to return
            
        Returns:
            List of due follow-ups
        """
        if not self.followups_table:
            return []
        
        try:
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            
            # Scan and filter (for production, add a GSI on followup_date)
            response = self.followups_table.scan(
                FilterExpression='#status = :status AND followup_date <= :now',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'pending',
                    ':now': now
                },
                Limit=limit
            )
            
            return sorted(
                response.get('Items', []),
                key=lambda x: x.get('followup_date', ''),
                reverse=False  # Oldest first
            )
        except Exception as e:
            print(f"Error getting due followups: {e}")
            return []
    
    def update_followup_status(
        self,
        followup_id: str,
        status: str,
        conversation_id: Optional[str] = None
    ) -> bool:
        """Update follow-up status (e.g., 'pending', 'sent', 'completed')."""
        if not self.followups_table:
            return False
        
        try:
            update_expr = 'SET #status = :status, updated_at = :timestamp'
            expr_attrs = {
                ':status': status,
                ':timestamp': datetime.utcnow().isoformat()
            }
            
            if conversation_id:
                update_expr += ', conversation_id = :conv_id'
                expr_attrs[':conv_id'] = conversation_id
            
            self.followups_table.update_item(
                Key={'followup_id': followup_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expr_attrs
            )
            return True
        except Exception as e:
            print(f"Error updating followup status: {e}")
            return False

