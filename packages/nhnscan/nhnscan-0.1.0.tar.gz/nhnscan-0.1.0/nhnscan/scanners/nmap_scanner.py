import re
from nhnscan.base import ScannerBase


class NmapScanner(ScannerBase):
    """Nmap 포트 스캐너"""
    
    def __init__(self):
        super().__init__('nmap', 'Nmap')
    
    def _print_windows_install_guide(self):
        """Windows 설치 가이드"""
        print("=" * 60)
        print("1. https://nmap.org/download.html 방문")
        print("2. 'Latest stable release self-installer' 다운로드")
        print("3. 설치 시 'Add Nmap to the system PATH' 체크")
        print("4. 설치 후 터미널 재시작")
        print("=" * 60)
    
    def validate_ip(self, ip):
        """IP 주소 검증"""
        if '/' in ip:
            ip_part = ip.split('/')[0]
            cidr_part = ip.split('/')[1]
            try:
                cidr = int(cidr_part)
                if not (0 <= cidr <= 32):
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
    
    def validate_ports(self, ports):
        """포트 검증"""
        if not ports.strip():
            return False
        
        if ports == '-':
            return True
        
        pattern = r'^[\d,\-]+$'
        if not re.match(pattern, ports):
            return False
        
        for part in ports.split(','):
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if not (1 <= start <= 65535 and 1 <= end <= 65535):
                        return False
                    if start > end:
                        return False
                except ValueError:
                    return False
            else:
                try:
                    port = int(part)
                    if not (1 <= port <= 65535):
                        return False
                except ValueError:
                    return False
        
        return True
    
    def scan(self, target_ip, ports):
        """Nmap 스캔 실행"""
        if not self.ensure_installed():
            return False
        
        if not self.validate_ip(target_ip):
            print("[!] 유효하지 않은 IP 주소입니다.")
            return False
        
        if not self.validate_ports(ports):
            print("[!] 유효하지 않은 포트 형식입니다.")
            print("[예시] 22,80,443 또는 1-1000 또는 - (전체)")
            return False
        
        if ports == '-':
            ports = '1-65535'
        
        cmd = ['nmap', '-sV', '-p', ports, target_ip]
        return self.run_command(cmd, timeout=300)
