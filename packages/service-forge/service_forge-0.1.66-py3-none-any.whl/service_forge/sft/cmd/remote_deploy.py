import os
import json
import requests
from pathlib import Path
from service_forge.sft.util.logger import log_error, log_info, log_success, log_warning
from service_forge.sft.config.sft_config import sft_config

def remote_deploy_tar(filename: str, service_center_url: str = None) -> None:
    """
    Remote deploy specified tar package from service-center
    """
    # If URL is not provided, try to get it from configuration
    if not service_center_url:
        service_center_url = getattr(sft_config, 'service_center_address', 'http://localhost:5000')
    
    # Ensure URL ends with /
    if not service_center_url.endswith('/'):
        service_center_url += '/'
    
    api_url = f"{service_center_url}api/v1/services/deploy-from-tar"
    
    log_info(f"Sending deployment request to {api_url}...")
    log_info(f"Tar package to deploy: {filename}")
    
    try:
        # Prepare request data
        data = {
            "filename": filename
        }
        
        # Send POST request
        response = requests.post(
            api_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code != 200:
            log_error(f"Deployment request failed, status code: {response.status_code}")
            try:
                error_data = response.json()
                log_error(f"Error message: {error_data.get('message', 'Unknown error')}")
                if 'data' in error_data and error_data['data']:
                    log_error(f"Details: {json.dumps(error_data['data'], indent=2, ensure_ascii=False)}")
            except:
                log_error(f"Response content: {response.text}")
            return
        
        # Parse response data
        result = response.json()
        
        if result.get('code') != 200:
            log_error(f"Deployment failed: {result.get('message', 'Unknown error')}")
            if 'data' in result and result['data']:
                log_error(f"Details: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")
            return
        
        # Deployment successful
        data = result.get('data', {})
        service_name = data.get('service_name', 'Unknown')
        version = data.get('version', 'Unknown')
        deploy_output = data.get('deploy_output', '')
        
        log_success(f"Successfully deployed service: {service_name} version: {version}")
        
        if deploy_output:
            log_info("Deployment output:")
            print(deploy_output)
        
    except requests.exceptions.Timeout:
        log_error("Deployment request timed out (exceeded 5 minutes), please check service status or try again later")
    except requests.exceptions.RequestException as e:
        log_error(f"Request failed: {str(e)}")
        log_info(f"Please check if service-center service is running normally and if the URL is correct: {service_center_url}")
    except Exception as e:
        log_error(f"Exception occurred while deploying tar package: {str(e)}")

def remote_list_and_deploy(service_center_url: str = None) -> None:
    """
    List remote tar packages first, then let user select which package to deploy
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
        # 发送GET请求获取tar包列表
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            log_error(f"Failed to get tar package list, status code: {response.status_code}")
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
        
        # Display tar package list
        log_info("Available tar package list:")
        for i, tar_file in enumerate(tar_files, 1):
            filename = tar_file.get('filename', '-')
            service_name = tar_file.get('service_name', '-')
            version = tar_file.get('version', '-')
            deployed_status = "Deployed" if tar_file.get('deployed_status', False) else "Not Deployed"
            
            print(f"{i}. {filename} (service: {service_name}, version: {version}, status: {deployed_status})")
        
        # Let user choose
        try:
            choice = input("\nEnter the number of the tar package to deploy (enter 'q' to exit): ").strip()
            
            if choice.lower() == 'q':
                log_info("Deployment cancelled")
                return
            
            index = int(choice) - 1
            if 0 <= index < len(tar_files):
                selected_tar = tar_files[index]
                filename = selected_tar.get('filename')
                
                if selected_tar.get('deployed_status', False):
                    log_warning(f"Tar package {filename} is already deployed, continue deployment?")
                    confirm = input("Enter 'y' to continue, any other key to cancel: ").strip().lower()
                    if confirm != 'y':
                        log_info("Deployment cancelled")
                        return
                
                log_info(f"Selected for deployment: {filename}")
                remote_deploy_tar(filename, service_center_url)
            else:
                log_error("Invalid selection")
                
        except ValueError:
            log_error("Please enter a valid number")
        except KeyboardInterrupt:
            log_info("\nDeployment cancelled")
        
    except requests.exceptions.RequestException as e:
        log_error(f"Request failed: {str(e)}")
        log_info(f"Please check if service-center service is running normally and if the URL is correct: {service_center_url}")
    except Exception as e:
        log_error(f"Exception occurred while getting tar package list: {str(e)}")