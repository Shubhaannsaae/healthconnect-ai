#!/usr/bin/env python3

"""
HealthConnect AI - API Endpoint Testing Script
Production-grade API testing with comprehensive coverage
Version: 1.0.0
Last Updated: 2025-06-20
"""

import asyncio
import json
import logging
import argparse
import time
from typing import Dict, List, Any, Optional
import uuid
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import aiohttp
    import pytest
    from faker import Faker
    import jwt
    from datetime import datetime, timedelta
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please run: pip install aiohttp pytest faker pyjwt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scripts/logs/api-testing.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

class APITester:
    """Production-grade API endpoint testing with authentication and validation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config['base_url']
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session with proper headers"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'HealthConnect-API-Tester/1.0'
            }
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Authenticate with the API and get access token"""
        try:
            auth_data = {
                'email': self.config['test_user']['email'],
                'password': self.config['test_user']['password']
            }
            
            async with self.session.post(f"{self.base_url}/auth/login", json=auth_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    
                    # Update session headers with auth token
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    
                    logger.info("Authentication successful")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def test_endpoint(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single API endpoint"""
        test_name = endpoint['name']
        method = endpoint['method'].upper()
        path = endpoint['path']
        url = f"{self.base_url}{path}"
        
        test_result = {
            'name': test_name,
            'method': method,
            'path': path,
            'status': 'PENDING',
            'response_time': 0,
            'status_code': None,
            'expected_status': endpoint.get('expected_status', 200),
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            
            # Prepare request data
            request_kwargs = {}
            if endpoint.get('data'):
                request_kwargs['json'] = endpoint['data']
            if endpoint.get('params'):
                request_kwargs['params'] = endpoint['params']
            if endpoint.get('headers'):
                request_kwargs['headers'] = endpoint['headers']
            
            # Make request
            async with self.session.request(method, url, **request_kwargs) as response:
                response_time = time.time() - start_time
                test_result['response_time'] = round(response_time * 1000, 2)  # ms
                test_result['status_code'] = response.status
                
                # Read response data
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                # Validate response
                if response.status == test_result['expected_status']:
                    test_result['status'] = 'PASSED'
                    
                    # Additional validations
                    if endpoint.get('validate_response'):
                        validation_errors = self.validate_response(response_data, endpoint['validate_response'])
                        if validation_errors:
                            test_result['status'] = 'FAILED'
                            test_result['errors'].extend(validation_errors)
                else:
                    test_result['status'] = 'FAILED'
                    test_result['errors'].append(f"Expected status {test_result['expected_status']}, got {response.status}")
                
                # Check response time
                max_response_time = endpoint.get('max_response_time', 5000)  # 5 seconds default
                if test_result['response_time'] > max_response_time:
                    test_result['status'] = 'FAILED'
                    test_result['errors'].append(f"Response time {test_result['response_time']}ms exceeds limit {max_response_time}ms")
                
                logger.info(f"Test {test_name}: {test_result['status']} ({test_result['response_time']}ms)")
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(str(e))
            logger.error(f"Test {test_name} error: {e}")
        
        self.test_results.append(test_result)
        return test_result
    
    def validate_response(self, response_data: Any, validation_rules: Dict[str, Any]) -> List[str]:
        """Validate response data against rules"""
        errors = []
        
        try:
            # Check required fields
            if validation_rules.get('required_fields'):
                for field in validation_rules['required_fields']:
                    if field not in response_data:
                        errors.append(f"Missing required field: {field}")
            
            # Check data types
            if validation_rules.get('field_types'):
                for field, expected_type in validation_rules['field_types'].items():
                    if field in response_data:
                        actual_type = type(response_data[field]).__name__
                        if actual_type != expected_type:
                            errors.append(f"Field {field} type mismatch: expected {expected_type}, got {actual_type}")
            
            # Check value ranges
            if validation_rules.get('value_ranges'):
                for field, range_def in validation_rules['value_ranges'].items():
                    if field in response_data:
                        value = response_data[field]
                        if isinstance(value, (int, float)):
                            if 'min' in range_def and value < range_def['min']:
                                errors.append(f"Field {field} value {value} below minimum {range_def['min']}")
                            if 'max' in range_def and value > range_def['max']:
                                errors.append(f"Field {field} value {value} above maximum {range_def['max']}")
            
            # Check array lengths
            if validation_rules.get('array_lengths'):
                for field, length_def in validation_rules['array_lengths'].items():
                    if field in response_data and isinstance(response_data[field], list):
                        length = len(response_data[field])
                        if 'min' in length_def and length < length_def['min']:
                            errors.append(f"Array {field} length {length} below minimum {length_def['min']}")
                        if 'max' in length_def and length > length_def['max']:
                            errors.append(f"Array {field} length {length} above maximum {length_def['max']}")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    async def run_load_test(self, endpoint: Dict[str, Any], concurrent_requests: int = 10, duration: int = 30):
        """Run load test on a specific endpoint"""
        logger.info(f"Starting load test: {concurrent_requests} concurrent requests for {duration} seconds")
        
        start_time = time.time()
        end_time = start_time + duration
        completed_requests = 0
        failed_requests = 0
        response_times = []
        
        async def make_request():
            nonlocal completed_requests, failed_requests
            
            while time.time() < end_time:
                try:
                    result = await self.test_endpoint(endpoint)
                    completed_requests += 1
                    response_times.append(result['response_time'])
                    
                    if result['status'] != 'PASSED':
                        failed_requests += 1
                        
                except Exception as e:
                    failed_requests += 1
                    logger.error(f"Load test request failed: {e}")
                
                await asyncio.sleep(0.1)  # Small delay between requests
        
        # Run concurrent requests
        tasks = [make_request() for _ in range(concurrent_requests)]
        await asyncio.gather(*tasks)
        
        # Calculate statistics
        total_time = time.time() - start_time
        requests_per_second = completed_requests / total_time if total_time > 0 else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        load_test_result = {
            'endpoint': endpoint['name'],
            'duration': total_time,
            'concurrent_requests': concurrent_requests,
            'completed_requests': completed_requests,
            'failed_requests': failed_requests,
            'requests_per_second': round(requests_per_second, 2),
            'avg_response_time': round(avg_response_time, 2),
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'success_rate': round((completed_requests - failed_requests) / completed_requests * 100, 2) if completed_requests > 0 else 0
        }
        
        logger.info(f"Load test completed: {load_test_result['requests_per_second']} req/s, {load_test_result['success_rate']}% success rate")
        return load_test_result
    
    async def run_all_tests(self, test_suite: List[Dict[str, Any]]):
        """Run all API tests"""
        logger.info(f"Starting API test suite with {len(test_suite)} tests")
        
        await self.setup_session()
        
        try:
            # Authenticate first
            if not await self.authenticate():
                logger.error("Authentication failed, aborting tests")
                return
            
            # Run tests
            for endpoint in test_suite:
                await self.test_endpoint(endpoint)
                await asyncio.sleep(0.1)  # Small delay between tests
            
            # Generate summary
            self.generate_test_report()
            
        finally:
            await self.cleanup_session()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAILED'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        avg_response_time = sum(r['response_time'] for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0,
                'avg_response_time': round(avg_response_time, 2)
            },
            'test_results': self.test_results,
            'generated_at': datetime.now().isoformat()
        }
        
        # Save report to file
        report_file = f"scripts/logs/api-test-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info("=" * 50)
        logger.info("API TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Errors: {error_tests}")
        logger.info(f"Success Rate: {report['summary']['success_rate']}%")
        logger.info(f"Average Response Time: {report['summary']['avg_response_time']}ms")
        logger.info(f"Report saved: {report_file}")
        
        # Print failed tests
        if failed_tests > 0 or error_tests > 0:
            logger.info("\nFAILED/ERROR TESTS:")
            for result in self.test_results:
                if result['status'] in ['FAILED', 'ERROR']:
                    logger.error(f"- {result['name']}: {result['status']}")
                    for error in result['errors']:
                        logger.error(f"  {error}")


def load_test_configuration() -> Dict[str, Any]:
    """Load test configuration"""
    config = {
        'base_url': 'http://localhost:8000/api/v1',
        'test_user': {
            'email': 'test@healthconnect-ai.com',
            'password': 'test123!'
        },
        'test_suite': [
            {
                'name': 'Health Check',
                'method': 'GET',
                'path': '/health',
                'expected_status': 200,
                'max_response_time': 1000,
                'validate_response': {
                    'required_fields': ['status', 'timestamp'],
                    'field_types': {'status': 'str', 'timestamp': 'str'}
                }
            },
            {
                'name': 'User Authentication',
                'method': 'POST',
                'path': '/auth/login',
                'data': {
                    'email': 'test@healthconnect-ai.com',
                    'password': 'test123!'
                },
                'expected_status': 200,
                'validate_response': {
                    'required_fields': ['access_token', 'refresh_token', 'user'],
                    'field_types': {'access_token': 'str', 'refresh_token': 'str'}
                }
            },
            {
                'name': 'Get Patient Profile',
                'method': 'GET',
                'path': '/patients/me',
                'expected_status': 200,
                'validate_response': {
                    'required_fields': ['id', 'email', 'first_name', 'last_name'],
                    'field_types': {'id': 'str', 'email': 'str'}
                }
            },
            {
                'name': 'Get Health Records',
                'method': 'GET',
                'path': '/health/records',
                'expected_status': 200,
                'validate_response': {
                    'required_fields': ['records', 'total', 'page'],
                    'field_types': {'records': 'list', 'total': 'int', 'page': 'int'}
                }
            },
            {
                'name': 'Create Health Record',
                'method': 'POST',
                'path': '/health/records',
                'data': {
                    'record_type': 'vital_signs',
                    'vital_signs': {
                        'heart_rate': 72,
                        'blood_pressure': {'systolic': 120, 'diastolic': 80},
                        'temperature': 37.0,
                        'oxygen_saturation': 98
                    }
                },
                'expected_status': 201,
                'validate_response': {
                    'required_fields': ['id', 'record_type', 'vital_signs'],
                    'field_types': {'id': 'str', 'record_type': 'str'}
                }
            },
            {
                'name': 'Get Devices',
                'method': 'GET',
                'path': '/devices',
                'expected_status': 200,
                'validate_response': {
                    'required_fields': ['devices'],
                    'field_types': {'devices': 'list'}
                }
            },
            {
                'name': 'Get Consultations',
                'method': 'GET',
                'path': '/consultations',
                'expected_status': 200,
                'validate_response': {
                    'required_fields': ['consultations'],
                    'field_types': {'consultations': 'list'}
                }
            },
            {
                'name': 'Get Alerts',
                'method': 'GET',
                'path': '/alerts',
                'expected_status': 200,
                'validate_response': {
                    'required_fields': ['alerts'],
                    'field_types': {'alerts': 'list'}
                }
            }
        ]
    }
    
    # Load from config file if exists
    config_file = Path('config/api-testing.json')
    if config_file.exists():
        with open(config_file) as f:
            file_config = json.load(f)
            config.update(file_config)
    
    return config


async def main():
    """Main function to run API tests"""
    parser = argparse.ArgumentParser(description='HealthConnect AI API Endpoint Tester')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--base-url', '-u', help='API base URL')
    parser.add_argument('--load-test', '-l', action='store_true', help='Run load tests')
    parser.add_argument('--concurrent', type=int, default=10, help='Concurrent requests for load test')
    parser.add_argument('--duration', type=int, default=30, help='Load test duration in seconds')
    parser.add_argument('--endpoint', '-e', help='Test specific endpoint only')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
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
    
    # Initialize tester
    tester = APITester(config)
    
    try:
        if args.load_test:
            # Run load tests
            await tester.setup_session()
            if await tester.authenticate():
                for endpoint in config['test_suite']:
                    if not args.endpoint or endpoint['name'] == args.endpoint:
                        await tester.run_load_test(endpoint, args.concurrent, args.duration)
            await tester.cleanup_session()
        else:
            # Run functional tests
            test_suite = config['test_suite']
            if args.endpoint:
                test_suite = [e for e in test_suite if e['name'] == args.endpoint]
            
            await tester.run_all_tests(test_suite)
            
    except KeyboardInterrupt:
        logger.info("Testing interrupted by user")
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure logs directory exists
    Path('scripts/logs').mkdir(exist_ok=True)
    
    # Run the tests
    asyncio.run(main())
