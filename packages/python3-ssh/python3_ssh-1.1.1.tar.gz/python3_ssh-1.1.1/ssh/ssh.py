import os
import time
import socket
import paramiko
import subprocess
import threading
from datetime import datetime
from func_timeout import func_set_timeout
from func_timeout.exceptions import FunctionTimedOut
import time
import functools
import logging
import traceback
import inspect
from pathlib import Path
from typing import Callable, Any
from typing import List, Dict, Any, Optional

log=logging.getLogger(__name__)
log.setLevel(logging.WARNING)
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | thread-%(threadName)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
log.addHandler(console_handler)



class ExecResult():
    def __init__(self, ip,port,exit_status_code, stdout="", stderr=""):
        self.__exit_status_code = exit_status_code
        self.__stdout = stdout
        self.__stderr = stderr
        if exit_status_code != 0:
            log.warning(f" {ip}:{port} | ExecResults: exit_status_code: {exit_status_code},stdout: {stdout}, stderr: {stderr}")
        else:
            log.info(f" {ip}:{port} | ExecResults: exit_status_code: {exit_status_code},stdout: {stdout}, stderr: {stderr}")

    @property
    def exit_status_code(self):
        return self.__exit_status_code

    @property
    def stdout(self):
        return self.__stdout

    @property
    def stderr(self):
        return self.__stderr

class _ThreadResult:
    def __init__(self):
        self.result = None
        self.error = None

class SSHClient(object):
    def __init__(self, ip="127.0.0.1", port=22, username="root", password="", connect_timeout=10,get_tty=False):
        log.info(f"{ip}:{port} | init SSHClient, ip:{ip}, port:{port}, username:{username},password:{password},connect_timeout:{connect_timeout},get_tty:{get_tty}")
        self.__ip = ip
        self.__port = port
        self.__username = username
        self.__password = password
        self.__connect_timeout = connect_timeout
        self.__ssh = None
        self.__sftp = None
        self.__get_tty = get_tty
        self.__connect()

    @property
    def ip(self):
        return self.__ip

    @property
    def port(self):
        return self.__port

    @property
    def is_sshable(self):
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.__ip,
                port=self.__port,
                username=self.__username,
                password=self.__password,
                look_for_keys=False,
                allow_agent=False,
                timeout=self.__connect_timeout
            )
            log.info(f"{self.__ip}:{self.__port} | create ssh session successfully.")
            return True
        except paramiko.ssh_exception.SSHException as e:
            log.warning(f"{self.__ip}:{self.__port} | cannot create ssh session, err msg is {str(e)}.")
            return False
        except Exception as e:
            log.warning(f"{self.__ip}:{self.__port} | server is not sshable.")
            return False
        finally:
            try:
                ssh.close()
            except Exception as e:
                pass

    def wait_for_sshable(self, timeout=60):
        log.info(f"{self.__ip}:{self.__port} | wait for sshable, timeout is {timeout}")
        count=0
        while True:
            count += 1
            log.info(f"{self.__ip}:{self.__port} | wait for sshable, count is {count}")
            if self.is_sshable:
                log.info(f"{self.__ip}:{self.__port} | sshable")
                return True
            if count > int(timeout/self.__connect_timeout):
                log.warning(f"{self.__ip}:{self.__port} | wait for sshable timeout.")
                return False
            time.sleep(self.__connect_timeout)

    def __connect(self):
        try:
            self.__ssh = paramiko.SSHClient()
            self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.__ssh.connect(
                self.__ip,
                port=self.__port,
                username=self.__username,
                password=self.__password,
                look_for_keys=False,
                allow_agent=False,
                timeout=self.__connect_timeout
            )
            log.info(f"{self.__ip}:{self.__port} | create ssh session successfully.")
            return True
        except socket.timeout as e:
            log.warning(f"{self.__ip}:{self.__port} | failed to ssh connect. server may not be sshable, please try again later...")
            return False
        except paramiko.ssh_exception.SSHException as e:
            log.warning(f"{self.__ip}:{self.__port} | failed to ssh connect. server may not be sshable, please try again later...")
        except Exception as e:
            log.warning(f"{self.__ip}:{self.__port} | failed to ssh connect. err msg is {str(e)}")
            return False

    def reconnect(self):
        log.info(f"{self.__ip}:{self.__port} | reconnect")
        self.close()
        return self.__connect()

    def close(self):
        try:
            self.__sftp.close()
        except:
            pass
        try:
            self.__ssh.close()
        except:
            pass

    def _exec(self, cmd, promt_response,timeout=60):
        log.info(f"{self.__ip}:{self.__port} | exec cmd:{cmd},promt_response: {promt_response},timeout:{timeout}")
        try:
            transport = self.__ssh.get_transport()
            if not transport or not transport.is_active():
                log.warning(f"{self.__ip}:{self.__port} | ssh connection is not active.")
                return ExecResult(self.__ip,self.__port,1, "", "SSH连接已关闭或不可用")

            if promt_response:
                channel = transport.open_session()
                # 设置终端尺寸
                channel.get_pty(width=80, height=100)
                channel.settimeout(3600)
                channel.exec_command(cmd)
                output = ""
                begin=datetime.now()
                stderr = ""
                while True:
                    end = datetime.now()
                    if (end-begin).total_seconds()>timeout:
                        output=""
                        stderr=f"timeout to run cmd.{cmd}"
                    if channel.recv_ready():
                        output_chunk  = channel.recv(1024).decode('utf-8', 'ignore')
                        output += output_chunk
                        print(output_chunk, end='')

                        # 检查输出是否包含预期的提示信息
                        for elem in promt_response:
                            prompt = elem["prompt"]
                            response = elem["response"]
                            if prompt in output:
                                # 发送相应的回答
                                channel.send(response)
                    if channel.recv_stderr_ready():
                        stderr_chunk =channel.recv_stderr(2024).decode('utf-8', 'ignore')
                        stderr += stderr_chunk
                        print(stderr_chunk, end='')
                    if channel.closed and not (channel.recv_ready() or channel.recv_stderr_ready()):
                        break
                return_code = channel.recv_exit_status()
                log.info(f"{self.__ip}:{self.__port} | exec cmd:{cmd},promt_response: {promt_response},timeout:{timeout},return_code:{return_code}")
                return ExecResult(self.__ip,self.__port,return_code, output, stderr)
            else:
                if self.__get_tty:
                    channel = transport.open_session()
                    # 设置终端尺寸
                    channel.get_pty(width=80, height=100)
                    channel.settimeout(3600)
                    stdin, stdout, stderr = self.__ssh.exec_command(
                        cmd,
                        get_pty=True,
                        timeout=timeout
                    )
                else:
                    stdin, stdout, stderr = self.__ssh.exec_command(
                        cmd,
                        get_pty=False,
                        timeout=timeout
                    )
                exit_status = stdout.channel.recv_exit_status()
                std_output = stdout.read().decode()
                std_err = stderr.read().decode()
                if exit_status == 0:
                    log.info(f"{self.__ip}:{self.__port} | exec cmd:{cmd},promt_response: {promt_response},timeout:{timeout},return_code:{exit_status},stdout:{std_output}")
                else:
                    log.warning(f"{self.__ip}:{self.__port} | exec cmd:{cmd},promt_response: {promt_response},timeout:{timeout},return_code:{exit_status},stdout:{std_output},stderr:{std_err}")
                return ExecResult(self.__ip,self.__port,exit_status, std_output, std_err)
        except Exception as e:
            log.warning(f"{self.__ip}:{self.__port} | exceptions occurs,err msg is {str(e)}")
            return ExecResult(self.__ip,self.__port,1, "", str(e))

    def exec(self, cmd, promt_response=[], timeout=60):
        log.info(f"{self.__ip}:{self.__port} | exec cmd:{cmd},promt_response: {promt_response},timeout:{timeout}")
        try:
            if not self.__ssh or not self.ssh_is_active():
                log.warning(f"{self.__ip}:{self.__port} | ssh transport is inactive, try reconnect...")
                if not self.reconnect():
                    log.error(f"{self.__ip}:{self.__port} | ssh reconnect failed, transport is not active.")
                    return ExecResult(self.__ip, self.__port, 1, "", "SSH连接已关闭或不可用，重连失败")

            thread_result = _ThreadResult()
            caller_thread_name = threading.current_thread().name
            def _thread_func():
                try:
                    threading.current_thread().name = caller_thread_name
                    thread_result.result = self._exec(cmd, promt_response, timeout)
                except Exception as inner_e:
                    thread_result.error = inner_e

            exec_thread = threading.Thread(target=_thread_func, daemon=True)
            exec_thread.start()

            exec_thread.join(timeout=timeout)

            if exec_thread.is_alive():
                log.error(f"{self.__ip}:{self.__port} | exec cmd timeout[{timeout}s], cmd: {cmd}")
                return ExecResult(self.__ip, self.__port, 1, "", f"执行命令超时，超时时间{timeout}秒")
            elif thread_result.error is not None:
                err_msg = str(thread_result.error)
                log.error(f"{self.__ip}:{self.__port} | exec cmd inner exceptions occurs, err msg: {err_msg}")
                return ExecResult(self.__ip, self.__port, 1, "", err_msg)
            else:
                return thread_result.result

        except Exception as e:
            err_msg = str(e)
            log.error(f"{self.__ip}:{self.__port} | exec func exceptions occurs, err msg: {err_msg}")
            return ExecResult(self.__ip, self.__port, 1, "", err_msg)

    def _scp_to_remote(self, local_path, remote_path):
        log.info(f"{self.__ip}:{self.__port} | 从本地拷贝文件到远端服务器: {local_path} -> {remote_path}")
        local_path = Path(local_path).resolve()
        remote_path = Path(remote_path)

        def sftp_mkdir_recursive(sftp, remote_dir):
            dir_parts = str(remote_dir).split(os.sep)
            current_dir = ""
            for part in dir_parts:
                if not part:
                    current_dir = os.sep if current_dir == "" else current_dir + os.sep
                    continue
                current_dir = os.path.join(current_dir, part)
                try:
                    sftp.chdir(current_dir)
                except OSError:
                    sftp.mkdir(current_dir)
                    sftp.chdir(current_dir)

        def sftp_copy_dir(sftp, local_dir, remote_dir):
            log.info(f" {self.__ip}:{self.__port} | 递归拷贝目录: {local_dir} -> {remote_dir}")
            sftp_mkdir_recursive(sftp, remote_dir)
            for entry in os.scandir(local_dir):
                local_entry_path = Path(entry.path)
                remote_entry_path = remote_dir / local_entry_path.name
                if entry.is_file():
                    try:
                        sftp.put(str(local_entry_path), str(remote_entry_path))
                        log.info(f" {self.__ip}:{self.__port} | 已拷贝文件: {local_entry_path} -> {remote_entry_path}")
                    except Exception as e:
                        log.error(
                            f" {self.__ip}:{self.__port} | 文件拷贝失败: {local_entry_path} -> {remote_entry_path}, 错误: {str(e)}")
                        return False
                elif entry.is_dir():
                    if not sftp_copy_dir(sftp, local_entry_path, remote_entry_path):
                        return False
            return True

        if local_path.is_file():
            remote_parent = remote_path.parent
            sftp_mkdir_recursive(self.__sftp, remote_parent)
            try:
                self.__sftp.put(str(local_path), str(remote_path))
            except Exception as e:
                log.error(f" {self.__ip}:{self.__port} | 文件上传失败: {local_path} -> {remote_path}, 错误: {str(e)}")
                return False
            try:
                self.__sftp.stat(str(remote_path))
            except OSError:
                log.warning(f" {self.__ip}:{self.__port} | 文件拷贝失败: 远端未找到 {remote_path}")
                return False
            log.info(f" {self.__ip}:{self.__port} | 文件拷贝完成: {local_path} -> {remote_path}")
            return True

        if local_path.is_dir():
            try:
                remote_stat = self.__sftp.stat(str(remote_path))
                if not S_ISDIR(remote_stat.st_mode):
                    log.warning(f" {self.__ip}:{self.__port} | 远端存在同名文件，删除后创建目录: {remote_path}")
                    self.__sftp.remove(str(remote_path))
            except OSError:
                pass

            if sftp_copy_dir(self.__sftp, local_path, remote_path):
                log.info(f" {self.__ip}:{self.__port} | 目录拷贝完成: {local_path} -> {remote_path}")
                return True
            else:
                log.error(f" {self.__ip}:{self.__port} | 目录拷贝失败: {local_path} -> {remote_path}")
                return False

        log.error(f" {self.__ip}:{self.__port} | 本地路径无效: {local_path}（不是文件或文件夹）")
        return False

    def scp_to_remote(self, local_path, remote_path):
        log.info(f" {self.__ip}:{self.__port} | SCP操作: 本地 {local_path} -> 远端 {remote_path}")
        try:
            if not self.__ssh:
                if not self.reconnect():
                    log.error(f"{self.__ip}:{self.__port} | SSH 通道未激活.")
                    return False
            if not self.__sftp:
                self.__sftp = self.__ssh.open_sftp()

            local_path = Path(local_path)
            remote_path = Path(remote_path)
            return self._scp_to_remote(local_path, remote_path)
        except Exception as e:
            log.error(f" {self.__ip}:{self.__port} | SCP操作失败: {local_path} -> {remote_path}, 错误: {str(e)}")
            return False

    def _scp_file_to_local(self, remote_path, local_path):
        if os.path.isfile(local_path):
            log.info(f" {self.__ip}:{self.__port} | 删除本地文件: {local_path}")
            subprocess.run(['rm', '-rf', local_path], capture_output=True, text=True)
        for i in range(3):
            try:
                self.__sftp.get(remote_path, local_path)
                log.info(f" {self.__ip}:{self.__port} | 文件拷贝完成: {remote_path} -> {local_path}")
                return True
            except OSError as e:
                log.warning(
                    f" {self.__ip}:{self.__port} | 文件拷贝失败: {remote_path} -> {local_path}, 错误: {str(e)}")
                self.reconnect()
                self.__sftp = self.__ssh.open_sftp()
            except Exception as e:
                log.warning(
                    f" {self.__ip}:{self.__port} | 文件拷贝失败: {remote_path} -> {local_path}, 错误: {str(e)}")
        else:
            log.error(f" {self.__ip}:{self.__port} | 文件拷贝失败: {remote_path} -> {local_path}")
            return False


    def ssh_is_active(self):
        try:
            if self.__ssh:
                return self.__ssh.get_transport().is_active()
            else:
                log.info(f" {self.__ip}:{self.__port} | SSH连接未激活")
                return False
        except Exception:
            log.warning(f" {self.__ip}:{self.__port} | SSH连接异常")
            return False

    def sftp_is_active(self):
        if not self.__ssh.get_transport() or not self.__ssh.get_transport().is_active():
            log.warning(f" {self.__ip}:{self.__port} | SSH连接未激活")
            return False
        if not self.__sftp:
            log.info(f" {self.__ip}:{self.__port} | SFTP连接未激活")
            return False
        try:
            self.__sftp.getcwd()
            log.info(f" {self.__ip}:{self.__port} | SFTP连接已激活")
            return True
        except (paramiko.ssh_exception.SSHException, IOError, OSError,Exception) as e:
            log.warning(f" {self.__ip}:{self.__port} | SFTP连接异常: {str(e)}")
            return False

    def scp_file_to_local(self, remote_path, local_path):
        log.info(f"{self.__ip}:{self.__port} | SCP文件开始: {remote_path} -> {local_path}")
        try:
            if not self.ssh_is_active():
                if not self.reconnect():
                    log.error(f"{self.__ip}:{self.__port} | SSH连接未激活且重连失败")
                    return False
            if not self.sftp_is_active():
                self.__sftp = self.__ssh.open_sftp()
            return self._scp_file_to_local(remote_path, local_path)
        except Exception:
            log.error(f"{self.__ip}:{self.__port} | SCP文件 {remote_path} -> {local_path} 异常")
            return False

    def __del__(self):
        self.close()
