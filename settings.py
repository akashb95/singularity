from dotenv import load_dotenv, find_dotenv

def load_env_vars(debug=True):
    load_dotenv(find_dotenv(), verbose=debug)
    return
