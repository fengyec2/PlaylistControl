import traceback
import sys

try:
    import utils.notification as n
    import core.database as db
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)
