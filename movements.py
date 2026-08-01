from datetime import datetime

from app_log import logger
from database import commit, execute

current_user = None


def set_current_user(user):
    global current_user
    current_user = user


def log_movement(product_id, quantity_delta, reason, reference_id=None):
    created_by = None
    if isinstance(current_user, dict):
        created_by = current_user.get('empid')
    execute(
        'INSERT INTO stock_movements '
        '(product_id, quantity_delta, reason, reference_id, created_by, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (product_id, quantity_delta, reason, reference_id, created_by,
         datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


def log_movement_committed(product_id, quantity_delta, reason, reference_id=None):
    try:
        log_movement(product_id, quantity_delta, reason, reference_id)
        commit()
        return True
    except Exception:
        logger.exception('failed to record stock movement')
        return False
