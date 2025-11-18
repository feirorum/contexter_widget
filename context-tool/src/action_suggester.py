"""Action suggestion rules based on detected patterns"""

from typing import List, Dict, Any, Optional
import yaml
import re
from pathlib import Path


class ActionSuggester:
    """Generate contextual action suggestions based on text type and content"""

    def __init__(self, actions_config_path: Optional[str] = None):
        """
        Initialize action suggester

        Args:
            actions_config_path: Path to actions.yaml configuration file
        """
        self.config = {}
        self.pattern_actions = {}
        self.universal_actions = []
        self.database_actions = {}

        if actions_config_path and Path(actions_config_path).exists():
            self._load_config(actions_config_path)

    def _load_config(self, config_path: str):
        """Load actions configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}

            # Parse pattern-based actions
            pattern_actions_config = self.config.get('pattern_actions', [])
            for pattern_config in pattern_actions_config:
                pattern_type = pattern_config.get('pattern_type')
                if pattern_type:
                    self.pattern_actions[pattern_type] = {
                        'pattern_regex': pattern_config.get('pattern_regex'),
                        'actions': pattern_config.get('actions', [])
                    }

            # Parse universal actions
            self.universal_actions = self.config.get('universal_actions', [])

            # Parse database actions
            self.database_actions = self.config.get('database_actions', {})

            print(f"✓ Loaded actions config from {config_path}")
            print(f"  - Pattern actions: {len(self.pattern_actions)}")
            print(f"  - Universal actions: {len(self.universal_actions)}")
            print(f"  - Database actions: {len(self.database_actions)}")

        except Exception as e:
            print(f"⚠ Failed to load actions config: {e}")
            print(f"  Using built-in actions instead")

    def _substitute_variables(self, template: str, variables: Dict[str, str]) -> str:
        """
        Substitute variables in template string

        Args:
            template: Template string with {var} placeholders
            variables: Dictionary of variable values

        Returns:
            String with variables substituted
        """
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def _extract_regex_groups(self, pattern: str, text: str) -> Dict[str, str]:
        """
        Extract regex capture groups from text

        Args:
            pattern: Regex pattern
            text: Text to match against

        Returns:
            Dictionary with match and match_N keys
        """
        variables = {}
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Full match
                variables['match'] = match.group(0)

                # Capture groups
                for i, group in enumerate(match.groups(), 1):
                    if group:
                        variables[f'match_{i}'] = group
        except Exception as e:
            print(f"⚠ Regex error: {e}")

        return variables

    def suggest_actions(
        self,
        text: str,
        text_type: Optional[str],
        exact_matches: List[Dict[str, Any]],
        patterns: Dict[str, List[str]]
    ) -> List[Dict[str, str]]:
        """
        Suggest actions based on detected patterns and matches

        Args:
            text: The selected text
            text_type: Primary pattern type (from PatternMatcher)
            exact_matches: Matches found in database
            patterns: All detected patterns

        Returns:
            List of suggested actions with labels and URLs/commands
        """
        actions = []

        # Base variables for substitution
        base_variables = {'text': text}

        # 1. Add config-based pattern actions
        if text_type and text_type in self.pattern_actions:
            config = self.pattern_actions[text_type]
            pattern_regex = config.get('pattern_regex')

            # Get the matched value
            matched_value = patterns.get(text_type, [text])[0] if text_type in patterns else text

            # Extract variables
            variables = base_variables.copy()
            variables['match'] = matched_value

            # If there's a custom regex, extract capture groups
            if pattern_regex:
                regex_vars = self._extract_regex_groups(pattern_regex, text)
                variables.update(regex_vars)

            # Add configured actions for this pattern type
            for action_config in config.get('actions', []):
                action = {
                    'label': self._substitute_variables(action_config.get('label', ''), variables),
                    'type': action_config.get('type', 'url'),
                    'icon': action_config.get('icon', 'external-link')
                }

                # Add URL or value based on type
                if action['type'] == 'url':
                    action['value'] = self._substitute_variables(action_config.get('url', ''), variables)
                elif action['type'] == 'copy':
                    action['value'] = self._substitute_variables(action_config.get('value', ''), variables)
                else:
                    action['value'] = self._substitute_variables(action_config.get('value', ''), variables)

                actions.append(action)

        # 2. Fallback to built-in actions if no config loaded
        elif text_type == 'jira_ticket':
            jira_id = patterns['jira_ticket'][0] if 'jira_ticket' in patterns else text
            actions.append({
                'label': 'Open in Jira',
                'type': 'url',
                'value': f'https://jira.company.com/browse/{jira_id}',
                'icon': 'external-link'
            })
            actions.append({
                'label': 'Copy ticket ID',
                'type': 'copy',
                'value': jira_id,
                'icon': 'clipboard'
            })

        elif text_type == 'email':
            email = patterns['email'][0] if 'email' in patterns else text
            actions.append({
                'label': 'Send email',
                'type': 'url',
                'value': f'mailto:{email}',
                'icon': 'mail'
            })
            actions.append({
                'label': 'Copy email',
                'type': 'copy',
                'value': email,
                'icon': 'clipboard'
            })

        elif text_type == 'url':
            url = patterns['url'][0] if 'url' in patterns else text
            actions.append({
                'label': 'Open URL',
                'type': 'url',
                'value': url,
                'icon': 'external-link'
            })
            actions.append({
                'label': 'Copy URL',
                'type': 'copy',
                'value': url,
                'icon': 'clipboard'
            })

        elif text_type == 'phone':
            phone = patterns['phone'][0] if 'phone' in patterns else text
            actions.append({
                'label': 'Call',
                'type': 'url',
                'value': f'tel:{phone}',
                'icon': 'phone'
            })
            actions.append({
                'label': 'Copy number',
                'type': 'copy',
                'value': phone,
                'icon': 'clipboard'
            })

        # 3. Add config-based database match actions
        for match in exact_matches:
            match_type = match.get('type')
            match_data = match.get('data', {})

            # Check if we have config for this match type
            if match_type in self.database_actions:
                action_configs = self.database_actions[match_type]

                for action_config in action_configs:
                    # Check condition if specified
                    condition = action_config.get('condition')
                    if condition and not match_data.get(condition):
                        continue  # Skip this action if condition not met

                    # Prepare variables for substitution
                    variables = base_variables.copy()
                    variables.update(match_data)  # Add all match data fields

                    # Build action
                    action = {
                        'label': self._substitute_variables(action_config.get('label', ''), variables),
                        'type': action_config.get('type', 'url'),
                        'icon': action_config.get('icon', 'external-link')
                    }

                    if action['type'] == 'url':
                        action['value'] = self._substitute_variables(action_config.get('url', ''), variables)
                    elif action['type'] == 'copy':
                        action['value'] = self._substitute_variables(action_config.get('value', ''), variables)
                    else:
                        action['value'] = self._substitute_variables(action_config.get('value', ''), variables)

                    actions.append(action)

            # Fallback to built-in database actions
            elif match_type == 'contact':
                contact = match_data
                if contact.get('email'):
                    actions.append({
                        'label': f"Email {contact.get('name', 'contact')}",
                        'type': 'url',
                        'value': f"mailto:{contact['email']}",
                        'icon': 'mail'
                    })

            elif match_type == 'project':
                # Built-in project actions can be added here
                pass

        # 4. Add universal actions from config
        for action_config in self.universal_actions:
            variables = base_variables.copy()

            action = {
                'label': self._substitute_variables(action_config.get('label', ''), variables),
                'type': action_config.get('type', 'url'),
                'icon': action_config.get('icon', 'external-link')
            }

            if 'description' in action_config:
                action['description'] = action_config['description']

            if action['type'] == 'url':
                action['value'] = self._substitute_variables(action_config.get('url', ''), variables)
            elif action['type'] == 'copy':
                action['value'] = self._substitute_variables(action_config.get('value', ''), variables)
            else:
                action['value'] = self._substitute_variables(action_config.get('value', ''), variables)

            actions.append(action)

        # Remove duplicates based on label
        seen_labels = set()
        unique_actions = []
        for action in actions:
            if action['label'] not in seen_labels:
                seen_labels.add(action['label'])
                unique_actions.append(action)

        return unique_actions

    def suggest_smart_actions(
        self,
        text: str,
        context_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate intelligent action suggestions based on full context

        Args:
            text: Selected text
            context_data: Full context analysis result

        Returns:
            List of smart action suggestions
        """
        actions = []

        # Get insights from context
        insights = context_data.get('insights', [])

        # Suggest based on insights
        for insight in insights:
            if 'overdue' in insight.lower():
                actions.append({
                    'label': 'Schedule follow-up',
                    'type': 'action',
                    'value': 'schedule_followup',
                    'icon': 'calendar'
                })

            if 'working on' in insight.lower() and 'JT-' in insight:
                actions.append({
                    'label': 'View related tickets',
                    'type': 'action',
                    'value': 'view_related_tickets',
                    'icon': 'list'
                })

        return actions
