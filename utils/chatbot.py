import google.generativeai as genai
import os

class CybersecurityChatbot:
    def __init__(self, api_key='YOUR_GEMINI_API_KEY'):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.chat_session = self.model.start_chat(history=[])
        else:
            print("Warning: Gemini API Key not found. Chatbot will be disabled.")
            self.model = None

    def get_response(self, user_message):
        """
        Sends a message to the Gemini API and returns the response.
        Enforces cybersecurity domain in the system prompt simulation.
        """
        if not self.model:
             return "Error: Chatbot is not configured (Missing API Key)."

        # Domain Validation / System Prompt Injection
        # We can simulate system prompt by pre-appending context if the API model doesn't support system instructions directly in this version
        # Or checking keywords.
        
        system_instruction = (
            "You are a specialized Cybersecurity Assistant for a Ransomware Detection Project. "
            "You MUST ONLY answer questions related to: Ransomware, Malware, Threat Intelligence, "
            "Security Best Practices, and Incident Response. "
            "If the user asks about anything else (e.g., general programming, unrelated topics), "
            "politely decline and ask them to focus on cybersecurity. "
            "Keep answers concise and academic.\n\n"
        )
        
        full_prompt = f"{system_instruction}User Query: {user_message}"

        try:
            response = self.chat_session.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"
