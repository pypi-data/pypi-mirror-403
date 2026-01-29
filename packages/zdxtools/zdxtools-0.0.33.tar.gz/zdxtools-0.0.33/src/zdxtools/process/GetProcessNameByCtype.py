import ctypes
import ctypes.wintypes
import os


def get_process_name_by_pid_windows(pid):
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    MAX_PATH = 260

    psapi = ctypes.WinDLL('Psapi.dll')
    kernel32 = ctypes.WinDLL('kernel32.dll')

    hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not hProcess:
        return None

    image_file_name = ctypes.create_string_buffer(MAX_PATH)
    if psapi.GetModuleBaseNameA(hProcess, None, image_file_name, MAX_PATH) == 0:
        kernel32.CloseHandle(hProcess)
        return None
    kernel32.CloseHandle(hProcess)
    return image_file_name.value.decode('utf-8')

if __name__ == '__main__':

    # Example usage
    pid = os.getpid()  # Replace with the actual PID
    process_name = get_process_name_by_pid_windows(pid)
    if process_name:
        print(f"The name of the process with PID {pid} is {process_name}.")
    else:
        print(f"No process found with PID {pid}.")
