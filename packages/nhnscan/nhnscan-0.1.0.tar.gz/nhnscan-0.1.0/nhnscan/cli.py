import sys
import argparse
from nhnscan import __version__
from nhnscan.scanners import NmapScanner, SNMPScanner


def print_banner():
    """배너 출력"""
    banner = """
╔═══════════════════════════════════════╗
║     NHN Security Scanner v0.1.0       ║
║   Simple wrapper for nmap & snmpwalk  ║
╚═══════════════════════════════════════╝
"""
    print(banner)


def print_menu():
    """메뉴 출력"""
    menu = """
[1] Nmap 포트 스캔
[2] SNMP 스캔 (v2c)
[3] 종료
"""
    print(menu)


def interactive_nmap_scan():
    """대화형 Nmap 스캔"""
    scanner = NmapScanner()
    
    print("\n=== Nmap 포트 스캔 ===")
    target_ip = input("대상 IP (CIDR 가능): ").strip()
    ports = input("포트 (예: 22,80,443 또는 1-65535 또는 -): ").strip()
    
    if not target_ip or not ports:
        print("[!] IP와 포트를 모두 입력해주세요.")
        return
    
    scanner.scan(target_ip, ports)


def interactive_snmp_scan():
    """대화형 SNMP 스캔"""
    scanner = SNMPScanner()
    
    print("\n=== SNMP 스캔 (v2c) ===")
    target_ip = input("대상 IP[:PORT]: ").strip()
    
    if not target_ip:
        print("[!] IP를 입력해주세요.")
        return
    
    print("[*] Community string: public (기본값)")
    custom = input("[?] 다른 community string 사용? (Enter=public): ").strip()
    community = custom if custom else 'public'
    
    scanner.scan(target_ip, community)


def interactive_mode():
    """대화형 모드"""
    print_banner()
    
    while True:
        print_menu()
        
        try:
            choice = input("선택: ").strip()
            
            if choice == '1':
                interactive_nmap_scan()
            elif choice == '2':
                interactive_snmp_scan()
            elif choice == '3':
                print("\n[*] 종료합니다.")
                sys.exit(0)
            else:
                print("[!] 잘못된 선택입니다. 1-3 중 선택해주세요.")
        
        except KeyboardInterrupt:
            print("\n\n[*] 종료합니다.")
            sys.exit(0)
        except Exception as e:
            print(f"\n[!] 오류 발생: {e}")


def create_parser():
    """argparse 파서 생성"""
    parser = argparse.ArgumentParser(
        description='NHN Security Scanner - CLI wrapper for nmap and snmpwalk',
        epilog='옵션 없이 실행하면 대화형 모드로 전환됩니다.'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'nhnscan {__version__}'
    )
    
    # Nmap 옵션 그룹
    nmap_group = parser.add_argument_group('Nmap 스캔')
    nmap_group.add_argument(
        '-n', '--nmap',
        nargs=2,
        metavar=('IP', 'PORTS'),
        help='Nmap 포트 스캔 (예: -n 192.168.1.100 22,80,443)'
    )
    nmap_group.add_argument(
        '-ns', '--nmap-ssh',
        metavar='IP',
        help='Nmap SSH 스캔 (포트 22 자동)'
    )
    nmap_group.add_argument(
        '-nw', '--nmap-web',
        metavar='IP',
        help='Nmap 웹 스캔 (포트 80,443 자동)'
    )
    
    # SNMP 옵션 그룹
    snmp_group = parser.add_argument_group('SNMP 스캔')
    snmp_group.add_argument(
        '-s', '--snmp',
        metavar='IP[:PORT]',
        help='SNMP 스캔 (기본 포트: 161, community: public)'
    )
    snmp_group.add_argument(
        '-c', '--community',
        metavar='STRING',
        default='public',
        help='SNMP community string (기본값: public)'
    )
    snmp_group.add_argument(
        '-sp', '--snmp-port',
        metavar='PORT',
        type=int,
        help='SNMP 포트 (기본값: 161)'
    )
    
    return parser


def cli_mode(args):
    """CLI 모드 실행"""
    executed = False
    
    # Nmap 스캔
    if args.nmap:
        scanner = NmapScanner()
        ip, ports = args.nmap
        scanner.scan(ip, ports)
        executed = True
    
    elif args.nmap_ssh:
        scanner = NmapScanner()
        scanner.scan(args.nmap_ssh, '22')
        executed = True
    
    elif args.nmap_web:
        scanner = NmapScanner()
        scanner.scan(args.nmap_web, '80,443')
        executed = True
    
    # SNMP 스캔
    elif args.snmp:
        scanner = SNMPScanner()
        scanner.scan(args.snmp, args.community, args.snmp_port)
        executed = True
    
    return executed


def main():
    """메인 함수"""
    parser = create_parser()
    
    # 인자가 없으면 대화형 모드
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    args = parser.parse_args()
    
    # CLI 모드 실행
    executed = cli_mode(args)
    
    # 아무 작업도 안 했으면 도움말 표시
    if not executed:
        parser.print_help()


if __name__ == "__main__":
    main()