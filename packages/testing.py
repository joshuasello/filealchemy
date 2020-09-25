import time


def exec_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        completion_time = str((end_time-start_time)*1000)
        print("Time to execute (milliseconds): "+completion_time+"\n")
        return result
    return wrapper
