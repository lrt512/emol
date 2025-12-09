#!/usr/bin/env python3
"""Generate docker-compose configuration files."""

import argparse
import os
import sys

PROD_TEMPLATE = """services:
  app:
    container_name: emol_prod
    image: emol:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - AWS_DEFAULT_REGION=ca-central-1
      - DJANGO_SETTINGS_MODULE=emol.settings.prod
    volumes:
      - emol_logs:/var/log/emol
      # Mount AWS credentials from /opt/emol_config (optional)
      # This will be automatically mounted if present:
      # - /opt/emol_config/emol_credentials.json:/opt/emol/emol_credentials.json:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  emol_logs:
"""

TEST_TEMPLATE = """services:
  app_test:
    container_name: emol_test
    image: emol:latest
    restart: unless-stopped
    ports:
      - "8080:8000"
    environment:
      - AWS_DEFAULT_REGION=ca-central-1
      - DJANGO_SETTINGS_MODULE=emol.settings.prod
    volumes:
      - emol_logs_test:/var/log/emol
      # Mount AWS credentials from /opt/emol_config (optional)
      # This will be automatically mounted if present:
      # - /opt/emol_config/emol_credentials.json:/opt/emol/emol_credentials.json:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  emol_logs_test:
"""

def generate_compose(mode: str, registry: str, version: str, config_dir: str) -> str:
    """Generate docker-compose configuration.
    
    Args:
        mode: Either 'prod' or 'test'
        registry: ECR registry URL
        version: Image version tag
        config_dir: Path to configuration directory
        
    Returns:
        Generated docker-compose YAML content
    """
    if mode == 'prod':
        content = PROD_TEMPLATE
    elif mode == 'test':
        content = TEST_TEMPLATE
    else:
        raise ValueError(f"Mode must be 'prod' or 'test', got '{mode}'")
    
    # Replace image tag
    image_tag = f"{registry}/emol:{version}"
    content = content.replace("image: emol:latest", f"image: {image_tag}")
    
    # Add credentials mount if file exists
    if os.path.exists(f"{config_dir}/emol_credentials.json"):
        mount_str = f"      - {config_dir}/emol_credentials.json:/opt/emol/emol_credentials.json:ro"
        
        # Insert before healthcheck
        lines = content.split('\n')
        new_lines = []
        inserted = False
        
        for line in lines:
            if line.strip().startswith('healthcheck:') and not inserted:
                new_lines.append(mount_str)
                inserted = True
            new_lines.append(line)
            
        content = '\n'.join(new_lines)
    
    return content


def main():
    parser = argparse.ArgumentParser(description='Generate docker-compose configuration files')
    parser.add_argument('mode', choices=['prod', 'test'], help='Deployment mode')
    parser.add_argument('--registry', required=True, help='ECR registry URL')
    parser.add_argument('--version', default='latest', help='Image version tag (default: latest)')
    parser.add_argument('--emol-home', default=os.path.expanduser('~/emol'), help='eMoL home directory')
    parser.add_argument('--config-dir', default='/opt/emol_config', help='Configuration directory')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Handle sudo user home directory for emol-home default
    emol_home = args.emol_home
    if 'SUDO_USER' in os.environ:
        actual_home = os.path.expanduser(f"~{os.environ['SUDO_USER']}")
        if args.emol_home.startswith('~'):
            emol_home = args.emol_home.replace('~', actual_home)
    
    try:
        content = generate_compose(args.mode, args.registry, args.version, args.config_dir)
        
        if args.output:
            output_path = args.output
        else:
            output_path = os.path.join(emol_home, f"docker-compose.{args.mode}.yml")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        print(f"Generated {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
