import re

class EmailUtil:

    @staticmethod
    def is_email(value):
        if not value:
            return False
        pattern = r'^[a-zA-Z0-9]+([._%+-]?[a-zA-Z0-9]+)*@[a-zA-Z0-9]+([.-]?[a-zA-Z0-9]+)*\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
