import os
import sys

def install(package):
    os.system(f"{sys.executable} -m pip install {package}")

dependencies = [
    "aiogram==3.0.0",
    "tonnelmp==1.2",
    "portalsmp==1.2",
    "sqlalchemy==2.0.30",
    "aiohttp==3.8.6",
    "python-dotenv==1.0.1",
    "pydantic==1.10.15"
]

for dep in dependencies:
    print(f"Устанавливаю {dep}...")
    install(dep)

print("Все зависимости установлены!")
