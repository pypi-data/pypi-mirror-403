import requests
import json
import hashlib
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta
from .config import config


class APIError(Exception):
    """Custom API error"""
    pass


class APICache:
    """Simple file-based cache for API responses"""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 300):
        self.cache_dir = cache_dir or Path.home() / ".nexula" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def _get_cache_key(self, method: str, endpoint: str, params: str = "") -> str:
        """Generate cache key from request"""
        key_str = f"{method}:{endpoint}:{params}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, method: str, endpoint: str, params: str = "") -> Optional[Dict]:
        """Get cached response if valid"""
        cache_key = self._get_cache_key(method, endpoint, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            
            # Check if expired
            cached_time = datetime.fromisoformat(cached['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                cache_file.unlink()  # Delete expired cache
                return None
            
            return cached['data']
        except:
            return None
    
    def set(self, method: str, endpoint: str, data: Dict, params: str = ""):
        """Cache response"""
        cache_key = self._get_cache_key(method, endpoint, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f)
        except:
            pass  # Fail silently
    
    def clear(self):
        """Clear all cache"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


class APIClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, enable_cache: bool = True):
        self.api_key = api_key or config.get_api_key()
        self.base_url = base_url or config.get_api_url()
        self.cache = APICache() if enable_cache else None
        
        if not self.api_key:
            raise APIError("Not authenticated. Run 'nexula auth login' first.")

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, use_cache: bool = True, **kwargs) -> Dict[str, Any]:
        """Make API request with error handling and caching"""
        # Check cache for GET requests
        if use_cache and self.cache and method == "GET":
            params_str = json.dumps(kwargs.get('params', {}), sort_keys=True)
            cached = self.cache.get(method, endpoint, params_str)
            if cached:
                return cached
        
        url = f"{self.base_url}{endpoint}"
        kwargs["headers"] = self._headers()
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            result = response.json() if response.content else {}
            
            # Cache GET responses
            if use_cache and self.cache and method == "GET":
                params_str = json.dumps(kwargs.get('params', {}), sort_keys=True)
                self.cache.set(method, endpoint, result, params_str)
            
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise APIError("Authentication failed. Check your API key.")
            elif e.response.status_code == 403:
                raise APIError("Permission denied. Check API key scopes.")
            elif e.response.status_code == 404:
                raise APIError("Resource not found.")
            else:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except:
                    error_detail = str(e)
                raise APIError(f"API error: {error_detail}")
        except requests.exceptions.ConnectionError:
            raise APIError(f"Cannot connect to {self.base_url}")
        except Exception as e:
            raise APIError(f"Request failed: {str(e)}")

    # Auth
    def verify_auth(self) -> Dict[str, Any]:
        """Verify authentication"""
        return self._request("GET", "/auth/me")

    # Workspaces
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all workspaces"""
        return self._request("GET", "/workspaces/")

    def get_workspace(self, workspace_id: int) -> Dict[str, Any]:
        """Get workspace details"""
        return self._request("GET", f"/workspaces/{workspace_id}")

    # Projects
    def list_projects(self, workspace_id: int) -> List[Dict[str, Any]]:
        """List projects in workspace"""
        return self._request("GET", f"/projects/?workspace_id={workspace_id}")

    def get_project(self, project_id: int) -> Dict[str, Any]:
        """Get project details"""
        return self._request("GET", f"/projects/{project_id}")

    def create_project(self, workspace_id: int, name: str, description: str = "", repo_url: str = "") -> Dict[str, Any]:
        """Create new project"""
        return self._request("POST", "/projects/", json={
            "workspace_id": workspace_id,
            "name": name,
            "description": description,
            "repo_url": repo_url
        })

    # AIBOM
    def generate_aibom(self, project_id: int, repo_path: str = "") -> Dict[str, Any]:
        """Generate AIBOM for project"""
        return self._request("POST", "/aibom/generate", json={
            "project_id": project_id
        })

    def get_aibom(self, aibom_id: int) -> Dict[str, Any]:
        """Get AIBOM details"""
        return self._request("GET", f"/aibom/{aibom_id}")

    def list_aiboms(self, project_id: int) -> List[Dict[str, Any]]:
        """List AIBOMs for project"""
        return self._request("GET", f"/aibom/project/{project_id}")

    # Scans
    def run_scan(self, project_id: int, scanner_types: List[str] = None) -> Dict[str, Any]:
        """Run security scan on project (uses unified scan)"""
        return self._request("POST", f"/scanner/scan/unified/{project_id}")

    def get_scan_status(self, scan_id: int) -> Dict[str, Any]:
        """Get scan status"""
        return self._request("GET", f"/scanner/scan/run/{scan_id}")

    def get_scan_results(self, scan_id: int) -> Dict[str, Any]:
        """Get scan results"""
        scan = self._request("GET", f"/scanner/scan/run/{scan_id}")
        findings = self._request("GET", f"/scanner/scan/findings/{scan_id}")
        return {
            "scan": scan,
            "findings": findings,
            "summary": {
                "total_findings": scan.get("total_findings", 0),
                "critical": scan.get("critical_count", 0),
                "high": scan.get("high_count", 0),
                "medium": scan.get("medium_count", 0),
                "low": scan.get("low_count", 0),
                "info": scan.get("info_count", 0)
            }
        }

    def list_scans(self, project_id: int) -> List[Dict[str, Any]]:
        """List scans for project"""
        return self._request("GET", f"/scanner/scan/runs/{project_id}")
    
    def get_fix_preview(self, finding_id: int) -> Dict[str, Any]:
        """Get fix preview for a finding"""
        return self._request("GET", f"/remediation/findings/{finding_id}/preview", use_cache=False)
    
    def apply_fix(self, finding_id: int, file_path: Optional[str] = None, create_backup: bool = True) -> Dict[str, Any]:
        """Apply automated fix for a finding"""
        return self._request("POST", f"/remediation/findings/{finding_id}/fix", 
                           json={"file_path": file_path, "create_backup": create_backup},
                           use_cache=False)
    
    def get_fix_suggestions(self, finding_id: int) -> Dict[str, Any]:
        """Get AI-powered fix suggestions"""
        return self._request("GET", f"/remediation/findings/{finding_id}/suggestions")
    
    def batch_get_findings(self, finding_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple findings in batch (more efficient)"""
        results = []
        for finding_id in finding_ids:
            try:
                preview = self.get_fix_preview(finding_id)
                results.append(preview)
            except APIError:
                continue
        return results
    
    def batch_apply_fixes(self, finding_ids: List[int], file_path: Optional[str] = None) -> Dict[str, Any]:
        """Apply fixes for multiple findings"""
        results = {
            "success": [],
            "failed": [],
            "total": len(finding_ids)
        }
        
        for finding_id in finding_ids:
            try:
                result = self.apply_fix(finding_id, file_path=file_path)
                if result.get("success"):
                    results["success"].append(finding_id)
                else:
                    results["failed"].append({"id": finding_id, "error": result.get("message")})
            except APIError as e:
                results["failed"].append({"id": finding_id, "error": str(e)})
        
        return results
    
    def clear_cache(self):
        """Clear API cache"""
        if self.cache:
            self.cache.clear()
