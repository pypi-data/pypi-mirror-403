import json
from pathlib import Path
from platformdirs import user_data_dir

data_dir = Path(user_data_dir("ospm"))
config_filename = "config.json"


class Config:
    def __init__(self, from_file: bool = True):
        if not from_file:
            self.default_password_length = 16
            self.password_ascii = True
            self.password_punctuation = False
            self.password_digits = True
            self.show_password_on_auto_generation = True
            self.current_vault = "vault"
        else:
            if not self.exists():
                self.init()
            with open(data_dir / config_filename, "r") as f:
                obj = json.loads(f.read())
                self.default_password_length = obj["default_password_length"]
                self.password_ascii = obj["gen_pass_ascii_letters"]
                self.password_digits = obj["gen_pass_digits"]
                self.password_punctuation = obj["gen_pass_punctuation"]
                self.show_password_on_auto_generation = obj["show_password_on_auto_generation"]
                self.current_vault = obj["current_vault"]

    @classmethod
    def exists(cls) -> bool:
        return Path.exists(data_dir / config_filename)

    @classmethod
    def init(cls) -> None:
        if not Path.exists(data_dir):
            Path.mkdir(data_dir, parents=True)

        cls(from_file=False).save()

    def to_json(self) -> str:
        return json.dumps(self.__dict__())

    def save(self):
        with open(data_dir / config_filename, "w") as f:
            f.write(self.to_json())

    def __dict__(self) -> dict:
        return {
            "default_password_length": self.default_password_length,
            "gen_pass_ascii_letters": self.password_ascii,
            "gen_pass_punctuation": self.password_punctuation,
            "gen_pass_digits": self.password_digits,
            "show_password_on_auto_generation": self.show_password_on_auto_generation,
            "current_vault": self.current_vault
        }