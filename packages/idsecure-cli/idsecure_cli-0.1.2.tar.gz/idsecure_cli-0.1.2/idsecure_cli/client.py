import httpx
import base64
import time
import json
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_TEMPLATE = {
    "Ativacao": "", "Validade": "", "admin": False, "admissao": None, "admissionDate": "",
    "allowParkingSpotCompany": None, "availableCompanies": None, "availableGroupsVisitorsList": None,
    "availableResponsibles": None, "bairro": None, "barras": None, "blackList": False, "bornDate": "",
    "canUseFacial": True, "cards": [], "cargo": None, "cep": None, "cidade": None, "comments": "",
    "contingency": False, "cpf": None, "dataLastLog": None, "dateLimit": None, "dateStartLimit": None,
    "deleted": False, "document": "", "dtAdmissao": "", "dtNascimento": "", "email": None,
    "emailAcesso": None, "endereco": None, "estadoCivil": None, "expireOnDateLimit": False,
    "foto": None, "fotoDoc": None, "groups": [], "groupsList": [], "idArea": 0,
    "idDevice": None, "idResponsavel": None, "idType": 0, "inativo": False, "mae": "",
    "nacionalidade": None, "name": "", "nascimento": None, "naturalidade": None,
    "objectGuid": None, "pai": "", "password": "", "phone": None, "photoDeleted": False,
    "photoIdFaceState": None, "photoTimestamp": 0, "pis": 0, "pisAnterior": 0,
    "ramal": None, "registration": "", "responsavelNome": None, "rg": None,
    "selectedGroupsVisitorsList": None, "selectedIdGroupsVisitorsList": None, "selectedIdResponsible": None,
    "selectedIdVisitedCompany": None, "selectedNameResponsible": None, "selectedResponsible": None,
    "selectedVisitedCompany": None, "senha": 0, "sexo": "M", "shelfLife": None, "shelfStartLife": None,
    "telefone": None, "templates": [], "templatesImages": [], "templatesList": [], "templatesPanic": [],
    "templatesPanicImages": [], "templatesPanicList": [], "timeOfRegistration": None, "userGroupsList": [],
    "veiculo_cor": None, "veiculo_marca": None, "veiculo_modelo": None, "veiculo_placa": None,
    "visitorCompany": None, "credits": [], "rulesList": [], "password_confirmation": "", "customFields": {}
}

class IDSecureClient:
    """
    Asynchronous client for IDSecure API.
    """
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def login(self, username: Optional[str] = None, password: Optional[str] = None) -> str:
        """
        Logs in to the IDSecure API and retrieves a JWT access token.
        """
        user = username or self.username
        pwd = password or self.password

        if not user or not pwd:
            raise ValueError("Username and password are required for login.")

        url = f"{self.base_url}/api/login/"
        payload = {
            "username": user,
            "password": pwd
        }
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        self.token = data.get("accessToken")
        
        if not self.token:
            raise ValueError("Login failed: accessToken not found in response.")
            
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        logger.info("Successfully logged in and obtained access token.")
        return self.token

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """
        Internal method to handle authenticated requests.
        """
        if not self.token:
            await self.login()

        url = f"{self.base_url}/{path.lstrip('/')}"
        
        # Ensure Content-Type is set for POST/PUT if not already set
        if method in ["POST", "PUT"] and "json" in kwargs:
             if "headers" not in kwargs:
                 kwargs["headers"] = {}
             kwargs["headers"].setdefault("Content-Type", "application/json")

        response = await self.client.request(method, url, **kwargs)
        
        if response.status_code == 401:
            logger.info("Token expired or unauthorized, attempting to re-login.")
            await self.login()
            response = await self.client.request(method, url, **kwargs)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if response.status_code == 400:
                logger.error(f"Bad Request (400) from IDSecure: {response.text}")
            elif response.status_code == 500:
                logger.error(f"Internal Server Error (500) from IDSecure: {response.text}")
                # Return a failure structure rather than raising
                return {"code": 500, "error": response.text or "Internal Server Error"}
            raise e
        
        if response.content:
            return response.json()
        return None

    # --- User Management ---

    async def list_users(self, start: int = 0, length: int = 100, draw: int = 0) -> Dict[str, Any]:
        """
        Retrieves a list of users.
        """
        params = {
            "start": start,
            "length": length,
            "draw": draw
        }
        return await self._request("POST", "api/user/list", params=params)

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves a single user's data.
        """
        return await self._request("GET", f"api/user/{user_id}")

    async def save_custom_fields(self) -> Any:
        """
        Finalizes user creation by saving custom fields.
        """
        return await self._request("POST", "api/util/savecustomfields", json=[])

    async def create_user(self, 
                          name: Optional[str] = None, 
                          registration: Optional[str] = None, 
                          id_device: Optional[int] = None,
                          image_path_or_base64: Optional[str] = None, 
                          user_data: Optional[Dict[str, Any]] = None, 
                          **kwargs) -> Dict[str, Any]:
        """
        Creates a new user. 
        If user_data is provided, it merges it into a default template.
        Arbitrary fields can be passed via **kwargs to override/set specific values.
        """
        # 1. Start with a fresh template
        template = USER_TEMPLATE.copy()
        template["photoTimestamp"] = int(time.time())

        # 2. Merge user_data
        if user_data:
            data_to_merge = user_data.copy()
            data_to_merge.pop("id", None)
            for key, value in data_to_merge.items():
                if value is not None:
                    template[key] = value

        # 3. Merge kwargs
        for key, value in kwargs.items():
            template[key] = value

        # 4. Explicit parameters override
        if name: template["name"] = name
        if registration: template["registration"] = registration
        if id_device: template["idDevice"] = id_device

        # 5. Handle image (Support 'foto' or 'image' aliases)
        img = image_path_or_base64 or kwargs.pop("foto", None) or kwargs.pop("image", None)
        if img:
            photo_base64 = None
            if img.startswith("data:image"):
                photo_base64 = img.split("base64,")[1]
            elif any(img.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                # Synchronous read for simplicity
                with open(img, "rb") as f:
                    photo_base64 = base64.b64encode(f.read()).decode('utf-8')
            else:
                photo_base64 = img
            
            template["foto"] = photo_base64
            template["photoTimestamp"] = int(time.time())

        # 6. Mandatory cleanup
        template["photoDeleted"] = False
        template["canUseFacial"] = True
        template["password_confirmation"] = ""
        if not template.get("admissionDate"): template["admissionDate"] = ""
        if not template.get("bornDate"): template["bornDate"] = ""
        
        for field in ["templates", "templatesImages", "templatesList", "templatesPanic", "templatesPanicImages", "templatesPanicList"]:
            template[field] = []

        # 7. Request
        logger.info(f"Creating user {template.get('name')}...")
        result = await self._request("POST", "api/user/", json=template)
        
        # 8. Finalize
        if result and result.get("newID"):
            await self.save_custom_fields()
        
        return result

    async def update_user(self, user_id: int, image_path_or_base64: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Updates an existing user using the 'Delete before Create' strategy.
        """
        # 1. Fetch
        logger.info(f"Fetching user {user_id} for update...")
        fetched_data = await self.get_user(user_id)
        if not fetched_data:
            raise ValueError(f"User {user_id} not found.")

        # 2. Delete
        logger.info(f"Deleting user {user_id} before re-creation...")
        await self.delete_user(user_id)

        # 3. Re-create
        return await self.create_user(
            image_path_or_base64=image_path_or_base64,
            user_data=fetched_data,
            **kwargs
        )

    async def delete_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Deletes a user by ID.
        """
        return await self._request("DELETE", f"api/user/{user_id}")

    # --- Device Management ---

    async def list_devices(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of devices.
        """
        return await self._request("GET", "api/device/")

    # --- Reports ---

    async def get_global_logs(self, start_timestamp: int, end_timestamp: int, **kwargs) -> Dict[str, Any]:
        """
        Retrieves global logs report.
        """
        payload = {
            "cameras": kwargs.get("cameras", []),
            "areas": kwargs.get("areas", []),
            "devices": kwargs.get("devices", []),
            "users": kwargs.get("users", []),
            "groups": kwargs.get("groups", []),
            "schedules": kwargs.get("schedules", []),
            "start": start_timestamp,
            "end": end_timestamp,
            "accessLogs": kwargs.get("accessLogs", []),
            "creditTypes": kwargs.get("creditTypes", []),
            "operators": kwargs.get("operators", []),
            "inspections": kwargs.get("inspections", [])
        }
        
        # Adding datatable params if provided
        draw = kwargs.get("draw", 1)
        start = kwargs.get("start", 0)
        length = kwargs.get("length", 100)
        
        path = f"api/report/logs/global?draw={draw}&start={start}&length={length}"
        if "order" in kwargs:
            # Simplified order handling
            order_col = kwargs["order"][0].get("column", 1)
            order_dir = kwargs["order"][0].get("dir", "desc")
            path += f"&order%5B0%5D%5Bcolumn%5D={order_col}&order%5B0%5D%5Bdir%5D={order_dir}"

        return await self._request("POST", path, json=payload)
