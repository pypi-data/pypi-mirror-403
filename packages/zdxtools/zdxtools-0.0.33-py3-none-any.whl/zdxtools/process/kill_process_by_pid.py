import platform
import subprocess
import traceback


def kill_process_by_pid(pid):
    commands = {
        'windows': [
            'taskkill /F /PID {}' # 用于结束进程的命令，{}会被替换成实际的PID
        ],
        'linux' or 'darwin': [
            # 注意：在Linux/Mac上应该是'lsof'或'lsof -i :{port}'，但'lsof'可能是个笔误，应为'lsoft'或'lsof'（如果已安装）
            'kill -9 {}' # 用于结束进程的命令，{}会被替换成实际的PID
        ]
    }
    # 获取操作系统类型
    os_type = platform.system().lower()
    # 查找进程ID
    try:
        # 注意：Windows上的处理需要额外注意，因为'netstat'的输出需要通过其他方式解析PID
        if os_type == 'windows':
            # 这里简化了处理，Windows上通常需要解析'netstat'的输出来找到PID
            # 这里我们假设你已经有了某种方式获取PID，或者你可以调用外部脚本来做这件事
            # 这里仅作为示例，我们直接跳过查找PID的步骤（实际中你需要实现它）
            # result,a = subprocess.run(commands['windows'][0])
            command = commands[os_type][0].format(pid)
            icmp_out = subprocess.Popen(command,encoding="gbk", shell=True,stdout=subprocess.PIPE)
            stdout, stderr = icmp_out.communicate(timeout=5)
        else:
            # Linux/Mac上，我们使用subprocess来调用'lsof'（注意：可能是'lsof'，但更常见的是'lsof -i :{port}'且需要'sudo'权限）
            # 注意：下面的命令可能需要sudo权限来执行
            command = commands[os_type][0].format(pid)
            icmp_out = subprocess.Popen(command,encoding="gbk", shell=True,stdout=subprocess.PIPE)
            stdout, stderr = icmp_out.communicate(timeout=5)
            # 结束进程
    except Exception as e:
        traceback.print_exc()
        print(f"发生错误: {e}")

if __name__ == '__main__':
    kill_process_by_pid(27108)