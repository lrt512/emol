#!/usr/bin/env python3
"""Generate docker-compose configuration files from templates."""

import argparse
import os
import sys
from pathlib import Path


def generate_compose(mode: str, registry: str, version: str, emol_home: str, config_dir: str) -> str:
    """Generate docker-compose configuration.
    
    Args:
        mode: Either 'prod' or 'test'
        registry: ECR registry URL
        version: Image version tag
        emol_home: Path to emol home directory
        config_dir: Path to configuration directory
        
    Returns:
        Generated docker-compose YAML content
    """
    if mode not in ('prod', 'test'):
        raise ValueError(f"Mode must be 'prod' or 'test', got '{mode}'")
    
    example_file = Path(emol_home) / f"docker-compose.{mode}.yml.example"
    if not example_file.exists():
        raise FileNotFoundError(f"Example file not found: {example_file}")
    
    with open(example_file, 'r') as f:
        content = f.read()
    
    # Replace image tag
    image_tag = f"{registry}/emol:{version}"
    content = content.replace("image: emol:latest", f"image: {image_tag}")
    
    # Determine port and container name based on mode
    if mode == 'test':
        port = "8080:80"
        container_name = "emol_test"
    else:
        port = "80:80"
        container_name = "emol_prod"
    
    # Replace port if needed (in case example has different port)
    import re
    content = re.sub(r'ports:\s*\n\s*-\s*"[^"]+"', f'ports:\n      - "{port}"', content)
    
    # Add container_name to the app service
    content = re.sub(
        r'(  app:\s*\n\s*image:)',
        f'  app:\n    container_name: {container_name}\n    image:',
        content
    )
    
    # Add configuration file mounts if they exist
    lines = content.split('\n')
    new_lines = []
    in_volumes = False
    last_volume_line = -1
    
    for i, line in enumerate(lines):
        # Track when we enter volumes section
        if line.rstrip() == '    volumes:':
            in_volumes = True
            new_lines.append(line)
            continue
        
        # Track the last actual volume mount (not comments)
        if in_volumes:
            # Skip commented mount lines for config files
            if line.strip().startswith('# - /opt/emol_config/'):
                continue
            
            # Check if we're leaving volumes section
            if line.strip().startswith('healthcheck:') or (line.startswith('volumes:') and not line.startswith('    ')):
                # Add credentials mount before leaving volumes section
                if os.path.exists(f"{config_dir}/emol_credentials.json"):
                    new_lines.append(f"      - {config_dir}/emol_credentials.json:/opt/emol/emol_credentials.json:ro")
                
                in_volumes = False
                new_lines.append(line)
                continue
            
            # Track last volume mount line
            if line.strip().startswith('- ') and not line.strip().startswith('# '):
                last_volume_line = len(new_lines)
            
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    # If we ended while still in volumes section, add credentials mount at the end
    if in_volumes:
        if os.path.exists(f"{config_dir}/emol_credentials.json"):
            new_lines.append(f"      - {config_dir}/emol_credentials.json:/opt/emol/emol_credentials.json:ro")
    
    content = '\n'.join(new_lines)
    
    return content


def main():
    parser = argparse.ArgumentParser(description='Generate docker-compose configuration files')
    parser.add_argument('mode', choices=['prod', 'test'], help='Deployment mode')
    parser.add_argument('--registry', required=True, help='ECR registry URL')
    parser.add_argument('--version', default='latest', help='Image version tag (default: latest)')
    parser.add_argument('--emol-home', default=os.path.expanduser('~/emol'), help='eMoL home directory')
    parser.add_argument('--config-dir', default='/opt/emol_config', help='Configuration directory')
    parser.add_argument('--output', help='Output file path (default: docker-compose.{mode}.yml in emol-home)')
    
    args = parser.parse_args()
    
    # Handle sudo user home directory
    emol_home = args.emol_home
    if 'SUDO_USER' in os.environ:
        actual_home = os.path.expanduser(f"~{os.environ['SUDO_USER']}")
        if args.emol_home.startswith('~'):
            emol_home = args.emol_home.replace('~', actual_home)
    
    try:
        content = generate_compose(args.mode, args.registry, args.version, emol_home, args.config_dir)
        
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

