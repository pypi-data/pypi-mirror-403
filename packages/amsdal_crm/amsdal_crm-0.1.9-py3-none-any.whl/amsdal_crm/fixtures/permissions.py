"""CRM permission fixtures."""

# CRM permissions for each entity type
CRM_PERMISSIONS = [
    # Contact permissions
    {'model': 'Contact', 'action': 'read'},
    {'model': 'Contact', 'action': 'create'},
    {'model': 'Contact', 'action': 'update'},
    {'model': 'Contact', 'action': 'delete'},
    # Account permissions
    {'model': 'Account', 'action': 'read'},
    {'model': 'Account', 'action': 'create'},
    {'model': 'Account', 'action': 'update'},
    {'model': 'Account', 'action': 'delete'},
    # Deal permissions
    {'model': 'Deal', 'action': 'read'},
    {'model': 'Deal', 'action': 'create'},
    {'model': 'Deal', 'action': 'update'},
    {'model': 'Deal', 'action': 'delete'},
    # Activity permissions
    {'model': 'Activity', 'action': 'read'},
    {'model': 'Activity', 'action': 'create'},
    {'model': 'Activity', 'action': 'update'},
    {'model': 'Activity', 'action': 'delete'},
    # Pipeline permissions (read-only for non-admins)
    {'model': 'Pipeline', 'action': 'read'},
    # Stage permissions (read-only for non-admins)
    {'model': 'Stage', 'action': 'read'},
]
