import requests
import os
import json

class StockAI:
    """
    Stock AI Client for protected endpoints.
    """
    # الرابط الافتراضي (يمكنك تغييره هنا لمرة واحدة)
    DEFAULT_URL = "http://127.0.0.1:5000"

    def __init__(self, api_key, base_url=None):
        """
        Initialize the client.
        :param api_key: Your API Key.
        :param base_url: Optional. Defaults to local server if not provided.
        """
        self.api_key = api_key
        # إذا لم يرسل المستخدم رابطاً، نستخدم الرابط الافتراضي
        self.base_url = (base_url or self.DEFAULT_URL).rstrip('/')
        
        self.headers = {
            "x-api-key": self.api_key
        }

    def _handle_response(self, response):
        try:
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise PermissionError("⛔ Authentication Required: Missing or invalid API Key.")
            elif response.status_code == 403:
                raise PermissionError("⛔ Access Denied: Invalid API Key.")
            else:
                raise Exception(f"❌ Server Error ({response.status_code}): {response.text}")
        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON response", "raw": response.text}

    # --- 1. Multi-Agent Analysis ---
    def analyze_multi_agent(self, file_path, symbol="UNKNOWN"):
        endpoint = f"{self.base_url}/api/ai_multi_agent_analysis"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        data = {'symbol': symbol}
        files = {'file': open(file_path, 'rb')}

        print(f"🚀 Analyzing {symbol}...")
        response = requests.post(endpoint, headers=self.headers, files=files, data=data)
        return self._handle_response(response)

    # --- 2. Direct Prediction ---
    def predict_stock(self, file_path, file_type=None, analysis_mode="normal", manual_price=None):
        endpoint = f"{self.base_url}/predict_stock"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_type:
            if file_path.lower().endswith('.csv'): file_type = 'csv'
            elif file_path.lower().endswith(('.png', '.jpg')): file_type = 'image'
        
        data = {'file_type': file_type, 'analysis_mode': analysis_mode}
        if manual_price: data['manual_price'] = manual_price

        files = {'file': open(file_path, 'rb')}
        response = requests.post(endpoint, headers=self.headers, files=files, data=data)
        return self._handle_response(response)

    # --- 3. Market Pulse ---
    def get_market_pulse(self):
        endpoint = f"{self.base_url}/api/market_pulse"
        response = requests.get(endpoint, headers=self.headers)
        return self._handle_response(response)