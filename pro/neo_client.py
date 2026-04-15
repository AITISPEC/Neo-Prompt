import requests
import json
import time
from .config import BASE_API_URL, USER_NUM, DEFAULT_CONTEXT_LENGTH, MODEL_PRIORITY

class NeoClient:
    def __init__(self):
        self.base_url = BASE_API_URL
        self.server_online = False
        self.current_model = None
        self.current_model_name = None
        self.model_available = False
        self.total_context = 0
        self.used_tokens = 0
        self.current_response_id = None
        self.models_list = []
        self.last_stats = {
            "speed": 0,
            "tokens": 0,
            "time": 0
        }

    def check_server_status(self):
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/models",
                headers={
                    "Authorization": USER_NUM,
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.server_online = True

                all_models = data.get("models", [])
                llm_models = [m for m in all_models if m.get("type") == "llm"]

                loaded_model_keys = []
                for model in llm_models:
                    if model.get("loaded_instances") and len(model["loaded_instances"]) > 0:
                        loaded_model_keys.append(model["key"])

                found_model_key = None
                found_model_name = None

                for priority in MODEL_PRIORITY:
                    if priority["key"] in loaded_model_keys:
                        found_model_key = priority["key"]
                        found_model_name = priority["name"]
                        break

                if not found_model_key and loaded_model_keys:
                    found_model_key = loaded_model_keys[0]
                    model_info = next((m for m in llm_models if m["key"] == found_model_key), None)
                    if model_info:
                        found_model_name = model_info.get("display_name") or found_model_key.split('/')[-1]
                    else:
                        found_model_name = found_model_key

                if found_model_key:
                    model_info = next((m for m in llm_models if m["key"] == found_model_key), None)
                    if model_info and model_info.get("loaded_instances"):
                        instance = model_info["loaded_instances"][0]
                        context_value = instance.get("config", {}).get("context_length")
                        self.total_context = context_value or DEFAULT_CONTEXT_LENGTH
                    else:
                        self.total_context = DEFAULT_CONTEXT_LENGTH

                    self.current_model = found_model_key
                    self.current_model_name = found_model_name
                    self.model_available = True
                    self.models_list = loaded_model_keys

                    return {
                        "status": "online",
                        "model": self.current_model_name,
                        "context": self.total_context,
                        "available_models": self.models_list
                    }
                else:
                    self.model_available = False
                    self.current_model = None
                    self.current_model_name = None
                    self.total_context = 0
                    return {
                        "status": "online_no_model",
                        "message": "Сервер онлайн, но нет подходящих моделей"
                    }
            else:
                self.server_online = False
                self.model_available = False
                return {
                    "status": "offline",
                    "message": f"HTTP {response.status_code}"
                }

        except Exception as e:
            self.server_online = False
            self.model_available = False
            return {
                "status": "offline",
                "message": str(e)
            }

    def send_message(self, message, reset_context=False):
        if not self.server_online or not self.model_available:
            return "⚠️ Сервер недоступен или модель не выбрана"

        if self.total_context > 0 and self.used_tokens >= self.total_context:
            return "⚠️ Контекст исчерпан. Начните новый чат."

        if reset_context:
            current_response_id = None
        else:
            current_response_id = self.current_response_id

        request_body = {
            "model": self.current_model,
            "messages": [{"role": "user", "content": message}],
            "store": True
        }
        if current_response_id:
            request_body["previous_response_id"] = current_response_id

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": USER_NUM,
                    "Content-Type": "application/json"
                },
                json=request_body,
                timeout=600
            )

            data = response.json()

            if response.status_code == 200:
                if data.get("usage"):
                    tokens_used = data["usage"].get("total_tokens", 0)
                    self.used_tokens += tokens_used

                if not reset_context and data.get("response_id"):
                    self.current_response_id = data["response_id"]

                if data.get("choices") and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return "⚠️ Пустой ответ"
            else:
                error_msg = f"HTTP {response.status_code}"
                if data.get("error"):
                    error_msg = data["error"].get("message", error_msg)
                return f"⚠️ Ошибка: {error_msg}"

        except Exception as e:
            return f"⚠️ Ошибка: {str(e)}"

    def update_last_stats(self, tokens, elapsed):
        self.last_stats["tokens"] = tokens
        self.last_stats["time"] = round(elapsed, 2)
        self.last_stats["speed"] = round(tokens / elapsed, 2) if elapsed > 0 else 0
        return self.last_stats

    def get_last_stats(self):
        return self.last_stats

    def send_message_with_preset_stream(self, message, preset_id, reset_context=False):
        if not self.server_online or not self.model_available:
            yield "⚠️ Сервер недоступен или модель не выбрана", "", ""
            return

        if self.total_context > 0 and self.used_tokens >= self.total_context:
            yield "⚠️ Контекст исчерпан. Начните новый чат.", "", ""
            return

        if reset_context:
            current_response_id = None
        else:
            current_response_id = self.current_response_id

        request_body = {
            "model": self.current_model,
            "messages": [{"role": "user", "content": message}],
            "preset": preset_id,
            "store": True,
            "stream": True
        }
        if current_response_id:
            request_body["previous_response_id"] = current_response_id

        start_time = time.time()
        full_content = ""
        full_reasoning = ""
        last_data = None
        tokens_used = 0

        try:
            with requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": USER_NUM,
                        "Content-Type": "application/json"
                    },
                    json=request_body,
                    stream=True,
                    timeout=600
            ) as response:

                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                last_data = data
                                if data.get('choices') and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'reasoning_content' in delta:
                                        full_reasoning += delta['reasoning_content']
                                    if 'content' in delta:
                                        full_content += delta['content']

                                    yield full_content, full_reasoning, "thinking"
                            except:
                                pass

                elapsed = time.time() - start_time

                if last_data and last_data.get("usage"):
                    tokens_used = last_data["usage"].get("total_tokens", 0)
                    self.used_tokens += tokens_used
                else:
                    # Если нет данных о токенах, примерно считаем
                    tokens_used = len(full_content.split()) + len(full_reasoning.split())
                    self.used_tokens += tokens_used

                # Принудительно обновляем статистику
                self.last_stats["tokens"] = tokens_used
                self.last_stats["time"] = round(elapsed, 2)
                self.last_stats["speed"] = round(tokens_used / elapsed, 2) if elapsed > 0 else 0

                if not reset_context and last_data and last_data.get("response_id"):
                    self.current_response_id = last_data["response_id"]

                yield full_content, full_reasoning, "final"

        except Exception as e:
            yield f"⚠️ Ошибка: {str(e)}", "", "error"

    def reset_chat(self):
        self.current_response_id = None
        self.used_tokens = 0

    def get_token_progress(self):
        if self.total_context <= 0:
            return 0, 0, 0
        percentage = (self.used_tokens / self.total_context) * 100
        return self.used_tokens, self.total_context, percentage