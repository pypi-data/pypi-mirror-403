from openai import OpenAI
import httpx 

 
class LLMClient:
    def __init__(self, api_key: str, base_url: str, model_name: str, timeout, max_retries,http_client:httpx.Client = None):
        try:
            self.client = OpenAI(
                api_key=api_key, 
                base_url=base_url,
                timeout=timeout,
                max_retries=max_retries,
                http_client=http_client
            )
            self.model_name = model_name
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM client: {e}") from e
   
    def complete_chat(self, prompt, tempature,system_prompt=None):
        """
        Generate a text response with configurable system prompt.
       
        Args:
            prompt (str): User prompt
            system_prompt (str): System prompt (optional)
            model (str): Model name (optional, uses config default)
            max_tokens (int): Maximum tokens to generate
           
        Returns:
            str: Generated text response
        """
        model = self.model_name
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=prompt,
                temperature=tempature
            )

            return response.choices[0].message.content 
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}") from e
        
    def generate_response(self, prompt,system_prompt=None):
        """
        Generate a text response with configurable system prompt.
       
        Args:
            prompt (str): User prompt
            system_prompt (str): System prompt (optional)
            model (str): Model name (optional, uses config default)
            max_tokens (int): Maximum tokens to generate
           
        Returns:
            str: Generated text response
        """
        model = self.model_name
        
        try:
            response = self.client.responses.create(
                model=model,
                input=prompt
            )
            return response.output_text
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}") from e
