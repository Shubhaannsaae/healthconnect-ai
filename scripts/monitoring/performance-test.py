#!/usr/bin/env python3

"""
HealthConnect AI - Performance Testing Script
Production-grade performance testing and load testing
Version: 1.0.0
Last Updated: 2025-06-20
"""

import asyncio
import json
import logging
import argparse
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sys
from pathlib import Path
import concurrent.futures

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import aiohttp
    import matplotlib.pyplot as plt
    import numpy as np
    from faker import Faker
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please run: pip install aiohttp matplotlib numpy faker")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scripts/logs/performance-test.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

class PerformanceTester:
    """Production-grade performance testing for HealthConnect AI platform"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config['base_url']
        self.results = []
        self.session = None
        
    async def setup_session(self):
        """Setup HTTP session with connection pooling"""
        connector = aiohttp.TCPConnector(
            limit=self.config.get('connection_pool_size', 100),
            limit_per_host=self.config.get('connections_per_host', 30),
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.get('request_timeout', 30),
            connect=self.config.get('connect_timeout', 10)
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'HealthConnect-Performance-Tester/1.0'
            }
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> Optional[str]:
        """Authenticate and get access token"""
        auth_config = self.config.get('auth', {})
        if not auth_config.get('enabled', False):
            return None
            
        try:
            auth_data = {
                'email': auth_config['email'],
                'password': auth_config['password']
            }
            
            async with self.session.post(f"{self.base_url}/auth/login", json=auth_data) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get('access_token')
                    
                    # Update session headers
                    self.session.headers.update({
                        'Authorization': f'Bearer {token}'
                    })
                    
                    return token
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a single HTTP request and measure performance"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        request_data = {
            'method': method,
            'endpoint': endpoint,
            'start_time': start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            kwargs = {}
            if data:
                kwargs['json'] = data
            if params:
                kwargs['params'] = params
                
            async with self.session.request(method, url, **kwargs) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # milliseconds
                
                # Try to read response body
                try:
                    response_body = await response.json()
                    response_size = len(json.dumps(response_body))
                except:
                    response_body = await response.text()
                    response_size = len(response_body)
                
                request_data.update({
                    'response_time_ms': round(response_time, 2),
                    'status_code': response.status,
                    'response_size_bytes': response_size,
                    'success': 200 <= response.status < 400,
                    'error': None
                })
                
        except asyncio.TimeoutError:
            request_data.update({
                'response_time_ms': (time.time() - start_time) * 1000,
                'status_code': 0,
                'response_size_bytes': 0,
                'success': False,
                'error': 'timeout'
            })
        except Exception as e:
            request_data.update({
                'response_time_ms': (time.time() - start_time) * 1000,
                'status_code': 0,
                'response_size_bytes': 0,
                'success': False,
                'error': str(e)
            })
        
        return request_data
    
    async def run_load_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run load test with specified configuration"""
        test_name = test_config['name']
        endpoint = test_config['endpoint']
        method = test_config.get('method', 'GET')
        concurrent_users = test_config.get('concurrent_users', 10)
        duration_seconds = test_config.get('duration_seconds', 60)
        ramp_up_seconds = test_config.get('ramp_up_seconds', 10)
        
        logger.info(f"Starting load test: {test_name}")
        logger.info(f"Endpoint: {method} {endpoint}")
        logger.info(f"Concurrent users: {concurrent_users}")
        logger.info(f"Duration: {duration_seconds}s")
        logger.info(f"Ramp-up: {ramp_up_seconds}s")
        
        test_results = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        async def user_session(user_id: int, start_delay: float):
            """Simulate a single user session"""
            await asyncio.sleep(start_delay)
            
            while time.time() < end_time:
                # Generate test data if needed
                request_data = None
                if test_config.get('generate_data'):
                    request_data = self.generate_test_data(test_config['data_template'])
                
                # Make request
                result = await self.make_request(method, endpoint, request_data)
                result['user_id'] = user_id
                result['test_name'] = test_name
                test_results.append(result)
                
                # Wait between requests
                think_time = test_config.get('think_time_seconds', 1)
                await asyncio.sleep(think_time)
        
        # Create user sessions with ramp-up
        tasks = []
        for user_id in range(concurrent_users):
            start_delay = (user_id / concurrent_users) * ramp_up_seconds
            task = asyncio.create_task(user_session(user_id, start_delay))
            tasks.append(task)
        
        # Wait for all tasks to complete or timeout
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), 
                                 timeout=duration_seconds + ramp_up_seconds + 30)
        except asyncio.TimeoutError:
            logger.warning("Load test timed out, cancelling remaining tasks")
            for task in tasks:
                task.cancel()
        
        # Analyze results
        total_time = time.time() - start_time
        analysis = self.analyze_results(test_results, total_time)
        analysis['test_config'] = test_config
        
        logger.info(f"Load test completed: {test_name}")
        logger.info(f"Total requests: {analysis['total_requests']}")
        logger.info(f"Success rate: {analysis['success_rate']:.2f}%")
        logger.info(f"Average response time: {analysis['avg_response_time']:.2f}ms")
        logger.info(f"Requests per second: {analysis['requests_per_second']:.2f}")
        
        return analysis
    
    def generate_test_data(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data based on template"""
        data = {}
        
        for field, field_config in template.items():
            field_type = field_config.get('type', 'string')
            
            if field_type == 'string':
                data[field] = fake.text(max_nb_chars=field_config.get('max_length', 50))
            elif field_type == 'email':
                data[field] = fake.email()
            elif field_type == 'name':
                data[field] = fake.name()
            elif field_type == 'integer':
                min_val = field_config.get('min', 0)
                max_val = field_config.get('max', 100)
                data[field] = fake.random_int(min=min_val, max=max_val)
            elif field_type == 'float':
                min_val = field_config.get('min', 0.0)
                max_val = field_config.get('max', 100.0)
                data[field] = round(fake.random.uniform(min_val, max_val), 2)
            elif field_type == 'choice':
                choices = field_config.get('choices', ['option1', 'option2'])
                data[field] = fake.random_element(choices)
            elif field_type == 'datetime':
                data[field] = fake.date_time_between(start_date='-1y', end_date='now').isoformat()
            elif field_type == 'vital_signs':
                data[field] = {
                    'heart_rate': fake.random_int(min=60, max=100),
                    'blood_pressure': {
                        'systolic': fake.random_int(min=110, max=140),
                        'diastolic': fake.random_int(min=70, max=90)
                    },
                    'temperature': round(fake.random.uniform(36.1, 37.2), 1),
                    'oxygen_saturation': fake.random_int(min=95, max=100)
                }
        
        return data
    
    def analyze_results(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """Analyze performance test results"""
        if not results:
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'p50_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'requests_per_second': 0,
                'errors': {}
            }
        
        # Basic metrics
        total_requests = len(results)
        successful_requests = len([r for r in results if r['success']])
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests) * 100
        
        # Response time metrics
        response_times = [r['response_time_ms'] for r in results]
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Percentiles
        p50_response_time = np.percentile(response_times, 50)
        p95_response_time = np.percentile(response_times, 95)
        p99_response_time = np.percentile(response_times, 99)
        
        # Throughput
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        
        # Error analysis
        errors = {}
        for result in results:
            if not result['success']:
                error_key = f"{result['status_code']}_{result.get('error', 'unknown')}"
                errors[error_key] = errors.get(error_key, 0) + 1
        
        # Response time distribution
        response_time_buckets = {
            '0-100ms': len([r for r in response_times if r <= 100]),
            '100-500ms': len([r for r in response_times if 100 < r <= 500]),
            '500-1000ms': len([r for r in response_times if 500 < r <= 1000]),
            '1000-5000ms': len([r for r in response_times if 1000 < r <= 5000]),
            '5000ms+': len([r for r in response_times if r > 5000])
        }
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': round(success_rate, 2),
            'avg_response_time': round(avg_response_time, 2),
            'min_response_time': round(min_response_time, 2),
            'max_response_time': round(max_response_time, 2),
            'p50_response_time': round(p50_response_time, 2),
            'p95_response_time': round(p95_response_time, 2),
            'p99_response_time': round(p99_response_time, 2),
            'requests_per_second': round(requests_per_second, 2),
            'errors': errors,
            'response_time_distribution': response_time_buckets,
            'test_duration_seconds': round(total_time, 2)
        }
    
    def generate_performance_report(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'summary': {
                'total_tests': len(test_results),
                'generated_at': datetime.now().isoformat(),
                'test_environment': self.config.get('environment', 'unknown')
            },
            'test_results': test_results,
            'overall_metrics': {}
        }
        
        if test_results:
            # Calculate overall metrics
            all_requests = sum(r['total_requests'] for r in test_results)
            all_successful = sum(r['successful_requests'] for r in test_results)
            avg_success_rate = statistics.mean([r['success_rate'] for r in test_results])
            avg_response_time = statistics.mean([r['avg_response_time'] for r in test_results])
            total_rps = sum(r['requests_per_second'] for r in test_results)
            
            report['overall_metrics'] = {
                'total_requests': all_requests,
                'total_successful_requests': all_successful,
                'average_success_rate': round(avg_success_rate, 2),
                'average_response_time': round(avg_response_time, 2),
                'total_requests_per_second': round(total_rps, 2)
            }
        
        return report
    
    def create_performance_charts(self, test_results: List[Dict[str, Any]], output_dir: str):
        """Create performance visualization charts"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        if not test_results:
            logger.warning("No test results to visualize")
            return
        
        # Response time comparison chart
        plt.figure(figsize=(12, 8))
        
        test_names = [r['test_config']['name'] for r in test_results]
        avg_times = [r['avg_response_time'] for r in test_results]
        p95_times = [r['p95_response_time'] for r in test_results]
        p99_times = [r['p99_response_time'] for r in test_results]
        
        x = np.arange(len(test_names))
        width = 0.25
        
        plt.bar(x - width, avg_times, width, label='Average', alpha=0.8)
        plt.bar(x, p95_times, width, label='95th Percentile', alpha=0.8)
        plt.bar(x + width, p99_times, width, label='99th Percentile', alpha=0.8)
        
        plt.xlabel('Test Cases')
        plt.ylabel('Response Time (ms)')
        plt.title('Response Time Comparison')
        plt.xticks(x, test_names, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path / 'response_time_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Success rate chart
        plt.figure(figsize=(10, 6))
        success_rates = [r['success_rate'] for r in test_results]
        
        plt.bar(test_names, success_rates, alpha=0.8, color='green')
        plt.xlabel('Test Cases')
        plt.ylabel('Success Rate (%)')
        plt.title('Success Rate by Test Case')
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)
        
        # Add value labels on bars
        for i, v in enumerate(success_rates):
            plt.text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path / 'success_rate_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Throughput chart
        plt.figure(figsize=(10, 6))
        throughput = [r['requests_per_second'] for r in test_results]
        
        plt.bar(test_names, throughput, alpha=0.8, color='blue')
        plt.xlabel('Test Cases')
        plt.ylabel('Requests per Second')
        plt.title('Throughput Comparison')
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on bars
        for i, v in enumerate(throughput):
            plt.text(i, v + max(throughput) * 0.01, f'{v:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path / 'throughput_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Performance charts saved to {output_path}")
    
    async def run_performance_tests(self, test_suite: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run complete performance test suite"""
        logger.info(f"Starting performance test suite with {len(test_suite)} tests")
        
        await self.setup_session()
        
        try:
            # Authenticate if required
            if self.config.get('auth', {}).get('enabled', False):
                token = await self.authenticate()
                if not token:
                    raise Exception("Authentication failed")
            
            # Run all tests
            test_results = []
            for test_config in test_suite:
                result = await self.run_load_test(test_config)
                test_results.append(result)
                
                # Wait between tests
                await asyncio.sleep(self.config.get('test_interval_seconds', 5))
            
            # Generate report
            report = self.generate_performance_report(test_results)
            
            # Create charts if matplotlib is available
            try:
                self.create_performance_charts(test_results, 'scripts/logs/charts')
            except Exception as e:
                logger.warning(f"Failed to create charts: {e}")
            
            return report
            
        finally:
            await self.cleanup_session()


def load_test_configuration() -> Dict[str, Any]:
    """Load performance test configuration"""
    config = {
        'base_url': 'http://localhost:8000/api/v1',
        'connection_pool_size': 100,
        'connections_per_host': 30,
        'request_timeout': 30,
        'connect_timeout': 10,
        'test_interval_seconds': 5,
        'environment': 'development',
        'auth': {
            'enabled': False,
            'email': 'test@healthconnect-ai.com',
            'password': 'test123!'
        },
        'test_suite': [
            {
                'name': 'Health Check Load Test',
                'endpoint': '/health',
                'method': 'GET',
                'concurrent_users': 50,
                'duration_seconds': 60,
                'ramp_up_seconds': 10,
                'think_time_seconds': 1
            },
            {
                'name': 'Patient Data Retrieval',
                'endpoint': '/patients/me',
                'method': 'GET',
                'concurrent_users': 20,
                'duration_seconds': 120,
                'ramp_up_seconds': 15,
                'think_time_seconds': 2
            },
            {
                'name': 'Health Record Creation',
                'endpoint': '/health/records',
                'method': 'POST',
                'concurrent_users': 10,
                'duration_seconds': 90,
                'ramp_up_seconds': 10,
                'think_time_seconds': 3,
                'generate_data': True,
                'data_template': {
                    'record_type': {'type': 'choice', 'choices': ['vital_signs', 'consultation', 'medication']},
                    'vital_signs': {'type': 'vital_signs'},
                    'notes': {'type': 'string', 'max_length': 200}
                }
            },
            {
                'name': 'Device Data Simulation',
                'endpoint': '/devices/data',
                'method': 'POST',
                'concurrent_users': 30,
                'duration_seconds': 180,
                'ramp_up_seconds': 20,
                'think_time_seconds': 1,
                'generate_data': True,
                'data_template': {
                    'device_id': {'type': 'string', 'max_length': 20},
                    'vital_signs': {'type': 'vital_signs'},
                    'timestamp': {'type': 'datetime'}
                }
            }
        ]
    }
    
    # Load from config file if exists
    config_file = Path('config/performance-test.json')
    if config_file.exists():
        with open(config_file) as f:
            file_config = json.load(f)
            config.update(file_config)
    
    return config


async def main():
    """Main function to run performance tests"""
    parser = argparse.ArgumentParser(description='HealthConnect AI Performance Tester')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--base-url', '-u', help='API base URL')
    parser.add_argument('--test', '-t', help='Run specific test only')
    parser.add_argument('--users', type=int, help='Number of concurrent users')
    parser.add_argument('--duration', type=int, help='Test duration in seconds')
    parser.add_argument('--output', '-o', help='Output directory for results')
    parser.add_argument('--charts', action='store_true', help='Generate performance charts')
    parser.add_argument('--log-level', '-l', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration
    config = load_test_configuration()
    if args.config:
        with open(args.config) as f:
            config.update(json.load(f))
    
    if args.base_url:
        config['base_url'] = args.base_url
    
    # Override test parameters if specified
    if args.users or args.duration:
        for test in config['test_suite']:
            if args.users:
                test['concurrent_users'] = args.users
            if args.duration:
                test['duration_seconds'] = args.duration
    
    # Filter tests if specific test requested
    if args.test:
        config['test_suite'] = [t for t in config['test_suite'] if t['name'] == args.test]
        if not config['test_suite']:
            logger.error(f"Test '{args.test}' not found")
            sys.exit(1)
    
    # Initialize tester
    tester = PerformanceTester(config)
    
    try:
        # Run performance tests
        report = await tester.run_performance_tests(config['test_suite'])
        
        # Save results
        output_dir = args.output or 'scripts/logs'
        Path(output_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        report_file = Path(output_dir) / f'performance-test-report-{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Performance test report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("PERFORMANCE TEST SUMMARY")
        print("="*60)
        
        if report['overall_metrics']:
            metrics = report['overall_metrics']
            print(f"Total Requests: {metrics['total_requests']}")
            print(f"Successful Requests: {metrics['total_successful_requests']}")
            print(f"Average Success Rate: {metrics['average_success_rate']}%")
            print(f"Average Response Time: {metrics['average_response_time']}ms")
            print(f"Total Throughput: {metrics['total_requests_per_second']} req/s")
        
        print(f"\nDetailed report: {report_file}")
        
        if args.charts:
            tester.create_performance_charts(report['test_results'], f"{output_dir}/charts")
        
    except KeyboardInterrupt:
        logger.info("Performance testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Performance testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure logs directory exists
    Path('scripts/logs').mkdir(exist_ok=True)
    
    # Run the performance tests
    asyncio.run(main())
