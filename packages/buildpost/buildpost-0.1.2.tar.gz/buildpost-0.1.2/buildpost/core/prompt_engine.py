"""Prompt template engine for loading and processing YAML prompts."""

import os
from typing import Dict, List, Optional
import yaml
from pathlib import Path


class PromptEngine:
    """Load and process prompt templates from YAML files."""

    def __init__(self, prompts_file: Optional[str] = None):
        """
        Initialize PromptEngine.

        Args:
            prompts_file: Path to prompts.yaml file. If None, uses default template.
        """
        if prompts_file and os.path.exists(prompts_file):
            self.prompts_file = prompts_file
        else:
            # Use built-in template
            package_dir = Path(__file__).parent.parent
            self.prompts_file = package_dir / "templates" / "prompts.yaml"

        self.data = self._load_prompts()
        self.prompts = self.data.get("prompts", {})
        self.platforms = self.data.get("platforms", {})
        self.config = self.data.get("config", {})

    def _load_prompts(self) -> Dict:
        """
        Load prompts from YAML file.

        Returns:
            Dictionary containing prompts, platforms, and config

        Raises:
            FileNotFoundError: If prompts file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not os.path.exists(self.prompts_file):
            raise FileNotFoundError(
                f"Prompts file not found: {self.prompts_file}\n"
                "Run 'buildpost init' to create default prompts."
            )

        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in prompts file: {e}")

    def get_prompt(self, prompt_name: str) -> Dict[str, str]:
        """
        Get a specific prompt template by name.

        Args:
            prompt_name: Name of the prompt (e.g., 'casual', 'professional')

        Returns:
            Dictionary with 'system' and 'template' keys

        Raises:
            KeyError: If prompt name doesn't exist
        """
        if prompt_name not in self.prompts:
            available = ', '.join(self.prompts.keys())
            raise KeyError(
                f"Prompt '{prompt_name}' not found. "
                f"Available prompts: {available}"
            )

        prompt_data = self.prompts[prompt_name]
        return {
            'system': prompt_data.get('system', '').strip(),
            'template': prompt_data.get('template', '').strip(),
            'name': prompt_data.get('name', prompt_name),
            'description': prompt_data.get('description', ''),
        }

    def render_prompt(self, prompt_name: str, variables: Dict) -> Dict[str, str]:
        """
        Render a prompt template with variables.

        Args:
            prompt_name: Name of the prompt template
            variables: Dictionary of variables to inject

        Returns:
            Dictionary with rendered 'system' and 'user' prompts
        """
        prompt = self.get_prompt(prompt_name)

        # Render template with variables
        rendered_template = prompt['template'].format(**variables)

        return {
            'system': prompt['system'],
            'user': rendered_template,
            'name': prompt['name'],
        }

    def list_prompts(self) -> List[Dict[str, str]]:
        """
        List all available prompts.

        Returns:
            List of dictionaries with prompt info
        """
        prompts_list = []
        for name, data in self.prompts.items():
            prompts_list.append({
                'name': name,
                'display_name': data.get('name', name),
                'description': data.get('description', 'No description'),
            })
        return prompts_list

    def get_platform(self, platform_name: str) -> Dict:
        """
        Get platform configuration.

        Args:
            platform_name: Name of the platform (e.g., 'twitter', 'linkedin')

        Returns:
            Dictionary with platform configuration

        Raises:
            KeyError: If platform doesn't exist
        """
        if platform_name not in self.platforms:
            available = ', '.join(self.platforms.keys())
            raise KeyError(
                f"Platform '{platform_name}' not found. "
                f"Available platforms: {available}"
            )

        return self.platforms[platform_name]

    def list_platforms(self) -> List[Dict[str, str]]:
        """
        List all available platforms.

        Returns:
            List of dictionaries with platform info
        """
        platforms_list = []
        for name, data in self.platforms.items():
            platforms_list.append({
                'name': name,
                'display_name': data.get('name', name),
                'max_length': data.get('max_length', 500),
            })
        return platforms_list

    def get_default_prompt(self) -> str:
        """Get default prompt name from config."""
        return self.config.get('default_prompt', 'casual')

    def get_default_platform(self) -> str:
        """Get default platform name from config."""
        return self.config.get('default_platform', 'twitter')

    def should_include_hashtags(self) -> bool:
        """Check if hashtags should be included by default."""
        return self.config.get('include_hashtags', True)

    def get_max_hashtags(self) -> int:
        """Get maximum number of hashtags."""
        return self.config.get('max_hashtags', 3)

    def get_platform_hashtags(self, platform_name: str) -> List[str]:
        """
        Get default hashtags for a platform.

        Args:
            platform_name: Platform name

        Returns:
            List of hashtag strings
        """
        try:
            platform = self.get_platform(platform_name)
            return platform.get('default_hashtags', [])
        except KeyError:
            return []
