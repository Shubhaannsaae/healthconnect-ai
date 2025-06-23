import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError
from population_health import PopulationHealthAnalyzer
from predictive_models import PredictiveModelEngine
import pandas as pd
import numpy as np
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
athena = boto3.client('athena')
quicksight = boto3.client('quicksight')
eventbridge = boto3.client('events')
bedrock_runtime = boto3.client('bedrock-runtime')

# Environment variables
ANALYTICS_RESULTS_TABLE = os.environ['ANALYTICS_RESULTS_TABLE']
POPULATION_METRICS_TABLE = os.environ['POPULATION_METRICS_TABLE']
PREDICTIVE_MODELS_TABLE = os.environ['PREDICTIVE_MODELS_TABLE']
ANALYTICS_BUCKET = os.environ['ANALYTICS_BUCKET']
ATHENA_DATABASE = os.environ['ATHENA_DATABASE']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']
QUICKSIGHT_ACCOUNT_ID = os.environ.get('QUICKSIGHT_ACCOUNT_ID')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for analytics engine
    
    Args:
        event: Analytics request or scheduled event
        context: Lambda context object
        
    Returns:
        Dict containing analytics results
    """
    try:
        # Determine event type and route accordingly
        if 'Records' in event:
            # DynamoDB stream trigger
            return handle_stream_event(event, context)
        elif 'source' in event and event['source'] == 'aws.events':
            # Scheduled analytics run
            return handle_scheduled_analytics(event, context)
        elif 'httpMethod' in event:
            # API Gateway trigger
            return handle_api_request(event, context)
        else:
            # Direct invocation
            return handle_direct_analytics_request(event, context)
            
    except Exception as e:
        logger.error(f"Error in analytics engine handler: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Analytics engine error',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def handle_api_request(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle API Gateway requests for analytics"""[2]
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'POST' and '/analytics/population' in path:
            # Run population health analytics
            body = json.loads(event['body']) if event.get('body') else {}
            return run_population_health_analytics(body)
            
        elif http_method == 'POST' and '/analytics/predictive' in path:
            # Run predictive analytics
            body = json.loads(event['body']) if event.get('body') else {}
            return run_predictive_analytics(body)
            
        elif http_method == 'GET' and '/analytics/results' in path:
            # Get analytics results
            query_params = event.get('queryStringParameters', {}) or {}
            return get_analytics_results(query_params)
            
        elif http_method == 'POST' and '/analytics/insights' in path:
            # Generate AI insights
            body = json.loads(event['body']) if event.get('body') else {}
            return generate_ai_insights(body)
            
        elif http_method == 'POST' and '/analytics/dashboard' in path:
            # Create or update dashboard
            body = json.loads(event['body']) if event.get('body') else {}
            return create_analytics_dashboard(body)
            
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        logger.error(f"Error handling API request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_scheduled_analytics(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle scheduled analytics runs"""[4]
    try:
        detail = event.get('detail', {})
        analytics_type = detail.get('analytics_type', 'comprehensive')
        
        results = {}
        
        if analytics_type in ['comprehensive', 'population']:
            # Run population health analytics
            pop_results = run_population_health_analytics({
                'time_range': 'last_24_hours',
                'include_trends': True,
                'generate_alerts': True
            })
            results['population_health'] = pop_results
        
        if analytics_type in ['comprehensive', 'predictive']:
            # Run predictive analytics
            pred_results = run_predictive_analytics({
                'models': ['risk_prediction', 'outbreak_detection', 'resource_optimization'],
                'forecast_horizon': '7_days'
            })
            results['predictive'] = pred_results
        
        if analytics_type in ['comprehensive', 'insights']:
            # Generate AI insights
            insights_results = generate_ai_insights({
                'data_sources': ['health_records', 'device_data', 'consultation_data'],
                'insight_types': ['trends', 'anomalies', 'recommendations']
            })
            results['ai_insights'] = insights_results
        
        # Store results
        store_analytics_results({
            'analytics_run_id': f"scheduled_{int(datetime.now().timestamp())}",
            'run_type': 'scheduled',
            'analytics_type': analytics_type,
            'results': results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return {
            'statusCode': 200,
            'analytics_completed': True,
            'results_summary': {k: 'completed' for k in results.keys()},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in scheduled analytics: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def run_population_health_analytics(params: Dict[str, Any]) -> Dict[str, Any]:
    """Run comprehensive population health analytics"""[4]
    try:
        # Initialize population health analyzer
        analyzer = PopulationHealthAnalyzer()
        
        # Get time range parameters
        time_range = params.get('time_range', 'last_7_days')
        include_trends = params.get('include_trends', True)
        generate_alerts = params.get('generate_alerts', False)
        
        # Calculate time boundaries
        end_time = datetime.now(timezone.utc)
        if time_range == 'last_24_hours':
            start_time = end_time - timedelta(hours=24)
        elif time_range == 'last_7_days':
            start_time = end_time - timedelta(days=7)
        elif time_range == 'last_30_days':
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=7)
        
        # Fetch health data from multiple sources
        health_data = fetch_health_data_for_analytics(start_time, end_time)
        
        # Run population health analysis
        analysis_results = analyzer.analyze_population_health(
            health_data,
            include_demographics=True,
            include_risk_stratification=True,
            include_outcome_metrics=True
        )
        
        # Calculate key metrics
        key_metrics = analyzer.calculate_key_population_metrics(health_data)
        
        # Detect health trends if requested
        trends = {}
        if include_trends:
            trends = analyzer.detect_health_trends(health_data, time_range)
        
        # Generate alerts if requested
        alerts = []
        if generate_alerts:
            alerts = analyzer.generate_population_health_alerts(analysis_results)
        
        # Prepare comprehensive results
        results = {
            'analysis_id': f"pop_health_{int(datetime.now().timestamp())}",
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_days': (end_time - start_time).days
            },
            'population_metrics': key_metrics,
            'health_analysis': analysis_results,
            'trends': trends,
            'alerts': alerts,
            'data_quality': analyzer.assess_data_quality(health_data),
            'recommendations': analyzer.generate_population_recommendations(analysis_results),
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store results in DynamoDB
        store_population_metrics(results)
        
        # Send analytics event
        send_analytics_event(results, 'population_health_analysis_complete')
        
        logger.info(f"Population health analytics completed: {results['analysis_id']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'analysis_id': results['analysis_id'],
                'results': results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in population health analytics: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def run_predictive_analytics(params: Dict[str, Any]) -> Dict[str, Any]:
    """Run predictive analytics and forecasting"""[4]
    try:
        # Initialize predictive model engine
        model_engine = PredictiveModelEngine()
        
        # Get parameters
        models = params.get('models', ['risk_prediction'])
        forecast_horizon = params.get('forecast_horizon', '7_days')
        confidence_level = params.get('confidence_level', 0.95)
        
        # Fetch historical data for modeling
        historical_data = fetch_historical_data_for_modeling()
        
        results = {}
        
        # Run requested predictive models
        for model_type in models:
            try:
                if model_type == 'risk_prediction':
                    results[model_type] = model_engine.predict_patient_risk(
                        historical_data, 
                        forecast_horizon, 
                        confidence_level
                    )
                elif model_type == 'outbreak_detection':
                    results[model_type] = model_engine.detect_disease_outbreaks(
                        historical_data,
                        sensitivity_threshold=0.8
                    )
                elif model_type == 'resource_optimization':
                    results[model_type] = model_engine.optimize_resource_allocation(
                        historical_data,
                        forecast_horizon
                    )
                elif model_type == 'readmission_prediction':
                    results[model_type] = model_engine.predict_readmission_risk(
                        historical_data,
                        time_window='30_days'
                    )
                elif model_type == 'medication_adherence':
                    results[model_type] = model_engine.predict_medication_adherence(
                        historical_data
                    )
                
            except Exception as model_error:
                logger.error(f"Error in {model_type} model: {str(model_error)}")
                results[model_type] = {
                    'success': False,
                    'error': str(model_error)
                }
        
        # Generate model performance metrics
        performance_metrics = model_engine.calculate_model_performance(results)
        
        # Create comprehensive prediction results
        prediction_results = {
            'prediction_id': f"pred_{int(datetime.now().timestamp())}",
            'models_run': models,
            'forecast_horizon': forecast_horizon,
            'confidence_level': confidence_level,
            'predictions': results,
            'performance_metrics': performance_metrics,
            'data_summary': {
                'records_analyzed': len(historical_data) if historical_data else 0,
                'time_range_analyzed': get_data_time_range(historical_data)
            },
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store prediction results
        store_predictive_results(prediction_results)
        
        # Send analytics event
        send_analytics_event(prediction_results, 'predictive_analysis_complete')
        
        logger.info(f"Predictive analytics completed: {prediction_results['prediction_id']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'prediction_id': prediction_results['prediction_id'],
                'results': prediction_results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in predictive analytics: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def generate_ai_insights(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI-powered insights from health data"""[1]
    try:
        # Get parameters
        data_sources = params.get('data_sources', ['health_records'])
        insight_types = params.get('insight_types', ['trends'])
        time_range = params.get('time_range', 'last_30_days')
        
        # Fetch data from specified sources
        combined_data = {}
        for source in data_sources:
            if source == 'health_records':
                combined_data['health_records'] = fetch_health_records_data(time_range)
            elif source == 'device_data':
                combined_data['device_data'] = fetch_device_data(time_range)
            elif source == 'consultation_data':
                combined_data['consultation_data'] = fetch_consultation_data(time_range)
            elif source == 'emergency_data':
                combined_data['emergency_data'] = fetch_emergency_data(time_range)
        
        # Generate insights using Bedrock
        insights = {}
        
        for insight_type in insight_types:
            try:
                if insight_type == 'trends':
                    insights['trends'] = generate_trend_insights(combined_data)
                elif insight_type == 'anomalies':
                    insights['anomalies'] = detect_anomaly_insights(combined_data)
                elif insight_type == 'recommendations':
                    insights['recommendations'] = generate_recommendation_insights(combined_data)
                elif insight_type == 'risk_factors':
                    insights['risk_factors'] = identify_risk_factor_insights(combined_data)
                elif insight_type == 'outcomes':
                    insights['outcomes'] = analyze_outcome_insights(combined_data)
                
            except Exception as insight_error:
                logger.error(f"Error generating {insight_type} insights: {str(insight_error)}")
                insights[insight_type] = {
                    'success': False,
                    'error': str(insight_error)
                }
        
        # Compile comprehensive insights report
        insights_report = {
            'insights_id': f"insights_{int(datetime.now().timestamp())}",
            'data_sources': data_sources,
            'insight_types': insight_types,
            'time_range': time_range,
            'insights': insights,
            'data_summary': calculate_data_summary(combined_data),
            'confidence_scores': calculate_insight_confidence(insights),
            'actionable_items': extract_actionable_items(insights),
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store insights
        store_ai_insights(insights_report)
        
        # Send analytics event
        send_analytics_event(insights_report, 'ai_insights_generated')
        
        logger.info(f"AI insights generated: {insights_report['insights_id']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'insights_id': insights_report['insights_id'],
                'insights': insights_report,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def fetch_health_data_for_analytics(start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    """Fetch health data from multiple sources for analytics"""
    try:
        # Use Athena to query consolidated health data
        query = f"""
        SELECT 
            patient_id,
            timestamp,
            health_data,
            device_type,
            consultation_type,
            emergency_level
        FROM {ATHENA_DATABASE}.consolidated_health_data
        WHERE timestamp BETWEEN '{start_time.isoformat()}' AND '{end_time.isoformat()}'
        ORDER BY timestamp DESC
        """
        
        # Execute Athena query
        response = athena.start_query_execution(
            QueryString=query,
            WorkGroup=ATHENA_WORKGROUP,
            ResultConfiguration={
                'OutputLocation': f's3://{ANALYTICS_BUCKET}/athena-results/'
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Wait for query completion
        while True:
            result = athena.get_query_execution(QueryExecutionId=query_execution_id)
            status = result['QueryExecution']['Status']['State']
            
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            
            import time
            time.sleep(2)
        
        if status == 'SUCCEEDED':
            # Get query results
            results = athena.get_query_results(QueryExecutionId=query_execution_id)
            
            # Parse results into structured data
            health_data = []
            for row in results['ResultSet']['Rows'][1:]:  # Skip header
                data = row['Data']
                health_record = {
                    'patient_id': data[0].get('VarCharValue', ''),
                    'timestamp': data[1].get('VarCharValue', ''),
                    'health_data': json.loads(data[2].get('VarCharValue', '{}')),
                    'device_type': data[3].get('VarCharValue', ''),
                    'consultation_type': data[4].get('VarCharValue', ''),
                    'emergency_level': data[5].get('VarCharValue', '')
                }
                health_data.append(health_record)
            
            return health_data
        else:
            logger.error(f"Athena query failed: {status}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching health data: {str(e)}")
        return []

def generate_trend_insights(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate trend insights using AI"""[1]
    try:
        # Prepare data summary for AI analysis
        data_summary = prepare_data_for_ai_analysis(data)
        
        prompt = f"""
        Analyze the following healthcare data and identify significant trends:
        
        Data Summary: {json.dumps(data_summary, indent=2)}
        
        Please identify:
        1. Key health trends over time
        2. Emerging patterns in patient populations
        3. Changes in disease prevalence
        4. Seasonal or cyclical patterns
        5. Demographic-specific trends
        
        Provide insights in JSON format with trend descriptions, confidence levels, and supporting data.
        """
        
        # Call Bedrock for AI analysis
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3000,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
            "system": "You are a healthcare data analyst AI specializing in population health trends."
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        trend_analysis = response_body['content'][0]['text']
        
        return {
            'trend_analysis': trend_analysis,
            'data_points_analyzed': len(data_summary),
            'analysis_confidence': 0.85,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating trend insights: {str(e)}")
        return {
            'error': str(e),
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

def create_analytics_dashboard(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update QuickSight analytics dashboard"""
    try:
        if not QUICKSIGHT_ACCOUNT_ID:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'QuickSight not configured'})
            }
        
        dashboard_name = params.get('dashboard_name', 'HealthConnect Analytics')
        dashboard_type = params.get('dashboard_type', 'population_health')
        
        # Define dashboard configuration based on type
        if dashboard_type == 'population_health':
            dashboard_config = create_population_health_dashboard_config()
        elif dashboard_type == 'predictive':
            dashboard_config = create_predictive_dashboard_config()
        elif dashboard_type == 'operational':
            dashboard_config = create_operational_dashboard_config()
        else:
            dashboard_config = create_comprehensive_dashboard_config()
        
        # Create or update QuickSight dashboard
        dashboard_id = f"healthconnect-{dashboard_type}-{int(datetime.now().timestamp())}"
        
        try:
            response = quicksight.create_dashboard(
                AwsAccountId=QUICKSIGHT_ACCOUNT_ID,
                DashboardId=dashboard_id,
                Name=dashboard_name,
                Definition=dashboard_config,
                Permissions=[
                    {
                        'Principal': f'arn:aws:quicksight:us-east-1:{QUICKSIGHT_ACCOUNT_ID}:user/default/admin',
                        'Actions': [
                            'quicksight:DescribeDashboard',
                            'quicksight:ListDashboardVersions',
                            'quicksight:UpdateDashboardPermissions',
                            'quicksight:QueryDashboard',
                            'quicksight:UpdateDashboard',
                            'quicksight:DeleteDashboard'
                        ]
                    }
                ]
            )
            
            dashboard_url = f"https://quicksight.aws.amazon.com/sn/dashboards/{dashboard_id}"
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'dashboard_id': dashboard_id,
                    'dashboard_url': dashboard_url,
                    'dashboard_type': dashboard_type,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                # Update existing dashboard
                response = quicksight.update_dashboard(
                    AwsAccountId=QUICKSIGHT_ACCOUNT_ID,
                    DashboardId=dashboard_id,
                    Name=dashboard_name,
                    Definition=dashboard_config
                )
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'dashboard_updated': True,
                        'dashboard_id': dashboard_id,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                }
            else:
                raise
        
    except Exception as e:
        logger.error(f"Error creating analytics dashboard: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def store_analytics_results(results: Dict[str, Any]) -> None:
    """Store analytics results in DynamoDB"""
    try:
        table = dynamodb.Table(ANALYTICS_RESULTS_TABLE)
        
        results['ttl'] = int(datetime.now().timestamp()) + 7776000  # 90 days TTL
        
        table.put_item(Item=results)
        
        logger.info(f"Stored analytics results: {results.get('analytics_run_id', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Error storing analytics results: {str(e)}")

def send_analytics_event(results: Dict[str, Any], event_type: str) -> None:
    """Send analytics event to EventBridge"""
    try:
        event_detail = {
            'analytics_type': results.get('analytics_type', 'unknown'),
            'analysis_id': results.get('analysis_id', results.get('prediction_id', results.get('insights_id'))),
            'event_type': event_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'healthconnect.analytics',
                    'DetailType': f'Analytics {event_type.replace("_", " ").title()}',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Error sending analytics event: {str(e)}")

# Helper functions for data processing and dashboard creation would continue here...
