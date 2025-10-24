"""Action suggestion rules based on detected patterns"""

from typing import List, Dict, Any, Optional


class ActionSuggester:
    """Generate contextual action suggestions based on text type and content"""

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

        # Pattern-based actions
        if text_type == 'jira_ticket':
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

        # Database match-based actions
        for match in exact_matches:
            match_type = match.get('type')

            if match_type == 'contact':
                contact = match.get('data', {})
                if contact.get('email'):
                    actions.append({
                        'label': f"Email {contact.get('name', 'contact')}",
                        'type': 'url',
                        'value': f"mailto:{contact['email']}",
                        'icon': 'mail'
                    })

            elif match_type == 'project':
                project = match.get('data', {})
                # Could add project-specific actions here
                pass

        # Universal actions
        actions.append({
            'label': 'Save as snippet',
            'type': 'action',
            'value': 'save_snippet',
            'icon': 'save'
        })

        actions.append({
            'label': 'Search Google',
            'type': 'url',
            'value': f'https://www.google.com/search?q={text}',
            'icon': 'search'
        })

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
