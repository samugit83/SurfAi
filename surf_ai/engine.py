import os
from dotenv import load_dotenv
import json
from models.models import call_model
from .browser_manager import BrowserManager
from .command_executor import CommandExecutor
from .element_highlighter import ElementHighlighter
from .screenshot_manager import ScreenshotManager
from .json_handler import JsonResponseHandler
from .logging_handler import LoggingConfigurator
from surf_ai.prompt import GEN_JSON_TASK_PROMPT, GEN_JSON_TASK_LOOP_PROMPT

class SurfAiEngine:
    def __init__(self):
        load_dotenv()
        self.execution_logs = []
        self.logger = LoggingConfigurator.configure_logger(self.execution_logs)
        self.json_task_model = os.getenv("SURF_AI_JSON_TASK_MODEL")
        
        # Initialize components
        self.browser_manager = BrowserManager(command_timeout=1500)
        self.command_executor = CommandExecutor(self.logger)
        self.highlighter = ElementHighlighter(self.logger)
        self.screenshot_manager = ScreenshotManager(truncation_length=400000)
        
        self.max_retries = 2
        self.retry_backoff = 2000

    def go_surf(self, prompt: str):
        try:
            self._initialize_task(prompt)
            with self.browser_manager.create_browser() as browser:
                context = self.browser_manager.create_context(browser)
                page = self.browser_manager.create_page(context)
                self._process_tasks(prompt, page)
        except Exception as e:
            self.logger.exception(f"Critical error: {str(e)}") 
            raise

    def _initialize_task(self, prompt: str):
        json_task_prompt = GEN_JSON_TASK_PROMPT.substitute(user_message=prompt)
        self.logger.debug(
            "🔵 Initial JSON prompt: %s", 
            json_task_prompt, 
            extra={'no_memory': True}  
        )
        response = call_model([{"role": "user", "content": json_task_prompt}], self.json_task_model)
        self.logger.debug(
            "🔵 Initial JSON response: %s", 
            response, 
            extra={'no_memory': True}  
        )
        self.json_task = json.loads(JsonResponseHandler.sanitize_response(response))

    def _process_tasks(self, prompt: str, page):
        while True:
            task = self.json_task['tasks'][-1]
            self._execute_task_commands(task, page)
            self._update_task_state(prompt, page, task)
            
            if self.json_task.get('is_last_task'):
                self.logger.debug("Final task completed")
                break

    def _execute_task_commands(self, task, page):
        commands = [cmd.strip() for cmd in task['commands'].split(';') if cmd.strip()]
        for command in commands:
            if self.command_executor.execute(command, page, task['task_name']):
                break

    def _update_task_state(self, prompt: str, page, task):
        self.highlighter.remove_highlight(page)
        self.highlighter.apply_highlight(page)
        self.screenshot_manager.capture(page, task['task_name'])
        
        loop_prompt = GEN_JSON_TASK_LOOP_PROMPT.substitute(
            json_task=json.dumps(self.json_task, indent=4),
            execution_logs=self.execution_logs,
            scraped_page=self.screenshot_manager.scraped_page,
            user_message=prompt
        )
        
        response = call_model([{"role": "user", "content": loop_prompt}], 
                            self.json_task_model, 
                            image_base64=self.screenshot_manager.screenshot_base64,
                            image_extension="png")
        self.logger.debug(
            "🔵 JSON updated tasks: %s", 
            response, 
            extra={'no_memory': True}  
        )
        
        self.json_task = JsonResponseHandler.update_task_structure(
            self.json_task,
            json.loads(JsonResponseHandler.sanitize_response(response))
        )

        self.logger.debug(
            "🔵 Whole JSON tasks %s", 
            self.json_task, 
            extra={'no_memory': True}  
        )

  