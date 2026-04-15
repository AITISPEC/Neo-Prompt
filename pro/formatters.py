import re

def format_thinking_display(text, is_final=False, visible_lines=3):
    if not text or text.strip() == "":
        return ""

    lines = text.strip().split('\n')
    lines = [line for line in lines if line.strip()]

    if is_final:
        if len(lines) > visible_lines:
            display_lines = lines[:visible_lines]
            hidden_count = len(lines) - visible_lines
            return f"""
            <div class="thinking-container">
                <div class="thinking-preview">{'<br>'.join(display_lines)}</div>
                <details class="thinking-details">
                    <summary style="font-weight: bold; font-size: 1.05em; cursor: pointer;">Показать ещё {hidden_count} строк</summary>
                    <div class="thinking-full">{'<br>'.join(lines)}</div>
                </details>
            </div>
            """
        else:
            return f"""
            <div class="thinking-container">
                <div class="thinking-preview">{'<br>'.join(lines)}</div>
            </div>
            """
    else:
        display_lines = lines[-visible_lines:] if len(lines) > visible_lines else lines
        return f"""
        <div class="thinking-container thinking-animated">
            <div class="thinking-preview">{'<br>'.join(display_lines)}</div>
            <span class="thinking-dots">...</span>
        </div>
        """

def format_response_display(text):
    if not text:
        return ""
    text = re.sub(r'\*\*Ответ:?\*\*:?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Ответ:?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\*\*.*?\*\*\s*', '', text)
    return text.strip()