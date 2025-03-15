#!/usr/bin/env python3
"""
AWS Route 53 IP Updater

This script gets the current public IP address of the server and updates
a specified AWS Route 53 hosted zone record with that IP address.
"""

import argparse
import logging
import sys
from typing import Optional

import boto3
import requests
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def get_public_ip() -> str:
    """
    Get the current public IP address of the server.
    
    Returns:
        str: The public IP address
    
    Raises:
        Exception: If unable to get the public IP address
    """
    ip_services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://ipinfo.io/ip"
    ]
    
    for service in ip_services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                ip_address = response.text.strip()
                logger.info(f"Successfully retrieved public IP: {ip_address}")
                return ip_address
        except requests.RequestException as e:
            logger.warning(f"Failed to get IP from {service}: {e}")
    
    error_msg = "Failed to retrieve public IP address from all services"
    logger.error(error_msg)
    raise Exception(error_msg)


def update_route53_record(hosted_zone_id: str, record_name: str, ip_address: str, ttl: int = 300, 
                          record_type: str = 'A', profile_name: Optional[str] = None) -> bool:
    """
    Update an AWS Route 53 record with the current IP address.
    
    Args:
        hosted_zone_id (str): The Route 53 hosted zone ID
        record_name (str): The DNS record name to update
        ip_address (str): The IP address to set
        ttl (int, optional): Time to live in seconds. Defaults to 300.
        record_type (str, optional): DNS record type. Defaults to 'A'.
        profile_name (Optional[str], optional): AWS profile name. Defaults to None.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create Route 53 client
        session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
        route53 = session.client('route53')
        
        # Ensure record_name ends with a period if it doesn't already
        if not record_name.endswith('.'):
            record_name = f"{record_name}."
        
        # Create the change batch
        change_batch = {
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': record_type,
                        'TTL': ttl,
                        'ResourceRecords': [
                            {
                                'Value': ip_address
                            }
                        ]
                    }
                }
            ]
        }
        
        # Make the change
        response = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch=change_batch
        )
        
        change_id = response['ChangeInfo']['Id']
        status = response['ChangeInfo']['Status']
        logger.info(f"Successfully submitted change (ID: {change_id}, Status: {status})")
        logger.info(f"Updated {record_name} to {ip_address}")
        return True
        
    except ClientError as e:
        logger.error(f"AWS API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def main():
    """Main function to parse arguments and execute the update."""
    parser = argparse.ArgumentParser(description='Update AWS Route 53 record with current public IP')
    
    parser.add_argument('--zone-id', required=True, help='AWS Route 53 Hosted Zone ID')
    parser.add_argument('--record-name', required=True, help='DNS record name to update')
    parser.add_argument('--ttl', type=int, default=300, help='TTL in seconds (default: 300)')
    parser.add_argument('--record-type', default='A', choices=['A'], help='Record type (default: A)')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Get current public IP
        ip_address = get_public_ip()
        
        # Update Route 53 record
        success = update_route53_record(
            args.zone_id,
            args.record_name,
            ip_address,
            args.ttl,
            args.record_type,
            args.profile
        )
        
        if success:
            logger.info("Route 53 record update completed successfully")
            return 0
        else:
            logger.error("Failed to update Route 53 record")
            return 1
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
