from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware


class InjectMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error"]

    def __init__(self, **kwargs):
        super().__init__()
        self.__kwargs = kwargs

    async def pre_process(self, obj, data, *args):
        for key, value in self.__kwargs.items():
            data[key] = value


