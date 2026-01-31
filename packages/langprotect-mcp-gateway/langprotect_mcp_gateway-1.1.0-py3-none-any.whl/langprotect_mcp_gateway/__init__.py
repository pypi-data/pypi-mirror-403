"""
LangProtect MCP Gateway
~~~~~~~~~~~~~~~~~~~~~~~

A security gateway for Model Context Protocol (MCP) that protects AI tool interactions.

Basic usage:
    from langprotect_mcp_gateway import LangProtectGateway
    
    gateway = LangProtectGateway()
    gateway.run()

Or via command line:
    langprotect-gateway
"""

__version__ = '1.1.0'
__author__ = 'LangProtect Security Team'
__license__ = 'MIT'

from .gateway import LangProtectGateway, main

__all__ = ['LangProtectGateway', 'main', '__version__']
