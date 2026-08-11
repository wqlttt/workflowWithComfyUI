import paramiko
import socket
import threading
from paramiko import SSHClient, AutoAddPolicy


class SSHTunnel:
    def __init__(self):
        self._client: SSHClient | None = None
        self._forward_thread: threading.Thread | None = None
        self._running = False
        self._local_port: int | None = None

    @property
    def is_connected(self) -> bool:
        return self._running and self._client is not None

    @property
    def local_port(self) -> int | None:
        return self._local_port

    def connect(self, host: str, port: int, username: str,
                password: str = None, key_file: str = None,
                remote_port: int = 8188, local_port: int = 8189):
        """建立 SSH 连接并启动端口转发"""
        if self._running:
            self.disconnect()

        self._client = SSHClient()
        self._client.set_missing_host_key_policy(AutoAddPolicy())

        try:
            if key_file:
                self._client.connect(
                    hostname=host, port=port, username=username,
                    key_filename=key_file, timeout=10
                )
            else:
                self._client.connect(
                    hostname=host, port=port, username=username,
                    password=password, timeout=10
                )
        except Exception as e:
            self._client = None
            raise RuntimeError(f"SSH 连接失败: {e}")

        self._local_port = local_port
        self._running = True
        self._forward_thread = threading.Thread(
            target=self._port_forward,
            args=(remote_port, local_port),
            daemon=True,
        )
        self._forward_thread.start()
        return local_port

    def _port_forward(self, remote_port: int, local_port: int):
        """端口转发线程"""
        transport = self._client.get_transport()
        if not transport:
            self._running = False
            return

        try:
            transport.request_port_forward("", local_port)
        except Exception:
            # 端口已被占用，尝试使用系统自动分配的端口
            pass

        while self._running:
            try:
                chan = transport.accept(1)
                if chan is None:
                    continue

                remote_sock = socket.create_connection(("localhost", remote_port))
                threading.Thread(
                    target=self._forward_data,
                    args=(chan, remote_sock),
                    daemon=True,
                ).start()
                threading.Thread(
                    target=self._forward_data,
                    args=(remote_sock, chan),
                    daemon=True,
                ).start()

            except Exception:
                if self._running:
                    continue
                break

    @staticmethod
    def _forward_data(src, dst):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                dst.send(data)
        except Exception:
            pass
        finally:
            try:
                src.close()
            except Exception:
                pass
            try:
                dst.close()
            except Exception:
                pass

    def exec_command(self, cmd: str) -> dict:
        """通过 SSH 执行命令并返回结果"""
        if not self._client:
            return {"ok": False, "error": "未连接"}

        try:
            stdin, stdout, stderr = self._client.exec_command(cmd, timeout=10)
            return {
                "ok": True,
                "stdout": stdout.read().decode("utf-8", errors="replace"),
                "stderr": stderr.read().decode("utf-8", errors="replace"),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_gpu_status(self) -> dict:
        """获取 GPU 状态"""
        result = self.exec_command(
            "nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,"
            "memory.used,memory.total,power.draw --format=csv,noheader,nounits"
        )
        if not result["ok"]:
            return {"ok": False, "error": result.get("error", "命令执行失败")}

        gpus = []
        for line in result["stdout"].strip().split("\n"):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "temp": float(parts[2]) if parts[2] else 0,
                    "gpu_util": int(parts[3]) if parts[3] else 0,
                    "mem_used": int(parts[4]) if parts[4] else 0,
                    "mem_total": int(parts[5]) if parts[5] else 0,
                    "power": float(parts[6]) if len(parts) > 6 and parts[6] else 0,
                })
        return {"ok": True, "gpus": gpus}

    def disconnect(self):
        self._running = False
        if self._forward_thread:
            self._forward_thread.join(timeout=2)
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._local_port = None


# 全局单例
tunnel = SSHTunnel()
