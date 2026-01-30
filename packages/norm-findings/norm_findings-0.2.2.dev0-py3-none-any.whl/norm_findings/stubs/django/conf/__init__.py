class Settings:
    def __getattr__(self, name):
        # Provide common default settings used by parsers
        defaults = {
            "QUALYS_WAS_WEAKNESS_IS_VULN": False,
            "QUALYS_WAS_UNIQUE_ID": False,
        }
        return defaults.get(name, None)

settings = Settings()
