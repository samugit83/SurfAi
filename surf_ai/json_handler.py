import json
import re

class JsonResponseHandler:
    @staticmethod
    def sanitize_response(response_str: str) -> str:
        response_str = re.sub(r'^```json\s*', '', response_str, flags=re.MULTILINE)
        response_str = re.sub(r'```$', '', response_str, flags=re.MULTILINE)
        
        response_str = re.sub(
            r'"\s*"\s*', 
            '', 
            response_str,
            flags=re.MULTILINE 
        )
        
        return response_str.strip()
    

    @staticmethod
    def update_task_structure(original_json, new_json):
        if 'updated_tasks' in new_json:
            existing_tasks = original_json.get('tasks', [])
            task_name_to_index = {task['task_name']: index for index, task in enumerate(existing_tasks)}
            
            for new_task in new_json['updated_tasks']:   
                task_name = new_task['task_name']
                if task_name in task_name_to_index: 
                    existing_tasks[task_name_to_index[task_name]] = new_task
                else:
                    existing_tasks.append(new_task)
            
            original_json['tasks'] = existing_tasks
            for key in new_json:
                if key not in ['tasks', 'updated_tasks_and_new_task']:
                    original_json[key] = new_json[key]
        return original_json
