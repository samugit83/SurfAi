import logging
import json
from typing import List, Dict
from .prompts import (
    CODE_SYSTEM_PROMPT, 
    EVALUATION_AGENT_PROMPT
)
from .utils import sanitize_gpt_response
from models.models import call_model
from .prompts import DEFAULT_TOOLS

class MemoryLogHandler(logging.Handler):
    def __init__(self, memory_logs: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_logs = memory_logs

    def emit(self, record):
        log_entry = self.format(record)
        self.memory_logs.append(log_entry)

class CodeAgent:
    def __init__(self, chat_history: List[Dict], import_libraries: List[str]):
        logging.basicConfig(level=logging.DEBUG)  
        self.chat_history = chat_history
        self.import_libraries = import_libraries
        self.memory_logs = []  # Initialize the logs list
        self.logger = logging.getLogger(__name__)
        self.json_plan = None
        self.logger.setLevel(logging.DEBUG)

        memory_handler = MemoryLogHandler(self.memory_logs)
        memory_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        memory_handler.setFormatter(formatter)
        self.logger.addHandler(memory_handler)

    def run_agent(self):
        try:
            self.logger.info(f"\n\n\n\n\n\n🟢 Starting agent with main task: {self.chat_history}")
            self.import_libraries = self.import_libraries + DEFAULT_TOOLS

            agent_prompt = CODE_SYSTEM_PROMPT.format(
                conversation_history=self.chat_history,
                import_libraries=self.import_libraries
            )

            agent_output_str = call_model(
                chat_history=[{"role": "user", "content": agent_prompt}],
                model="gpt-4o"
            )

            agent_output_str = sanitize_gpt_response(agent_output_str)
            self.json_plan = json.loads(agent_output_str)

            print(f"\n\n🔵 Code agent json plan: {json.dumps(self.json_plan, indent=4)}")

            max_iterations = 2
            iteration = 0

            while iteration <= max_iterations + 1:
                iteration += 1
                print(f"\n\n🟠 Executing iteration: {iteration}")
                subtasks = self.json_plan["subtasks"]
                results = {}

                # Execute each subtask in the JSON plan
                for subtask in subtasks:
                    code_string = subtask["code"]
                    # Pass in the logger to the exec context
                    temp_namespace = {"logger": self.logger}
                    
                    # Execute the code string which now uses logger for output
                    exec(code_string, temp_namespace)
                    
                    tool_name = subtask["tool_name"]
                    input_tool_name = subtask.get("input_from_tool", "")

                    # If the tool exists in the temp_namespace, proceed
                    if tool_name in temp_namespace:
                        tool_func = temp_namespace[tool_name]

                        # Determine input if specified
                        if input_tool_name:
                            previous_result = results.get(input_tool_name, {})
                            result = tool_func(previous_result)  # Call the function with the previous result
                        else:
                            result = tool_func()

                        results[tool_name] = result
                        self.logger.info(f"\n\n🟣 Output from '{tool_name}': {result}")

                print(f"\n🟠 Memory logs at iteration {iteration}: {self.memory_logs}")

                evaluation_prompt = EVALUATION_AGENT_PROMPT.format(
                    original_prompt=agent_prompt,
                    original_json_plan=json.dumps(self.json_plan, indent=4),
                    max_iterations=max_iterations,
                    iteration=iteration,
                    logs=self.memory_logs
                )

                evaluation_output_str = call_model(
                    chat_history=[{"role": "user", "content": evaluation_prompt}],
                    model="gpt-4o"
                )

                evaluation_output_str = sanitize_gpt_response(evaluation_output_str)
                print('\n\n🟠 evaluation_output_str', evaluation_output_str)

                evaluation_output = json.loads(evaluation_output_str)

                # Check if the evaluation is satisfactory
                if iteration < max_iterations + 1:
                    if evaluation_output.get("satisfactory", False):
                        print(f"\n\n\🟢🟢🟢 Evaluation is satisfactory, returning final answer: {evaluation_output.get('final_answer', '')}")
                        return evaluation_output.get("final_answer", "")
                    else:
                        if evaluation_output.get("satisfactory", False) is False and evaluation_output.get("max_iterations_reached", False) is False:
                            print(f"\n\n🔴🔴🔴 Evaluation is not satisfactory, updating json plan: {evaluation_output}")
                            self.json_plan = evaluation_output.get("new_json_plan", {})
                        elif evaluation_output.get("max_iterations_reached", False):
                            self.logger.warning("\n\n🔴 Max iterations reached without satisfactory evaluation.")
                            return evaluation_output.get("final_answer", "")
                else:
                    self.logger.warning("\n\n🔴 Max iterations reached without satisfactory evaluation.")
                    return evaluation_output.get("final_answer", "")
                    
        except Exception as e:
            self.logger.error(f"\n\n\n\n🔴 Error running agent: {e}")
