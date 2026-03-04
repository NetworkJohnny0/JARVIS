#!/usr/bin/env python3
"""
JARVIS Self-Repair Agent
Monitors system health and automatically repairs issues
"""

import os
import sys
import json
import time
import socket
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    def __init__(self):
        self.thresholds = {
            'cpu': 80.0,
            'memory': 85.0,
            'disk': 90.0
        }
        
    def get_cpu_usage(self) -> float:
        try:
            with open('/proc/loadavg') as f:
                load = float(f.read().split()[0])
            return min(load * 25, 100)
        except:
            return 0.0
            
    def get_memory_usage(self) -> float:
        try:
            with open('/proc/meminfo') as f:
                lines = f.readlines()
            mem = {}
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].rstrip(':')] = int(parts[1])
            total = mem.get('MemTotal', 1)
            free = mem.get('MemFree', 0) + mem.get('Buffers', 0) + mem.get('Cached', 0)
            return ((total - free) / total) * 100
        except:
            return 0.0
            
    def get_disk_usage(self, path='/') -> float:
        try:
            stat = os.statvfs(path)
            return ((stat.f_blocks - stat.f_bfree) / stat.f_blocks) * 100
        except:
            return 0.0
            
    def check_critical_services(self) -> List[str]:
        critical = ['sshd', 'docker', 'systemd', 'NetworkManager']
        issues = []
        for service in critical:
            result = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True, text=True
            )
            if result.returncode != 0 and 'inactive' in result.stdout:
                issues.append(f"Service {service} is not running")
        return issues
        
    def get_health_report(self) -> Dict:
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'services': self.check_critical_services(),
            'network': self.check_network()
        }
        
    def check_network(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            return False

class AutoRepair:
    def __init__(self):
        self.repaired_issues = []
        self.thresholds = {'cpu': 80.0, 'memory': 85.0, 'disk': 90.0}
        
    def fix_high_cpu(self) -> bool:
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')[1:]
            processes = []
            for line in lines[:10]:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        cpu = float(parts[2])
                        if cpu > 50:
                            processes.append((parts[10], cpu, parts[1]))
                    except:
                        pass
            if processes:
                logger.warning(f"High CPU: {processes[:3]}")
            return True
        except Exception as e:
            logger.error(f"Failed to fix high CPU: {e}")
            return False
            
    def fix_high_memory(self) -> bool:
        try:
            subprocess.run(['sync'], capture_output=True)
            subprocess.run('echo 3 > /proc/sys/vm/drop_caches', shell=True, capture_output=True)
            logger.info("Memory caches cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to fix memory: {e}")
            return False
            
    def fix_disk_space(self) -> bool:
        try:
            temp_dirs = ['/tmp', '/var/tmp']
            cleaned = 0
            for d in temp_dirs:
                if os.path.exists(d):
                    for root, dirs, files in os.walk(d):
                        for f in files:
                            fp = os.path.join(root, f)
                            try:
                                age = time.time() - os.stat(fp).st_mtime
                                if age > 86400:
                                    os.remove(fp)
                                    cleaned += 1
                            except:
                                pass
            logger.info(f"Cleaned {cleaned} old temp files")
            return True
        except Exception as e:
            logger.error(f"Failed to fix disk: {e}")
            return False
            
    def fix_network(self) -> bool:
        try:
            subprocess.run(['systemctl', 'restart', 'NetworkManager'], capture_output=True)
            logger.info("Network restart attempted")
            return True
        except Exception as e:
            logger.error(f"Failed to fix network: {e}")
            return False
            
    def auto_repair(self, health: Dict) -> List[str]:
        fixes = []
        
        if health['cpu'] > self.thresholds['cpu']:
            if self.fix_high_cpu():
                fixes.append("High CPU - identified heavy processes")
                
        if health['memory'] > self.thresholds['memory']:
            if self.fix_high_memory():
                fixes.append("High Memory - cleared caches")
                
        if health['disk'] > self.thresholds['disk']:
            if self.fix_disk_space():
                fixes.append("High Disk - cleaned temp files")
                
        if not health['network']:
            if self.fix_network():
                fixes.append("Network - restarted network service")
                
        self.repaired_issues.extend(fixes)
        return fixes

class JARVISAgent:
    def __init__(self):
        self.health_monitor = SystemHealthMonitor()
        self.auto_repair = AutoRepair()
        self.monitoring = False
        self.check_interval = 60
        
    def start_monitoring(self):
        self.monitoring = True
        logger.info("JARVIS Agent monitoring started")
        
        while self.monitoring:
            try:
                health = self.health_monitor.get_health_report()
                logger.info(f"Health: CPU={health['cpu']:.1f}% MEM={health['memory']:.1f}% DISK={health['disk']:.1f}%")
                
                fixes = self.auto_repair.auto_repair(health)
                for fix in fixes:
                    logger.info(f"Auto-repair: {fix}")
                    
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
            time.sleep(self.check_interval)
            
    def stop_monitoring(self):
        self.monitoring = False
        
    def get_status(self) -> Dict:
        health = self.health_monitor.get_health_report()
        return {
            'health': health,
            'repairs': self.auto_repair.repaired_issues[-10:],
            'monitoring': self.monitoring
        }

if __name__ == '__main__':
    Path('/var/lib/jarvis/logs').mkdir(parents=True, exist_ok=True)
    
    agent = JARVISAgent()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        agent.start_monitoring()
    else:
        print("= - jarvis-agent.py:224" * 50)
        print("JARVIS SelfRepair Agent v1.0 - jarvis-agent.py:225")
        print("= - jarvis-agent.py:226" * 50)
        health = agent.health_monitor.get_health_report()
        print(f"\nSystem Health: - jarvis-agent.py:228")
        print(f"CPU:     {health['cpu']:.1f}% - jarvis-agent.py:229")
        print(f"Memory:  {health['memory']:.1f}% - jarvis-agent.py:230")
        print(f"Disk:    {health['disk']:.1f}% - jarvis-agent.py:231")
        print(f"Network: {'ONLINE' if health['network'] else 'OFFLINE'} - jarvis-agent.py:232")
        
        if health['services']:
            print(f"\nService Issues: - jarvis-agent.py:235")
            for s in health['services']:
                print(f"{s} - jarvis-agent.py:237")
        else:
            print(f"\nAll critical services: OK - jarvis-agent.py:239")
