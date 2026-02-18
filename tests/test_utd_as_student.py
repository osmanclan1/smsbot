#!/usr/bin/env python3
"""
UTD Support Test - Acting Like a Troubled Student

This script simulates a REAL student experience:
- Uses casual language, typos, vague questions
- Tries multiple approaches when frustrated
- Tests ambiguous scenarios
- Simulates confusion and desperation
- Finds where UTD's support BREAKS DOWN

Test scenarios (as a student would ask them):
1. "i cant register" (casual, no details)
2. "registration won't work" (frustrated, ambiguous)
3. "whats wrong with my account" (vague, confused)
4. "i have a hold but idk what it means" (young person language)
"""

import asyncio
import json
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# UTD URLs - Update these based on actual UTD website structure
UTD_BASE_URL = "https://www.utdallas.edu"
UTD_REGISTRAR = "https://www.utdallas.edu/registrar"
UTD_BURSAR = "https://www.utdallas.edu/bursar"
UTD_FINANCIAL_AID = "https://www.utdallas.edu/financial-aid"
UTD_STUDENT_PORTAL = "https://www.utdallas.edu/student-portal"
UTD_CONTACT = "https://www.utdallas.edu/contact"
UTD_ADVISING = "https://www.utdallas.edu/advising"

# Test scenarios with different student problems
TEST_SCENARIOS = [
    {
        'name': 'Registration Hold',
        'problem': "I can't register because of a hold and I don't know why",
        'queries': ['i cant register', 'hold on account', 'registration wont work'],
        'keywords': ['hold', 'registration', 'clear', 'resolve'],
        'urls': [UTD_REGISTRAR, f"{UTD_BASE_URL}/registrar/holds"]
    },
    {
        'name': 'Payment Issue',
        'problem': "I have a balance but don't know how to pay or what it's for",
        'queries': ['how do i pay', 'outstanding balance', 'payment due', 'what do i owe'],
        'keywords': ['payment', 'balance', 'pay', 'tuition', 'fee'],
        'urls': [UTD_BURSAR, f"{UTD_BASE_URL}/bursar/payment"]
    },
    {
        'name': 'Financial Aid Confusion',
        'problem': "My financial aid hasn't come through and I don't know why",
        'queries': ['financial aid not showing', 'when does aid come', 'aid status', 'fafsa help'],
        'keywords': ['financial aid', 'fafsa', 'aid', 'scholarship', 'grant'],
        'urls': [UTD_FINANCIAL_AID, f"{UTD_BASE_URL}/financial-aid/status"]
    },
    {
        'name': 'Class Registration',
        'problem': "I can't find the classes I need or they're all full",
        'queries': ['classes full', 'cant find classes', 'registration help', 'class search'],
        'keywords': ['class', 'course', 'registration', 'schedule', 'enrollment'],
        'urls': [UTD_REGISTRAR, f"{UTD_BASE_URL}/registrar/registration"]
    },
    {
        'name': 'Deadline Confusion',
        'problem': "I don't know when important deadlines are or I missed one",
        'queries': ['when is deadline', 'missed deadline', 'important dates', 'deadline help'],
        'keywords': ['deadline', 'due date', 'important dates', 'calendar', 'schedule'],
        'urls': [UTD_REGISTRAR, f"{UTD_BASE_URL}/academic-calendar"]
    },
    {
        'name': 'Vague Account Problem',
        'problem': "Something is wrong with my account but I don't know what",
        'queries': ['whats wrong', 'account issues', 'something wrong', 'account blocked'],
        'keywords': ['account', 'problem', 'issue', 'error', 'status'],
        'urls': [UTD_STUDENT_PORTAL, UTD_CONTACT]
    }
]

# Student-like queries (casual, vague, frustrated, with typos)
STUDENT_QUERIES = [
    # Scenario 1: Casual, no details
    ("i cant register", "cant register", "can't register"),
    ("registration wont work", "registration won't work", "cant register for classes"),
    
    # Scenario 2: Vague, confused
    ("whats wrong with my account", "what's wrong", "why cant i do anything"),
    ("account blocked", "account locked", "my account has issues"),
    
    # Scenario 3: Young person language
    ("i have a hold but idk what it means", "hold on account", "what is a hold"),
    ("hold but dont know why", "hold idk", "registration hold help"),
    
    # Scenario 4: Frustrated, multiple attempts
    ("tried everything still cant register", "nothing works", "registration broken"),
    ("urgent need to register", "registration deadline help", "need help asap"),
    
    # Scenario 5: Edge cases
    ("error message when i try", "what does this error mean", "system error"),
    ("help me", "i need help", "who do i contact"),
]


async def navigate_with_retry(page: "Page", url: str, max_retries: int = 3, timeout: int = 60000) -> bool:
    """
    Navigate to URL with retry logic and better timeout handling.
    Tries 'domcontentloaded' first (faster), then 'load', then 'networkidle'.
    """
    for attempt in range(max_retries):
        try:
            # Try domcontentloaded first (fastest, most reliable)
            await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            # Give it a moment for dynamic content
            await asyncio.sleep(2)
            return True
        except PlaywrightTimeout:
            if attempt < max_retries - 1:
                print(f"      ⚠️  Timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                await asyncio.sleep(2)
                continue
            else:
                # Last attempt - try with 'load' instead
                try:
                    await page.goto(url, wait_until='load', timeout=timeout)
                    await asyncio.sleep(2)
                    return True
                except:
                    return False
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"      ⚠️  Error (attempt {attempt + 1}/{max_retries}): {str(e)[:50]}")
                await asyncio.sleep(2)
                continue
            return False
    return False


class StudentPersona:
    """Simulates a confused, frustrated student."""
    
    def __init__(self):
        self.frustration_level = 0
        self.attempts = 0
        self.paths_tried = []
        self.failed_searches = []
        
    def get_search_query(self, scenario: str) -> str:
        """Get a student-like search query (with potential typos/variations)."""
        queries = {
            "registration_hold": [
                "i cant register",
                "registration wont work", 
                "hold on my account",
                "i have a hold idk why",
                "what does hold mean",
                "cant register help",
            ],
            "payment": [
                "how do i pay",
                "outstanding balance",
                "payment due",
                "what do i owe",
                "cant pay",
            ],
            "financial_aid": [
                "financial aid not showing",
                "when does aid come",
                "aid status",
                "fafsa help",
            ],
            "vague_problem": [
                "whats wrong",
                "account issues",
                "something wrong with my account",
                "cant do anything",
                "help me",
            ],
            "frustrated": [
                "tried everything",
                "nothing works",
                "system broken",
                "urgent help needed",
                "need to talk to someone",
            ]
        }
        
        if scenario in queries:
            return random.choice(queries[scenario])
        return random.choice(STUDENT_QUERIES)[0]
    
    def simulate_clicking_around(self):
        """Simulate a student clicking random links when frustrated."""
        time.sleep(random.uniform(1, 3))  # Reading time
        return random.choice([True, False])  # Sometimes clicks, sometimes doesn't


class TestResults:
    """Tracks test results from student perspective."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            'student_scenarios': {},
            'faq_failures': [],
            'search_failures': [],
            'confusion_points': [],
            'resolution_time': None,
            'did_student_find_answer': False,
            'student_frustration_events': []
        }
    
    def add_faq_failure(self, failure: str):
        """Record FAQ failure."""
        self.results['faq_failures'].append(failure)
    
    def add_search_failure(self, query: str, reason: str):
        """Record search failure."""
        self.results['search_failures'].append({
            'query': query,
            'reason': reason
        })
    
    def add_frustration_event(self, event: str, reason: str):
        """Record when student gets frustrated."""
        self.results['student_frustration_events'].append({
            'event': event,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_confusion_point(self, page: str, issue: str):
        """Record where student got confused."""
        self.results['confusion_points'].append({
            'page': page,
            'issue': issue,
            'timestamp': datetime.now().isoformat()
        })
    
    def set_answer_found(self, found: bool):
        """Record if student found answer."""
        self.results['did_student_find_answer'] = found
        self.results['resolution_time'] = (datetime.now() - self.start_time).total_seconds()
    
    def print_student_report(self):
        """Print report from student's perspective."""
        print("\n" + "=" * 80)
        print("STUDENT EXPERIENCE REPORT - 'I CAN'T REGISTER'")
        print("=" * 80)
        
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"\n⏱️  Time spent trying to solve problem: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        if self.results['did_student_find_answer']:
            print("✅ Student eventually found answer")
        else:
            print("❌ Student gave up or couldn't find answer")
        
        # Frustration events
        if self.results['student_frustration_events']:
            print(f"\n😤 FRUSTRATION EVENTS ({len(self.results['student_frustration_events'])}):")
            for i, event in enumerate(self.results['student_frustration_events'], 1):
                print(f"   {i}. {event['event']}")
                print(f"      Reason: {event['reason']}")
        
        # Confusion points
        if self.results['confusion_points']:
            print(f"\n🤔 WHERE STUDENT GOT CONFUSED ({len(self.results['confusion_points'])}):")
            for i, point in enumerate(self.results['confusion_points'], 1):
                print(f"   {i}. {point['page']}")
                print(f"      Issue: {point['issue']}")
        
        # FAQ failures
        if self.results['faq_failures']:
            print(f"\n❌ FAQ FAILURES ({len(self.results['faq_failures'])}):")
            for failure in self.results['faq_failures']:
                print(f"   • {failure}")
        
        # Search failures
        if self.results['search_failures']:
            print(f"\n🔍 SEARCH FAILURES ({len(self.results['search_failures'])}):")
            for failure in self.results['search_failures']:
                print(f"   • Query: '{failure['query']}'")
                print(f"     Result: {failure['reason']}")
        
        # Scenario results
        if self.results.get('scenario_results'):
            print(f"\n📋 SCENARIO RESULTS:")
            for scenario_name, scenario_data in self.results['scenario_results'].items():
                status = "✅" if scenario_data['found_answer'] else "❌"
                print(f"   {status} {scenario_name}: {scenario_data['duration']:.1f}s")
        
        # Verdict
        print("\n" + "=" * 80)
        print("VERDICT: DOES UTD NEED YOUR SMS BOT?")
        print("=" * 80)
        
        total_problems = (
            len(self.results['student_frustration_events']) +
            len(self.results['confusion_points']) +
            len(self.results['faq_failures']) +
            len(self.results['search_failures'])
        )
        
        if not self.results['did_student_find_answer']:
            print("\n🔥 STRONG NEED - Student couldn't solve problem")
            print("   Your SMS bot could resolve this in seconds.")
        elif total_problems >= 5:
            print("\n🔥 STRONG NEED - Too many friction points")
            print("   Student experienced multiple failures. SMS bot would eliminate these.")
        elif total_problems >= 3:
            print("\n⚠️  MODERATE NEED - Several pain points identified")
            print("   SMS bot would improve experience significantly.")
        elif duration > 300:  # > 5 minutes
            print("\n⚠️  MODERATE NEED - Takes too long")
            print("   Student spent over 5 minutes. SMS bot would be instant.")
        else:
            print("\n✅ WEAK NEED - Current system works")
            print("   Consider testing different scenarios or departments.")
        
        print("\n" + "=" * 80)


async def student_tries_faq(page: "Page", url: str, department: str, persona: StudentPersona, results: TestResults, scenario: Optional[Dict] = None) -> Dict:
    """Student tries to find answer in FAQ (casual language, typos)."""
    result = {
        'found_answer': False,
        'time_spent': 0,
        'pages_visited': 0,
        'queries_tried': [],
        'confused': False
    }
    
    start_time = time.time()
    
    try:
        print(f"\n   📚 Student goes to {department} FAQ...")
        
        # Navigate to page with retry
        success = await navigate_with_retry(page, url, max_retries=3, timeout=60000)
        if not success:
            results.add_frustration_event(
                f"Couldn't load {department} page",
                "Page timeout or connection error"
            )
            result['time_spent'] = time.time() - start_time
            return result
        
        result['pages_visited'] += 1
        await asyncio.sleep(random.uniform(1, 2))  # Student reading time
        
        # Get queries based on scenario or default
        if scenario:
            search_queries = scenario.get('queries', [])[:3]  # Try first 3 queries
        else:
            search_queries = [
                persona.get_search_query("registration_hold"),
                persona.get_search_query("vague_problem"),
                "cant register help"
            ]
        
        for query in search_queries:
            result['queries_tried'].append(query)
            print(f"      Student searches: '{query}'")
            
            # Try to find search box
            search_selectors = [
                'input[type="search"]',
                '#search',
                '.search-input',
                '[name="search"]',
                'input[placeholder*="search" i]',
                'input[placeholder*="Search" i]'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = await page.query_selector(selector)
                    if search_box:
                        break
                except:
                    continue
            
            if search_box:
                # Student types query (with potential typos)
                await search_box.fill(query)
                await asyncio.sleep(random.uniform(0.5, 1))  # Typing time
                await search_box.press('Enter')
                
                # Wait for results
                await page.wait_for_timeout(2000)
                result['pages_visited'] += 1
                
                # Check if results are helpful
                page_text = await page.text_content('body')
                page_text_lower = (page_text or "").lower()
                
                # Student looks for keywords (use scenario keywords if available)
                if scenario:
                    helpful_keywords = scenario.get('keywords', [])
                else:
                    helpful_keywords = ['hold', 'registration', 'clear', 'resolve', 'remove', 'account']
                found_keywords = [kw for kw in helpful_keywords if kw in page_text_lower]
                
                if found_keywords:
                    # Check if it's actually helpful or just generic
                    generic_phrases = ['contact us', 'email us', 'call us', 'reach out']
                    is_generic = any(phrase in page_text_lower for phrase in generic_phrases)
                    
                    # Check if any scenario keywords are present
                    has_relevant_content = any(kw in page_text_lower for kw in helpful_keywords)
                    if not is_generic and has_relevant_content:
                        result['found_answer'] = True
                        print(f"      ✅ Found relevant information")
                        break
                    else:
                        results.add_frustration_event(
                            f"Search '{query}' only returned generic contact info",
                            "No actual answers, just 'contact us'"
                        )
                else:
                    results.add_search_failure(query, "No relevant results found")
            else:
                # No search box - student tries to scan page manually
                print(f"      ⚠️  No search box found, scanning page...")
                page_text = await page.text_content('body')
                page_text_lower = (page_text or "").lower()
                
                # Check for scenario keywords or default
                if scenario:
                    check_keywords = scenario.get('keywords', [])
                else:
                    check_keywords = ['hold', 'registration']
                
                if any(kw in page_text_lower for kw in check_keywords):
                    # But is it clear or confusing?
                    if any(word in page_text_lower for word in ['contact', 'email', 'call', 'office']):
                        results.add_confusion_point(url, "Information exists but unclear next steps")
                    result['found_answer'] = True
                    break
        
        result['time_spent'] = time.time() - start_time
        
        if not result['found_answer']:
            results.add_frustration_event(
                f"Couldn't find answer in {department} FAQ",
                f"Tried {len(result['queries_tried'])} different searches"
            )
            results.add_faq_failure(f"{department} FAQ: No clear answer found")
            result['confused'] = True
        
    except Exception as e:
        result['time_spent'] = time.time() - start_time
        results.add_frustration_event(
            f"Error on {department} page",
            str(e)
        )
    
    return result


async def student_tries_live_chat(page: "Page", base_url: str, persona: StudentPersona, results: TestResults) -> Dict:
    """Student tries live chat (frustrated, needs quick help)."""
    result = {
        'found_chat': False,
        'chat_available': False,
        'wait_time': 0
    }
    
    try:
        print(f"\n   💬 Frustrated student looks for live chat...")
        
        await page.goto(base_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(1)
        
        # Student looks for chat widget (scans page)
        chat_indicators = [
            'iframe[title*="chat" i]',
            '.chat-widget',
            '#chat',
            '[data-chat]',
            '[id*="chat" i]',
            '[class*="chat" i]',
            'button:has-text("Chat")',
            'a:has-text("Chat")',
        ]
        
        for indicator in chat_indicators:
            try:
                chat_element = await page.query_selector(indicator)
                if chat_element:
                    result['found_chat'] = True
                    result['chat_available'] = True
                    print(f"      ✅ Found chat widget")
                    break
            except:
                continue
        
        # Also check for embedded chat services in scripts
        if not result['found_chat']:
            scripts = await page.evaluate('''() => {
                const scripts = Array.from(document.querySelectorAll('script'));
                return scripts.map(s => s.src || s.textContent || '').filter(Boolean).join(' ');
            }''')
            
            chat_services = ['intercom', 'drift', 'zendesk', 'livechat', 'olark', 'tawk']
            if any(service in scripts.lower() for service in chat_services):
                result['found_chat'] = True
                result['chat_available'] = True
                print(f"      ✅ Chat service detected in page code")
        
        if not result['found_chat']:
            results.add_frustration_event(
                "Couldn't find live chat option",
                "No visible chat widget or link"
            )
            print(f"      ❌ No chat found")
        else:
            print(f"      ⚠️  Chat requires manual testing (wait time, quality)")
            
    except Exception as e:
        results.add_frustration_event("Error looking for chat", str(e))
    
    return result


async def student_tries_multiple_pages(page: "Page", persona: StudentPersona, results: TestResults, scenario: Optional[Dict] = None) -> Dict:
    """Student clicks around different pages when frustrated (realistic behavior)."""
    result = {
        'pages_tried': [],
        'found_anything': False
    }
    
    # Use scenario URLs if available, otherwise default
    if scenario:
        pages_to_try = [(url, f"Scenario page: {url}") for url in scenario.get('urls', [])]
    else:
        pages_to_try = [
            (f"{UTD_BASE_URL}/student", "Student Portal"),
            (f"{UTD_BASE_URL}/registrar/holds", "Registrar Holds Page"),
            (f"{UTD_BASE_URL}/registrar/registration", "Registration Page"),
            (f"{UTD_BASE_URL}/contact", "Contact Page"),
        ]
    
    # Get keywords to look for
    if scenario:
        keywords = scenario.get('keywords', [])
    else:
        keywords = ['hold', 'registration']
    
    try:
        print(f"\n   🔄 Frustrated student tries different pages...")
        
        for url, name in pages_to_try:
            try:
                print(f"      Checking: {name}")
                success = await navigate_with_retry(page, url, max_retries=2, timeout=30000)
                if not success:
                    continue
                
                await asyncio.sleep(1)  # Student reading
                
                result['pages_tried'].append(name)
                page_text = await page.text_content('body')
                page_text_lower = (page_text or "").lower()
                
                # Student looks for anything related
                if any(kw in page_text_lower for kw in keywords):
                    result['found_anything'] = True
                    # But is it helpful?
                    if 'contact' in page_text_lower or 'email' in page_text_lower:
                        results.add_confusion_point(name, "Info exists but unclear next steps")
                        print(f"      ⚠️  Found info but unclear what to do")
                    else:
                        print(f"      ✅ Found relevant info")
                else:
                    print(f"      ❌ No relevant info")
            except:
                continue
        
    except Exception as e:
        results.add_frustration_event("Error trying different pages", str(e))
    
    return result


async def run_student_simulation(headless: bool = False):
    """Run the complete student simulation."""
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not installed!")
        print("\nInstall it with:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return None
    
    results = TestResults()
    persona = StudentPersona()
    
    print("=" * 80)
    print("STUDENT SIMULATION - MULTIPLE SCENARIOS")
    print("=" * 80)
    print("\nSimulating confused, frustrated students who:")
    print("  • Use casual language and typos")
    print("  • Don't know technical terms")
    print("  • Try multiple vague queries")
    print("  • Get frustrated and click around")
    print("  • Test where UTD's support BREAKS DOWN")
    print(f"\nTesting {len(TEST_SCENARIOS)} different student problems...")
    
    async with async_playwright() as p:
        print("\n🚀 Launching browser (visible mode so you can watch the students struggle)...")
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        page.set_default_timeout(60000)  # Increased default timeout
        
        # Set realistic viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            # Test each scenario
            scenario_results = {}
            
            for idx, scenario in enumerate(TEST_SCENARIOS, 1):
                print("\n" + "=" * 80)
                print(f"SCENARIO {idx}/{len(TEST_SCENARIOS)}: {scenario['name']}")
                print("=" * 80)
                print(f"Problem: {scenario['problem']}")
                
                scenario_start = datetime.now()
                scenario_found_answer = False
                
                # Try primary URL first
                primary_url = scenario['urls'][0] if scenario['urls'] else UTD_BASE_URL
                department = scenario['name']
                
                # Student tries FAQ
                faq_result = await student_tries_faq(
                    page, primary_url, department, persona, results, scenario
                )
                
                if faq_result['found_answer']:
                    scenario_found_answer = True
                    results.set_answer_found(True)
                else:
                    # Student gets frustrated, tries other pages from scenario
                    print(f"\n   😤 Student is frustrated, trying other pages...")
                    pages_result = await student_tries_multiple_pages(
                        page, persona, results, scenario
                    )
                    
                    if pages_result['found_anything']:
                        scenario_found_answer = True
                        results.set_answer_found(True)
                
                # Record scenario result
                scenario_duration = (datetime.now() - scenario_start).total_seconds()
                scenario_results[scenario['name']] = {
                    'found_answer': scenario_found_answer,
                    'duration': scenario_duration
                }
                
                # Small delay between scenarios
                await asyncio.sleep(2)
            
            # Test live chat once (applies to all scenarios)
            print("\n" + "=" * 80)
            print("BONUS: Student desperately looks for live chat")
            print("=" * 80)
            
            chat_result = await student_tries_live_chat(page, UTD_BASE_URL, persona, results)
            
            if chat_result['found_chat']:
                print("      ⚠️  Chat found but requires manual testing:")
                print("         • How long is the wait?")
                print("         • Do they ask clarifying questions?")
                print("         • Do they just link to FAQ?")
                print("         • Do they escalate to email?")
            
            # Store scenario results
            results.results['scenario_results'] = scenario_results
            
        finally:
            await browser.close()
    
    # Final verdict
    if not results.results['did_student_find_answer']:
        results.set_answer_found(False)
    
    # Generate report
    results.print_student_report()
    
    # Save results
    output_file = f"utd_student_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results.results, f, indent=2, default=str)
    print(f"\n💾 Full results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    import sys
    
    # Default to visible browser so user can watch
    headless_mode = '--headless' in sys.argv
    
    try:
        results = asyncio.run(run_student_simulation(headless=headless_mode))
        if results:
            # Exit code based on need level
            total_problems = (
                len(results.results['student_frustration_events']) +
                len(results.results['confusion_points']) +
                len(results.results['faq_failures']) +
                len(results.results['search_failures'])
            )
            
            if not results.results['did_student_find_answer'] or total_problems >= 5:
                sys.exit(0)  # Strong need = success for test
            elif total_problems >= 3:
                sys.exit(0)  # Moderate need
            else:
                sys.exit(1)  # Weak need
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
