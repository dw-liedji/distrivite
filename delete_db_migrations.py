import os

os.system("find ./apps/ -path '*/migrations/*.pyc' -delete")
os.system("find ./apps/ -path '*/migrations/0*.py' -delete")
os.system("find ./apps/ -path '*/__pycache__/*.pyc' -delete")
os.system("find ./distrivite/ -path '*/__pycache__/*.pyc' -delete")
os.system("find . -path '*.sqlite3' -delete")
