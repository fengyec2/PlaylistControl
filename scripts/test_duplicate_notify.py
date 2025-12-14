from config.config_manager import config
from utils.notification import notify_duplicate

# Ensure preference is win10toast
config.set('notifications.duplicates.preferred_backend', 'win10toast')
config.set('notifications.duplicates.enabled', True)
config.set('notifications.duplicates.duration_seconds', 5)

print('Calling notify_duplicate (should show a Windows toast if win10toast installed)...')
notify_duplicate('Test Song', 'Test Artist', app_name='TestApp')
print('Done (if toast was shown, check your notification area).')
