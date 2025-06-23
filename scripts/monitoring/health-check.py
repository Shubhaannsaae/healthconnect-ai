#!/usr/bin/env python3

"""
HealthConnect AI - Health Check Script
Production-grade system health monitoring and alerting
Version: 1.0.0
Last Updated: 2025-06-20
"""

import asyncio
import json
import logging
import argparse
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import aiohttp
    import psutil
    import boto3
    from botocore.exceptions import ClientError
    import redis
    import psycopg2
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please run: pip install aiohttp psutil boto3 redis psycopg2-binary")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scripts/logs/health-check.log')
    ]
)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Production-grade health monitoring for HealthConnect AI platform"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_results = {}
        self.alerts = []
        
    async def check_api_health(self) -> Dict[str, Any]:
        """Check API endpoint health"""
        api_config = self.config.get('api', {})
        base_url = api_config.get('base_url', 'http://localhost:8000')
        timeout = api_config.get('timeout', 10)
        
        result = {
            'service': 'API',
            'status': 'UNKNOWN',
            'response_time': 0,
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                # Check health endpoint
                async with session.get(f"{base_url}/health") as response:
                    response_time = (time.time() - start_time) * 1000
                    result['response_time'] = round(response_time, 2)
                    
                    if response.status == 200:
                        data = await response.json()
                        result['status'] = 'HEALTHY'
                        result['details'] = {
                            'status_code': response.status,
                            'response_data': data,
                            'response_time_ms': result['response_time']
                        }
                    else:
                        result['status'] = 'UNHEALTHY'
                        result['details'] = {
                            'status_code': response.status,
                            'error': f"HTTP {response.status}"
                        }
                        
                        self.alerts.append({
                            'service': 'API',
                            'severity': 'HIGH',
                            'message': f"API health check failed with status {response.status}",
                            'timestamp': datetime.now().isoformat()
                        })
                
                # Check additional endpoints
                endpoints_to_check = api_config.get('endpoints', [])
                endpoint_results = {}
                
                for endpoint in endpoints_to_check:
                    try:
                        async with session.get(f"{base_url}{endpoint}") as ep_response:
                            endpoint_results[endpoint] = {
                                'status_code': ep_response.status,
                                'healthy': ep_response.status < 500
                            }
                    except Exception as e:
                        endpoint_results[endpoint] = {
                            'status_code': None,
                            'healthy': False,
                            'error': str(e)
                        }
                
                result['details']['endpoints'] = endpoint_results
                
        except asyncio.TimeoutError:
            result['status'] = 'UNHEALTHY'
            result['details'] = {'error': 'Request timeout'}
            self.alerts.append({
                'service': 'API',
                'severity': 'HIGH',
                'message': f"API health check timed out after {timeout}s",
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            result['status'] = 'UNHEALTHY'
            result['details'] = {'error': str(e)}
            self.alerts.append({
                'service': 'API',
                'severity': 'HIGH',
                'message': f"API health check failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check PostgreSQL database health"""
        db_config = self.config.get('database', {})
        
        result = {
            'service': 'Database',
            'status': 'UNKNOWN',
            'response_time': 0,
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            
            # Connect to database
            conn = psycopg2.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                database=db_config.get('database', 'healthconnect_dev'),
                user=db_config.get('user', 'healthconnect_user'),
                password=db_config.get('password', ''),
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            
            # Basic connectivity test
            cursor.execute('SELECT 1')
            cursor.fetchone()
            
            # Check database version
            cursor.execute('SELECT version()')
            version = cursor.fetchone()[0]
            
            # Check active connections
            cursor.execute('SELECT count(*) FROM pg_stat_activity')
            active_connections = cursor.fetchone()[0]
            
            # Check database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            db_size = cursor.fetchone()[0]
            
            # Check table counts
            cursor.execute("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
                FROM pg_stat_user_tables
                ORDER BY n_tup_ins DESC
                LIMIT 5
            """)
            table_stats = cursor.fetchall()
            
            response_time = (time.time() - start_time) * 1000
            result['response_time'] = round(response_time, 2)
            result['status'] = 'HEALTHY'
            result['details'] = {
                'version': version,
                'active_connections': active_connections,
                'database_size': db_size,
                'response_time_ms': result['response_time'],
                'top_tables': [
                    {
                        'schema': row[0],
                        'table': row[1],
                        'inserts': row[2],
                        'updates': row[3],
                        'deletes': row[4]
                    } for row in table_stats
                ]
            }
            
            # Check for high connection count
            max_connections = db_config.get('max_connections', 100)
            if active_connections > max_connections * 0.8:
                self.alerts.append({
                    'service': 'Database',
                    'severity': 'MEDIUM',
                    'message': f"High connection count: {active_connections}/{max_connections}",
                    'timestamp': datetime.now().isoformat()
                })
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            result['status'] = 'UNHEALTHY'
            result['details'] = {'error': str(e)}
            self.alerts.append({
                'service': 'Database',
                'severity': 'CRITICAL',
                'message': f"Database health check failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis cache health"""
        redis_config = self.config.get('redis', {})
        
        result = {
            'service': 'Redis',
            'status': 'UNKNOWN',
            'response_time': 0,
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            
            # Connect to Redis
            r = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                password=redis_config.get('password'),
                socket_timeout=10,
                socket_connect_timeout=10
            )
            
            # Test basic operations
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            # Test set/get operation
            test_key = 'health_check_test'
            test_value = str(time.time())
            r.set(test_key, test_value, ex=60)
            retrieved_value = r.get(test_key).decode('utf-8')
            
            if retrieved_value != test_value:
                raise Exception("Redis set/get test failed")
            
            r.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            result['response_time'] = round(response_time, 2)
            result['status'] = 'HEALTHY'
            result['details'] = {
                'version': info.get('redis_version'),
                'uptime_seconds': info.get('uptime_in_seconds'),
                'connected_clients': info.get('connected_clients'),
                'used_memory': info.get('used_memory_human'),
                'used_memory_peak': info.get('used_memory_peak_human'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'response_time_ms': result['response_time']
            }
            
            # Check memory usage
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            if max_memory > 0 and used_memory > max_memory * 0.8:
                self.alerts.append({
                    'service': 'Redis',
                    'severity': 'MEDIUM',
                    'message': f"High memory usage: {info.get('used_memory_human')}",
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            result['status'] = 'UNHEALTHY'
            result['details'] = {'error': str(e)}
            self.alerts.append({
                'service': 'Redis',
                'severity': 'HIGH',
                'message': f"Redis health check failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check system resource health"""
        result = {
            'service': 'System',
            'status': 'HEALTHY',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Load average (Unix only)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                pass  # Windows doesn't have load average
            
            result['details'] = {
                'cpu': {
                    'usage_percent': round(cpu_percent, 2),
                    'count': cpu_count,
                    'load_average': load_avg
                },
                'memory': {
                    'usage_percent': round(memory_percent, 2),
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2)
                },
                'disk': {
                    'usage_percent': round(disk_percent, 2),
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2)
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
            
            # Check thresholds and generate alerts
            thresholds = self.config.get('system_thresholds', {})
            
            if cpu_percent > thresholds.get('cpu_warning', 80):
                severity = 'CRITICAL' if cpu_percent > thresholds.get('cpu_critical', 95) else 'MEDIUM'
                self.alerts.append({
                    'service': 'System',
                    'severity': severity,
                    'message': f"High CPU usage: {cpu_percent}%",
                    'timestamp': datetime.now().isoformat()
                })
                if severity == 'CRITICAL':
                    result['status'] = 'UNHEALTHY'
            
            if memory_percent > thresholds.get('memory_warning', 80):
                severity = 'CRITICAL' if memory_percent > thresholds.get('memory_critical', 95) else 'MEDIUM'
                self.alerts.append({
                    'service': 'System',
                    'severity': severity,
                    'message': f"High memory usage: {memory_percent}%",
                    'timestamp': datetime.now().isoformat()
                })
                if severity == 'CRITICAL':
                    result['status'] = 'UNHEALTHY'
            
            if disk_percent > thresholds.get('disk_warning', 80):
                severity = 'CRITICAL' if disk_percent > thresholds.get('disk_critical', 95) else 'MEDIUM'
                self.alerts.append({
                    'service': 'System',
                    'severity': severity,
                    'message': f"High disk usage: {disk_percent:.1f}%",
                    'timestamp': datetime.now().isoformat()
                })
                if severity == 'CRITICAL':
                    result['status'] = 'UNHEALTHY'
            
        except Exception as e:
            result['status'] = 'UNHEALTHY'
            result['details'] = {'error': str(e)}
            self.alerts.append({
                'service': 'System',
                'severity': 'HIGH',
                'message': f"System health check failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    def check_aws_services_health(self) -> Dict[str, Any]:
        """Check AWS services health"""
        aws_config = self.config.get('aws', {})
        
        result = {
            'service': 'AWS',
            'status': 'HEALTHY',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        if not aws_config.get('enabled', False):
            result['status'] = 'SKIPPED'
            result['details'] = {'message': 'AWS health checks disabled'}
            return result
        
        try:
            region = aws_config.get('region', 'us-east-1')
            
            # Check S3
            s3_client = boto3.client('s3', region_name=region)
            s3_buckets = aws_config.get('s3_buckets', [])
            s3_results = {}
            
            for bucket in s3_buckets:
                try:
                    s3_client.head_bucket(Bucket=bucket)
                    s3_results[bucket] = {'status': 'accessible'}
                except ClientError as e:
                    s3_results[bucket] = {'status': 'error', 'error': str(e)}
                    self.alerts.append({
                        'service': 'AWS',
                        'severity': 'HIGH',
                        'message': f"S3 bucket {bucket} not accessible: {str(e)}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Check DynamoDB tables
            dynamodb = boto3.resource('dynamodb', region_name=region)
            tables = aws_config.get('dynamodb_tables', [])
            dynamodb_results = {}
            
            for table_name in tables:
                try:
                    table = dynamodb.Table(table_name)
                    table_status = table.table_status
                    dynamodb_results[table_name] = {'status': table_status}
                    
                    if table_status != 'ACTIVE':
                        self.alerts.append({
                            'service': 'AWS',
                            'severity': 'MEDIUM',
                            'message': f"DynamoDB table {table_name} status: {table_status}",
                            'timestamp': datetime.now().isoformat()
                        })
                except ClientError as e:
                    dynamodb_results[table_name] = {'status': 'error', 'error': str(e)}
                    self.alerts.append({
                        'service': 'AWS',
                        'severity': 'HIGH',
                        'message': f"DynamoDB table {table_name} error: {str(e)}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Check Lambda functions
            lambda_client = boto3.client('lambda', region_name=region)
            functions = aws_config.get('lambda_functions', [])
            lambda_results = {}
            
            for function_name in functions:
                try:
                    response = lambda_client.get_function(FunctionName=function_name)
                    lambda_results[function_name] = {
                        'status': response['Configuration']['State'],
                        'last_modified': response['Configuration']['LastModified']
                    }
                except ClientError as e:
                    lambda_results[function_name] = {'status': 'error', 'error': str(e)}
                    self.alerts.append({
                        'service': 'AWS',
                        'severity': 'HIGH',
                        'message': f"Lambda function {function_name} error: {str(e)}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            result['details'] = {
                's3_buckets': s3_results,
                'dynamodb_tables': dynamodb_results,
                'lambda_functions': lambda_results
            }
            
            # Determine overall status
            all_services = list(s3_results.values()) + list(dynamodb_results.values()) + list(lambda_results.values())
            if any(service.get('status') == 'error' for service in all_services):
                result['status'] = 'UNHEALTHY'
            
        except Exception as e:
            result['status'] = 'UNHEALTHY'
            result['details'] = {'error': str(e)}
            self.alerts.append({
                'service': 'AWS',
                'severity': 'HIGH',
                'message': f"AWS health check failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        logger.info("Starting comprehensive health checks...")
        
        start_time = time.time()
        
        # Run all checks
        checks = [
            ('api', self.check_api_health()),
            ('database', self.check_database_health()),
            ('redis', self.check_redis_health()),
            ('system', self.check_system_health()),
            ('aws', self.check_aws_services_health())
        ]
        
        # Execute API check asynchronously, others synchronously
        api_result = await checks[0][1]
        self.health_results['api'] = api_result
        
        for name, check_func in checks[1:]:
            if asyncio.iscoroutine(check_func):
                result = await check_func
            else:
                result = check_func
            self.health_results[name] = result
        
        total_time = time.time() - start_time
        
        # Generate overall status
        overall_status = 'HEALTHY'
        unhealthy_services = []
        
        for service, result in self.health_results.items():
            if result['status'] == 'UNHEALTHY':
                overall_status = 'UNHEALTHY'
                unhealthy_services.append(service)
            elif result['status'] == 'UNKNOWN' and overall_status == 'HEALTHY':
                overall_status = 'DEGRADED'
        
        health_summary = {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'check_duration_seconds': round(total_time, 2),
            'services': self.health_results,
            'alerts': self.alerts,
            'summary': {
                'total_services': len(self.health_results),
                'healthy_services': len([r for r in self.health_results.values() if r['status'] == 'HEALTHY']),
                'unhealthy_services': len(unhealthy_services),
                'total_alerts': len(self.alerts),
                'critical_alerts': len([a for a in self.alerts if a['severity'] == 'CRITICAL'])
            }
        }
        
        logger.info(f"Health check completed in {total_time:.2f}s - Status: {overall_status}")
        
        return health_summary
    
    def save_results(self, results: Dict[str, Any]):
        """Save health check results to file"""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"scripts/logs/health-check-{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Health check results saved to {filename}")


def load_config() -> Dict[str, Any]:
    """Load health check configuration"""
    config = {
        'api': {
            'base_url': 'http://localhost:8000/api/v1',
            'timeout': 10,
            'endpoints': ['/health', '/auth/status']
        },
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'healthconnect_dev',
            'user': 'healthconnect_user',
            'password': 'dev_password',
            'max_connections': 100
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'password': None
        },
        'system_thresholds': {
            'cpu_warning': 80,
            'cpu_critical': 95,
            'memory_warning': 80,
            'memory_critical': 95,
            'disk_warning': 80,
            'disk_critical': 95
        },
        'aws': {
            'enabled': False,
            'region': 'us-east-1',
            's3_buckets': [],
            'dynamodb_tables': [],
            'lambda_functions': []
        }
    }
    
    # Load from config file if exists
    config_file = Path('config/health-check.json')
    if config_file.exists():
        with open(config_file) as f:
            file_config = json.load(f)
            config.update(file_config)
    
    return config


async def main():
    """Main function to run health checks"""
    parser = argparse.ArgumentParser(description='HealthConnect AI Health Check')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--save-results', '-s', action='store_true', help='Save results to file')
    parser.add_argument('--alerts-only', '-a', action='store_true', help='Show only alerts')
    parser.add_argument('--service', help='Check specific service only')
    parser.add_argument('--log-level', '-l', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration
    config = load_config()
    if args.config:
        with open(args.config) as f:
            config.update(json.load(f))
    
    # Initialize health checker
    checker = HealthChecker(config)
    
    try:
        # Run health checks
        results = await checker.run_all_checks()
        
        # Save results if requested
        if args.save_results:
            checker.save_results(results)
        
        # Display results
        if args.alerts_only:
            if results['alerts']:
                print(json.dumps({'alerts': results['alerts']}, indent=2))
            else:
                print("No alerts found")
        else:
            print(json.dumps(results, indent=2, default=str))
        
        # Exit with appropriate code
        if results['overall_status'] == 'UNHEALTHY':
            sys.exit(1)
        elif results['overall_status'] == 'DEGRADED':
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Health check interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure logs directory exists
    Path('scripts/logs').mkdir(exist_ok=True)
    
    # Run the health check
    asyncio.run(main())
