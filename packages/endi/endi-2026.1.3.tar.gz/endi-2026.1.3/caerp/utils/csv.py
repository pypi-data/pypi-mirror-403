import csv
import io
import logging

from caerp.exception import MessageException
from caerp.utils.strings import bytes_to_string

logger = logging.getLogger(__name__)


def guess_csv_dialect(file_buffer):
    """
    Guess the csv dialect using the whole file content

    :param file_buffer: A file buffer with a read method
    """
    dialect = csv.Sniffer().sniff(file_buffer.read())
    file_buffer.seek(0)
    return dialect


def get_csv_reader(file_buffer):
    """
    Return a csv DictReader based on the provided buffer

    :param file_buffer: A file buffer with a read method and bytes data
    :param dialect: A csv.Dialect object
    :returns: a csv.DictReader
    """

    file_buffer.seek(0)
    data = file_buffer.read()
    file_buffer.seek(0)

    if isinstance(data, bytes):
        converted_data = bytes_to_string(data)
        file_buffer = io.StringIO(converted_data)
        file_buffer.seek(0)

    dialect = guess_csv_dialect(file_buffer)
    return csv.DictReader(file_buffer, dialect=dialect)


def test_content_is_csv(file_buffer):
    """
    Assert that the file content is a valid CSV

    :param file_buffer: A file buffer in bytes format with a read method
    """
    try:
        reader = get_csv_reader(file_buffer)
    except csv.Error:
        raise MessageException("Le fichier ne semble pas être un CSV valide")

    try:
        first_line = next(reader)
        keys = list(first_line.keys())
    except StopIteration:
        raise MessageException(
            "Le fichier semble vide ou ne contient pas de données CSV valides"
        )

    if not first_line or None in first_line or len(keys) < 2:
        logger.debug(f"Invalid CSV content, first_line : {first_line}")
        logger.debug(f"Keys: {keys}")
        raise MessageException("Le fichier ne contient pas de données CSV valides")
    return True
