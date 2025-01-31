import os
import logging
import json
import re
import base64
from typing import List
from dotenv import load_dotenv
from models.models import call_model 
from playwright.sync_api import sync_playwright
from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
from surf_ai.prompt import GEN_JSON_TASK_PROMPT, GEN_JSON_TASK_LOOP_PROMPT

class MemoryLogHandler(logging.Handler):
    def __init__(self, execution_logs: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execution_logs = execution_logs

    def emit(self, record):
        if getattr(record, 'no_memory', False):
            return
        log_entry = self.format(record)
        self.execution_logs.append(log_entry)
        
class SurfAiEngine: 
    def __init__(self): 
        logging.basicConfig(level=logging.DEBUG)
        self.execution_logs = []  
        self.logger = logging.getLogger(__name__)
        load_dotenv()
        self.json_task_model = os.getenv("SURF_AI_JSON_TASK_MODEL")
        self.scraped_page = None
        self.screenshot_url = None 
        self.screenshot_base64 = None 
        self.max_retries = 2
        self.retry_backoff = 2000
        self.command_timeout = 1500 
        self.truncation_length = 400000     

        memory_handler = MemoryLogHandler(self.execution_logs) 
        memory_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        memory_handler.setFormatter(formatter) 
        self.logger.addHandler(memory_handler)   

    def go_surf(self, prompt: str):   
        self.logger.debug("🟢 Starting the process of surfing the web")
        try:
            json_task_prompt = GEN_JSON_TASK_PROMPT.substitute(user_message=prompt)
            chat_history = [{"role": "user", "content": json_task_prompt}]
            response = call_model(chat_history=chat_history, model=self.json_task_model)
            json_task_response = self.sanitize_gpt_json_response(response)
            self.logger.debug(
                "🔵 Generated JSON response: %s", 
                response, 
                extra={'no_memory': True}  
            )
            self.json_task = json.loads(json_task_response)

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled"
                    ]
                )
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 960},  
                    device_scale_factor=1,
                    bypass_csp=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
                )
                context.add_init_script(
                    """
                    Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                    }); 
                    Object.defineProperty(navigator, 'vendor', {
                    get: () => 'Google Inc.'
                    });
                    """
                )
                page = context.new_page()
                page.set_default_timeout(self.command_timeout) 

                while True:
                    task = self.json_task['tasks'][-1]
                    self.logger.debug(f"Executing task: {task['task_name']}")

                    # Split commands by semicolon and clean whitespace
                    commands = [cmd.strip() for cmd in task['commands'].split(';') if cmd.strip()]
                    self.logger.debug(f"Commands: {commands}") 
                    task_success = False

                    
                    for command in commands: 
                        try:
                            success = self.execute_command(command, page, task['task_name']) 
                            if success:
                                self.logger.debug(f"🟢 task_name: '{task['task_name']}', Command executed successfully: '{command}'") 
                                task_success = True
                                break    
                            else:
                                self.logger.debug(f"🔴 task_name: '{task['task_name']}', Command failed: '{command}'")
                        except Exception as e:
                            if self.is_critical_error(e):  
                                break
                    if task_success:
                        self.logger.debug(f"🟢 Task completed: '{task['task_name']}'")
                    else:
                        self.logger.error(f"🔴 All commands failed for task: '{task['task_name']}'")  

                    self.remove_highlight_from_elements(page)
                    self.highlight_and_scrape_after_command(page, task['task_name']) 

                    loop_prompt = GEN_JSON_TASK_LOOP_PROMPT.substitute(
                        json_task=json.dumps(self.json_task, indent=4),
                        execution_logs=self.execution_logs,
                        scraped_page=self.scraped_page,
                        user_message=prompt
                    )
                    
                    chat_history = [{"role": "user", "content": loop_prompt}]
                    response = call_model(chat_history=chat_history, model=self.json_task_model, 
                                        image_base64=self.screenshot_base64, image_extension="png")
                    json_task_response = self.sanitize_gpt_json_response(response) 
                    self.logger.debug(
                        "🔵 Generated JSON response : %s",
                        json_task_response,
                        extra={'no_memory': True} 
                    ) 

                    try:
                        parsed_json_task_response = json.loads(json_task_response)
                    except (json.JSONDecodeError, KeyError) as e:
                        if 'execution_logs_summary' not in self.json_task['tasks'][-1]:
                            self.json_task['tasks'][-1]['execution_logs_summary'] = ""
                        self.json_task['tasks'][-1]['execution_logs_summary'] += f"The model returned a malformed JSON response: {str(e)}. I will create a new task to try again."
                        continue 

                    if 'updated_tasks_and_new_task' in parsed_json_task_response:
                        new_tasks = parsed_json_task_response['updated_tasks_and_new_task']
                        existing_tasks = self.json_task.get('tasks', [])
                        
                        task_name_to_index = {task['task_name']: index for index, task in enumerate(existing_tasks)}
                        
                        for new_task in new_tasks:
                            task_name = new_task['task_name'] 
                            if task_name in task_name_to_index:
                                existing_tasks[task_name_to_index[task_name]] = new_task
                            else:
                                existing_tasks.append(new_task)
                        
                        self.json_task['tasks'] = existing_tasks
                        
                        for key in parsed_json_task_response:
                            if key not in ['tasks', 'updated_tasks_and_new_task']:
                                self.json_task[key] = parsed_json_task_response[key]
                    else:
                        self.json_task = parsed_json_task_response

                    if self.json_task.get('is_last_task'): 
                        self.logger.debug("Final task completed")
                        break 

                    self.logger.debug( 
                        "🔵 Updated JSON task: %s", 
                        json.dumps(self.json_task, indent=4), 
                        extra={'no_memory': True} 
                    )

                browser.close()  

        except Exception as e:
            self.logger.exception("Critical error in go_surf: %s", str(e))
            raise

    def execute_command(self, command: str, page, task_name: str) -> bool:
        for attempt in range(self.max_retries + 1):
            try:
                exec(command, {'page': page, 'self': self})    
                return True
            except PlaywrightTimeoutError as e:  
                if attempt == self.max_retries: 
                    error_msg = (f"⏰ task_name: '{task_name}'. Timed out in command: '{command}'\n"
                                f"Error: {str(e)}\n") 
                    self.logger.debug(error_msg) 
                    return False
                page.wait_for_timeout(self.retry_backoff * (attempt + 1))
            except PlaywrightError as e:
                error_msg = (f"🎭 task_name: '{task_name}'. Playwright error in command: '{command}'\n"
                            f"Error: {str(e)}\n")
                self.logger.debug(error_msg)
                return False
            except Exception as e:
                error_msg = (f"🐍 task_name: '{task_name}'. Python error in command': '{command}'\n"
                            f"Error: {str(e)}\n")
                self.logger.debug(error_msg) 
                return False
        return False  
   
    def highlight_and_scrape_after_command(self, page, task_name):    
        try:
            self.apply_highlight_to_elements(page)
            self.take_screenshot(page, task_name) 
            
            elements_html = page.evaluate('''() => {
                return Array.from(document.querySelectorAll('*[data-highlight-number]'));
            }''') 
            
            scraped_content = f"<!-- Visible Interactive Elements ({len(elements_html)}) -->\n" + '\n'.join(elements_html)
            if len(scraped_content) > self.truncation_length:
                self.scraped_page = scraped_content[:self.truncation_length]
                self.logger.debug(
                    "🟠 Scraped page was truncated from: %d to: %d",
                    len(scraped_content),
                    len(self.scraped_page),
                    extra={'no_memory': True} 
                )
            else:
                self.scraped_page = scraped_content   


        except Exception as e:
            self.logger.error(f"🔴 Scraping failed: {str(e)}", exc_info=True)
            self.scraped_page = "CONTENT_UNAVAILABLE"
 

    def apply_highlight_to_elements(self, page):
        """Apply highlights with unique colors and numbering to all interactive visible elements."""
        try:
            page.wait_for_function('''() => {
                return document.readyState === 'complete' &&  
                    document.body &&
                    document.body.clientHeight > 0;   
            }''', timeout=5000)
            page.wait_for_timeout(3000)

            numbering_script = """
                let counter = 1;
                const getRandomColor = () => {
                    const hue = Math.floor(Math.random() * 360);
                    const saturation = 70 + Math.floor(Math.random() * 20); 
                    const lightness = 30 + Math.floor(Math.random() * 10);  
                    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
                };

                interactiveSelectors = [
                    'input', 'textarea', 'button', 'select', 'output',
                    'a[href]', 'area[href]',
                    '[contenteditable]', 
                    '[tabindex]:not([tabindex="-1"])',
                    '[onclick]', '[ondblclick]', '[onchange]', '[onsubmit]', '[onkeydown]',
                    'audio[controls]', 'video[controls]',
                    'details', 'details > summary',
                    '[role="button"]', '[role="checkbox"]', '[role="radio"]',
                    '[role="link"]', '[role="textbox"]', '[role="searchbox"]',
                    '[role="combobox"]', '[role="listbox"]', '[role="menu"]',
                    '[role="menuitem"]', '[role="slider"]', '[role="switch"]',
                    '[role="tab"]', '[role="treeitem"]', '[role="gridcell"]',
                    '[role="option"]', '[role="spinbutton"]', '[role="scrollbar"]',
                    'iframe', 'object', 'embed'
                ]
                const voidElements = ['input', 'img', 'br', 'hr', 'area', 'base', 'col', 'select', 'textarea',
                                    'embed', 'link', 'meta', 'param', 'source', 'track', 'wbr'];
                
                // Clear previous body labels
                if (window.surfAiLabels) {
                    window.surfAiLabels.forEach(label => label.remove()); 
                    window.surfAiLabels = [];
                }
                
                const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && 
                        style.visibility === 'visible' &&
                        el.offsetParent !== null &&
                        interactiveSelectors.some(selector => el.matches(selector)) &&
                        !el.dataset.highlightNumber;
                });

                elements.forEach(el => {
                    el.style.overflow = 'visible';
                    const number = counter++;
                    const tagName = el.tagName.toLowerCase(); 

                    el.dataset.originalBorder = el.style.border || '';
                    el.dataset.originalBoxSizing = el.style.boxSizing || '';
                    el.dataset.originalPosition = el.style.position || '';
                    
                    el.dataset.highlightNumber = number; 
                    const color = getRandomColor();
                    el.style.border = `2px solid ${color}`; 
                    el.style.boxSizing = 'border-box';
                    el.style.position = 'relative';

                    const label = document.createElement('span'); 
                    label.className = 'surf-ai-highlight-label';
                    label.textContent = number;
                    label.style.backgroundColor = color;
                    label.style.fontFamily = 'Arial';
                    label.style.mixBlendMode = 'normal';
                    label.style.pointerEvents = 'none';
                    label.style.color = 'white';
                    label.style.padding = '0 4px';
                    label.style.height = '21px';
                    label.style.display = 'flex'; 
                    label.style.alignItems = 'center';
                    label.style.justifyContent = 'center';
                    label.style.fontSize = '17px';
                    label.style.fontWeight = 'bold'; 
                    label.style.borderRadius = '2px';
                    label.style.zIndex = '99999';

                    if (voidElements.includes(tagName)) {
                        const rect = el.getBoundingClientRect();
                        const scrollX = window.pageXOffset;
                        const scrollY = window.pageYOffset;
                        
                        // Find the first positioned ancestor
                        let parent = el.parentElement;
                        let positionedParent = null;
                        while (parent) {
                            const style = getComputedStyle(parent);
                            if (style.position !== 'static') {
                                positionedParent = parent;  
                                break; 
                            }
                            parent = parent.parentElement;
                        }

                        if (positionedParent) { 
                            const parentRect = positionedParent.getBoundingClientRect();
                            label.style.position = 'absolute';
                            label.style.top = `${rect.top - parentRect.top + scrollY}px`;
                            label.style.left = `${rect.left - parentRect.left + scrollX}px`;
                            positionedParent.appendChild(label);
                        } else {
                            label.style.position = 'absolute';
                            label.style.top = `${rect.top + scrollY}px`;
                            label.style.left = `${rect.left + scrollX}px`;
                            document.body.appendChild(label);
                        }

                        const labelRect = label.getBoundingClientRect();
                        if (labelRect.right > window.innerWidth) {
                            label.style.left = `${rect.left + scrollX}px`;
                        }
                        if (labelRect.bottom > window.innerHeight) {
                            label.style.top = `${rect.top + scrollY - labelRect.height}px`;
                        }

                        if (labelRect.left < 0) {
                            label.style.left = `${scrollX}px`;
                        }

                        if (!window.surfAiLabels) window.surfAiLabels = [];
                        window.surfAiLabels.push(label);

                    } else {
                        // Position relative to parent element 
                        label.style.position = 'absolute'; 
                        label.style.top = '0px';
                        label.style.left = '0px';
                        el.appendChild(label);
                    }
                });
            """
            
            page.evaluate(numbering_script)
            page.wait_for_timeout(500)

        except Exception as e:
            self.logger.debug(f"Failed to apply highlights and numbering: {str(e)}")

    def remove_highlight_from_elements(self, page):
        """Remove highlights and numbering from all elements."""
        try:
            remove_labels_script = """

                if (window.surfAiLabels) {
                    window.surfAiLabels.forEach(label => label.remove());
                    window.surfAiLabels = [];
                }
                
                const elements = Array.from(document.querySelectorAll('*[data-highlight-number]'));
                elements.forEach(el => {
                    const labels = el.getElementsByClassName('surf-ai-highlight-label');
                    while(labels.length > 0) {
                        labels[0].remove();
                    } 
                    
                    el.style.border = el.dataset.originalBorder || '';
                    el.style.boxSizing = el.dataset.originalBoxSizing || '';
                    el.style.position = el.dataset.originalPosition || '';  

                    delete el.dataset.highlightNumber;
                    delete el.dataset.originalBorder;
                    delete el.dataset.originalBoxSizing;
                    delete el.dataset.originalPosition;
                });
            """
            page.evaluate(remove_labels_script)
            
        except Exception as e:
            self.logger.debug(f"Failed to remove highlights: {str(e)}")

                
    def take_screenshot(self, page, task_name):
        from datetime import datetime
        current_time = datetime.now().strftime("%H-%M-%S")
        screenshot_path = f"./surf_ai/screenshots/{current_time}_{task_name}.png"
        page.screenshot(path=screenshot_path, full_page=False)
        self.screenshot_url = screenshot_path
        
        with open(screenshot_path, "rb") as image_file:
            self.screenshot_base64 = base64.b64encode(image_file.read()).decode('utf-8')

    def is_critical_error(self, error) -> bool:
        """Determine if error should abort the entire process"""
        return isinstance(error, (KeyboardInterrupt, TimeoutError)) 


    @staticmethod
    def sanitize_gpt_json_response(response_str: str) -> str:
        response_str = re.sub(r'^```json\s*', '', response_str, flags=re.MULTILINE)
        response_str = re.sub(r'```$', '', response_str, flags=re.MULTILINE)
        
        response_str = re.sub(
            r'"\s*"\s*', 
            '', 
            response_str,
            flags=re.MULTILINE
        )
        
        # Remove trailing semicolons in commands
        response_str = re.sub(
            r';(\s*["}\]])', 
            r'\1', 
            response_str,
            flags=re.MULTILINE
        )
        
        return response_str.strip()
    
     