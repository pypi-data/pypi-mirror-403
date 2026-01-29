import ctypes
from ctypes import wintypes
from ..ctypes.copy_struct_generic import copy_struct_generic
# 定义一些必要的Windows API常量
TH32CS_SNAPPROCESS = 0x00000002


# 定义PROCESSENTRY32结构体
class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", wintypes.PULONG),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.CHAR * 260),
    ]


# 创建CreateToolhelp32Snapshot和Process32First/Next的原型
CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
CreateToolhelp32Snapshot.restype = wintypes.HANDLE

Process32First = ctypes.windll.kernel32.Process32First
Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
Process32First.restype = wintypes.BOOL

Process32Next = ctypes.windll.kernel32.Process32Next
Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
Process32Next.restype = wintypes.BOOL


def get_process_list():
    # 获取进程快照
    snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pe32 = PROCESSENTRY32()
    pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)

    # 遍历进程
    processes = {}
    if Process32First(snapshot, ctypes.byref(pe32)):
        processes[pe32.szExeFile.decode()] = copy_struct_generic(pe32,PROCESSENTRY32)
        while Process32Next(snapshot, ctypes.byref(pe32)):
            # processes.append(pe32.szExeFile.decode())
            processes[pe32.szExeFile.decode()] = copy_struct_generic(pe32,PROCESSENTRY32)
            # print(pe32.th32ProcessID)
            # print(pe32.th32DefaultHeapID)
                # print(pe32.th32DefaultHeapID.contents)
            # 关闭句柄
    ctypes.windll.kernel32.CloseHandle(snapshot)
    return processes
def find_pid_by_name(name):
    '''
    根据名称获得进程id
    :param name:
    :return:
    '''
    process  = get_process_list()
    if process.get(name,None):
        return process.get(name,None).th32ProcessID
    else:return False
if __name__ == '__main__':
    print(find_pid_by_name('ShareMouse.exe'))