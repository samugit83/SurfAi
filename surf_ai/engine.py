import os
import time
import json
from dotenv import load_dotenv
from models.models import call_model
from .browser_manager import BrowserManager
from .command_executor import CommandExecutor
from .element_highlighter import ElementHighlighter
from .screenshot_manager import ScreenshotManager 
from .json_handler import JsonResponseHandler
from .logging_handler import LoggingConfigurator
from surf_ai.prompt import GEN_JSON_TASK_PROMPT, GEN_JSON_TASK_LOOP_PROMPT, FINAL_ANSWER_PROMPT

class SurfAiEngine:
    def __init__(self):
        load_dotenv()
        self.execution_logs = [] 
        self.logger = LoggingConfigurator.configure_logger(self.execution_logs)
        self.json_task_model = os.getenv("SURF_AI_JSON_TASK_MODEL")
        self.browser_manager = BrowserManager(command_timeout=10000)
        self.command_executor = CommandExecutor(self.logger)
        self.highlighter = ElementHighlighter(self.logger)
        self.screenshot_manager = ScreenshotManager(truncation_length=400000)
        self.max_retries = 2      
        self.retry_backoff = 2000 
        self.final_answer = None  

    def go_surf(self, prompt: str): 
        try:
            self._initialize_task(prompt)
            with self.browser_manager.create_browser() as browser:
                context = self.browser_manager.create_context(browser) 
                page = self.browser_manager.create_page(context)
                self._process_tasks(prompt, page)
                self.logger.debug("🟢 Final answer: %s", self.final_answer, extra={'no_memory': True})
            return self.final_answer
        except Exception as e:
            self.logger.exception(f"Critical error: {str(e)}")    
            raise

    def _call_model_with_retry(self, messages, model, **kwargs): 
        """
        Helper method that wraps the call_model function in a retry loop.
        It retries if the response is None, if it doesn't have the expected attribute,
        or if the JSON cannot be parsed.
        """
        attempts = 0 
        while attempts <= self.max_retries: 
            try:
                response = call_model(messages, model, **kwargs, output_format="json_object")
                if response is None:
                    raise ValueError("Received None as response from call_model")
                sanitized = JsonResponseHandler.sanitize_response(response)
                json.loads(sanitized)
                return response
            except (AttributeError, ValueError, json.JSONDecodeError) as e:
                attempts += 1
                self.logger.warning( 
                    "Received invalid response from call_model (attempt %d/%d) due to error: %s. Retrying in %dms...",
                    attempts, self.max_retries, e, self.retry_backoff,
                    extra={'no_memory': True}
                )
                if attempts > self.max_retries: 
                    self.logger.error("Max retries exceeded for call_model.", extra={'no_memory': True})
                    raise
                time.sleep(self.retry_backoff / 1000.0)  

    def _initialize_task(self, prompt: str):
        json_task_prompt = GEN_JSON_TASK_PROMPT.substitute(user_message=prompt)
        response = self._call_model_with_retry(
            [{"role": "user", "content": json_task_prompt}],
            self.json_task_model
        )
        self.json_task = json.loads(JsonResponseHandler.sanitize_response(response))
        self.logger.debug( 
            "🔵 Initial JSON response: %s", 
            json.dumps(self.json_task, indent=4), 
            extra={'no_memory': True}   
        )

    def _process_tasks(self, prompt: str, page):
        while True:
            task = self.json_task['tasks'][-1] 
            self._execute_task_commands(task, page)
            self._update_task_state(prompt, page, task)
              
            if self.json_task.get('is_last_task'):
                final_answer_prompt = FINAL_ANSWER_PROMPT.substitute( 
                    json_task=json.dumps(self.json_task, indent=4),
                    user_message=prompt
                )
                response = call_model(
                    [{"role": "user", "content": final_answer_prompt}],
                    self.json_task_model,
                    output_format="text"
                )
                self.logger.debug("Final task completed")
                self.final_answer = response  
                break 
 
    def _execute_task_commands(self, task, page):    
        if task.get('data_extraction') and (task.get('commands') == 'data_extraction' or task.get('commands') is None):
            return
        if task.get('commands') is None:  
            return 
        commands = [cmd.strip() for cmd in task['commands'].split(';') if cmd.strip()]
        for command in commands:  
            if self.command_executor.execute(command, page, task['task_name']):
                break     
 
    def _update_task_state(self, prompt: str, page, task): 
        self.highlighter.remove_highlight(page)   
        pages = page.context.pages
        if len(pages) > 1:
            page = pages[-1]  
            time.sleep(3)
            self.logger.debug("🟡 Multiple pages detected; switching to the last opened page.")
        self.highlighter.apply_highlight(page) 
        time.sleep(1)
        self.screenshot_manager.capture(page, task['task_name'])
 
        
        loop_prompt = GEN_JSON_TASK_LOOP_PROMPT.substitute( 
            json_task=json.dumps(self.json_task, indent=4), 
            execution_logs=self.execution_logs,
            scraped_page=self.screenshot_manager.scraped_page,
            user_message=prompt
        ) 
        
        response = self._call_model_with_retry(
            [{"role": "user", "content": loop_prompt}],
            self.json_task_model,
            image_base64=self.screenshot_manager.screenshot_base64,
            image_extension="png"
        ) 

        
        self.json_task = JsonResponseHandler.update_task_structure(
            self.json_task,
            json.loads(JsonResponseHandler.sanitize_response(response)) 
        )

        self.logger.debug(
            "🔵 Whole JSON tasks %s", 
            json.dumps(self.json_task, indent=4), 
            extra={'no_memory': True}
        )  
