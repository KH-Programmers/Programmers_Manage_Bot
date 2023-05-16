from logging import Logger, Formatter, FileHandler, StreamHandler


def createLogger(name: str, level: int) -> Logger:
    logger = Logger(name=name, level=level)
    formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fileHandler = FileHandler(filename=f"{name}.log", mode="a", encoding="utf-8")
    fileHandler.setFormatter(formatter)
    streamHandler = StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger
