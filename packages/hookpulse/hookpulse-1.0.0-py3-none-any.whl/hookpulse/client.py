"""
HookPulse API Client

Main client class for interacting with the HookPulse API.
"""

import requests
from typing import Optional, Dict, Any, List
from .exceptions import HookPulseError, HookPulseAPIError, HookPulseAuthError


class HookPulseClient:
    """
    Client for interacting with the HookPulse API.
    
    Args:
        api_key: Your HookPulse API key (required)
        brand_uuid: Your HookPulse brand UUID (required)
        base_url: Base URL for the API (default: https://api.hookpulse.io)
        timeout: Request timeout in seconds (default: 30)
    
    Example:
        >>> client = HookPulseClient(
        ...     api_key="your-api-key",
        ...     brand_uuid="your-brand-uuid"
        ... )
    """
    
    def __init__(
        self,
        api_key: str,
        brand_uuid: str,
        base_url: str = "https://api.hookpulse.io",
        timeout: int = 30
    ):
        if not api_key:
            raise HookPulseAuthError("API key is required")
        if not brand_uuid:
            raise HookPulseAuthError("Brand UUID is required")
        
        self.api_key = api_key
        self.brand_uuid = brand_uuid
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            "x-hookpulse-api-key": self.api_key,
            "x-brand-uuid": self.brand_uuid,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the HookPulse API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path (e.g., "/v1/api/add_schedule/")
            params: Query parameters
            json_data: JSON request body
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            Response JSON data
        
        Raises:
            HookPulseAPIError: If the API returns an error
            HookPulseAuthError: If authentication fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise HookPulseAuthError("Authentication failed. Please check your API key and brand UUID.")
            
            # Handle other errors
            if not response.ok:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    error_data = {"error": response.text or f"HTTP {response.status_code}"}
                
                error_message = error_data.get("error", f"API request failed with status {response.status_code}")
                raise HookPulseAPIError(
                    error_message,
                    status_code=response.status_code,
                    response=error_data
                )
            
            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise HookPulseError(f"Request failed: {str(e)}")
    
    # Domain Management
    def add_domain(self, domain: str, protocol: str = "https", rate_limit_per_second: Optional[int] = None, 
                   max_concurrent: Optional[int] = None) -> Dict[str, Any]:
        """Add a new domain to your HookPulse account"""
        data = {
            "domain": domain,
            "protocol": protocol
        }
        if rate_limit_per_second is not None:
            data["rate_limit_per_second"] = rate_limit_per_second
        if max_concurrent is not None:
            data["max_concurrent"] = max_concurrent
        return self._request("POST", "/v1/api/add_domain/", json_data=data)
    
    def get_domains(self, page: int = 1) -> Dict[str, Any]:
        """Get paginated list of domains"""
        return self._request("GET", "/v1/api/get_domain_paginated/", params={"page": page})
    
    def get_domain_uuid(self, domain: str, protocol: str = "https") -> Dict[str, Any]:
        """Get UUID for a specific domain"""
        return self._request("POST", "/v1/api/get_domain_uuid/", json_data={
            "domain": domain,
            "protocol": protocol
        })
    
    # Webhook Templates
    def create_webhook_template(self, name: str, url: str, method: str = "POST", 
                               headers: Optional[Dict[str, str]] = None,
                               body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a webhook template"""
        data = {
            "name": name,
            "url": url,
            "method": method
        }
        if headers:
            data["headers"] = headers
        if body:
            data["body"] = body
        return self._request("POST", "/v1/api/add_webhook_template/", json_data=data)
    
    def get_webhook_templates(self, page: int = 1) -> Dict[str, Any]:
        """Get paginated list of webhook templates"""
        return self._request("GET", "/v1/api/get_webhook_template_paginated/", params={"page": page})
    
    def get_webhook_template(self, template_uuid: str) -> Dict[str, Any]:
        """Get a specific webhook template by UUID"""
        return self._request("POST", "/v1/api/get_webhook_template_uuid/", json_data={"template_uuid": template_uuid})
    
    def update_webhook_template(self, template_uuid: str, **kwargs) -> Dict[str, Any]:
        """Update a webhook template"""
        data = {"template_uuid": template_uuid}
        data.update(kwargs)
        return self._request("POST", "/v1/api/update_webhook_template/", json_data=data)
    
    def delete_webhook_template(self, template_uuid: str) -> Dict[str, Any]:
        """Delete a webhook template"""
        return self._request("POST", "/v1/api/delete_webhook_template/", json_data={"template_uuid": template_uuid})
    
    # Workflow Templates
    def create_workflow_template(self, name: str, steps: List[Dict[str, Any]], 
                                 mode: str = "concurrent", **kwargs) -> Dict[str, Any]:
        """Create a workflow template"""
        data = {
            "name": name,
            "steps": steps,
            "mode": mode
        }
        data.update(kwargs)
        return self._request("POST", "/v1/api/add_workflow_template/", json_data=data)
    
    def get_workflow_templates(self, page: int = 1) -> Dict[str, Any]:
        """Get paginated list of workflow templates"""
        return self._request("GET", "/v1/api/get_workflow_template_paginated/", params={"page": page})
    
    def get_workflow_template(self, template_uuid: str) -> Dict[str, Any]:
        """Get a specific workflow template by UUID"""
        return self._request("POST", "/v1/api/get_workflow_template_uuid/", json_data={"template_uuid": template_uuid})
    
    def update_workflow_template(self, template_uuid: str, **kwargs) -> Dict[str, Any]:
        """Update a workflow template"""
        data = {"template_uuid": template_uuid}
        data.update(kwargs)
        return self._request("POST", "/v1/api/update_workflow_template/", json_data=data)
    
    def delete_workflow_template(self, template_uuid: str) -> Dict[str, Any]:
        """Delete a workflow template"""
        return self._request("POST", "/v1/api/delete_workflow_template/", json_data={"template_uuid": template_uuid})
    
    # Schedules
    def create_schedule(self, webhook_url: str, schedule_type: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new schedule
        
        Args:
            webhook_url: URL to call when schedule triggers
            schedule_type: Type of schedule (interval, cron, clocked, solar, debounce)
            **kwargs: Additional schedule parameters based on type
        
        Example:
            >>> # Interval schedule
            >>> client.create_schedule(
            ...     webhook_url="https://example.com/webhook",
            ...     schedule_type="interval",
            ...     interval_seconds=3600
            ... )
            >>> # Cron schedule
            >>> client.create_schedule(
            ...     webhook_url="https://example.com/webhook",
            ...     schedule_type="cron",
            ...     cron_expression="0 9 * * *",
            ...     timezone="America/New_York"
            ... )
        """
        data = {
            "webhook_url": webhook_url,
            "schedule_type": schedule_type
        }
        data.update(kwargs)
        return self._request("POST", "/v1/api/add_schedule/", json_data=data)
    
    def get_schedules(self, page: int = 1, status: Optional[str] = None) -> Dict[str, Any]:
        """Get paginated list of schedules"""
        params = {"page": page}
        if status:
            params["status"] = status
        return self._request("GET", "/v1/api/get_schedule_paginated/", params=params)
    
    def get_schedule(self, schedule_uuid: str) -> Dict[str, Any]:
        """Get a specific schedule by UUID"""
        return self._request("POST", "/v1/api/get_schedule_uuid/", json_data={"schedule_uuid": schedule_uuid})
    
    def update_schedule(self, schedule_uuid: str, **kwargs) -> Dict[str, Any]:
        """Update a schedule"""
        data = {"schedule_uuid": schedule_uuid}
        data.update(kwargs)
        return self._request("POST", "/v1/api/update_schedule/", json_data=data)
    
    def delete_schedule(self, schedule_uuid: str) -> Dict[str, Any]:
        """Delete a schedule"""
        return self._request("POST", "/v1/api/delete_schedule/", json_data={"schedule_uuid": schedule_uuid})
    
    def update_schedule_status(self, schedule_uuid: str, status: str) -> Dict[str, Any]:
        """Update schedule status (active, paused, stopped)"""
        return self._request("POST", "/v1/api/update_schedule_status/", json_data={
            "schedule_uuid": schedule_uuid,
            "status": status
        })
    
    # System Secrets
    def create_secret(self, key: str, value: str) -> Dict[str, Any]:
        """Create a system secret"""
        return self._request("POST", "/v1/api/add_system_secret/", json_data={
            "key": key,
            "value": value
        })
    
    def get_secrets(self, page: int = 1) -> Dict[str, Any]:
        """Get paginated list of system secrets"""
        return self._request("GET", "/v1/api/get_system_secret_paginated/", params={"page": page})
    
    def get_secret(self, secret_uuid: str) -> Dict[str, Any]:
        """Get a specific secret by UUID (value is not returned for security)"""
        return self._request("POST", "/v1/api/get_system_secret_uuid/", json_data={"secret_uuid": secret_uuid})
    
    def update_secret(self, secret_uuid: str, value: str) -> Dict[str, Any]:
        """Update a system secret"""
        return self._request("POST", "/v1/api/update_system_secret/", json_data={
            "secret_uuid": secret_uuid,
            "value": value
        })
    
    def delete_secret(self, secret_uuid: str) -> Dict[str, Any]:
        """Delete a system secret"""
        return self._request("POST", "/v1/api/delete_system_secret/", json_data={"secret_uuid": secret_uuid})
    
    # Human Approvals
    def approve_execution(self, execution_plan_uuid: str) -> Dict[str, Any]:
        """Approve a workflow execution waiting for human approval"""
        return self._request("POST", "/v1/api/human_approval_action/", json_data={
            "execution_plan_uuid": execution_plan_uuid,
            "action": "approve"
        })
    
    def reject_execution(self, execution_plan_uuid: str) -> Dict[str, Any]:
        """Reject a workflow execution waiting for human approval"""
        return self._request("POST", "/v1/api/human_approval_action/", json_data={
            "execution_plan_uuid": execution_plan_uuid,
            "action": "reject"
        })
    
    # Timezones
    def get_timezones(self) -> Dict[str, Any]:
        """Get list of all supported IANA timezones"""
        return self._request("GET", "/v1/api/get_timezones/")
    
    # Resources (generic)
    def get_resources(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get all resources"""
        return self._request("GET", "/resources", params={"limit": limit, "offset": offset})
    
    def create_resource(self, name: str, resource_type: Optional[str] = None) -> Dict[str, Any]:
        """Create a new resource"""
        data = {"name": name}
        if resource_type:
            data["type"] = resource_type
        return self._request("POST", "/resources", json_data=data)
    
    def delete_resource(self, resource_id: str) -> None:
        """Delete a resource"""
        self._request("DELETE", f"/resources/{resource_id}")
