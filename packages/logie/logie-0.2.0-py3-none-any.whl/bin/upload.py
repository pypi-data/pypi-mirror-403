import configparser
import subprocess

# token.ini 읽기
config = configparser.ConfigParser()
config.read('/home/kimyh/library/token.ini')

username = config['PyPI']['username']
password = config['PyPI']['password']

# subprocess 로 twine upload 실행
subprocess.run([
    'twine', 'upload', 'dist/*',
    '-u', username,
    '-p', password
])
