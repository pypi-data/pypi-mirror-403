class RodinaException(Exception):
    pass


class IncorrectLoginData(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return "Вы ввели неверные cookie!"


class ThisIsYouError(RodinaException):
    def __init__(self, user_id):
        self.user_id = user_id

    def __str__(self) -> str:
        return f"Вы не можете совершить данное действие самому себе\nID пользователя: {self.user_id}"
