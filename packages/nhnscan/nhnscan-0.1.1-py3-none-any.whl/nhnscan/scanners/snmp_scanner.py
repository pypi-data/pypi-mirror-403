import re
from nhnscan.base import ScannerBase


class SNMPScanner(ScannerBase):
    """SNMP 스캐너 (v2c)"""
    
    def __init__(self):
        super().__init__('snmpwalk', 'SNMP Tools')
    
    def _print_windows_install_guide(self):
        """Windows 설치 가이드"""
        print("=" * 60)
        print("1. https://sourceforge.net/projects/net-snmp/files/net-snmp%20binaries/5.5-binaries/net-snmp-5.5.0-2.x64.exe/download 방문")
        print("2. Windows 바이너리 다운로드")
        print("3. 설치 후 환경 변수 PATH에 추가")
        print("   (보통 C:\\usr\\bin)")
        print("4. 터미널 재시작")
        print("\n또는 WSL(Linux) 사용 권장:")
        print("  wsl --install")
        print("  sudo apt-get install snmp")
        print("=" * 60)
    
    def validate_ip(self, ip):
        """IP 주소 검증 (포트 포함 가능)"""
        # IP:PORT 형식 분리
        if ':' in ip:
            ip_part, port_part = ip.rsplit(':', 1)
            try:
                port = int(port_part)
                if not (1 <= port <= 65535):
                    return False
            except ValueError:
                return False
        else:
            ip_part = ip
        
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip_part):
            return False
        
        parts = ip_part.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    def scan(self, target_ip, community='public', port=None):
        """SNMP 스캔 실행 (v2c)"""
        if not self.ensure_installed():
            return False
        
        # 포트가 IP에 포함된 경우 분리
        if ':' in target_ip and port is None:
            ip_part, port_part = target_ip.rsplit(':', 1)
            target = target_ip
        elif port:
            ip_part = target_ip
            target = f"{target_ip}:{port}"
        else:
            ip_part = target_ip
            target = target_ip
        
        if not self.validate_ip(target):
            print("[!] 유효하지 않은 IP 주소입니다.")
            return False
        
        cmd = ['snmpwalk', '-v2c', '-c', community, target]
        success = self.run_command(cmd, timeout=60)
        
        if not success:
            print(f"[힌트] Community string이 '{community}'가 아니거나 SNMP가 비활성화되어 있을 수 있습니다.")
        
        return success