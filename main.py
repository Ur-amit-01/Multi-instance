"""
Optimized Multi-Bot Launcher with Shared Requirements
----------------------------------------------------
Launches multiple bots from different branches while installing requirements only once
"""

import subprocess
import os
import re
import time
from multiprocessing import Process
from logger_setup import setup_logger, get_logger

# Base configuration
BASE_DIR = "/app"
REPO_URL = "https://github.com/Ur-amit-01/Hobby-project.git"
ID_PATTERN = re.compile(r'^\d{5,}$')
INSTALL_LOCK = False  # Global lock for requirements installation

# Initialize main logger
logger = setup_logger('BotLauncher')

# ====================== BOT CONFIGS ====================== #
BOT_CONFIGS = [
    {
        "name": "PDF merger",
        "token": "7610694593:AAFO8HifPDyFeiKrL7choPKqa080XnfYa38",
        "db_name": "merger",
        "admins": "7150972327",
        "branch": "Merger"
    },
    {
        "name": "Restricted content saver",
        "token": "7604734109:AAFJIqhqzMLwcWOMLgzhiCXgp9-0EXk14FM",
        "db_name": "restricted",
        "admins": "7150972327",
        "session_string": "BQFP49AAn6jgY8Wwp8nhPAiF1PoD6hVxl0HWUtx8AldMjcpUOpkB0jI63t8aRNmAHQ_CWyU7CPZCiQVSOFMeL-5pLl2Z2D18R7uJx52rivl46MEe1i9aFC9gUxXRHChvUgAJWTAyytSg_BVKb8LhAKnPvNQoeV8znsy6U0wtEHY9a_lu04-fxzB5mAWZDrS12HGbkZvsocaEHgMLiGUl3q83bThYzHAciMjgzKxNiKB7VeLsyy5Ua01Ndh2uRP1KL43sp-KtF9wSw4wNV-LGtAGnMhDBG8_0Yt3zKIBk21KtM7BGsZZinxdgfs3sU53EmoAk61B8YEJ5MfAikBSRI00B8Ng4AAAAAAGVhUI_AA",
        "branch": "Restricted"
    },
    {
        "name": "Request approver",
        "token": "7279071790:AAFzrFOtlOHOJVZj_9VdF1sGwrOzv8R_Z70",
        "db_name": "request",
        "admins": "7150972327",
        "session_string": "BQFP49AAn6jgY8Wwp8nhPAiF1PoD6hVxl0HWUtx8AldMjcpUOpkB0jI63t8aRNmAHQ_CWyU7CPZCiQVSOFMeL-5pLl2Z2D18R7uJx52rivl46MEe1i9aFC9gUxXRHChvUgAJWTAyytSg_BVKb8LhAKnPvNQoeV8znsy6U0wtEHY9a_lu04-fxzB5mAWZDrS12HGbkZvsocaEHgMLiGUl3q83bThYzHAciMjgzKxNiKB7VeLsyy5Ua01Ndh2uRP1KL43sp-KtF9wSw4wNV-LGtAGnMhDBG8_0Yt3zKIBk21KtM7BGsZZinxdgfs3sU53EmoAk61B8YEJ5MfAikBSRI00B8Ng4AAAAAAGVhUI_AA",
        "branch": "Acceptor"
    },
    {
        "name": "File renamer",
        "token": "8069066795:AAHNEYLjuWokOlI2xbG_Yqys4_OjiRg4Ay0",
        "db_name": "Renamer",
        "admins": "7150972327",
        "branch": "Renamer"
    }
]

# ====================== CORE FUNCTIONS ====================== #

def install_shared_requirements():
    """Install requirements once in a shared location"""
    global INSTALL_LOCK
    
    # Create shared requirements directory
    shared_dir = os.path.join(BASE_DIR, "shared_requirements")
    os.makedirs(shared_dir, exist_ok=True)
    
    # Clone a temporary repo for requirements
    temp_repo = os.path.join(shared_dir, "temp_repo")
    if not os.path.exists(temp_repo):
        subprocess.run([
            "git", "clone",
            "--depth", "1",
            REPO_URL,
            temp_repo
        ], check=True)
    
    # Install requirements with lock to prevent concurrent installations
    while INSTALL_LOCK:
        time.sleep(1)
    
    INSTALL_LOCK = True
    try:
        os.chdir(temp_repo)
        if not os.path.exists(os.path.join(shared_dir, ".installed")):
            logger.info("Installing shared requirements...")
            subprocess.run([
                "pip", "install",
                "--no-cache-dir",
                "--disable-pip-version-check",
                "-r", "requirements.txt"
            ], check=True)
            # Create marker file
            open(os.path.join(shared_dir, ".installed"), 'w').close()
    finally:
        INSTALL_LOCK = False
        os.chdir(BASE_DIR)

def clone_bot_repo(bot_config):
    """Clone a specific branch for a bot"""
    bot_dir = os.path.join(BASE_DIR, bot_config["name"])
    branch = bot_config.get("branch", "main")
    
    if os.path.exists(bot_dir):
        # Update existing clone
        logger.info(f"Updating existing clone for {bot_config['name']}")
        os.chdir(bot_dir)
        subprocess.run(["git", "fetch"], check=True)
        subprocess.run(["git", "checkout", branch], check=True)
        subprocess.run(["git", "pull", "origin", branch], check=True)
    else:
        # Fresh clone
        logger.info(f"Cloning fresh repo for {bot_config['name']}")
        subprocess.run([
            "git", "clone",
            "--branch", branch,
            "--single-branch",
            "--depth", "1",
            REPO_URL,
            bot_dir
        ], check=True)
    
    os.chdir(BASE_DIR)
    return bot_dir

def setup_environment_vars(bot_config):
    """Setup environment variables for a bot"""
    try:
        # Process admin IDs
        admin_list = [int(admin) if ID_PATTERN.search(admin) else admin 
                    for admin in bot_config["admins"].split()]
        os.environ["ADMIN"] = " ".join(str(admin) for admin in admin_list)
        
        # Set other environment variables
        os.environ["BOT_TOKEN"] = bot_config["token"]
        os.environ["DB_NAME"] = bot_config["db_name"]
        os.environ["SESSION_STRING"] = bot_config.get("session_string", "")
        
        get_logger('EnvSetup').info(
            f"Environment configured for {bot_config['name']}\n"
            f"Branch: {bot_config.get('branch', 'main')}\n"
            f"Admins: {admin_list}\n"
            f"DB: {bot_config['db_name']}\n"
            f"Session: {'set' if bot_config.get('session_string') else 'not set'}"
        )
    except Exception as e:
        get_logger('EnvSetup').error(f"Error setting up environment: {str(e)}")
        raise

def launch_bot(bot_config):
    """Launch a single bot instance"""
    bot_logger = get_logger(f"Bot.{bot_config['name']}")
    
    try:
        # Clone/update the bot repo
        bot_dir = clone_bot_repo(bot_config)
        
        # Setup environment
        setup_environment_vars(bot_config)
        
        # Launch bot
        bot_logger.info("Launching bot process")
        os.chdir(bot_dir)
        subprocess.run(["python", "bot.py"], check=True)
    except Exception as e:
        bot_logger.error(f"Bot failed: {str(e)}")
        raise
    finally:
        # Clean up environment variables
        for var in ["ADMIN", "BOT_TOKEN", "DB_NAME", "SESSION_STRING"]:
            if var in os.environ:
                del os.environ[var]
        os.chdir(BASE_DIR)

# ====================== MAIN ====================== #
def main():
    """Main execution function"""
    logger.info("="*50)
    logger.info(" OPTIMIZED MULTI-BOT LAUNCHER ".center(50, "="))
    logger.info("="*50)
    
    try:
        # Install shared requirements first
        install_shared_requirements()
        
        # Launch bots with staggered start
        processes = []
        for i, bot_config in enumerate(BOT_CONFIGS):
            p = Process(target=launch_bot, args=(bot_config,))
            p.start()
            processes.append(p)
            logger.info(f"Started {bot_config['name']} (branch: {bot_config.get('branch', 'main')})
            
            # Stagger launches to reduce resource contention
            if i < len(BOT_CONFIGS) - 1:
                time.sleep(10)
        
        # Wait for all processes to complete
        for p in processes:
            p.join()
            
        logger.info("All bot processes completed")
    except Exception as e:
        logger.critical(f"Launcher failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
