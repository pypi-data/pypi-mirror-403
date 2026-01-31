import json
import os


def setup():
    home_directory = os.path.expanduser("~")
    mridumanda_directory = ".mridumanda"
    
    if os.path.isfile(os.path.join(home_directory, mridumanda_directory, "weather.json")):
        return
    else:
        with open(os.path.join(home_directory, mridumanda_directory, "weather.json"), "x") as file:
            json.dump({}, file, indent=4)
        