import logging
import sys
from logging.handlers import RotatingFileHandler
from tkinter import messagebox

from layout import resource_path

logger = logging.getLogger('inventory')
_configured = False


def setup_logging():
    global _configured
    if _configured:
        return
    _configured = True
    handler = RotatingFileHandler(
        resource_path('app.log'), maxBytes=1_000_000, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    sys.excepthook = _handle_uncaught
    logger.info('Application started')


def install_tk_hook(window):
    window.report_callback_exception = _handle_tk


def _handle_uncaught(exc_type, exc, tb):
    logger.error('Uncaught exception', exc_info=(exc_type, exc, tb))


def _handle_tk(exc, val, tb):
    logger.error('Tk callback exception', exc_info=(exc, val, tb))
    messagebox.showerror('Unexpected Error', str(val))
