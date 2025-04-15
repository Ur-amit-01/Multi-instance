"""
Multi-Bot Launcher with Branch Support
--------------------------------------
Launcher that supports deploying specific branches for each bot
"""

import subprocess
import os
import re
from multiprocessing import Process
from logger_setup import setup_logger, get_logger

# Base configuration
BASE_DIR = "/app"
REPO_URL = "https://github.com/Ur-amit-01/Post-Manager.git"
ID_PATTERN = re.compile(r'^\d{5,}$')

# Initialize main logger
logger = setup_logger('BotLauncher')

# ====================== BOT CONFIGS WITH BRANCHES ====================== #
BOT1_CONFIG = {
    "name": "PDF merger",
    "token": "7610694593:AAFO8HifPDyFeiKrL7choPKqa080XnfYa38",
    "db_name": "merger",
    "admins": "7150972327",
    "branch": "Merger"  # Specify branch for this bot
}

BOT2_CONFIG = {
    "name": "Restricted content saver",
    "token": "7604734109:AAFJIqhqzMLwcWOMLgzhiCXgp9-0EXk14FM",
    "db_name": "restricted",
    "admins": "7150972327",
    "session_string": "BQFP49AAn6jgY8Wwp8nhPAiF1PoD6hVxl0HWUtx8AldMjcpUOpkB0jI63t8aRNmAHQ_CWyU7CPZCiQVSOFMeL-5pLl2Z2D18R7uJx52rivl46MEe1i9aFC9gUxXRHChvUgAJWTAyytSg_BVKb8LhAKnPvNQoeV8znsy6U0wtEHY9a_lu04-fxzB5mAWZDrS12HGbkZvsocaEHgMLiGUl3q83bThYzHAciMjgzKxNiKB7VeLsyy5Ua01Ndh2uRP1KL43sp-KtF9wSw4wNV-LGtAGnMhDBG8_0Yt3zKIBk21KtM7BGsZZinxdgfs3sU53EmoAk61B8YEJ5MfAikBSRI00B8Ng4AAAAAAGVhUI_AA",
    "branch": "Restricted"  # Different branch for this bot
}

BOT3_CONFIG = {
    "name": "Request approver",
    "token": "7279071790:AAFzrFOtlOHOJVZj_9VdF1sGwrOzv8R_Z70",
    "db_name": "request",
    "admins": "7150972327",
    "session_string": "BQFP49AAn6jgY8Wwp8nhPAiF1PoD6hVxl0HWUtx8AldMjcpUOpkB0jI63t8aRNmAHQ_CWyU7CPZCiQVSOFMeL-5pLl2Z2D18R7uJx52rivl46MEe1i9aFC9gUxXRHChvUgAJWTAyytSg_BVKb8LhAKnPvNQoeV8znsy6U0wtEHY9a_lu04-fxzB5mAWZDrS12HGbkZvsocaEHgMLiGUl3q83bThYzHAciMjgzKxNiKB7VeLsyy5Ua01Ndh2uRP1KL43sp-KtF9wSw4wNV-LGtAGnMhDBG8_0Yt3zKIBk21KtM7BGsZZinxdgfs3sU53EmoAk61B8YEJ5MfAikBSRI00B8Ng4AAAAAAGVhUI_AA"),
    "branch": "Acceptor"  # Feature branch for this bot
}

BOT4_CONFIG = {
    "name": "File renamer",
    "token": "8069066795:AAHNEYLjuWokOlI2xbG_Yqys4_OjiRg4Ay0",
    "db_name": "Renamer",
    "admins": "7150972327",
    "branch": "Renamer"  # Different branch for this bot
}

ACTIVE_BOTS = [BOT1_CONFIG, BOT2_CONFIG, BOT3_CONFIG, BOT4_CONFIG]

# ====================== CORE FUNCTIONS ====================== #

def clone_repo_with_branch(repo_url, target_dir, branch="main"):
    """Clone a specific branch of the repository"""
    try:
        logger.info(f"Cloning branch '{branch}' from {repo_url} to {target_dir}")
        subprocess.run([
            "git", "clone", 
            "--branch", branch,
            "--single-branch",
            repo_url, 
            target_dir
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone branch {branch}: {str(e)}")
        raise

def install_requirements(bot_dir):
    """Install required packages for a specific bot"""
    logger.info(f"Installing requirements in {bot_dir}")
    try:
        os.chdir(bot_dir)
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
        logger.info("Requirements installed successfully")
    except Exception as e:
        logger.error(f"Failed to install requirements: {str(e)}")
        raise
    finally:
        os.chdir(BASE_DIR)

def setup_environment_vars(bot_config):
    """Setup all environment variables for the bot"""
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
        return admin_list
    except Exception as e:
        get_logger('EnvSetup').error(f"Error setting up environment: {str(e)}")
        raise

def launch_bot(bot_config):
    """Launch a single bot instance with specific branch"""
    bot_logger = get_logger(f"Bot.{bot_config['name']}")
    bot_dir = os.path.join(BASE_DIR, bot_config["name"])
    branch = bot_config.get("branch", "main")
    
    bot_logger.info(f"Starting bot instance from branch '{branch}'")
    
    try:
        # Clone the specific branch
        clone_repo_with_branch(REPO_URL, bot_dir, branch)
        
        # Install requirements for this bot
        install_requirements(bot_dir)
        
        # Configure environment
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
    logger.info(" MULTI-BOT LAUNCHER WITH BRANCH SUPPORT ".center(50, "="))
    logger.info("="*50)
    
    try:
        processes = []
        for bot_config in ACTIVE_BOTS:
            p = Process(target=launch_bot, args=(bot_config,))
            p.start()
            processes.append(p)
            logger.info(f"Started process for {bot_config['name']} (branch: {bot_config.get('branch', 'main')})")
        
        for p in processes:
            p.join()
            
        logger.info("All bot processes completed")
    except Exception as e:
        logger.critical(f"Launcher failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
