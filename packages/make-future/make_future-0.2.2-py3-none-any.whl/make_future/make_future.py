import concurrent.futures
import secrets
import traceback
import multiprocessing as mp

CHUNK_SIZE = 10000

class PoolTimeOut(Exception):
    pass

def print_progress(cnt, lmt, err):
    percentage = 0
    if lmt>0:
        percentage = 100*cnt/lmt
    percentage = round(percentage, 1)

    if cnt > 0:
        percentage_error = 100*err/cnt
        percentage_error = round(percentage_error, 1)
    else:
        percentage_error = 0.0
    print(f'\33[2K{percentage}% - {cnt}/{lmt} ({err} errors {percentage_error}%)\r', end="")

def make_future(job_function, input_data, num_processes=None, debug=False):

    if debug:
        res = []
        for item in input_data:
            res.append(job_function(item))
        return res
    result_array = []
    total_input = len(input_data)
    already_computed = 0
    def split_list(lst, chunk_size):
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    chunks = split_list(input_data, CHUNK_SIZE)


    i = 0
    nb_error = 0
    for l in chunks:
        output_internal = internal_make_future(job_function, l, num_processes, already_computed, total_input, nb_error)
        nb_error += output_internal[0]
        result_array += output_internal[1]
        already_computed += len(l)
        i +=1

    return result_array

def internal_make_future(job_function, input_data, num_processes=None, i=0, total_input=1, err=0):
    err = err
    lmt = total_input
    print_progress(i, lmt, err)

    executor = concurrent.futures.ProcessPoolExecutor(num_processes, mp_context=mp.get_context('fork'))

    futures = []
    mapping = {}

    for c, v in enumerate(input_data):
        future = executor.submit(job_function, v)
        futures.append(future)
        mapping[future] = v

    result_array = []

    for future in concurrent.futures.as_completed(futures, ):
        i += 1
        try:
            result_array.append(future.result())
        except Exception as e:
            err += 1

            uniq = secrets.token_hex(15)
            file_name = f'/tmp/{uniq}.log'

            with open(file_name, 'w') as fp:
                fp.write(traceback.format_exc())

            print(f'{str(mapping[future])} -> {type(future.exception()).__name__} -> {file_name}')

        print_progress(i, lmt, err)
    return [err, result_array]