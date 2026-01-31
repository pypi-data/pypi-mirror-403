import requests
import json
from typing import Optional, Dict, List, Any, Union

class OpenDBS:
    def __init__(self, base_url: str, token: Optional[str] = None, ignore_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.ignore_ssl = ignore_ssl
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def set_token(self, token: str):
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method, 
                url, 
                json=data, 
                params=params, 
                verify=not self.ignore_ssl
            )
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_body = e.response.json()
                if 'error' in error_body:
                    error_msg = error_body['error']
            except:
                pass
            raise Exception(f"OpenDBS Error: {error_msg}")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Could not connect to OpenDBS at {self.base_url}. Is the server running?")

    # --- Authentication ---

    def login(self, username, password):
        res = self._request("POST", "/api/auth/login", {"username": username, "password": password})
        if 'token' in res:
            self.set_token(res['token'])
        return res

    def register(self, user_data):
        return self._request("POST", "/api/auth/register", user_data)

    def regenerate_api_key(self):
        return self._request("POST", "/api/auth/regenerate-api-key")

    # --- Database Management ---

    def list_databases(self, include_racks=False):
        res = self._request("GET", "/api/databases", params={"include_racks": str(include_racks).lower()})
        return res.get("databases", [])

    def create_database(self, name):
        return self._request("POST", "/api/databases", {"name": name})

    def delete_database(self, name):
        return self._request("DELETE", f"/api/databases/{name}")

    # --- Rack Management ---

    def list_racks(self, database):
        res = self._request("GET", f"/api/databases/{database}/racks")
        return res.get("racks", [])

    def create_rack(self, database, name, type="nosql", schema=None):
        payload = {"name": name, "type": type}
        if schema:
            payload["schema"] = schema
        return self._request("POST", f"/api/databases/{database}/racks", payload)

    def delete_rack(self, database, rack):
        return self._request("DELETE", f"/api/databases/{database}/racks/{rack}")

    def clear_rack(self, database, rack):
        return self._request("DELETE", f"/api/databases/{database}/racks/{rack}/clear")

    # --- Documents (NoSQL) ---

    def insert(self, database, rack, document):
        return self._request("POST", f"/api/databases/{database}/racks/{rack}/documents", document)

    def find(self, database, rack, query=None, populate=False):
        params = query or {}
        if populate:
            params["populate"] = "true"
        res = self._request("GET", f"/api/databases/{database}/racks/{rack}/documents", params=params)
        return res.get("results", [])

    def find_one(self, database, rack, doc_id, populate=False):
        res = self.find(database, rack, {"id": doc_id}, populate)
        return res[0] if res else None

    def update(self, database, rack, doc_id, updates):
        return self._request("PUT", f"/api/databases/{database}/racks/{rack}/documents/{doc_id}", updates)

    def delete(self, database, rack, doc_id):
        return self._request("DELETE", f"/api/databases/{database}/racks/{rack}/documents/{doc_id}")

    # --- SQL Operations ---

    def sql(self, database, query):
        res = self._request("POST", f"/api/sql/{database}/execute", {"query": query})
        if isinstance(res, dict) and 'results' in res:
            return res['results']
        return res

    # --- Search Features ---

    def search(self, database, rack, query_body):
        res = self._request("POST", f"/api/databases/{database}/racks/{rack}/search", query_body)
        return res.get("results", [])

    def fuzzy_search(self, database, rack, field, query):
        return self.search(database, rack, {"type": "fuzzy", "field": field, "query": query})

    def vector_search(self, database, rack, field, vector, k=5):
        return self.search(database, rack, {"type": "vector", "field": field, "vector": vector, "k": k})
    
    # --- Backup ---

    def create_backup(self):
        return self._request("POST", "/api/backup/create")

    def list_backups(self):
        res = self._request("GET", "/api/backup/list")
        return res.get("backups", [])
