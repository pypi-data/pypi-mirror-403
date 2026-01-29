#!/usr/bin/env python3
"""
Leapfrog - Environment Variable Manager
Leap between development environments with ease 🐸

A robust CLI tool for managing development environment configurations
across all tech stacks and programming languages.
"""

import argparse
import json
import os
import shutil
import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile

__version__ = "1.1.0"

# Color codes for better UX
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def colored(text: str, color: str) -> str:
    """Add color to text if terminal supports it"""
    if os.getenv('NO_COLOR') or not sys.stdout.isatty():
        return text
    return f"{color}{text}{Colors.RESET}"

def print_success(message: str):
    """Print success message with green checkmark"""
    print(f"{colored('✓', Colors.GREEN)} {message}")

def print_error(message: str):
    """Print error message with red X"""
    print(f"{colored('✗', Colors.RED)} {message}")

def print_warning(message: str):
    """Print warning message with yellow triangle"""
    print(f"{colored('⚠', Colors.YELLOW)} {message}")

def print_info(message: str):
    """Print info message with blue dot"""
    print(f"{colored('•', Colors.BLUE)} {message}")

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class LeapfrogConfig:
    """Manages leapfrog configuration and storage"""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / 'environments.json'
        self.backup_dir = self.config_dir / 'backups'
        self.templates_dir = self.config_dir / 'templates'
        
        # Create directories
        for directory in [self.config_dir, self.backup_dir, self.templates_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize config file
        if not self.config_file.exists():
            self._save_config({})
    
    def _get_config_dir(self) -> Path:
        """Get platform-appropriate config directory"""
        if sys.platform == "win32":
            config_base = Path(os.getenv('APPDATA', self.home_dir))
        elif sys.platform == "darwin":
            config_base = self.home_dir / 'Library' / 'Application Support'
        else:
            config_base = Path(os.getenv('XDG_CONFIG_HOME', self.home_dir / '.config'))
        
        return config_base / 'leapfrog'
    
    def _save_config(self, config: dict):
        """Save configuration with atomic write for safety"""
        temp_file = self.config_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.config_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _load_config(self) -> dict:
        """Load configuration with error handling"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print_warning(f"Config file issue: {e}. Creating fresh config.")
            return {}

class EnvironmentValidator:
    """Validates environment files and configurations"""
    
    @staticmethod
    def validate_env_syntax(file_path: Path) -> List[str]:
        """Validate .env file syntax and return any issues"""
        issues = []
        if not file_path.exists():
            return ["File does not exist"]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' not in line:
                        issues.append(f"Line {line_num}: Missing '=' separator")
                        continue
                    
                    key, _ = line.split('=', 1)
                    key = key.strip()
                    
                    # Check for valid variable name
                    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
                        issues.append(f"Line {line_num}: Invalid variable name '{key}'")
                    
                    # Check for spaces in key
                    if ' ' in key:
                        issues.append(f"Line {line_num}: Variable name cannot contain spaces")
        
        except Exception as e:
            issues.append(f"Error reading file: {e}")
        
        return issues
    
    @staticmethod
    def check_common_variables(env_vars: dict) -> List[str]:
        """Check for common required variables"""
        warnings = []
        common_vars = ['NODE_ENV', 'ENV', 'ENVIRONMENT']
        
        if not any(var in env_vars for var in common_vars):
            warnings.append("No environment identifier found (NODE_ENV, ENV, ENVIRONMENT)")
        
        return warnings
    
    @staticmethod
    def detect_sensitive_values(env_vars: dict) -> List[str]:
        """Detect potentially sensitive values"""
        sensitive_patterns = [
            (r'password', 'PASSWORD'),
            (r'secret', 'SECRET'),
            (r'key', 'KEY'),
            (r'token', 'TOKEN'),
            (r'api.*key', 'API_KEY'),
        ]
        
        sensitive_vars = []
        for key, value in env_vars.items():
            key_lower = key.lower()
            for pattern, type_name in sensitive_patterns:
                if re.search(pattern, key_lower):
                    sensitive_vars.append(f"{key} (appears to be {type_name})")
                    break
        
        return sensitive_vars

class LeapfrogManager:
    """Main environment management class"""
    
    def __init__(self):
        self.config = LeapfrogConfig()
        self.validator = EnvironmentValidator()
    
    def _get_project_root(self) -> Path:
        """Find project root by looking for common files"""
        current = Path.cwd()
        indicators = ['.git', 'package.json', 'requirements.txt', 'go.mod', 
                     'composer.json', 'pom.xml', '.env', 'Dockerfile']
        
        for parent in [current] + list(current.parents):
            if any((parent / indicator).exists() for indicator in indicators):
                return parent
        
        return current
    
    def _backup_current_env(self) -> Optional[Path]:
        """Create timestamped backup of current .env file"""
        env_file = self._get_project_root() / '.env'
        if not env_file.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_name = self._get_project_root().name
        backup_name = f"{project_name}_env_backup_{timestamp}.txt"
        backup_path = self.config.backup_dir / backup_name
        
        try:
            shutil.copy2(env_file, backup_path)
            print_info(f"Backed up current .env to {backup_path.name}")
            
            # Keep only last 10 backups per project
            self._cleanup_old_backups(project_name)
            return backup_path
        except Exception as e:
            print_warning(f"Could not create backup: {e}")
            return None
    
    def _cleanup_old_backups(self, project_name: str, keep: int = 10):
        """Remove old backup files, keeping only the most recent"""
        pattern = f"{project_name}_env_backup_*.txt"
        backups = sorted(
            self.config.backup_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for old_backup in backups[keep:]:
            try:
                old_backup.unlink()
            except Exception:
                pass  # Ignore cleanup errors
    
    def _read_env_file(self, file_path: Path = None) -> Dict[str, str]:
        """Read and parse environment file with robust error handling"""
        if file_path is None:
            file_path = self._get_project_root() / '.env'
        
        env_vars = {}
        if not file_path.exists():
            return env_vars
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        env_vars[key] = value
        
        except Exception as e:
            raise ValidationError(f"Error reading {file_path}: {e}")
        
        return env_vars
    
    def _write_env_file(self, env_vars: Dict[str, str], file_path: Path = None):
        """Write environment variables to file with proper formatting"""
        if file_path is None:
            file_path = self._get_project_root() / '.env'
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Environment configuration managed by Leapfrog 🐸\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Project: {self._get_project_root().name}\n\n")
                
                # Group variables by type for better organization
                grouped_vars = self._group_variables(env_vars)
                
                for group_name, variables in grouped_vars.items():
                    if group_name != "Other":
                        f.write(f"# {group_name}\n")
                    
                    for key, value in variables.items():
                        # Quote values that contain spaces or special characters
                        if ' ' in value or any(char in value for char in '()[]{}*?'):
                            f.write(f'{key}="{value}"\n')
                        else:
                            f.write(f'{key}={value}\n')
                    
                    f.write('\n')
        
        except Exception as e:
            raise ValidationError(f"Error writing {file_path}: {e}")
    
    def _group_variables(self, env_vars: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Group environment variables by type for better organization"""
        groups = {
            "Environment": {},
            "Database": {},
            "API & URLs": {},
            "Security": {},
            "Other": {}
        }
        
        for key, value in env_vars.items():
            key_lower = key.lower()
            
            if any(term in key_lower for term in ['env', 'environment', 'node_env']):
                groups["Environment"][key] = value
            elif any(term in key_lower for term in ['db_', 'database', 'mongo', 'sql', 'redis']):
                groups["Database"][key] = value
            elif any(term in key_lower for term in ['url', 'api', 'endpoint', 'host', 'port']):
                groups["API & URLs"][key] = value
            elif any(term in key_lower for term in ['key', 'secret', 'token', 'password', 'auth']):
                groups["Security"][key] = value
            else:
                groups["Other"][key] = value
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def hatch_environment(self, env_name: str, from_current: bool = False, 
                         description: str = None, force: bool = False) -> bool:
        """Create a new environment configuration"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', env_name):
            print_error("Environment name can only contain letters, numbers, hyphens, and underscores")
            return False
        
        config = self.config._load_config()
        
        # Check if environment exists
        original_created = None
        if env_name in config:
            if not force:
                print_error(f"Environment '{env_name}' already exists")
                print_info(f"Use '--force' to overwrite: leapfrog hatch {env_name} --from-current --force")
                return False
            else:
                print_warning(f"Overwriting existing environment '{env_name}'")
                # Preserve original creation date
                original_created = config[env_name].get('created')
        
        env_vars = {}
        if from_current:
            try:
                env_vars = self._read_env_file()
                if not env_vars:
                    print_error("No .env file found in current directory or file is empty")
                    return False
                
                # Validate the environment file
                issues = self.validator.validate_env_syntax(self._get_project_root() / '.env')
                if issues:
                    print_warning("Found issues in current .env file:")
                    for issue in issues:
                        print(f"  - {issue}")
                    
                    response = input(colored("Continue anyway? (y/N): ", Colors.YELLOW))
                    if response.lower() != 'y':
                        return False
                
            except ValidationError as e:
                print_error(str(e))
                return False
        
        # Create environment configuration
        config[env_name] = {
            'variables': env_vars,
            'created': original_created if original_created else datetime.now().isoformat(),
            'modified': datetime.now().isoformat() if force else None,
            'description': description or f"Environment configuration for {env_name}",
            'project': self._get_project_root().name,
            'variable_count': len(env_vars)
        }
        
        self.config._save_config(config)
        
        if force:
            print_success(f"Environment '{colored(env_name, Colors.BOLD)}' updated successfully! 🔄")
        else:
            print_success(f"Environment '{colored(env_name, Colors.BOLD)}' hatched successfully! 🥚→🐸")
        
        if from_current:
            print_info(f"Captured {len(env_vars)} variables from current .env")
            
            # Show sensitive variables warning
            sensitive = self.validator.detect_sensitive_values(env_vars)
            if sensitive:
                print_warning(f"Detected {len(sensitive)} potentially sensitive variables")
        
        return True
    
    def leap_to_environment(self, env_name: str) -> bool:
        """Switch to specified environment"""
        config = self.config._load_config()
        
        if env_name not in config:
            print_error(f"Environment '{env_name}' not found in the pond")
            self._suggest_similar_environments(env_name, config)
            return False
        
        try:
            # Backup current environment
            self._backup_current_env()
            
            # Write new environment
            env_vars = config[env_name]['variables']
            self._write_env_file(env_vars)
            
            print_success(f"Leaped to environment '{colored(env_name, Colors.BOLD)}' 🐸")
            print_info(f"Applied {len(env_vars)} variables to .env")
            
            # Update last used timestamp
            config[env_name]['last_used'] = datetime.now().isoformat()
            self.config._save_config(config)
            
            return True
            
        except ValidationError as e:
            print_error(str(e))
            return False
    
    def _suggest_similar_environments(self, env_name: str, config: dict):
        """Suggest similar environment names"""
        if not config:
            print_info("No environments in your pond yet. Use 'leapfrog hatch' to create one!")
            return
        
        # Simple similarity check
        suggestions = []
        for existing in config.keys():
            if env_name.lower() in existing.lower() or existing.lower() in env_name.lower():
                suggestions.append(existing)
        
        if suggestions:
            print_info(f"Did you mean: {', '.join(suggestions)}?")
        else:
            print_info(f"Available environments: {', '.join(config.keys())}")
    
    def show_pond(self) -> bool:
        """List all environments in the pond"""
        config = self.config._load_config()
        
        if not config:
            print(f"\n{colored('🏞️  Your pond is empty!', Colors.BLUE)}")
            print("Use 'leapfrog hatch <env_name> --from-current' to add your first environment")
            return True
        
        print(f"\n{colored('🏞️  Environments in your pond:', Colors.BLUE)}")
        
        # Sort by last used, then by name
        sorted_envs = sorted(
            config.items(),
            key=lambda x: (x[1].get('last_used', ''), x[0])
        )
        
        for env_name, env_data in sorted_envs:
            var_count = env_data.get('variable_count', len(env_data.get('variables', {})))
            created = env_data.get('created', 'Unknown')
            last_used = env_data.get('last_used')
            project = env_data.get('project', 'Unknown')
            
            if created != 'Unknown':
                created_date = datetime.fromisoformat(created).strftime('%Y-%m-%d')
            else:
                created_date = 'Unknown'
            
            # Show recently used environments differently
            if last_used:
                last_used_date = datetime.fromisoformat(last_used)
                if (datetime.now() - last_used_date).days < 7:
                    env_name_display = colored(f"🐸 {env_name}", Colors.GREEN)
                else:
                    env_name_display = f"🐸 {env_name}"
            else:
                env_name_display = f"🥚 {env_name}"
            
            print(f"  {env_name_display}")
            print(f"    └─ {var_count} variables • Project: {project} • Created: {created_date}")
            
            if env_data.get('description') and env_data['description'] != f"Environment configuration for {env_name}":
                print(f"    └─ {env_data['description']}")
        
        print(f"\n💡 Recently used environments are marked with {colored('🐸', Colors.GREEN)}")
        return True
    
    def prune_environment(self, env_name: str) -> bool:
        """Remove an environment from the pond"""
        config = self.config._load_config()
        
        if env_name not in config:
            print_error(f"Environment '{env_name}' not found in the pond")
            return False
        
        # Confirmation prompt
        print_warning(f"This will permanently remove environment '{env_name}'")
        response = input(colored("Are you sure? (y/N): ", Colors.YELLOW))
        
        if response.lower() != 'y':
            print_info("Pruning cancelled")
            return False
        
        del config[env_name]
        self.config._save_config(config)
        print_success(f"Environment '{colored(env_name, Colors.BOLD)}' pruned from the pond")
        return True
    
    def search_environments(self, query: str) -> bool:
        """Search for environments by name or variables"""
        config = self.config._load_config()
        
        if not config:
            print_warning("No environments to search")
            return False
        
        query_lower = query.lower()
        results = []
        
        # Search through all environments
        for env_name, env_data in config.items():
            matches = []
            
            # Check environment name
            if query_lower in env_name.lower():
                matches.append(f"name: {env_name}")
            
            # Check description
            description = env_data.get('description', '')
            if query_lower in description.lower():
                matches.append(f"description")
            
            # Check variable names and values
            env_vars = env_data.get('variables', {})
            for var_name, var_value in env_vars.items():
                if query_lower in var_name.lower():
                    matches.append(f"variable name: {var_name}")
                elif query_lower in var_value.lower():
                    # Don't show value if sensitive
                    is_sensitive = any(s in var_name.upper() for s in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN'])
                    if is_sensitive:
                        matches.append(f"variable value: {var_name}=***")
                    else:
                        value_preview = var_value[:30] + "..." if len(var_value) > 30 else var_value
                        matches.append(f"variable value: {var_name}={value_preview}")
            
            if matches:
                results.append((env_name, env_data, matches))
        
        # Display results
        if not results:
            print(f"\n{colored('No results found for:', Colors.YELLOW)} '{query}'")
            return False
        
        print(f"\n{colored('Search results for:', Colors.BOLD)} '{colored(query, Colors.BLUE)}'")
        print(f"Found {len(results)} environment(s)\n")
        
        for env_name, env_data, matches in results:
            var_count = len(env_data.get('variables', {}))
            project = env_data.get('project', 'Unknown')
            
            print(f"{colored('🐸 ' + env_name, Colors.GREEN)}")
            print(f"  Project: {project} • Variables: {var_count}")
            print(f"  Matches ({len(matches)}):")
            
            # Show first 5 matches
            for match in matches[:5]:
                print(f"    - {match}")
            
            if len(matches) > 5:
                print(f"    ... and {len(matches) - 5} more")
            
            print()  # Blank line between results
        
        return True
    
    def get_variable(self, env_name: str, var_name: str) -> bool:
        """Get a specific variable from an environment"""
        config = self.config._load_config()
        
        if env_name not in config:
            print_error(f"Environment '{env_name}' not found")
            return False
        
        env_vars = config[env_name]['variables']
        
        if var_name not in env_vars:
            print_error(f"Variable '{var_name}' not found in environment '{env_name}'")
            
            # Suggest similar variable names
            similar = [key for key in env_vars.keys() if var_name.lower() in key.lower()]
            if similar:
                print_info(f"Similar variables: {', '.join(similar[:5])}")
            return False
        
        value = env_vars[var_name]
        
        # Check if sensitive
        is_sensitive = any(sensitive in var_name.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN'])
        
        if is_sensitive:
            print_warning(f"'{var_name}' appears to be sensitive")
            response = input(colored("Show value anyway? (y/N): ", Colors.YELLOW))
            if response.lower() != 'y':
                print_info("Value hidden for security")
                return True
        
        print(f"{colored(var_name, Colors.BOLD)} = {value}")
        return True
    
    def set_variable(self, env_name: str, var_name: str, var_value: str) -> bool:
        """Set a specific variable in an environment"""
        config = self.config._load_config()
        
        if env_name not in config:
            print_error(f"Environment '{env_name}' not found")
            return False
        
        # Check if variable exists
        env_vars = config[env_name]['variables']
        is_new = var_name not in env_vars
        
        # Update the variable
        old_value = env_vars.get(var_name)
        env_vars[var_name] = var_value
        
        # Update metadata
        config[env_name]['modified'] = datetime.now().isoformat()
        config[env_name]['variable_count'] = len(env_vars)
        
        self.config._save_config(config)
        
        if is_new:
            print_success(f"Added new variable '{colored(var_name, Colors.BOLD)}' to environment '{env_name}'")
        else:
            print_success(f"Updated variable '{colored(var_name, Colors.BOLD)}' in environment '{env_name}'")
            
            # Show change if not sensitive
            is_sensitive = any(sensitive in var_name.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN'])
            if not is_sensitive and old_value:
                print_info(f"Old value: {old_value[:50]}{'...' if len(old_value) > 50 else ''}")
                print_info(f"New value: {var_value[:50]}{'...' if len(var_value) > 50 else ''}")
        
        return True
    
    def show_environment(self, env_name: str) -> bool:
        """Show environment details without switching to it"""
        config = self.config._load_config()
        
        if env_name not in config:
            print_error(f"Environment '{env_name}' not found")
            self._suggest_similar_environments(env_name, config)
            return False
        
        env_data = config[env_name]
        env_vars = env_data['variables']
        
        print(f"\n{colored('Environment:', Colors.BOLD)} {colored(env_name, Colors.BLUE)}")
        
        # Metadata
        created = env_data.get('created', 'Unknown')
        if created != 'Unknown':
            created_date = datetime.fromisoformat(created).strftime('%Y-%m-%d %H:%M:%S')
        else:
            created_date = 'Unknown'
        
        modified = env_data.get('modified')
        last_used = env_data.get('last_used')
        project = env_data.get('project', 'Unknown')
        description = env_data.get('description', '')
        
        print(f"{colored('Project:', Colors.BOLD)} {project}")
        print(f"{colored('Created:', Colors.BOLD)} {created_date}")
        
        if modified:
            modified_date = datetime.fromisoformat(modified).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{colored('Modified:', Colors.BOLD)} {modified_date}")
        
        if last_used:
            last_used_date = datetime.fromisoformat(last_used).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{colored('Last used:', Colors.BOLD)} {last_used_date}")
        
        if description and description != f"Environment configuration for {env_name}":
            print(f"{colored('Description:', Colors.BOLD)} {description}")
        
        print(f"{colored('Variables:', Colors.BOLD)} {len(env_vars)}")
        
        if not env_vars:
            print_warning("No variables in this environment")
            return True
        
        # Group and display variables
        grouped = self._group_variables(env_vars)
        for group_name, variables in grouped.items():
            if variables:
                print(f"\n  {colored(group_name + ':', Colors.BOLD)}")
                for key, value in variables.items():
                    # Hide sensitive values
                    if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                        display_value = "***"
                    else:
                        display_value = value[:50] + "..." if len(value) > 50 else value
                    
                    print(f"    {key} = {display_value}")
        
        # Show sensitive variable warning
        sensitive = self.validator.detect_sensitive_values(env_vars)
        if sensitive:
            print(f"\n{colored('🔒 Contains sensitive variables:', Colors.YELLOW)} {len(sensitive)}")
        
        return True
    
    def diff_environments(self, env1_name: str, env2_name: str) -> bool:
        """Compare two environments and show differences"""
        config = self.config._load_config()
        
        # Validate both environments exist
        if env1_name not in config:
            print_error(f"Environment '{env1_name}' not found")
            return False
        
        if env2_name not in config:
            print_error(f"Environment '{env2_name}' not found")
            return False
        
        env1_vars = config[env1_name]['variables']
        env2_vars = config[env2_name]['variables']
        
        # Find differences
        all_keys = set(env1_vars.keys()) | set(env2_vars.keys())
        only_in_env1 = set(env1_vars.keys()) - set(env2_vars.keys())
        only_in_env2 = set(env2_vars.keys()) - set(env1_vars.keys())
        common_keys = set(env1_vars.keys()) & set(env2_vars.keys())
        
        # Find variables with different values
        different_values = {}
        for key in common_keys:
            if env1_vars[key] != env2_vars[key]:
                different_values[key] = (env1_vars[key], env2_vars[key])
        
        # Display results
        print(f"\n{colored('Comparing environments:', Colors.BOLD)} {colored(env1_name, Colors.BLUE)} ↔ {colored(env2_name, Colors.BLUE)}")
        
        if not only_in_env1 and not only_in_env2 and not different_values:
            print_success("Environments are identical!")
            return True
        
        # Variables only in env1
        if only_in_env1:
            print(f"\n{colored(f'Only in {env1_name}:', Colors.YELLOW)} ({len(only_in_env1)} variables)")
            for key in sorted(only_in_env1):
                value = env1_vars[key]
                if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                    value = "***"
                else:
                    value = value[:50] + "..." if len(value) > 50 else value
                print(f"  - {key} = {value}")
        
        # Variables only in env2
        if only_in_env2:
            print(f"\n{colored(f'Only in {env2_name}:', Colors.YELLOW)} ({len(only_in_env2)} variables)")
            for key in sorted(only_in_env2):
                value = env2_vars[key]
                if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                    value = "***"
                else:
                    value = value[:50] + "..." if len(value) > 50 else value
                print(f"  + {key} = {value}")
        
        # Variables with different values
        if different_values:
            print(f"\n{colored('Different values:', Colors.RED)} ({len(different_values)} variables)")
            for key in sorted(different_values.keys()):
                val1, val2 = different_values[key]
                
                if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                    val1_display = "***"
                    val2_display = "***"
                else:
                    val1_display = val1[:50] + "..." if len(val1) > 50 else val1
                    val2_display = val2[:50] + "..." if len(val2) > 50 else val2
                
                print(f"  {colored('~', Colors.YELLOW)} {key}")
                print(f"    {colored(env1_name, Colors.BLUE)}: {val1_display}")
                print(f"    {colored(env2_name, Colors.BLUE)}: {val2_display}")
        
        # Summary
        total_diff = len(only_in_env1) + len(only_in_env2) + len(different_values)
        print(f"\n{colored('Summary:', Colors.BOLD)}")
        print(f"  Total variables in {env1_name}: {len(env1_vars)}")
        print(f"  Total variables in {env2_name}: {len(env2_vars)}")
        print(f"  Differences found: {total_diff}")
        
        return True
    
    def croak_validation(self, env_name: str = None) -> bool:
        """Validate environment (current .env or stored environment)"""
        if env_name:
            # Validate stored environment
            config = self.config._load_config()
            if env_name not in config:
                print_error(f"Environment '{env_name}' not found")
                return False
            
            env_vars = config[env_name]['variables']
            print(f"\n{colored('🐸 Croaking validation for stored environment:', Colors.BLUE)} {colored(env_name, Colors.BOLD)}")
        else:
            # Validate current .env file
            try:
                env_file = self._get_project_root() / '.env'
                env_vars = self._read_env_file(env_file)
                print(f"\n{colored('🐸 Croaking validation for current .env:', Colors.BLUE)} {env_file}")
                
                if not env_vars:
                    print_error("No .env file found or file is empty")
                    return False
                
                # Validate syntax
                issues = self.validator.validate_env_syntax(env_file)
                if issues:
                    print_error("Syntax issues found:")
                    for issue in issues:
                        print(f"  - {issue}")
                    return False
                
            except ValidationError as e:
                print_error(str(e))
                return False
        
        print_success(f"Environment is valid! Found {len(env_vars)} variables")
        
        # Show warnings
        warnings = self.validator.check_common_variables(env_vars)
        for warning in warnings:
            print_warning(warning)
        
        # Group and display variables
        grouped = self._group_variables(env_vars)
        for group_name, variables in grouped.items():
            if variables:
                print(f"\n  {colored(group_name + ':', Colors.BOLD)}")
                for key, value in variables.items():
                    # Hide sensitive values
                    if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                        display_value = "***"
                    else:
                        display_value = value[:50] + "..." if len(value) > 50 else value
                    
                    print(f"    {key} = {display_value}")
        
        # Show sensitive variable warning
        sensitive = self.validator.detect_sensitive_values(env_vars)
        if sensitive:
            print(f"\n{colored('🔒 Sensitive variables detected:', Colors.YELLOW)}")
            for var in sensitive:
                print(f"  - {var}")
        
        return True

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description='🐸 Leapfrog - Leap between development environments with ease',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
{colored('Examples:', Colors.BOLD)}
  leapfrog hatch dev1 --from-current    Hatch new environment from current .env
  leapfrog leap dev1                     Leap to dev1 environment  
  leapfrog pond                          Show all environments in your pond
  leapfrog show production               Show production environment details
  leapfrog diff dev staging              Compare dev and staging environments
  leapfrog get DB_HOST production        Get specific variable
  leapfrog set DB_HOST localhost dev     Update specific variable
  leapfrog search "mongo"                Search for environments with "mongo"
  leapfrog croak                         Validate current .env file
  leapfrog prune dev1                    Remove dev1 environment

{colored('Environment lifecycle:', Colors.BOLD)}
  🥚 hatch    → Create new environment (like hatching a tadpole)
  🐸 leap     → Switch between environments (hop to different lily pads)  
  🏞️  pond     → View all your environments together
  👁️  show     → Peek at environment without switching
  🔀 diff     → Compare two environments
  📖 get      → Get specific variable value
  ✏️  set      → Update specific variable
  🔍 search   → Search across all environments
  ✂️  prune    → Remove old environments (clean up the pond)
  🔊 croak    → Validate environments (make sure they're alive)

{colored('Version:', Colors.BOLD)} {__version__}
        '''
    )
    
    parser.add_argument('--version', action='version', version=f'Leapfrog {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Hatch command
    hatch_parser = subparsers.add_parser('hatch', help='🥚 Create new environment')
    hatch_parser.add_argument('name', help='Environment name')
    hatch_parser.add_argument('--from-current', action='store_true',
                             help='Create from current .env file')
    hatch_parser.add_argument('--description', help='Environment description')
    hatch_parser.add_argument('--force', '-f', action='store_true',
                             help='Overwrite existing environment')
    
    # Leap command  
    leap_parser = subparsers.add_parser('leap', help='🐸 Switch to environment')
    leap_parser.add_argument('name', help='Environment name to leap to')
    
    # Pond command
    subparsers.add_parser('pond', help='🏞️ Show all environments')
    
    # Prune command
    prune_parser = subparsers.add_parser('prune', help='✂️ Remove environment')
    prune_parser.add_argument('name', help='Environment name to remove')
    
    # Croak command
    croak_parser = subparsers.add_parser('croak', help='🔊 Validate environment')
    croak_parser.add_argument('name', nargs='?', help='Environment name (optional, defaults to current .env)')
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='🔀 Compare two environments')
    diff_parser.add_argument('env1', help='First environment name')
    diff_parser.add_argument('env2', help='Second environment name')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='👁️  Show environment details')
    show_parser.add_argument('name', help='Environment name to display')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='📖 Get variable from environment')
    get_parser.add_argument('var_name', help='Variable name')
    get_parser.add_argument('env_name', help='Environment name')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='✏️  Set variable in environment')
    set_parser.add_argument('var_name', help='Variable name')
    set_parser.add_argument('var_value', help='Variable value')
    set_parser.add_argument('env_name', help='Environment name')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='🔍 Search environments')
    search_parser.add_argument('query', help='Search query (searches names, variables, values)')
    
    return parser

def main():
    """Main entry point"""
    try:
        parser = create_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # Initialize the manager
        manager = LeapfrogManager()
        
        # Execute commands
        success = True
        
        if args.command == 'hatch':
            success = manager.hatch_environment(
                args.name, 
                args.from_current, 
                args.description,
                args.force
            )
        elif args.command == 'leap':
            success = manager.leap_to_environment(args.name)
        elif args.command == 'pond':
            success = manager.show_pond()
        elif args.command == 'prune':
            success = manager.prune_environment(args.name)
        elif args.command == 'croak':
            success = manager.croak_validation(args.name)
        elif args.command == 'diff':
            success = manager.diff_environments(args.env1, args.env2)
        elif args.command == 'show':
            success = manager.show_environment(args.name)
        elif args.command == 'get':
            success = manager.get_variable(args.env_name, args.var_name)
        elif args.command == 'set':
            success = manager.set_variable(args.env_name, args.var_name, args.var_value)
        elif args.command == 'search':
            success = manager.search_environments(args.query)
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{colored('Operation cancelled by user', Colors.YELLOW)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if os.getenv('DEBUG'):
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()