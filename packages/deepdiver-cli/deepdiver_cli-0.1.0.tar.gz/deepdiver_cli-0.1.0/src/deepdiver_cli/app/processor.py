from deepdiver_cli.plugins.datafilter import NoOpFilter
from deepdiver_cli.plugins.datamask import NoOpMasker
from deepdiver_cli.plugins.descyptor import NoOpDecryptor


_data_masker = NoOpMasker()
_log_decryptor = NoOpDecryptor()
_filter = NoOpFilter()


def set_desensitizer(desensitizer):
    global _data_masker
    _data_masker = desensitizer


def get_desensitizer():
    return _data_masker


def set_decryptor(descyptor):
    global _log_decryptor
    _log_decryptor = descyptor


def get_decryptor():
    return _log_decryptor


def set_filter(filter):
    global _filter
    _filter = filter


def get_filter():
    return _filter
