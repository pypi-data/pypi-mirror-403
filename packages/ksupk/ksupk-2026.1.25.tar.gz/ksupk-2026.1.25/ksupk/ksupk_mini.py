# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import hashlib
import datetime
import shutil
import json
import string
import random
from threading import Thread
import inspect


class ThreadWithReturnValue(Thread):
    """
    x1 = ThreadWithReturnValue(1, target=some_func, args=(arg1, arg2), kwargs={"kwarg1": kwarg1, "kwarg2": kwarg2,})
    x2 = ThreadWithReturnValue(2, target=some_func, args=(arg1, arg2), kwargs={"kwarg1": kwarg1, "kwarg2": kwarg2,})
    x1.start(), x2.start()
    return_of_some_func_1, return_of_some_func_2 = x1.join(), x2.join()
    """

    def __init__(self, index: int = -1, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._index = index
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def get_index(self):
        return self._index

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def get_files_list(dirPath: str) -> list:
    return [os.path.join(path, name) for path, subdirs, files in os.walk(dirPath) for name in files]


def get_dirs_list(dirPath: str) -> list:
    dirs = [os.path.join(path, name) for path, subdirs, files in os.walk(dirPath) for name in subdirs]
    return list(set(dirs))


def is_folder_empty(folder_path: str) -> bool:
    if(len(os.listdir(folder_path)) == 0):
        return True
    else:
        return False


def rel_path(file_path: str, folder_path: str) -> str:
    return os.path.relpath(file_path, folder_path)


def get_rel_path_of_files(files: list, folder_path: str) -> list:
    return [rel_path(file_i, folder_path) for file_i in files]


def get_abs_path_of_files(files: list) -> list:
    return [os.path.abspath(file_i) for file_i in files]


def rm_folder_content(folder_path: str, root_dir_too: bool = False, does_not_exists_is_ok = False):
    """Удаляет всё содержимое папки. Саму папку не трогает, если root_dir_too == False"""
    if(does_not_exists_is_ok == True and os.path.isdir(folder_path) == False):
        return
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for file_i in files:
            os.remove(os.path.join(root, file_i))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    if(root_dir_too == True):
        os.rmdir(folder_path)


def write_to_file_str(file_name : str, s : str) -> None:
    with open(file_name, 'w', encoding="utf-8") as fd:
        fd.write(s)
        fd.flush()


def read_from_file_str(file_name : str) -> str:
    with open(file_name, 'r', encoding="utf-8") as fd:
        S = fd.read()
    return S


def save_json(save_path: str, d: dict, indents: int = 4):
    write_to_file_str(save_path, json.dumps(d, indent=indents))


def restore_json(json_path: str) -> dict:
    return json.loads(read_from_file_str(json_path))


def mkdir_with_p(path: str, p: bool = True):
    """
    Создаст директорию, даже если ещё нет родительских.
    Если конечная уже существует, то не вернёт ошибку
    """
    os.makedirs(path, exist_ok=True)


def mkdir_needed_for_file(file: str):
    needed_dir_to_exists = os.path.dirname(file)
    if not os.path.isdir(needed_dir_to_exists):
        mkdir_with_p(needed_dir_to_exists)


def get_link_unwinding(link_path: str) -> str or None:
    """Вернёт конечный файл, на который (рекурсивно) ссылаются ссылки. """
    if os.path.exists(link_path) == False:
        return None
    elif os.path.islink(link_path) == False:
        return link_path
    else:
        linkto = os.readlink(link_path)
        if os.path.islink(linkto) == False:
            return linkto
        else:
            return get_link_unwinding(linkto)


def get_time_str(template="%y.%m.%d %H:%M:%S.%f") -> str:
    # time_str = datetime.datetime.now().strftime("[%y.%m.%d %H:%M:%S.%f]")
    time_str = datetime.datetime.now().strftime(template)
    return time_str


def get_datetime_from_str(s: str, tamplate: str) -> "datetime.datetime":
    """
    like this:
    get_datetime_from_str("24.11.07 10:12:36.590061", "%y.%m.%d %H:%M:%S.%f")
    get_datetime_from_str("2024-08-07 13:36", "%Y-%m-%d %H:%M")
    """
    return datetime.datetime.strptime(s, tamplate)


def get_timestamp_of_file(file_path: str, tamplate: str = "%Y-%m-%d_%H-%M-%S") -> str:
    dt_m = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
    return dt_m.strftime(tamplate)


def calc_hash_of_file(file_path: str, retun_str: bool = True, algo = hashlib.sha256) -> str | bytes:
    buff_BLOCKSIZE = 65536  # 64 kB
    sha = algo()
    with open(file_path, "rb") as temp:
        file_buffer = temp.read(buff_BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = temp.read(buff_BLOCKSIZE)
    if retun_str:
        return sha.hexdigest()
    else:
        return sha.digest()


def calc_hash(x: str | bytes | bytearray, algo = hashlib.sha256, 
    force_return_str: bool = False, force_return_bytes: bool = False) -> str | bytes | tuple[str, bytes]:
    return_mode = None
    if isinstance(x, str):
        x = s.encode("utf-8")
        return_mode = 1
    elif isinstance(x, bytes) or isinstance(x, bytearray):
        return_mode = 2
    else:
        raise ValueError(f"x ({type(x)}) must be str, bytes or bytearray")
    hl = algo(x)
    if force_return_str:
        return_mode = 1
    elif force_return_bytes:
        return_mode = 2
    elif force_return_str and force_return_bytes:
        return_mode = 3
    if return_mode == 1:
        return hl.hexdigest()
    elif return_mode == 2:
        return hl.digest()
    elif return_mode == 3:
        return hl.hexdigest(), hl.digest()
    else:
        return None


def calc_hash_of_str(s: str, retun_str: bool = True, algo = hashlib.sha256) -> str | bytes:
    hl = algo( s.encode("utf-8") )
    if retun_str:
        return hl.hexdigest()
    else:
        return hl.digest()


def calc_hash_of_hashes(hashes: list, retun_str: bool = True, algo = hashlib.sha256) -> str:
    hash_files = ""
    li = 0
    for hash_i in hashes:
        hash_files += hash_i
        li-=-1
        if li == 30:
            hash_files = calc_hash_of_str(hash_files)
            li = 0
    hash_files = calc_hash_of_str(hash_files, algo=algo, retun_str=retun_str)
    return hash_files


def calc_hash_of_dir(dir_path: str, hierarchy: bool = False, retun_str: bool = True, algo = hashlib.sha256) -> str | bytes:
    files = get_files_list(dir_path)
    sha = algo()

    for file_i in files:
        buff_BLOCKSIZE = 65536  # 64 kB
        with open(file_i, "rb") as fd:
            file_buffer = fd.read(buff_BLOCKSIZE)
            while len(file_buffer) > 0:
                sha.update(file_buffer)
                file_buffer = fd.read(buff_BLOCKSIZE)
    
    if hierarchy:
        files_sorted = sorted(get_rel_path_of_files(files + get_dirs_list(dir_path), dir_path))
        for file_i in files_sorted:
            sha.update(file_i.encode("utf-8"))

    if retun_str:
        return sha.hexdigest()
    else:
        return sha.digest()


def get_dirs_needed_for_files(files: list) -> list:
    dirs = set()
    for file_i in files:
        dir_i = os.path.dirname(file_i)
        dirs.add(dir_i)
    dirs = sorted(list(dirs))
    return dirs


def get_file_size(file: str) -> int:
    file = os.path.abspath(file)
    return os.path.getsize(file)
    # return os.stat(file).st_size


def get_dir_size(dir_path: str) -> int:
    files = get_files_list(os.path.abspath(dir_path))
    res = 0
    for file_i in files:
        res += get_file_size(file_i)
    return res


def str_to_bytes(s: str) -> bytes:
    a = list(map(int, s[1:len(s)-1].split(", ")))
    return bytes(a)


def bytes_to_str(bs: bytes) -> str:
    a = list(bs)  # list of ints
    res = ", ".join(map(str, a))
    return f"[{res}]"


def int_to_bytes(x: int) -> bytes:
    return x.to_bytes(length=(max(x.bit_length(), 1) + 7) // 8, byteorder='big')


def bytes_to_int(bs: bytes, set_auto_max_str_digits: bool = True) -> int:
    if set_auto_max_str_digits:
        sys.set_int_max_str_digits(0)
    res = int.from_bytes(bs, byteorder='big')
    return res


def is_int(x) -> bool:
    try:
        int(x)
        return True
    except ValueError:
        return False


def is_float(x) -> bool:
    try:
        float(x)
        return True
    except ValueError:
        return False


def utf8_to_bytes(s: str) -> bytes:
    return s.encode("utf-8")


def bytes_to_utf8(bs: bytes) -> str:
    return str(bs, "utf-8")


def gen_random_string(_lenght : int = 20, pool: str = None, seed: int | None = None) -> str:
    rnd = random.Random(seed) if seed is not None else random.Random(get_random_int(fast=True))
    if pool is None:
        pool = string.ascii_letters + string.digits
    s = "".join(rnd.choices(pool, k=_lenght))
    return s


def get_random_int(fast: bool = False) -> int:
    if fast:
        return random.randint(-2147483647, 2147483647)
    else:
        return bytes_to_int(os.urandom(8))


def exe_lowout(command: str, debug: bool = True, std_out_pipe: bool = False, std_err_pipe: bool = False) -> tuple:
    """
    Аргумент command - команда для выполнения в терминале. Например: "ls -lai ."
    Возвращает кортеж, где элементы:
        0 - строка stdout or None if std_out_pipe == False
        1 - строка stderr or None if std_err_pipe == False
        2 - returncode
    """
    if(debug):
        print(f"> {command}")
    
    if(std_out_pipe == True):
        if(std_err_pipe == True):
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # https://stackoverflow.com/questions/1180606/using-subprocess-popen-for-process-with-large-output
            out = process.stdout.read().decode("utf-8")
            err = process.stderr.read().decode("utf-8")
        else:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            out = process.stdout.read().decode("utf-8")
            err = None
    else:
        if(std_err_pipe == True):
            process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
            out = None
            err = process.stderr.read().decode("utf-8")
        else:
            process = subprocess.Popen(command, shell=True)
            out = None
            err = None
    errcode = process.returncode
    return (out, err, errcode)


def exe(command: str, debug: bool = True, std_out_fd = subprocess.PIPE, std_err_fd = subprocess.PIPE, stdin_msg: str = None) -> tuple:
    '''
    Аргумент command - команда для выполнения в терминале. Например: "ls -lai ."
    if(std_out_fd or std_err_fd) == subprocess.DEVNULL   |=>    No output enywhere
    if(std_out_fd or std_err_fd) == subprocess.PIPE      |=>    All output to return
    if(std_out_fd or std_err_fd) == open(path, "w")      |=>    All output to file path
    Возвращает кортеж, где элементы:
        0 - строка stdout
        1 - строка stderr
        2 - returncode
    '''
    _ENCODING = "utf-8"

    if(debug):
        #pout(f"> " + " ".join(command))
        if(stdin_msg != None):
            print(f"> {command}, with stdin=\"{stdin_msg}\"")
        else:
            print(f"> {command}")

    #proc = subprocess.run(command, shell=True, capture_output=True, input=stdin_msg.encode("utf-8"))
    if(stdin_msg == None):
        proc = subprocess.run(command, shell=True, stdout=std_out_fd, stderr=std_err_fd)
    else:
        proc = subprocess.run(command, shell=True, stdout=std_out_fd, stderr=std_err_fd, input=stdin_msg.encode("utf-8"))
    
    #return (proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8"))

    res_stdout = proc.stdout.decode("utf-8") if proc.stdout != None else None
    res_errout = proc.stderr.decode("utf-8") if proc.stderr != None else None
    return (res_stdout, res_errout, proc.returncode)


def create_random_file(path: str, min_bytes_count: int = 1027, max_bytes_count: int = 18388608, seed: int | None = None):
    if min_bytes_count > max_bytes_count:
        raise ValueError(f"min_bytes_count={min_bytes_count} cannot be greater than max_bytes_count={max_bytes_count}")
    if seed is None:
        r = random.Random()
    else:
        r = random.Random(seed)

    i, N = 0, random.randint(min_bytes_count, max_bytes_count)
    block_size = 8388608 # 8*1024*1024 == 8 MB
    with open(path, 'wb') as fd:
        while i < N:
            if i+block_size > N:
                count_to_write = N-i
            else:
                count_to_write = block_size
            fd.write(r.randbytes(count_to_write))
            i += count_to_write
        fd.flush()


def gen_rnd_dir_tree(root_path: str, seed: int | None = None,
             min_files_count: int = None, max_files_count: int = None,
             file_prob: float = 0.5, dir_prob: float = 0.2,
             file_size_min: int = 1027, file_size_max: int = 18388608) -> dict[str, int]:
    """
    Return dict with {file_name: file_size}
    """

    if not os.path.isdir(root_path):
        raise ValueError(f"\"{root_path}\" is not directory. ")
    if file_size_min > file_size_max:
        raise ValueError(f"file_size_min={file_size_min} cannot be greater than file_size_max={file_size_max}. ")
    if min_files_count is not None and max_files_count is not None and min_files_count > max_files_count:
        raise ValueError(f"min_files_count={min_files_count} cannot be greater than max_files_count={max_files_count}. ")

    if seed is None:
        seed = get_random_int()
    r = random.Random(seed)

    N_min, N_max = min_files_count, max_files_count
    curN = 0
    p, dp = file_prob, dir_prob
    res = {}

    dirs = [root_path]

    while True:
        if N_max is not None and curN >= N_max:
            break
        cur_dir = r.choice(dirs)
        if r.random() < p:
            seed += 1
            file_path = os.path.join(cur_dir, gen_random_string(r.randint(5, 15), seed=seed))
            res[file_path] = r.randint(file_size_min, file_size_max)
            curN += 1
        elif r.random() < dp:
            seed += 1
            new_dir = os.path.join(cur_dir, gen_random_string(r.randint(5, 15), seed=seed))
            dirs.append(new_dir)
        else:
            if N_min is not None and curN < N_min:
                continue
            break

    return res


def create_random_dir(dir_tree: dict, seed: int | None = None):
    """
    dir_tree is dict[str, int] from gen_rnd_dir_tree
    """
    if seed is None:
        seed = get_random_int()
    r = random.Random(seed)
    needed_dirs = get_dirs_needed_for_files([file_i for file_i in dir_tree])
    for needed_dir_i in needed_dirs:
        mkdir_with_p(needed_dir_i)
    for file_i in dir_tree:
        seed += 1
        create_random_file(file_i, dir_tree[file_i], dir_tree[file_i], seed=seed)


def get_current_function_name() -> str:
    """
    Return function name, where this function (get_function_name) was called.
    """
    """
    try:
        pass
    except Exception as e:
        error_text = f"{traceback.format_exc()}\n{e}"
    """
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    function_name = caller_frame.f_code.co_name
    return function_name
