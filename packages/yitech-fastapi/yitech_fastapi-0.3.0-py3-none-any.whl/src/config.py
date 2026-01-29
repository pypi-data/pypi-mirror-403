from os import path
from yitool.yi_config import YiConfig

config_file = path.join(path.dirname(__file__), "../application.yml")
config = YiConfig.from_file(config_file)

settings = config.settings
