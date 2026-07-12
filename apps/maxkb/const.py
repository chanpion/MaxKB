# -*- coding: utf-8 -*-
#
import os

from dotenv import load_dotenv

from .conf import ConfigManager

__all__ = ['BASE_DIR', 'PROJECT_DIR', 'VERSION', 'CONFIG']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
# 本地开发使用项目根目录下的 logs，避免写入容器路径 /opt/maxkb/logs 导致权限错误
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
VERSION = '2.0.0'

# load environment variables from .env file
load_dotenv()
# print(os.getenv('MAXKB_CONFIG'))
if os.getenv('MAXKB_CONFIG') is not None:
    CONFIG = ConfigManager.load_user_config(root_path=PROJECT_DIR)
else:
    CONFIG = ConfigManager.load_user_config(root_path=os.path.join(PROJECT_DIR, 'conf'))

