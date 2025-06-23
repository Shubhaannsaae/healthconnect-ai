#!/usr/bin/env python3

"""
HealthConnect AI - Log Analysis Script
Production-grade log analysis and monitoring
Version: 1.0.0
Last Updated: 2025-06-20
"""

import re
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sys
from pathlib import Path
from collections import defaultdict, Counter
import gzip

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    from wordcloud import WordCloud
except ImportError as e:
    print(f"Warning: Optional dependencies missing: {e}")
    print("Install with: pip install matplotlib pandas numpy wordcloud")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scripts/logs/log-analyzer.log')
    ]
)
logger = logging.getLogger(__name__)

class LogAnalyzer:
    """Production-grade log analysis for HealthConnect AI platform"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_patterns = self.setup_log_patterns()
        self.analysis_results = {}
        
    def setup_log_patterns(self) -> Dict[str, re.Pattern]:
        """Setup regex patterns for log parsing"""
        patterns = {
            # Common log formats
            'apache_combined': re.compile(
                r'(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
                r'"(?P<method>\S+) (?P<url>\S+) (?P<protocol>\S+)" '
                r'(?P<status>\d+) (?P<size>\S+) "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"'
            ),
            'nginx_access': re.compile(
                r'(?P<ip>\S+) - \S+ \[(?P<timestamp>[^\]]+)\] '
                r'"(?P<method>\S+) (?P<url>\S+) (?P<protocol>\S+)" '
                r'(?P<status>\d+) (?P<size>\d+) "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)" '
                r'"(?P<forwarded>[^"]*)" (?P<response_time>\S+)'
            ),
            'application_log': re.compile(
                r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\s]*) '
                r'- (?P<level>\w+) - (?P<message>.*)'
            ),
            'django_log': re.compile(
                r'\[(?P<timestamp>[^\]]+)\] (?P<level>\w+) (?P<logger>\S+): (?P<message>.*)'
            ),
            'error_log': re.compile(
                r'(?P<timestamp>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) '
                r'\[(?P<level>\w+)\] (?P<pid>\d+)#(?P<tid>\d+): (?P<message>.*)'
            ),
            # Health-specific patterns
            'health_alert': re.compile(
                r'(?P<timestamp>\S+) - (?P<level>\w+) - HEALTH_ALERT: '
                r'Patient: (?P<patient_id>\S+), Alert: (?P<alert_type>\S+), '
                r'Severity: (?P<severity>\w+), Message: (?P<message>.*)'
            ),
            'device_data': re.compile(
                r'(?P<timestamp>\S+) - (?P<level>\w+) - DEVICE_DATA: '
                r'Device: (?P<device_id>\S+), Type: (?P<device_type>\S+), '
                r'Data: (?P<data>.*)'
            ),
            'consultation': re.compile(
                r'(?P<timestamp>\S+) - (?P<level>\w+) - CONSULTATION: '
                r'Session: (?P<session_id>\S+), Patient: (?P<patient_id>\S+), '
                r'Provider: (?P<provider_id>\S+), Action: (?P<action>\S+)'
            ),
            'api_request': re.compile(
                r'(?P<timestamp>\S+) - (?P<level>\w+) - API_REQUEST: '
                r'Method: (?P<method>\S+), Endpoint: (?P<endpoint>\S+), '
                r'Status: (?P<status>\d+), Duration: (?P<duration>\d+)ms, '
                r'User: (?P<user_id>\S+)'
            )
        }
        
        return patterns
    
    def parse_log_line(self, line: str, log_type: str = 'auto') -> Optional[Dict[str, Any]]:
        """Parse a single log line"""
        line = line.strip()
        if not line:
            return None
        
        # Try to determine log type automatically
        if log_type == 'auto':
            for pattern_name, pattern in self.log_patterns.items():
                match = pattern.match(line)
                if match:
                    result = match.groupdict()
                    result['log_type'] = pattern_name
                    result['raw_line'] = line
                    return result
            
            # If no pattern matches, return basic structure
            return {
                'log_type': 'unknown',
                'raw_line': line,
                'timestamp': None,
                'level': 'UNKNOWN',
                'message': line
            }
        else:
            # Use specific pattern
            if log_type in self.log_patterns:
                pattern = self.log_patterns[log_type]
                match = pattern.match(line)
                if match:
                    result = match.groupdict()
                    result['log_type'] = log_type
                    result['raw_line'] = line
                    return result
        
        return None
    
    def read_log_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read and parse log file"""
        log_entries = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Log file not found: {file_path}")
            return log_entries
        
        try:
            # Handle compressed files
            if file_path.suffix == '.gz':
                open_func = gzip.open
                mode = 'rt'
            else:
                open_func = open
                mode = 'r'
            
            with open_func(file_path, mode, encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        parsed = self.parse_log_line(line)
                        if parsed:
                            parsed['line_number'] = line_num
                            parsed['file_path'] = str(file_path)
                            log_entries.append(parsed)
                    except Exception as e:
                        logger.warning(f"Error parsing line {line_num} in {file_path}: {e}")
            
            logger.info(f"Parsed {len(log_entries)} log entries from {file_path}")
            
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")
        
        return log_entries
    
    def analyze_error_patterns(self, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns in logs"""
        errors = [entry for entry in log_entries if entry.get('level') in ['ERROR', 'CRITICAL', 'FATAL']]
        warnings = [entry for entry in log_entries if entry.get('level') == 'WARNING']
        
        # Error frequency by type
        error_messages = [entry.get('message', '') for entry in errors]
        error_patterns = Counter()
        
        # Common error patterns
        common_patterns = [
            (r'Connection.*refused', 'Connection Refused'),
            (r'Timeout.*expired', 'Timeout'),
            (r'Permission.*denied', 'Permission Denied'),
            (r'File.*not found', 'File Not Found'),
            (r'Database.*error', 'Database Error'),
            (r'Authentication.*failed', 'Authentication Failed'),
            (r'Memory.*error', 'Memory Error'),
            (r'Invalid.*request', 'Invalid Request'),
            (r'Rate.*limit.*exceeded', 'Rate Limit Exceeded'),
            (r'Service.*unavailable', 'Service Unavailable')
        ]
        
        for message in error_messages:
            categorized = False
            for pattern, category in common_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    error_patterns[category] += 1
                    categorized = True
                    break
            
            if not categorized:
                error_patterns['Other'] += 1
        
        # Error timeline
        error_timeline = defaultdict(int)
        for entry in errors:
            if entry.get('timestamp'):
                try:
                    # Parse timestamp (handle different formats)
                    timestamp_str = entry['timestamp']
                    # Simplified parsing - in production, use proper datetime parsing
                    hour = timestamp_str.split('T')[1][:2] if 'T' in timestamp_str else '00'
                    error_timeline[hour] += 1
                except:
                    error_timeline['unknown'] += 1
        
        return {
            'total_errors': len(errors),
            'total_warnings': len(warnings),
            'error_patterns': dict(error_patterns.most_common(10)),
            'error_timeline': dict(error_timeline),
            'error_rate': len(errors) / len(log_entries) * 100 if log_entries else 0,
            'recent_errors': errors[-10:] if errors else []
        }
    
    def analyze_performance_metrics(self, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance metrics from logs"""
        api_requests = [entry for entry in log_entries if entry.get('log_type') == 'api_request']
        
        if not api_requests:
            return {'message': 'No API request logs found'}
        
        # Response time analysis
        response_times = []
        status_codes = Counter()
        endpoints = Counter()
        methods = Counter()
        
        for request in api_requests:
            try:
                duration = int(request.get('duration', 0))
                response_times.append(duration)
                
                status_codes[request.get('status', 'unknown')] += 1
                endpoints[request.get('endpoint', 'unknown')] += 1
                methods[request.get('method', 'unknown')] += 1
            except ValueError:
                continue
        
        # Calculate percentiles
        if response_times:
            response_times.sort()
            p50 = np.percentile(response_times, 50)
            p95 = np.percentile(response_times, 95)
            p99 = np.percentile(response_times, 99)
            avg_response_time = np.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            p50 = p95 = p99 = avg_response_time = max_response_time = min_response_time = 0
        
        # Error rate by status code
        total_requests = len(api_requests)
        error_requests = sum(count for status, count in status_codes.items() 
                           if str(status).startswith(('4', '5')))
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'avg_response_time': round(avg_response_time, 2),
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'p50_response_time': round(p50, 2),
            'p95_response_time': round(p95, 2),
            'p99_response_time': round(p99, 2),
            'error_rate': round(error_rate, 2),
            'status_code_distribution': dict(status_codes.most_common()),
            'top_endpoints': dict(endpoints.most_common(10)),
            'method_distribution': dict(methods),
            'slow_requests': [req for req in api_requests 
                            if int(req.get('duration', 0)) > 5000]  # > 5 seconds
        }
    
    def analyze_health_alerts(self, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze health alerts from logs"""
        health_alerts = [entry for entry in log_entries if entry.get('log_type') == 'health_alert']
        
        if not health_alerts:
            return {'message': 'No health alert logs found'}
        
        # Alert analysis
        alert_types = Counter()
        severity_distribution = Counter()
        patient_alerts = Counter()
        
        for alert in health_alerts:
            alert_types[alert.get('alert_type', 'unknown')] += 1
            severity_distribution[alert.get('severity', 'unknown')] += 1
            patient_alerts[alert.get('patient_id', 'unknown')] += 1
        
        # Critical alerts
        critical_alerts = [alert for alert in health_alerts 
                          if alert.get('severity') == 'CRITICAL']
        
        return {
            'total_alerts': len(health_alerts),
            'critical_alerts': len(critical_alerts),
            'alert_types': dict(alert_types.most_common(10)),
            'severity_distribution': dict(severity_distribution),
            'patients_with_most_alerts': dict(patient_alerts.most_common(10)),
            'recent_critical_alerts': critical_alerts[-5:] if critical_alerts else []
        }
    
    def analyze_device_activity(self, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze device activity from logs"""
        device_logs = [entry for entry in log_entries if entry.get('log_type') == 'device_data']
        
        if not device_logs:
            return {'message': 'No device activity logs found'}
        
        # Device analysis
        device_activity = Counter()
        device_types = Counter()
        
        for log in device_logs:
            device_activity[log.get('device_id', 'unknown')] += 1
            device_types[log.get('device_type', 'unknown')] += 1
        
        return {
            'total_device_events': len(device_logs),
            'active_devices': len(device_activity),
            'most_active_devices': dict(device_activity.most_common(10)),
            'device_type_distribution': dict(device_types),
            'devices_by_type': len(device_types)
        }
    
    def generate_visualizations(self, analysis_results: Dict[str, Any], output_dir: str):
        """Generate visualization charts"""
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
        except ImportError:
            logger.warning("Matplotlib/Pandas not available, skipping visualizations")
            return
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Error patterns chart
        if 'error_analysis' in analysis_results:
            error_data = analysis_results['error_analysis']
            if error_data.get('error_patterns'):
                plt.figure(figsize=(12, 6))
                patterns = list(error_data['error_patterns'].keys())
                counts = list(error_data['error_patterns'].values())
                
                plt.bar(patterns, counts, alpha=0.8, color='red')
                plt.title('Error Patterns Distribution')
                plt.xlabel('Error Type')
                plt.ylabel('Count')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(output_path / 'error_patterns.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        # Performance metrics chart
        if 'performance_analysis' in analysis_results:
            perf_data = analysis_results['performance_analysis']
            if isinstance(perf_data, dict) and 'status_code_distribution' in perf_data:
                plt.figure(figsize=(10, 6))
                status_codes = list(perf_data['status_code_distribution'].keys())
                counts = list(perf_data['status_code_distribution'].values())
                
                colors = ['green' if str(code).startswith('2') else 
                         'yellow' if str(code).startswith('3') else
                         'orange' if str(code).startswith('4') else 'red'
                         for code in status_codes]
                
                plt.bar(status_codes, counts, alpha=0.8, color=colors)
                plt.title('HTTP Status Code Distribution')
                plt.xlabel('Status Code')
                plt.ylabel('Count')
                plt.tight_layout()
                plt.savefig(output_path / 'status_codes.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        # Health alerts severity chart
        if 'health_analysis' in analysis_results:
            health_data = analysis_results['health_analysis']
            if isinstance(health_data, dict) and 'severity_distribution' in health_data:
                plt.figure(figsize=(8, 8))
                severities = list(health_data['severity_distribution'].keys())
                counts = list(health_data['severity_distribution'].values())
                
                colors = ['red' if sev == 'CRITICAL' else
                         'orange' if sev == 'HIGH' else
                         'yellow' if sev == 'MEDIUM' else 'green'
                         for sev in severities]
                
                plt.pie(counts, labels=severities, colors=colors, autopct='%1.1f%%')
                plt.title('Health Alert Severity Distribution')
                plt.tight_layout()
                plt.savefig(output_path / 'alert_severity.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        logger.info(f"Visualizations saved to {output_path}")
    
    def analyze_logs(self, log_files: List[str]) -> Dict[str, Any]:
        """Perform comprehensive log analysis"""
        logger.info(f"Starting log analysis for {len(log_files)} files")
        
        all_log_entries = []
        
        # Read all log files
        for log_file in log_files:
            entries = self.read_log_file(log_file)
            all_log_entries.extend(entries)
        
        if not all_log_entries:
            logger.warning("No log entries found")
            return {'message': 'No log entries found'}
        
        logger.info(f"Analyzing {len(all_log_entries)} log entries")
        
        # Perform different types of analysis
        analysis_results = {
            'summary': {
                'total_entries': len(all_log_entries),
                'analysis_timestamp': datetime.now().isoformat(),
                'log_files_analyzed': len(log_files),
                'date_range': self.get_date_range(all_log_entries)
            },
            'error_analysis': self.analyze_error_patterns(all_log_entries),
            'performance_analysis': self.analyze_performance_metrics(all_log_entries),
            'health_analysis': self.analyze_health_alerts(all_log_entries),
            'device_analysis': self.analyze_device_activity(all_log_entries)
        }
        
        return analysis_results
    
    def get_date_range(self, log_entries: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get date range of log entries"""
        timestamps = [entry.get('timestamp') for entry in log_entries if entry.get('timestamp')]
        
        if not timestamps:
            return {'start': 'unknown', 'end': 'unknown'}
        
        # Simple date extraction (in production, use proper datetime parsing)
        dates = []
        for ts in timestamps:
            try:
                if 'T' in str(ts):
                    date_part = str(ts).split('T')[0]
                    dates.append(date_part)
            except:
                continue
        
        if dates:
            dates.sort()
            return {'start': dates[0], 'end': dates[-1]}
        
        return {'start': 'unknown', 'end': 'unknown'}


def main():
    """Main function to run log analysis"""
    parser = argparse.ArgumentParser(description='HealthConnect AI Log Analyzer')
    parser.add_argument('files', nargs='+', help='Log files to analyze')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--output', '-o', default='scripts/logs', help='Output directory')
    parser.add_argument('--charts', action='store_true', help='Generate visualization charts')
    parser.add_argument('--format', choices=['json', 'text'], default='json', help='Output format')
    parser.add_argument('--log-level', '-l', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration
    config = {}
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    
    # Initialize analyzer
    analyzer = LogAnalyzer(config)
    
    try:
        # Analyze logs
        results = analyzer.analyze_logs(args.files)
        
        # Save results
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        if args.format == 'json':
            output_file = output_dir / f'log-analysis-{timestamp}.json'
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Analysis results saved to {output_file}")
        else:
            output_file = output_dir / f'log-analysis-{timestamp}.txt'
            with open(output_file, 'w') as f:
                f.write("LOG ANALYSIS REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Analysis Date: {results.get('summary', {}).get('analysis_timestamp', 'unknown')}\n")
                f.write(f"Total Entries: {results.get('summary', {}).get('total_entries', 0)}\n")
                f.write(f"Files Analyzed: {results.get('summary', {}).get('log_files_analyzed', 0)}\n\n")
                
                # Error summary
                error_data = results.get('error_analysis', {})
                f.write(f"ERRORS: {error_data.get('total_errors', 0)}\n")
                f.write(f"WARNINGS: {error_data.get('total_warnings', 0)}\n")
                f.write(f"ERROR RATE: {error_data.get('error_rate', 0):.2f}%\n\n")
                
                # Performance summary
                perf_data = results.get('performance_analysis', {})
                if isinstance(perf_data, dict):
                    f.write(f"TOTAL REQUESTS: {perf_data.get('total_requests', 0)}\n")
                    f.write(f"AVG RESPONSE TIME: {perf_data.get('avg_response_time', 0)}ms\n")
                    f.write(f"ERROR RATE: {perf_data.get('error_rate', 0):.2f}%\n\n")
            
            logger.info(f"Analysis report saved to {output_file}")
        
        # Generate charts if requested
        if args.charts:
            analyzer.generate_visualizations(results, f"{args.output}/charts")
        
        # Print summary to console
        print("\nLOG ANALYSIS SUMMARY")
        print("=" * 40)
        summary = results.get('summary', {})
        print(f"Total Entries: {summary.get('total_entries', 0)}")
        print(f"Files Analyzed: {summary.get('log_files_analyzed', 0)}")
        
        error_data = results.get('error_analysis', {})
        print(f"Errors Found: {error_data.get('total_errors', 0)}")
        print(f"Warnings Found: {error_data.get('total_warnings', 0)}")
        
        perf_data = results.get('performance_analysis', {})
        if isinstance(perf_data, dict):
            print(f"API Requests: {perf_data.get('total_requests', 0)}")
            print(f"Avg Response Time: {perf_data.get('avg_response_time', 0)}ms")
        
        health_data = results.get('health_analysis', {})
        if isinstance(health_data, dict):
            print(f"Health Alerts: {health_data.get('total_alerts', 0)}")
            print(f"Critical Alerts: {health_data.get('critical_alerts', 0)}")
        
    except KeyboardInterrupt:
        logger.info("Log analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Log analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure logs directory exists
    Path('scripts/logs').mkdir(exist_ok=True)
    
    # Run the log analyzer
    main()
