import subprocess
import os
from multiprocessing import Process

def run_bot1():
    os.chdir("/app")
    subprocess.call(["git", "clone", "https://github.com/Ur-amit-01/File_share_2.0.git", "Normal file_store"])
    os.chdir("Post-Manager-Bot1")
    
    # Set environment variables for bot 1
    os.environ["BOT_TOKEN"] = ""
    os.environ["DATABASE_URL"] = ""
    
    subprocess.call(["pip", "install", "-r", "requirements.txt"])
    subprocess.call(["python", "main.py"])

def run_bot2():
    os.chdir("/app")
    subprocess.call(["git", "clone", "https://github.com/Ur-amit-01/Teleshare.git", "Teleshare"])
    os.chdir("Post-Manager-Bot2")

    # Set environment variables for bot 2
    os.environ["BOT_TOKEN"] = ""
    os.environ["DATABASE_URL"] = ""
    
    subprocess.call(["pip", "install", "-r", "requirements.txt"])
    subprocess.call(["python", "-m", "bot.main"])

    
if __name__ == "__main__":
    p1 = Process(target=run_bot1)
    p2 = Process(target=run_bot2)
    
    p1.start()
    p2.start()

    p1.join()
    p2.join()
