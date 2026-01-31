#!/usr/bin/env python3
"""
LangProtect MCP Gateway - Security Gateway for MCP Servers
"""

import sys
import json
import os
import subprocess
import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

log_level = os.environ.get("LOGLEVEL", "DEBUG" if os.getenv('DEBUG', 'false').lower() == 'true' else "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format='[%(asctime)s] %(levelname)s: %(message)s', handlers=[logging.StreamHandler(sys.stderr)])
logger = logging.getLogger('langprotect-gateway')


class MCPServer:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.command = config.get('command')
        self.args = config.get('args', [])
        self.env = config.get('env', {})
        self.tools: List[Dict] = []
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        logger.info(f"Configured MCP server: {name} ({self.command} {' '.join(self.args)})")
    
    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    def start(self) -> bool:
        try:
            env = {**os.environ, **self.env}
            self.process = subprocess.Popen([self.command] + self.args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, bufsize=1)
            init_request = {"jsonrpc": "2.0", "id": self._next_id(), "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "langprotect-gateway", "version": "1.0.0"}}}
            self.process.stdin.write(json.dumps(init_request) + "\n")
            self.process.stdin.flush()
            response_line = self.process.stdout.readline()
            if not response_line:
                logger.error(f"Failed to initialize {self.name}")
                return False
            response = json.loads(response_line)
            if "error" in response:
                logger.error(f"Initialize error for {self.name}: {response['error']}")
                return False
            self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
            self.process.stdin.flush()
            logger.info(f"Started MCP server: {self.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")
            return False
    
    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None
    
    def call(self, method: str, params: Dict) -> Dict:
        if not self.process or self.process.poll() is not None:
            raise Exception(f"Server {self.name} is not running")
        request = {"jsonrpc": "2.0", "id": self._next_id(), "method": method, "params": params}
        logger.debug(f"-> {self.name}.{method}")
        try:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            response_line = self.process.stdout.readline()
            if not response_line:
                raise Exception(f"No response from {self.name}")
            response = json.loads(response_line)
            logger.debug(f"<- {self.name}: {str(response)[:200]}")
            return response
        except Exception as e:
            logger.error(f"Error calling {self.name}.{method}: {e}")
            raise
    
    def discover_tools(self) -> List[Dict]:
        try:
            response = self.call("tools/list", {})
            if "result" in response:
                self.tools = response["result"].get("tools", [])
                logger.info(f"Discovered {len(self.tools)} tools from {self.name}")
                return self.tools
            return []
        except Exception as e:
            logger.warning(f"Could not discover tools from {self.name}: {e}")
            return []


class LangProtectAuth:
    def __init__(self, url: str, email: str, password: str):
        self.url = url
        self.email = email
        self.password = password
        self.jwt_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
    
    def login(self) -> bool:
        try:
            logger.info(f"Authenticating with {self.url}...")
            response = requests.post(f"{self.url}/v1/group-users/signin", json={'email': self.email, 'password': self.password}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get('access_token')
                self.token_expiry = datetime.now() + timedelta(days=6)
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def ensure_token(self) -> bool:
        if not self.jwt_token or (self.token_expiry and datetime.now() > self.token_expiry):
            return self.login()
        return True
    
    def scan(self, tool_name: str, arguments: Dict, server_name: str) -> Dict:
        self.ensure_token()
        try:
            payload = {'prompt': json.dumps({'tool': tool_name, 'arguments': arguments, 'server': server_name}), 'client_ip': '127.0.0.1', 'user_agent': f'LangProtect-MCP-Gateway/1.0 (server={server_name})', 'source': 'mcp-gateway'}
            response = requests.post(f"{self.url}/v1/group-logs/scan", json=payload, headers={'Authorization': f'Bearer {self.jwt_token}', 'Content-Type': 'application/json'}, timeout=5)
            if response.status_code != 200:
                logger.warning(f"Backend returned {response.status_code}, allowing request (fail-open)")
                return {'status': 'allowed', 'error': f'Backend error: {response.status_code}'}
            result = response.json()
            # Handle scan service timeout - fail open
            if result.get('detections', {}).get('error') == 'Scan service timeout':
                logger.warning("Scan service timeout, allowing request (fail-open)")
                return {'status': 'allowed', 'id': result.get('id'), 'error': 'Scan timeout'}
            return result
        except requests.exceptions.Timeout:
            logger.warning("Backend scan timeout, allowing request (fail-open)")
            return {'status': 'allowed', 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return {'status': 'allowed', 'error': str(e)}


class LangProtectGateway:
    def __init__(self, mcp_json_path: Optional[str] = None):
        self.mcp_json_path = mcp_json_path
        
        # Load credentials from env vars first, then potentially from config
        self.langprotect_url = os.getenv('LANGPROTECT_URL', 'http://localhost:8000')
        self.email = os.getenv('LANGPROTECT_EMAIL')
        self.password = os.getenv('LANGPROTECT_PASSWORD')
        
        # Try to load credentials from mcp.json env section (like Lasso)
        if mcp_json_path and (not self.email or not self.password):
            self._load_env_from_config(mcp_json_path)
        
        self.auth: Optional[LangProtectAuth] = None
        self.mcp_servers: Dict[str, MCPServer] = {}
        self.tool_to_server: Dict[str, str] = {}
        self.all_tools: List[Dict] = []
        logger.debug(f"LANGPROTECT_URL: {self.langprotect_url}")
        logger.debug(f"LANGPROTECT_EMAIL: {self.email}")
    
    def _load_env_from_config(self, path: str):
        """Load credentials from mcp.json env section (Lasso-style)"""
        try:
            expanded_path = os.path.expanduser(path)
            with open(expanded_path, 'r') as f:
                config = json.load(f)
            
            # Look for env vars in the gateway's config section
            mcp_servers = config.get('mcpServers', {})
            for gateway_name in ['langprotect-gateway', 'langprotect', 'mcp-gateway']:
                gateway_config = mcp_servers.get(gateway_name, {})
                env_section = gateway_config.get('env', {})
                if env_section:
                    if not self.langprotect_url or self.langprotect_url == 'http://localhost:8000':
                        self.langprotect_url = env_section.get('LANGPROTECT_URL', self.langprotect_url)
                    if not self.email:
                        self.email = env_section.get('LANGPROTECT_EMAIL')
                    if not self.password:
                        self.password = env_section.get('LANGPROTECT_PASSWORD')
                    logger.info(f"Loaded credentials from config env section")
                    break
        except Exception as e:
            logger.debug(f"Could not load env from config: {e}")
    
    def initialize(self) -> bool:
        if self.email and self.password:
            self.auth = LangProtectAuth(self.langprotect_url, self.email, self.password)
            if not self.auth.login():
                logger.error("Failed to authenticate with LangProtect backend")
                return False
        else:
            logger.warning("No LangProtect credentials - running in pass-through mode")
        if not self.load_servers():
            return False
        if not self.start_servers():
            return False
        logger.info("=" * 50)
        logger.info("LangProtect Gateway initialized")
        logger.info(f"Backend: {self.langprotect_url}")
        logger.info(f"Servers: {len(self.mcp_servers)}")
        logger.info(f"Tools: {len(self.all_tools)}")
        logger.info("=" * 50)
        return True
    
    def load_servers(self) -> bool:
        # Mode 1: Single server via environment variables (for wrapper scripts)
        mcp_command = os.getenv('MCP_SERVER_COMMAND')
        mcp_args = os.getenv('MCP_SERVER_ARGS')
        if mcp_command:
            logger.info(f"Single server mode: {mcp_command}")
            args_list = [arg.strip() for arg in mcp_args.split(',')] if mcp_args else []
            server_name = os.getenv('MCP_SERVER_NAME', 'proxied-server')
            self.mcp_servers[server_name] = MCPServer(server_name, {'command': mcp_command, 'args': args_list, 'env': {}})
            return True
        
        # Mode 2: Config file (mcp.json)
        if self.mcp_json_path:
            return self.load_from_mcp_json(self.mcp_json_path)
        
        logger.warning("No MCP servers configured")
        return False
    
    def load_from_mcp_json(self, path: str) -> bool:
        try:
            expanded_path = os.path.expanduser(path)
            with open(expanded_path, 'r') as f:
                config = json.load(f)
            
            # Try multiple config structures:
            # 1. Lasso-style: mcpServers.langprotect-gateway.servers (nested)
            # 2. VS Code style: servers (direct)
            # 3. Claude Desktop style: mcpServers (direct)
            
            servers = {}
            
            # Check for Lasso-style nested config
            mcp_servers = config.get('mcpServers', {})
            for gateway_name in ['langprotect-gateway', 'langprotect', 'mcp-gateway']:
                gateway_config = mcp_servers.get(gateway_name, {})
                if 'servers' in gateway_config:
                    servers = gateway_config['servers']
                    logger.info(f"Found nested servers config under mcpServers.{gateway_name}.servers")
                    break
            
            # Fallback to direct config
            if not servers:
                servers = config.get('servers', config.get('mcpServers', {}))
            
            if not servers:
                logger.error("No servers found in config file")
                return False
            
            for name, cfg in servers.items():
                # Skip gateway self-references
                if name in ['langprotect-gateway', 'langprotect', 'mcp-gateway']:
                    continue
                self.mcp_servers[name] = MCPServer(name, cfg)
            
            logger.info(f"Loaded {len(self.mcp_servers)} servers from config")
            return len(self.mcp_servers) > 0
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return False
    
    def start_servers(self) -> bool:
        started = 0
        for name, server in list(self.mcp_servers.items()):
            if server.start():
                tools = server.discover_tools()
                for tool in tools:
                    tool_name = tool.get('name')
                    if tool_name:
                        self.tool_to_server[tool_name] = name
                        tool_copy = tool.copy()
                        tool_copy['description'] = f"[{name}] {tool_copy.get('description', '')}"
                        self.all_tools.append(tool_copy)
                started += 1
            else:
                del self.mcp_servers[name]
        return started > 0
    
    def shutdown(self):
        for server in self.mcp_servers.values():
            server.stop()
    
    def handle_request(self, request: Dict) -> Optional[Dict]:
        method = request.get('method')
        request_id = request.get('id')
        params = request.get('params', {})
        logger.info(f"Request: {method} (id={request_id})")
        try:
            if method == 'initialize':
                return {'jsonrpc': '2.0', 'id': request_id, 'result': {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'langprotect-gateway', 'version': '1.0.0'}}}
            elif method == 'notifications/initialized':
                return None
            elif method == 'tools/list':
                logger.info(f"Returning {len(self.all_tools)} tools")
                return {'jsonrpc': '2.0', 'id': request_id, 'result': {'tools': self.all_tools}}
            elif method == 'tools/call':
                return self._handle_call_tool(request_id, params)
            else:
                return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32601, 'message': f'Method not found: {method}'}}
        except Exception as e:
            logger.error(f"Error handling {method}: {e}")
            return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32603, 'message': str(e)}}
    
    def _handle_call_tool(self, request_id, params: Dict) -> Dict:
        tool_name = params.get('name', '')
        arguments = params.get('arguments', {})
        server_name = self.tool_to_server.get(tool_name)
        if not server_name:
            return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32602, 'message': f'Unknown tool: {tool_name}'}}
        server = self.mcp_servers.get(server_name)
        if not server:
            return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32602, 'message': f'Server not found: {server_name}'}}
        logger.info(f"Tool call: {server_name}.{tool_name}")
        if self.auth:
            scan_result = self.auth.scan(tool_name, arguments, server_name)
            status = scan_result.get('status', '').lower()
            if status == 'blocked':
                reason = scan_result.get('detections', {}).get('MCPActionControl', {}).get('reason', 'Policy violation')
                logger.warning(f"BLOCKED: {tool_name} - {reason}")
                return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32000, 'message': f'LangProtect: {reason}'}}
            logger.info(f"ALLOWED (log_id={scan_result.get('id')})")
        try:
            response = server.call('tools/call', {'name': tool_name, 'arguments': arguments})
            if 'result' in response:
                return {'jsonrpc': '2.0', 'id': request_id, 'result': response['result']}
            elif 'error' in response:
                return {'jsonrpc': '2.0', 'id': request_id, 'error': response['error']}
            return response
        except Exception as e:
            return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32603, 'message': f'Error executing tool: {e}'}}
    
    def run(self):
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    if response:
                        print(json.dumps(response), flush=True)
                except json.JSONDecodeError as e:
                    print(json.dumps({'jsonrpc': '2.0', 'error': {'code': -32700, 'message': f'Parse error: {e}'}}), flush=True)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()


def parse_args():
    parser = argparse.ArgumentParser(description='LangProtect MCP Gateway')
    parser.add_argument('--mcp-json-path', type=str, help='Path to mcp.json configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.debug:
        os.environ['DEBUG'] = 'true'
        logging.getLogger('langprotect-gateway').setLevel(logging.DEBUG)
    gateway = LangProtectGateway(mcp_json_path=args.mcp_json_path)
    if not gateway.initialize():
        sys.exit(1)
    gateway.run()


if __name__ == '__main__':
    main()
