def get_logger(logger_name: str, level='INFO'):
    """
    Check if logger instance already exists. Default will be set to INFO.
    """
    import logging
    if logger_name in logging.Logger.manager.loggerDict.keys():
        # Logger exists, so return it
        return logging.getLogger(logger_name)
    else:
        log_level = {'NOTSET': 0, 'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}.get(level, 20)
        logger = logging.getLogger(name=logger_name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=handler)
        logger.setLevel(level=log_level)
        return logger