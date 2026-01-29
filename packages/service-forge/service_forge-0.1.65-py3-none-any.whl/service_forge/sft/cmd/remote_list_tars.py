import os
import json
import requests
from pathlib import Path
from rich.console import Console
from rich.table import Table
from service_forge.sft.util.logger import log_error, log_info, log_success, log_warning
from service_forge.sft.config.sft_config import sft_config

def remote_list_tars(service_center_url: str = None) -> None:
    """
    Get remote tar package list and status from service-center
    """
    # If URL is not provided, try to get it from configuration
    if not service_center_url:
        service_center_url = getattr(sft_config, 'service_center_address', 'http://localhost:5000')
    
    # Ensure URL ends with /
    if not service_center_url.endswith('/'):
        service_center_url += '/'
    
    api_url = f"{service_center_url}api/v1/services/tar-list"
    
    log_info(f"Getting tar package list from {api_url}...")
    
    try:
        # 发送GET请求
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            log_error(f"Failed to get tar package list, status code: {response.status_code}")
            try:
                error_data = response.json()
                log_error(f"Error message: {error_data.get('message', 'Unknown error')}")
            except:
                log_error(f"Response content: {response.text}")
            return
        
        # Parse response data
        result = response.json()
        
        if result.get('code') != 200:
            log_error(f"Failed to get tar package list: {result.get('message', 'Unknown error')}")
            return
        
        tar_files = result.get('data', [])
        
        if not tar_files:
            log_info("No tar packages found")
            return
        
        # Use rich table to display results
        console = Console()
        table = Table(title="Remote Server Tar Package List", show_header=True, header_style="bold magenta")
        table.add_column("Filename", style="cyan", no_wrap=True)
        table.add_column("Service Name", style="green", no_wrap=True)
        table.add_column("Version", style="blue", no_wrap=True)
        table.add_column("Size", justify="right", style="yellow")
        table.add_column("Modified Time", style="dim")
        table.add_column("Deploy Status", justify="center", style="bold")
        
        for tar_file in tar_files:
            # Format file size
            size = _format_size(tar_file.get('file_size', 0))
            
            # Format modification time
            modified_time = _format_time(tar_file.get('modified_time', 0))
            
            # Deployment status
            deployed_status = "✅ Deployed" if tar_file.get('deployed_status', False) else "❌ Not Deployed"
            status_style = "green" if tar_file.get('deployed_status', False) else "red"
            
            table.add_row(
                tar_file.get('filename', '-'),
                tar_file.get('service_name', '-'),
                tar_file.get('version', '-'),
                size,
                modified_time,
                f"[{status_style}]{deployed_status}[/{status_style}]"
            )
        
        console.print(table)
        log_success(f"Found {len(tar_files)} tar packages in total")
        
    except requests.exceptions.RequestException as e:
        log_error(f"Request failed: {str(e)}")
        log_info(f"Please check if service-center service is running normally and if the URL is correct: {service_center_url}")
    except Exception as e:
        log_error(f"Exception occurred while getting tar package list: {str(e)}")

def _format_size(size_bytes: int) -> str:
    """Format file size"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def _format_time(timestamp: float) -> str:
    """Format timestamp"""
    if timestamp == 0:
        return "-"
    
    try:
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "-"