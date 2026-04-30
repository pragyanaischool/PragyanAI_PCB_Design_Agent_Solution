# orchestration/llm/groq_client.py

import os
import time
from typing import List, Dict, Optional


# ==================================================
# IMPORT GROQ SAFELY
# ==================================================
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False


# ==================================================
# CLIENT CLASS
# ==================================================
class GroqClient:
    """
    Robust Groq LLM wrapper
    """

    def __init__(
        self,
        model: str = "llama3-70b-8192",
        temperature: float = 0.2,
        max_retries: int = 2
    ):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.client = None

        if GROQ_AVAILABLE and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception:
                self.client = None

    # ==================================================
    # INTERNAL CALL
    # ==================================================
    def _call(self, messages: List[Dict]) -> str:
        """
        Low-level call with retries
        """

        if not self.client:
            return "[LLM Disabled: No API key or Groq not installed]"

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt >= self.max_retries:
                    return f"[LLM Error] {str(e)}"
                time.sleep(1)

        return "[LLM Failure]"

    # ==================================================
    # CHAT INTERFACE
    # ==================================================
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None
    ) -> str:
        """
        Chat-style interaction
        """

        temp = temperature if temperature is not None else self.temperature

        return self._call(messages)

    # ==================================================
    # SIMPLE PROMPT
    # ==================================================
    def complete(self, prompt: str) -> str:
        """
        Single prompt → response
        """
        return self.chat([
            {"role": "user", "content": prompt}
        ])

    # ==================================================
    # JSON RESPONSE MODE
    # ==================================================
    def complete_json(self, prompt: str) -> str:
        """
        Encourage structured JSON output
        """

        messages = [
            {
                "role": "system",
                "content": "Return ONLY valid JSON. No explanation."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        return self.chat(messages)

    # ==================================================
    # STREAMING (OPTIONAL)
    # ==================================================
    def stream(self, prompt: str):
        """
        Stream response chunks (if supported)
        """

        if not self.client:
            yield "[Streaming not available]"
            return

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            for chunk in stream:
                yield chunk.choices[0].delta.content or ""

        except Exception as e:
            yield f"[Stream Error] {str(e)}"

    # ==================================================
    # HEALTH CHECK
    # ==================================================
    def is_available(self) -> bool:
        return self.client is not None


# ==================================================
# GLOBAL INSTANCE
# ==================================================
groq_client = GroqClient()


# ==================================================
# QUICK TEST
# ==================================================
if __name__ == "__main__":
    client = GroqClient()

    print("Available:", client.is_available())

    response = client.complete("Explain resistor in PCB")
    print(response)
  
