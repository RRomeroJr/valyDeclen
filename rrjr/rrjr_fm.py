import os
from typing import IO
from typing import Any
def sp_open(file, mode, **kwargs) -> IO[Any]:
    if (mode == "seq"):
        return open_avoid_overwrite(file, **kwargs)
    else:
        return open(file, mode, **kwargs)

def g_seq_filename(filename: str):
    num = 0
    output_name = filename
    test_name = output_name
    while os.path.exists(test_name):
        num += 1
        split = os.path.splitext(os.path.basename(output_name))
        test_name = ''.join(split[0] + str(num) + split[1])
        
    output_name = test_name
    return output_name
def open_avoid_overwrite(filename: str, **kwargs):
    output_name = g_seq_filename(filename)
    print(output_name)

    return open(
        output_name,
        "w",
        kwargs.get("buffering", -1),
        kwargs.get("encoding", None),
        kwargs.get("errors", None),
        kwargs.get("newline", None),
        kwargs.get("closefd", True),
        kwargs.get("opener", None)
    )
