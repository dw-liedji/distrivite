import os

os.system("find ./apps/ -path '*/migrations/*.pyc' -delete")
os.system("find ./apps/ -path '*/migrations/0*.py' -delete")
os.system("find ./apps/ -path '*/__pycache__/*.pyc' -delete")
