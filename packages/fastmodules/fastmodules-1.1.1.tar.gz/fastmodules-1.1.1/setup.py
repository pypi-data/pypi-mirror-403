from setuptools import setup, find_packages

setup(
name='fastmodules',
version='1.1.1',
description='Downloads most used modules',
long_description='Downloads most used modules',
packages=find_packages(),
install_requires=['BeautifulSoup4', 'pyTelegramBotAPI', 'flask', 'keyboard', 'pyautogui', 'requests', 'numpy', 'pillow', 'pandas', 'mouse']
)
