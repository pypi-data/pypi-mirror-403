"""
serialize.py

Reads / writes a list of dicts to a simple json text file.

Provides:
fileRead(fname)
__fileInitialise(fname)
fileWrite(fname, data)
fileAppend(fname, data)
fileSort(fname)
fileInsert(fname)
fileTidy(fname)

file spec: ordered json list like
[,
{"timestamp": 1515010320.0, "open": "172.2950", "high": "172.3600", "low": "172.2400", "close": "172.3395", "volume": "53448"},
{"timestamp": 1515010380.0, "open": "172.3300", "high": "172.3500", "low": "172.2800", "close": "172.2850", "volume": "33566"},
{"timestamp": 1515010440.0, "open": "172.2800", "high": "172.2950", "low": "172.2000", "close": "172.2450", "volume": "57776"},
{"timestamp": 1515010500.0, "open": "172.2350", "high": "172.3600", "low": "172.2350", "close": "172.3400", "volume": "44514"},
{"timestamp": 1515010560.0, "open": "172.3500", "high": "172.4200", "low": "172.3500", "close": "172.3950", "volume": "30515"}]

A single trailing newline is required. Note placement of commas.

The '[,' is replaced by '[' by fileTidy() to allow loading.

"""

import os
# simplejson can serialize Decimal
try:
    import simplejson as json
except ImportError:
    import json

encoding = 'utf-8'      # 1-byte encoding is assumed


def fileGetLastValue(fname, key):
    """

    Parameters
    ----------
    fname :

    key :


    Returns
    -------
    type


    """
    if os.path.isfile(fname):
        try:
            with open(fname, 'rb') as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b"\n":   # step back until EOL
                    f.seek(-2, os.SEEK_CUR)
                # clean up to valid json
                last = f.readline().decode().replace(',]', '').replace(']', '')
            return json.loads(last)[key]
        except:
            pass
    return 1


def fileGetFirstValue(fname, key):
    if os.path.isfile(fname):
        try:
            with open(fname, 'rb') as f:
                _ = f.readline()
                last = f.readline().decode().replace(',]', '').replace('},', '}')
            return json.loads(last)[key]
        except:
            pass
    return 1


def fileRead(fname):
    """Read json data from a file, return dict.

    Parameters
    ----------
    fname :


    Returns
    -------

    """
    if os.path.isfile(fname):
        with open(fname, 'r') as data_file:
            json_data = json.load(data_file)
        return json_data
    return dict()


def fileTidy(fname):
    """Clear up leading '[,' if file exists and '[,' exists in the file.

    Parameters
    ----------
    fname :


    Returns
    -------

    """
    if os.path.isfile(fname):
        with open(fname, 'rb+', buffering=0) as f:
            byte = f.read(1)
            while byte != b'[' and byte != b'':
                byte = f.read(1)
            byte = f.read(1)
            if byte == b',':
                f.seek(-1, os.SEEK_CUR)
                f.write(b' ')
                f.close()


def __fileInitialize(fname):
    """
    Initialise a file with an empty list, ready for appending.
    Unfortunately, we will need to remove the leading ',' when appending the
    first record. If the file exists, ignore it.
    """
    if not os.path.isfile(fname):
        with open(fname, mode='w', encoding=encoding) as data_file:
            data_file.write("[]\n")


def fileWrite(fname, data, overwrite=False):
    """Write list of dicts to new json file.

    Parameters
    ----------
    fname :

    data :

    overwrite :
         (Default value = False)

    Returns
    -------

    """
    if os.path.isfile(fname) and overwrite is False:
        raise ValueError('File already exists')
    else:
        with open(fname, 'w', encoding=encoding) as data_file:
            # fileGetLastTimestamp() relies on line breaks between records.
            json.dump(data.sort(key=lambda row: row['timestamp']), data_file, separators=(',\n', ': '))
            data_file.close()
        fileTidy(fname)


def fileAppend(fname, data):
    """Append a dict or list of dicts to the data file.

    Cobbled together from https://stackoverflow.com/a/31224105
    it overwrites the closing ']' with the new record + a new ']'.
    POSIX expects a trailing newline.
    There is some difficulty when we are appending to an empty file; you end up
    with invalid json. In which case, you can use fileWrite().
    This is worked around by calling __fileInitialize().
    This function should be fast.

    Parameters
    ----------
    fname :

    data :


    Returns
    -------

    """
    __fileInitialize(fname)
    try:
        if type(data) is list:
            # loop over rows
            with open(fname, mode='r+', encoding=encoding) as data_file:
                data_file.seek(0, os.SEEK_END)
                position = data_file.tell() - 2
                data_file.seek(position)
                for record in data:
                    data_file.write(",\n{}".format(json.dumps(record)))
                data_file.write("]\n")
                data_file.close()
        elif type(data) is dict:
            # single row
            with open(fname, mode='r+', encoding=encoding) as data_file:
                data_file.seek(0, os.SEEK_END)
                position = data_file.tell() - 2
                data_file.seek(position)
                data_file.write(",\n{}]\n".format(json.dumps(data)))
                data_file.close()
    except Exception as e:
        raise e


def fileInsert(fname, data):
    """Search for right timestamp and insert record

    Parameters
    ----------
    fname :

    data :


    Returns
    -------

    """
    raise ValueError('Not implemented')


def fileUniq(fname):
    """remove duplicate entries

    Parameters
    ----------
    fname :


    Returns
    -------

    """
    raise ValueError('Not implemented')


def fileSort(fname):
    """Sort by time key, rewrite

    Parameters
    ----------
    fname :


    Returns
    -------

    """
    # https://stackoverflow.com/a/73050
    raise ValueError('Not implemented')
