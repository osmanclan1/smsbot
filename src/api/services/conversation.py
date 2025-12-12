"""
Conversation engine with OpenAI GPT-4 integration.
"""

import os
import json
import re
from typing import Dict, List, Optional
from openai import OpenAI
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from storage.dynamodb import DynamoDBService
from api.services.knowledge_base import KnowledgeBaseService
from utils.logger import finish


class ConversationEngine:
    """Engine for handling AI conversations."""
    
    # Link request patterns - common ways students ask for links
    LINK_REQUEST_PATTERNS = [
        r'\bwhere\s+(do\s+I\s+)?(pay|register|drop|withdraw|apply|login|access)',
        r'\b(link|url|page|website|portal)\s+(for|to|to\s+pay|to\s+register)',
        r'\b(payment|registration|registration\s+page|academic\s+calendar|drop\s+class|withdraw)',
        r'\bsend\s+me\s+(the\s+)?(link|url|page)',
        r'\bhow\s+do\s+I\s+(pay|register|drop|access|login)',
        r'\b(pay|register|drop|login|access)\s+(link|page|url|website)',
    ]
    
    # Policy explanation patterns - ways students ask about policies
    POLICY_REQUEST_PATTERNS = [
        r'\b(explain|what\s+is|tell\s+me\s+about|how\s+does)\s+(the\s+)?(withdrawal|withdraw|drop|payment|refund|SAP|satisfactory\s+academic|attendance|policy)',
        r'\b(withdrawal|withdraw|drop|payment|refund|SAP|satisfactory\s+academic|attendance)\s+(policy|rule|requirement|works)',
        r'\bcan\s+I\s+(withdraw|drop|get\s+a\s+refund|still\s+pay)',
        r'\bwhat\s+happens\s+if\s+I\s+(withdraw|drop|don\'t\s+pay)',
    ]
    
    # Financial aid question patterns
    FINANCIAL_AID_PATTERNS = [
        r'\b(financial\s+aid|fafsa|pell|grant|scholarship|disbursement|verification|refund)',
        r'\bwhy\s+(didn\'t|did\s+not|hasn\'t|has\s+not)\s+(my\s+)?(aid|money|funds|payment)',
        r'\bwhen\s+(will|do)\s+(I\s+get|my\s+aid|financial\s+aid)',
        r'\b(explain|what\s+is|tell\s+me\s+about)\s+(fafsa|verification|disbursement|pell|financial\s+aid)',
        r'\b(dependent|independent|eligibility|sap)\s+(status|requirement)',
    ]
    
    # Hold-related patterns
    HOLD_PATTERNS = [
        r'\b(hold|blocked|can\'t\s+register|registration\s+blocked)',
        r'\bwhy\s+can\'t\s+I\s+register',
        r'\b(fix|remove|resolve|clear)\s+(my\s+)?(hold|block)',
        r'\bwhat\s+(is|does)\s+(the\s+)?(hold|block)\s+mean',
    ]
    
    # Registration troubleshooting patterns
    REGISTRATION_TROUBLESHOOT_PATTERNS = [
        r'\bwhy\s+can\'t\s+I\s+register',
        r'\b(can\'t|cannot)\s+register',
        r'\bregistration\s+(error|blocked|won\'t\s+work|problem)',
        r'\bwhat\s+(message|error)\s+(do\s+I\s+see|am\s+I\s+seeing)',
        r'\b(error|message|blocked)\s+(when\s+)?(trying\s+to\s+)?register',
    ]
    
    # Next steps wizard patterns
    NEXT_STEPS_PATTERNS = [
        r'\bwhat\s+(do\s+I\s+need\s+to\s+do|should\s+I\s+do|are\s+my\s+next\s+steps)',
        r'\btell\s+me\s+what\s+I\s+need\s+to\s+do',
        r'\bwhat\'s\s+next',
        r'\bhelp\s+me\s+figure\s+out\s+what\s+to\s+do',
        r'\bwhat\s+should\s+I\s+do\s+next',
        r'\bchecklist|next\s+steps|what\s+to\s+do',
    ]
    
    # Wizard questions (in order)
    WIZARD_QUESTIONS = [
        {
            'key': 'registered',
            'question': 'Have you registered for classes yet? (yes/no)',
            'follow_up': 'Which semester are you trying to register for?'
        },
        {
            'key': 'payment',
            'question': 'Do you have any outstanding balance or payment due? (yes/no/not sure)',
            'follow_up': 'How much do you owe? (or "not sure")'
        },
        {
            'key': 'documents',
            'question': 'Do you need to submit any documents? (transcripts, vaccination proof, financial aid forms, etc.)',
            'follow_up': 'What documents do you need to submit?'
        },
        {
            'key': 'holds',
            'question': 'Do you have any holds on your account? (yes/no/not sure)',
            'follow_up': 'What does the hold message say?'
        }
    ]
    
    TRIGGER_MESSAGES = {
        "overdue_balance": "Hi! I noticed you have an outstanding balance on your account. I'm here to help you understand your options and get it paid. What questions do you have?",
        "not_registered": "Hey! Registration opens soon. Want help planning your classes and getting registered?",
        "upcoming_deadline": "Hi! I wanted to let you know about an important deadline coming up. Would you like me to help you prepare?",
        "hold_on_account": "Hi! There's a hold on your account that might prevent registration. I can help you understand what it is and how to resolve it. What would you like to know?",
        # Phase 1: New proactive reminder triggers
        "payment_deadline_7days": "Hi! Your payment deadline is in 7 days. Want help understanding your payment options or setting up EZ Pay?",
        "payment_deadline_3days": "Hi! Your payment deadline is in 3 days. I can help you pay now or set up a payment plan. What would you like to do?",
        "payment_deadline_1day": "⚠️ Your payment deadline is tomorrow! Let me help you get this sorted quickly. What questions do you have?",
        "registration_opens": "Good news! Registration opens soon. I can help you find classes, check prerequisites, and get registered. Ready to start?",
        "class_starts_soon": "Heads up! Classes start soon. Make sure you're registered, have your textbooks, and know where your classes are. Need help with any of that?",
        "drop_deadline_warning": "Reminder: The deadline to drop classes with a refund is coming up. If you need to adjust your schedule, let me know and I can help!",
        "financial_aid_deadline": "Important: Financial aid deadline is approaching. Need help with FAFSA, scholarships, or other aid options? I'm here to help!",
        "advising_reminder": "Time for advising! Schedule a meeting with your advisor to plan next semester. Want help finding your advisor or preparing questions?",
        "graduation_checklist": "Congrats on getting close to graduation! Let me help you check off remaining requirements and deadlines. What do you need help with?",
        "default": "Hi! I'm here to help with any questions about Oakton Community College. How can I assist you today?"
    }
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None
    ):
        """Initialize conversation engine."""
        self.db = DynamoDBService()
        self.kb = KnowledgeBaseService(
            openai_api_key=openai_api_key,
            pinecone_api_key=pinecone_api_key
        )
        
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
    
    def get_initial_message(self, trigger_type: Optional[str] = None) -> str:
        """Get initial message based on trigger type."""
        return self.TRIGGER_MESSAGES.get(trigger_type or "default", self.TRIGGER_MESSAGES["default"])
    
    def generate_response(
        self,
        conversation_id: str,
        user_message: str,
        phone_number: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate AI response to user message.
        
        Args:
            conversation_id: Conversation ID
            user_message: User's message
            phone_number: Phone number (optional, used for profile checks)
            
        Returns:
            Dictionary with response text and action (if any)
        """
        # Validate conversation_id
        if not conversation_id or not conversation_id.strip():
            return {"response": "I'm sorry, I encountered an error. Let's start fresh!"}
        
        # Get conversation from database
        conversation = self.db.get_conversation(conversation_id)
        if not conversation:
            return {"response": "I'm sorry, I couldn't find our conversation. Let's start fresh!"}
        
        # Get phone number from conversation if not provided
        if not phone_number:
            phone_number = conversation.get('phone_number')
        
        # Check if student profile exists
        student_profile = None
        needs_profile_setup = False
        students_table_available = False
        
        if phone_number and self.db.students_table:
            try:
                # Verify table actually exists by trying to describe it
                self.db.students_table.meta.client.describe_table(TableName=self.db.students_table_name)
                students_table_available = True
                student_profile = self.db.get_student(phone_number)
                # Check if this is a new conversation (only 1-2 messages) and no profile exists
                messages = conversation.get('messages', [])
                is_new_conversation = len([m for m in messages if m.get('role') == 'user']) <= 1
                needs_profile_setup = is_new_conversation and not student_profile
            except Exception as e:
                # Table doesn't exist or other error - skip profile collection
                students_table_available = False
                print(f"Note: Students table not available, skipping profile collection: {e}")
        
        # Add user message to conversation
        self.db.add_message(conversation_id, 'user', user_message)
        
        # Get conversation history
        messages = conversation.get('messages', [])
        
        # Check if we're in profile collection flow
        is_in_profile_flow = self._is_in_profile_collection_flow(conversation)
        
        # Detect if this is a link request, policy question, financial aid question, hold question, registration troubleshoot, or next steps wizard
        is_link_request = self._is_link_request(user_message)
        is_policy_request = self._is_policy_request(user_message)
        is_financial_aid_request = self._is_financial_aid_request(user_message)
        is_hold_request = self._is_hold_request(user_message)
        is_in_hold_flow = self._is_in_hold_diagnosis_flow(conversation)
        is_registration_troubleshoot = self._is_registration_troubleshoot_request(user_message)
        is_in_registration_flow = self._is_in_registration_troubleshoot_flow(conversation)
        is_next_steps_request = self._is_next_steps_request(user_message)
        is_in_wizard_flow = self._is_in_wizard_flow(conversation)
        
        # Get relevant context from knowledge base (prioritize links if link request)
        context = self.kb.get_context_for_conversation(
            user_message, 
            messages, 
            prioritize_links=is_link_request
        )
        
        # Build system prompt
        trigger_type = conversation.get('trigger_type', 'default')
        trigger_context = ""
        
        # Add trigger-specific context to help AI be more proactive
        if trigger_type:
            trigger_context = f"\nCURRENT CONVERSATION CONTEXT:\nThis conversation was initiated by a '{trigger_type}' trigger. "
            
            if 'payment_deadline' in trigger_type:
                trigger_context += "You're reminding the student about a payment deadline. Be proactive: offer payment options, explain EZ Pay, and help them take action now."
            elif trigger_type == 'registration_opens':
                trigger_context += "Registration is opening. Help them get ready: check prerequisites, find classes, and register early."
            elif trigger_type == 'class_starts_soon':
                trigger_context += "Classes start soon. Make sure they're ready: registered, have textbooks, know locations."
            elif 'deadline' in trigger_type:
                trigger_context += "There's an important deadline coming up. Explain what it means, why it matters, and help them prepare."
            elif trigger_type in ['advising_reminder', 'graduation_checklist']:
                trigger_context += "This is academic planning related. Help them organize, prepare questions, and take next steps."
        
        # Build base system prompt
        base_prompt = """You're a proactive SMS assistant for Oakton Community College. Help students with: tuition/payments (EZ Pay), registration, financial aid, deadlines, account holds, general info.

BE PROACTIVE: Offer next steps, break down tasks (1, 2, 3...), reference previous context, anticipate needs, use encouraging language.

STYLE: Friendly, SMS-length (160-300 chars), numbered steps, include full URLs.

REMINDERS: Acknowledge deadline immediately, explain importance, offer specific help, give next steps.

Call finish() when: action completed (paid/registered), issue resolved, student done, or conversation ends.

Result types: paid, registered, resolved, reminder_sent, escalated, no_response, abandoned.

Use provided context. Always be proactive and helpful."""
        
        # Add profile collection instructions if needed
        if needs_profile_setup or is_in_profile_flow:
            profile_progress = self._get_profile_progress(conversation) if is_in_profile_flow else {}
            base_prompt += """

PROFILE SETUP: This is a new student. Collect their basic information naturally:
1. Ask for their name first: "Hi! To help you better, what's your name?"
2. After they answer, ask for student ID: "Thanks [name]! What's your student ID?"
3. Then ask about program: "What program are you studying?"

Ask ONE question at a time. Wait for their answer before asking the next. Be friendly and casual.
Once you have their name, use it in your responses."""
        
            if profile_progress:
                collected_info = "\n".join([f"- {k}: {v}" for k, v in profile_progress.items()])
                base_prompt += f"\n\nCOLLECTED SO FAR:\n{collected_info}\n\nContinue collecting missing information."
        
        # Add link request handling instructions
        if is_link_request:
            base_prompt += """

LINK REQUESTS: The student is asking for a link/page. Respond quickly with:
- The exact URL they need (full URL, not shortened)
- A brief 1-sentence explanation of what the page is for
- Format: "Here's the [page name] → [full URL]. [Brief explanation]"
Example: "Here's the payment page → https://www.oakton.edu/paying-for-college/payment-options.php. Pay your tuition here."
If multiple relevant links exist, list the most important one first."""
        
        # Add policy explanation instructions
        if is_policy_request:
            base_prompt += """

POLICY EXPLANATIONS: The student is asking about a policy. Explain it like they're 17 years old:
- Use simple, plain English (no jargon)
- Maximum 3 sentences
- Focus on what it means for them personally
- Be clear about deadlines, consequences, and what they need to do
- Cover: withdrawal policy, payment policy, refund schedule, SAP (Satisfactory Academic Progress), attendance requirements

Format: "[Policy name] means [simple explanation]. [What they need to know]. [What to do/avoid]."
Example: 'Withdrawal policy means you can drop classes before a deadline and get a refund. After the deadline, you'll get a W on your transcript but no refund. Check the important dates page for exact deadlines."""
        
        # Add financial aid explanation instructions
        if is_financial_aid_request:
            base_prompt += """

FINANCIAL AID EXPLANATIONS: The student is asking about financial aid. Explain in plain English:
- Use simple language (no financial jargon)
- Explain what it means, why it might be delayed, what they need to do, and who to contact
- Cover: FAFSA, verification, disbursement, refunds, SAP, Pell eligibility, dependent/independent status

Common explanations:
- FAFSA: Free application for federal student aid. Fill it out every year to get grants/loans.
- Verification: School needs to check your FAFSA info. Submit documents they request.
- Disbursement: When aid money gets sent to your school account (usually after classes start).
- SAP: You must pass classes and keep good grades to keep getting aid.
- Pell Grant: Free money from government (don\'t pay back) based on financial need.
- Dependent vs Independent: If you're under 24, you're usually dependent (use parents' income).

If they ask "why didn't my aid hit?":
1. Explain common delays (verification pending, classes not started, SAP issues)
2. Tell them what to check
3. Give them Oakton Financial Aid office contact info

Always include: 'Contact Oakton Financial Aid office at [phone/email from context] if you need more help.'"""
        
        # Add hold diagnosis instructions
        if is_hold_request or is_in_hold_flow:
            hold_message = self._get_hold_message_from_conversation(conversation) if is_in_hold_flow else None
            
            if not hold_message and not is_in_hold_flow:
                # First time asking about hold - ask for the hold message
                base_prompt += """

HOLD DIAGNOSIS: The student is asking about a hold. Start by asking:
"What hold message do you see exactly? You can type the first line or describe it."

Wait for their response before providing fix steps."""
            else:
                # We have the hold message or are in flow - provide diagnosis
                hold_context = f"\n\nHOLD MESSAGE FROM STUDENT: {hold_message}" if hold_message else ""
                base_prompt += f"""

HOLD DIAGNOSIS + FIX GUIDE: The student has a hold. Provide step-by-step fix instructions:
1. What the hold means (in simple terms)
2. Who to contact (specific office/phone/email from context)
3. Documents needed (if any)
4. How long removal takes (if known)
5. Step-by-step instructions to resolve

                Format:
"Your [hold type] hold means [explanation]. To fix it:
1. [First step]
2. [Second step]
3. [Third step]

Contact [office name] at [phone/email] if you need help. Usually takes [timeframe] to remove."

Use the hold message and knowledge base context to identify the hold type and provide specific instructions.{hold_context}"""
        
        # Add registration troubleshooting instructions
        if is_registration_troubleshoot or is_in_registration_flow:
            error_message = self._get_registration_error_from_conversation(conversation) if is_in_registration_flow else None
            
            if not error_message and not is_in_registration_flow:
                # First time asking about registration problem - ask for error message
                base_prompt += """

REGISTRATION TROUBLESHOOTING: The student can't register. Start by asking:
"What message do you see on your screen when you try to register? Type the exact error or describe it."

Wait for their response before providing fix steps."""
            else:
                # We have the error message or are in flow - provide diagnosis
                error_context = f"\n\nERROR MESSAGE FROM STUDENT: {error_message}" if error_message else ""
                base_prompt += f"""

REGISTRATION TROUBLESHOOTING: The student can't register. Common causes and fixes:
1. HOLD: Account hold blocking registration → Fix the hold first
2. UNPAID BALANCE: Outstanding balance → Pay balance or set up payment plan
3. PREREQUISITE: Missing prerequisite course → Complete prerequisite or get override
4. ADVISING REQUIREMENT: Must meet with advisor → Schedule advising appointment
5. TIME CONFLICT: Classes overlap → Change class times
6. CLASS FULL: No seats available → Waitlist or choose different class

Provide exact fix steps based on the error message:
- What the error means
- Why it's happening
- Step-by-step fix (1, 2, 3...)
- Link to relevant Oakton page
- Who to contact if needed

Format:
"Your error means [explanation]. Here's how to fix it:
1. [First step]
2. [Second step]
3. [Third step]

[Link to relevant page if available]

Contact [office] at [phone/email] if you need help."

Use the error message and knowledge base context to identify the cause and provide specific fix instructions.{error_context}"""
        
        # Add next steps wizard instructions
        if is_next_steps_request or is_in_wizard_flow:
            wizard_progress = self._get_wizard_progress(conversation)
            next_question = self._get_next_wizard_question(wizard_progress)
            
            if next_question and len(wizard_progress['answers']) < len(self.WIZARD_QUESTIONS):
                # Still asking questions
                answers_summary = "\n".join([f"- {k}: {v}" for k, v in wizard_progress['answers'].items()])
                base_prompt += f"""

NEXT STEPS WIZARD: You're helping the student figure out what they need to do next. Ask diagnostic questions one at a time.

CURRENT PROGRESS:
{answers_summary if answers_summary else "No answers yet"}

NEXT QUESTION TO ASK: "{next_question['question']}"

After they answer, ask the next question. Don't provide the checklist until all questions are answered."""
            else:
                # All questions answered - generate checklist
                answers_summary = "\n".join([f"- {k}: {v}" for k, v in wizard_progress['answers'].items()])
                base_prompt += f"""

NEXT STEPS WIZARD: All diagnostic questions answered. Generate a personalized checklist.

STUDENT ANSWERS:
{answers_summary}

Based on their answers, create a numbered checklist of what they need to do next. Format:

"Based on your situation, here's what you need to do next:

1️⃣ [First action item - be specific]
2️⃣ [Second action item - be specific]
3️⃣ [Third action item - be specific]

[Add more items as needed]

For each item, include:
- What to do
- When to do it (if there's a deadline)
- Where to go/link (if applicable)
- Who to contact (if needed)

Use the knowledge base context to provide accurate information and links."""
        
        system_prompt = base_prompt + trigger_context
        
        # Build messages for OpenAI
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        # Phase 2: Add student profile context if available
        student_context = ""
        try:
            phone_number = conversation.get('phone_number')
            if phone_number and self.db.students_table:
                student_profile = self.db.get_student(phone_number)
                if student_profile:
                    student_context = "\n\nSTUDENT PROFILE:\n"
                    if student_profile.get('name'):
                        student_context += f"Name: {student_profile['name']}\n"
                    if student_profile.get('program'):
                        student_context += f"Program: {student_profile['program']}\n"
                    if student_profile.get('enrollment_status'):
                        student_context += f"Enrollment Status: {student_profile['enrollment_status']}\n"
                    if student_profile.get('metadata'):
                        metadata = student_profile['metadata']
                        if metadata.get('balance'):
                            student_context += f"Outstanding Balance: ${metadata.get('balance')}\n"
        except Exception as e:
            print(f"Note: Could not load student profile: {e}")
        
        # Phase 2: Add upcoming deadlines context
        deadlines_context = ""
        try:
            if self.db.deadlines_table:
                upcoming = self.db.get_upcoming_deadlines(days_ahead=30)
                if upcoming:
                    deadlines_context = "\n\nUPCOMING IMPORTANT DEADLINES:\n"
                    for deadline in upcoming[:5]:  # Top 5 most urgent
                        days_until = deadline.get('days_until', '?')
                        desc = deadline.get('description', '')[:100]
                        deadlines_context += f"- {days_until} days: {desc}\n"
        except Exception as e:
            print(f"Note: Could not load deadlines: {e}")
        
        # Add context if available
        if context:
            openai_messages.append({
                "role": "system",
                "content": f"Relevant information from Oakton website:\n\n{context}{student_context}{deadlines_context}"
            })
        elif student_context or deadlines_context:
            openai_messages.append({
                "role": "system",
                "content": f"{student_context}{deadlines_context}"
            })
        
        # Add conversation history
        for msg in messages[-6:]:  # Last 6 messages for context (reduced from 10 to save tokens)
            role = msg.get('role', 'user')
            if role in ['user', 'assistant']:
                openai_messages.append({
                    "role": role,
                    "content": msg.get('content', '')
                })
        
        # Add current user message
        openai_messages.append({"role": "user", "content": user_message})
        
        # Generate response with function calling capability
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=openai_messages,
                temperature=0.7,
                max_tokens=500,
                functions=[{
                    "name": "finish",
                    "description": "Call this function when the conversation is complete or resolved",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "result_type": {
                                "type": "string",
                                "enum": ["paid", "registered", "resolved", "reminder_sent", "escalated", "no_response", "abandoned"],
                                "description": "Type of result"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional information about the result"
                            }
                        },
                        "required": ["result_type"]
                    }
                }],
                function_call="auto"
            )
            
            message = response.choices[0].message
            
            # Check if function was called
            if message.function_call and message.function_call.name == "finish":
                function_args = json.loads(message.function_call.arguments)
                result_type = function_args.get("result_type", "resolved")
                metadata = function_args.get("metadata", {})
                
                # Call finish function
                phone_number = conversation.get('phone_number')
                finish(conversation_id, result_type, phone_number, metadata)
                
                return {
                    "response": "Great! I've logged that we've resolved this. Is there anything else I can help you with?",
                    "action": "finish",
                    "result_type": result_type
                }
            
            # Get text response
            response_text = message.content or "I'm sorry, I didn't understand that. Could you rephrase?"
            
            # Phase 2: Extract action items from AI response (wrap in try/except so errors don't break response)
            try:
                action_items = self._extract_action_items(response_text, conversation)
                for action_item in action_items:
                    try:
                        self.db.add_action_item(
                            conversation_id=conversation_id,
                            action=action_item['action'],
                            status='pending',
                            due_date=action_item.get('due_date')
                        )
                    except Exception as e:
                        # Silently skip if table doesn't exist
                        print(f"Note: Could not save action item (table may not exist): {e}")
            except Exception as e:
                print(f"Note: Error extracting action items: {e}")
            
            # Extract and save profile information if in profile collection flow (only if table is available)
            # Wrap in try/except so errors don't break the response
            try:
                if students_table_available and phone_number and (needs_profile_setup or is_in_profile_flow):
                    profile_data = self._extract_profile_from_message(user_message, conversation)
                    if profile_data:
                        try:
                            # Double-check table exists before trying to use it
                            if self.db.students_table:
                                try:
                                    self.db.students_table.meta.client.describe_table(TableName=self.db.students_table_name)
                                except Exception:
                                    # Table doesn't exist, skip profile saving
                                    print(f"Note: Students table does not exist, skipping profile save")
                                    profile_data = None
                                
                                if profile_data:
                                    # Get existing profile or create new
                                    existing_profile = self.db.get_student(phone_number) or {}
                                    
                                    # Merge new data
                                    updated_data = {
                                        'name': profile_data.get('name') or existing_profile.get('name'),
                                        'student_id': profile_data.get('student_id') or existing_profile.get('student_id'),
                                        'program': profile_data.get('program') or existing_profile.get('program'),
                                        'email': profile_data.get('email') or existing_profile.get('email'),
                                    }
                                    
                                    # Only update if we have at least one new field
                                    if any(updated_data.values()):
                                        self.db.create_or_update_student(
                                            phone_number=phone_number,
                                            student_id=updated_data.get('student_id'),
                                            name=updated_data.get('name'),
                                            email=updated_data.get('email'),
                                            program=updated_data.get('program')
                                        )
                        except ValueError as e:
                            # Table doesn't exist - this is expected in some deployments
                            if "does not exist" in str(e):
                                print(f"Note: Students table does not exist, skipping profile save")
                            else:
                                print(f"Note: Could not save profile data: {e}")
                        except Exception as e:
                            # Other errors - log but don't fail
                            print(f"Note: Could not save profile data: {e}")
            except Exception as e:
                print(f"Note: Error in profile collection flow: {e}")
            
            # Add assistant response to conversation (wrap in try/except so errors don't break response)
            try:
                self.db.add_message(conversation_id, 'assistant', response_text)
            except Exception as e:
                print(f"Note: Could not save message to conversation (this is OK): {e}")
            
            return {"response": response_text}
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Check if it's a ResourceNotFoundException - this is expected if tables don't exist
            if 'ResourceNotFound' in error_type or 'ResourceNotFoundException' in error_msg:
                # This is likely from a missing table - log but don't fail the conversation
                print(f"Note: DynamoDB table not found (this is OK if tables aren't created yet): {error_msg}")
                # If we have a response_text, return it; otherwise return generic
                # But response_text won't be available here if error happened before generation
                return {"response": "I'm here to help! Could you rephrase your question?"}
            else:
                print(f"Error generating response: {error_msg}")
                traceback.print_exc()
                return {"response": "I'm sorry, I encountered an error. Please try again in a moment."}
    
    def _is_in_profile_collection_flow(self, conversation: Dict) -> bool:
        """
        Check if conversation is in profile collection flow.
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            True if in profile collection flow
        """
        messages = conversation.get('messages', [])
        # Check if we've asked profile questions
        profile_keywords = ['what\'s your name', 'your name', 'student id', 'student ID', 'what program', 'program are you']
        for msg in reversed(messages[-10:]):  # Check last 10 messages
            if msg.get('role') == 'assistant':
                content = msg.get('content', '').lower()
                if any(keyword in content for keyword in profile_keywords):
                    return True
        return False
    
    def _get_profile_progress(self, conversation: Dict) -> Dict:
        """
        Get profile collection progress from conversation.
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            Dictionary with collected profile fields
        """
        messages = conversation.get('messages', [])
        profile_data = {}
        
        # Look for answers to profile questions
        last_question = None
        for msg in messages[-10:]:  # Check last 10 messages
            if msg.get('role') == 'assistant':
                content = msg.get('content', '').lower()
                if 'what\'s your name' in content or 'your name' in content:
                    last_question = 'name'
                elif 'student id' in content or 'student ID' in content:
                    last_question = 'student_id'
                elif 'what program' in content or 'program are you' in content:
                    last_question = 'program'
            elif msg.get('role') == 'user' and last_question:
                # This might be an answer to the last question
                answer = msg.get('content', '').strip()
                if answer and len(answer) < 100:  # Reasonable length for profile fields
                    profile_data[last_question] = answer
                last_question = None
        
        return profile_data
    
    def _extract_profile_from_message(self, user_message: str, conversation: Dict) -> Dict:
        """
        Extract profile information from user message based on conversation context.
        
        Args:
            user_message: User's message
            conversation: Conversation dictionary
            
        Returns:
            Dictionary with extracted profile fields
        """
        profile_data = {}
        messages = conversation.get('messages', [])
        
        # Get the last assistant message to understand context
        last_assistant_msg = None
        for msg in reversed(messages[-5:]):
            if msg.get('role') == 'assistant':
                last_assistant_msg = msg.get('content', '').lower()
                break
        
        if not last_assistant_msg:
            return profile_data
        
        user_msg_lower = user_message.lower().strip()
        
        # Check if last question was about name
        if 'what\'s your name' in last_assistant_msg or 'your name' in last_assistant_msg:
            # Clean up the name (remove common prefixes/suffixes)
            name = user_message.strip()
            # Remove "my name is", "i'm", etc.
            name = re.sub(r'^(my name is|i\'m|i am|this is|it\'s|it is)\s+', '', name, flags=re.I).strip()
            # Remove trailing punctuation
            name = re.sub(r'[.,!?]+$', '', name).strip()
            if name and len(name) < 100:
                profile_data['name'] = name
        
        # Check if last question was about student ID
        elif 'student id' in last_assistant_msg:
            # Extract potential student ID (alphanumeric, typically 7-10 chars)
            student_id = re.sub(r'[^a-zA-Z0-9]', '', user_message.strip())
            if student_id and 5 <= len(student_id) <= 15:
                profile_data['student_id'] = student_id.upper()
        
        # Check if last question was about program
        elif 'what program' in last_assistant_msg or 'program are you' in last_assistant_msg:
            program = user_message.strip()
            # Remove common phrases
            program = re.sub(r'^(i\'m studying|i study|i\'m in|majoring in|studying|program is)\s+', '', program, flags=re.I).strip()
            program = re.sub(r'[.,!?]+$', '', program).strip()
            if program and len(program) < 100:
                profile_data['program'] = program
        
        return profile_data
    
    def _is_link_request(self, message: str) -> bool:
        """
        Detect if user is asking for a link.
        
        Args:
            message: User message
            
        Returns:
            True if message appears to be a link request
        """
        message_lower = message.lower()
        for pattern in self.LINK_REQUEST_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_policy_request(self, message: str) -> bool:
        """
        Detect if user is asking about a policy.
        
        Args:
            message: User message
            
        Returns:
            True if message appears to be a policy question
        """
        message_lower = message.lower()
        for pattern in self.POLICY_REQUEST_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_financial_aid_request(self, message: str) -> bool:
        """
        Detect if user is asking about financial aid.
        
        Args:
            message: User message
            
        Returns:
            True if message appears to be a financial aid question
        """
        message_lower = message.lower()
        for pattern in self.FINANCIAL_AID_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_hold_request(self, message: str) -> bool:
        """
        Detect if user is asking about a hold.
        
        Args:
            message: User message
            
        Returns:
            True if message appears to be a hold question
        """
        message_lower = message.lower()
        for pattern in self.HOLD_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_in_hold_diagnosis_flow(self, conversation: Dict) -> bool:
        """
        Check if conversation is in hold diagnosis flow.
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            True if in hold diagnosis flow
        """
        messages = conversation.get('messages', [])
        # Check if we've asked about hold message
        for msg in reversed(messages[-5:]):  # Check last 5 messages
            if msg.get('role') == 'assistant' and 'hold message' in msg.get('content', '').lower():
                return True
        return False
    
    def _get_hold_message_from_conversation(self, conversation: Dict) -> Optional[str]:
        """
        Extract hold message from conversation if user provided it.
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            Hold message text if found, None otherwise
        """
        messages = conversation.get('messages', [])
        # Look for user message after we asked about hold
        asked_about_hold = False
        for msg in messages[-5:]:  # Check last 5 messages
            if msg.get('role') == 'assistant' and 'hold message' in msg.get('content', '').lower():
                asked_about_hold = True
            elif asked_about_hold and msg.get('role') == 'user':
                # This is likely the hold message
                return msg.get('content', '').strip()
        return None
    
    def _is_registration_troubleshoot_request(self, message: str) -> bool:
        """
        Detect if user is asking about registration problems.
        
        Args:
            message: User message
            
        Returns:
            True if message appears to be a registration troubleshoot question
        """
        message_lower = message.lower()
        for pattern in self.REGISTRATION_TROUBLESHOOT_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_in_registration_troubleshoot_flow(self, conversation: Dict) -> bool:
        """
        Check if conversation is in registration troubleshoot flow.
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            True if in registration troubleshoot flow
        """
        messages = conversation.get('messages', [])
        # Check if we've asked about error message
        for msg in reversed(messages[-5:]):  # Check last 5 messages
            if msg.get('role') == 'assistant' and ('error message' in msg.get('content', '').lower() or 'message do you see' in msg.get('content', '').lower()):
                return True
        return False
    
    def _get_registration_error_from_conversation(self, conversation: Dict) -> Optional[str]:
        """
        Extract registration error message from conversation if user provided it.
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            Error message text if found, None otherwise
        """
        messages = conversation.get('messages', [])
        # Look for user message after we asked about error
        asked_about_error = False
        for msg in messages[-5:]:  # Check last 5 messages
            if msg.get('role') == 'assistant' and ('error message' in msg.get('content', '').lower() or 'message do you see' in msg.get('content', '').lower()):
                asked_about_error = True
            elif asked_about_error and msg.get('role') == 'user':
                # This is likely the error message
                return msg.get('content', '').strip()
        return None
    
    def _is_next_steps_request(self, message: str) -> bool:
        """
        Detect if user is asking for next steps.
        
        Args:
            message: User message
            
        Returns:
            True if message appears to be a next steps request
        """
        message_lower = message.lower()
        for pattern in self.NEXT_STEPS_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_in_wizard_flow(self, conversation: Dict) -> bool:
        """
        Check if conversation is in next steps wizard flow.
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            True if in wizard flow
        """
        messages = conversation.get('messages', [])
        # Check if we've asked any wizard questions
        for msg in reversed(messages[-10:]):  # Check last 10 messages
            content = msg.get('content', '').lower()
            if msg.get('role') == 'assistant':
                # Check if we asked any wizard question
                for q in self.WIZARD_QUESTIONS:
                    if q['question'].lower().split('?')[0] in content:
                        return True
        return False
    
    def _get_wizard_progress(self, conversation: Dict) -> Dict:
        """
        Get wizard progress - which questions have been asked and answered.
        
        Args:
            conversation: Conversation dictionary
            
        Returns:
            Dictionary with wizard state: current_question_index, answers
        """
        messages = conversation.get('messages', [])
        answers = {}
        current_question_index = 0
        
        # Track which questions have been asked
        asked_questions = []
        for msg in messages[-15:]:  # Check last 15 messages
            if msg.get('role') == 'assistant':
                content = msg.get('content', '').lower()
                for i, q in enumerate(self.WIZARD_QUESTIONS):
                    question_text = q['question'].lower().split('?')[0]
                    if question_text in content and i not in asked_questions:
                        asked_questions.append(i)
                        current_question_index = i + 1
            elif msg.get('role') == 'user' and asked_questions:
                # This might be an answer to the last asked question
                last_asked = asked_questions[-1] if asked_questions else None
                if last_asked is not None and self.WIZARD_QUESTIONS[last_asked]['key'] not in answers:
                    answers[self.WIZARD_QUESTIONS[last_asked]['key']] = msg.get('content', '').strip()
        
        return {
            'current_question_index': current_question_index,
            'answers': answers,
            'asked_questions': asked_questions
        }
    
    def _get_next_wizard_question(self, wizard_progress: Dict) -> Optional[Dict]:
        """
        Get the next wizard question to ask.
        
        Args:
            wizard_progress: Wizard progress dictionary
            
        Returns:
            Next question dictionary or None if all questions answered
        """
        current_index = wizard_progress['current_question_index']
        if current_index >= len(self.WIZARD_QUESTIONS):
            return None
        return self.WIZARD_QUESTIONS[current_index]
    
    def _extract_action_items(self, response_text: str, conversation: Dict) -> List[Dict]:
        """
        Extract action items from AI response (Phase 2).
        Looks for patterns like "Action:", "TODO:", or numbered steps.
        
        Returns:
            List of action item dictionaries
        """
        action_items = []
        
        # Simple pattern matching for action items
        # In production, could use OpenAI function calling or structured output
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Look for action indicators
            if line.startswith('Action:') or line.startswith('ACTION:'):
                action = line.replace('Action:', '').replace('ACTION:', '').strip()
                if action:
                    action_items.append({'action': action})
            elif line.startswith('TODO:') or line.startswith('To do:'):
                action = line.replace('TODO:', '').replace('To do:', '').strip()
                if action:
                    action_items.append({'action': action})
            # Look for numbered steps that might be actionable
            elif re.match(r'^\d+[\.\)]\s+', line) and len(line) > 10:
                # Could be an action item
                action = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
                # Only add if it sounds like an action (contains verbs)
                action_verbs = ['pay', 'register', 'submit', 'complete', 'schedule', 'contact', 'meet', 'apply']
                if any(verb in action.lower() for verb in action_verbs):
                    action_items.append({'action': action})
        
        return action_items
    
    def process_message(
        self,
        phone_number: str,
        user_message: str
    ) -> Dict[str, str]:
        """
        Process incoming message (for Lambda handler).
        
        Args:
            phone_number: Student phone number
            user_message: User's message
            
        Returns:
            Response dictionary
        """
        # Check if student profile exists
        student_profile = None
        students_table_available = False
        if self.db.students_table:
            try:
                # Verify table actually exists
                self.db.students_table.meta.client.describe_table(TableName=self.db.students_table_name)
                students_table_available = True
                student_profile = self.db.get_student(phone_number)
            except Exception as e:
                # Table doesn't exist - skip profile checks
                students_table_available = False
                print(f"Note: Students table not available: {e}")
        
        # Find active conversation for this phone number
        conversation = self.db.get_conversation_by_phone(phone_number)
        
        is_new_conversation = False
        if not conversation:
            # Create new conversation and use the returned ID directly
            conversation_id = self.db.create_conversation(phone_number)
            # Validate conversation_id was created
            if not conversation_id:
                return {"response": "I'm sorry, I encountered an error. Please try again."}
            # Get the conversation we just created
            conversation = self.db.get_conversation(conversation_id)
            # If still None, there's an issue - but try to continue anyway
            if not conversation:
                print(f"Warning: Could not retrieve conversation {conversation_id} after creation")
                # Create a minimal conversation dict to continue
                conversation = {
                    'conversation_id': conversation_id,
                    'phone_number': phone_number,
                    'messages': [],
                    'status': 'active'
                }
            is_new_conversation = True
        else:
            conversation_id = conversation.get('conversation_id')
            # Validate conversation_id exists
            if not conversation_id:
                return {"response": "I'm sorry, I encountered an error. Please try again."}
        
        # Check if we need to collect profile (new conversation, no profile, and table is available)
        needs_profile_setup = students_table_available and is_new_conversation and not student_profile
        
        # Generate response
        return self.generate_response(conversation_id, user_message, phone_number=phone_number)


def process_message(event, context):
    """Lambda handler for processing messages."""
    try:
        body = json.loads(event.get('body', '{}'))
        phone_number = body.get('phone_number')
        message = body.get('message')
        
        if not phone_number or not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'phone_number and message required'})
            }
        
        engine = ConversationEngine()
        result = engine.process_message(phone_number, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

