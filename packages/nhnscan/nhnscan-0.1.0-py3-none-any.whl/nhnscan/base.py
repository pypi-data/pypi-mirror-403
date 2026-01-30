import subprocess
import shutil
import sys


class ScannerBase:
    """모든 스캐너의 베이스 클래스"""
    
    def __init__(self, tool_name, display_name=None):
        self.tool_name = tool_name
        self.display_name = display_name or tool_name
        self.is_installed = self._check_installation()
    
    def _check_installation(self):
        """도구 설치 확인"""
        return shutil.which(self.tool_name) is not None
    
    def install_tool(self):
        """도구 자동 설치"""
        if sys.platform.startswith('win'):
            print(f"[!] Windows에서는 수동 설치가 필요합니다.")
            print(f"[*] {self.display_name} 설치 가이드:")
            self._print_windows_install_guide()
            return False
        elif sys.platform.startswith('linux'):
            return self._install_linux()
        elif sys.platform == 'darwin':
            return self._install_macos()
        else:
            print(f"[!] {sys.platform}에서는 자동 설치를 지원하지 않습니다.")
            return False
    
    def _print_windows_install_guide(self):
        """Windows 설치 가이드 (각 스캐너에서 오버라이드)"""
        print(f"[*] {self.tool_name} 설치 방법을 확인해주세요.")
    
    def _install_linux(self):
        """Linux 설치"""
        print(f"[*] {self.tool_name} 설치 중...")
        
        if shutil.which('apt-get'):
            cmd = ['sudo', 'apt-get', 'install', '-y', self.tool_name]
        elif shutil.which('yum'):
            cmd = ['sudo', 'yum', 'install', '-y', self.tool_name]
        elif shutil.which('dnf'):
            cmd = ['sudo', 'dnf', 'install', '-y', self.tool_name]
        else:
            print("[!] 지원하지 않는 패키지 매니저입니다.")
            return False
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[+] {self.tool_name} 설치 완료!")
            self.is_installed = True
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] 설치 실패: {e.stderr}")
            return False
        except PermissionError:
            print("[!] sudo 권한이 필요합니다.")
            return False
    
    def _install_macos(self):
        """macOS 설치 (Homebrew)"""
        if not shutil.which('brew'):
            print("[!] Homebrew가 설치되어 있지 않습니다.")
            print("[*] https://brew.sh 에서 Homebrew를 먼저 설치해주세요.")
            return False
        
        print(f"[*] {self.tool_name} 설치 중...")
        cmd = ['brew', 'install', self.tool_name]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"[+] {self.tool_name} 설치 완료!")
            self.is_installed = True
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] 설치 실패: {e}")
            return False
    
    def ensure_installed(self):
        """설치 확인 및 자동 설치 제안"""
        if self.is_installed:
            return True
        
        print(f"[!] {self.display_name}이(가) 설치되어 있지 않습니다.")
        
        if sys.platform.startswith('win'):
            print(f"[!] Windows에서는 수동 설치가 필요합니다.")
            self._print_windows_install_guide()
            return False
        
        response = input(f"[?] {self.display_name}을(를) 설치하시겠습니까? (y/n): ").strip().lower()
        
        if response == 'y':
            return self.install_tool()
        else:
            print(f"[!] {self.display_name} 없이는 스캔을 실행할 수 없습니다.")
            return False
    
    def run_command(self, cmd, timeout=300):
        """명령어 실행 공통 로직"""
        print(f"\n[실행] {' '.join(cmd)}\n")
        print("=" * 60)
        
        try:
            result = subprocess.run(cmd, timeout=timeout)
            return result.returncode == 0
                
        except subprocess.TimeoutExpired:
            print(f"[!] 스캔 시간 초과 ({timeout}초)")
            return False
        except KeyboardInterrupt:
            print("\n[!] 사용자에 의해 중단되었습니다.")
            return False
        except Exception as e:
            print(f"[!] 오류 발생: {e}")
            return False