"""
Cognito Stack for HealthConnect AI
Implements user authentication and authorization
"""

from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    Duration,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class CognitoStack(Stack):
    """Cognito infrastructure stack for user management"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        env_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create Cognito resources
        self.create_user_pool()
        self.create_identity_pool()
        self.create_user_groups()
        self.create_lambda_triggers()
        
    def create_user_pool(self):
        """Create Cognito User Pool"""
        
        # Pre-signup Lambda trigger
        pre_signup_trigger = lambda_.Function(
            self, "PreSignupTrigger",
            function_name=f"healthconnect-pre-signup-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Pre-signup trigger: {json.dumps(event)}")
    
    # Auto-confirm users for healthcare providers
    if event['request']['userAttributes'].get('custom:user_type') == 'provider':
        event['response']['autoConfirmUser'] = True
        event['response']['autoVerifyEmail'] = True
    
    return event
            """),
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Post-confirmation Lambda trigger
        post_confirmation_trigger = lambda_.Function(
            self, "PostConfirmationTrigger",
            function_name=f"healthconnect-post-confirmation-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Post-confirmation trigger: {json.dumps(event)}")
    
    # Add user to appropriate group based on user type
    cognito = boto3.client('cognito-idp')
    user_pool_id = event['userPoolId']
    username = event['userName']
    user_type = event['request']['userAttributes'].get('custom:user_type', 'patient')
    
    try:
        # Add user to group
        group_name = f"HealthConnect-{user_type.title()}s"
        cognito.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        logger.info(f"Added user {username} to group {group_name}")
    except Exception as e:
        logger.error(f"Error adding user to group: {str(e)}")
    
    return event
            """),
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Grant permissions to post-confirmation trigger
        post_confirmation_trigger.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:AdminAddUserToGroup",
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminListGroupsForUser"
                ],
                resources=[f"arn:aws:cognito-idp:{self.region}:{self.account}:userpool/*"]
            )
        )
        
        # Create User Pool
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name=f"healthconnect-users-{self.env_name}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True
            ),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                ),
                given_name=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                ),
                family_name=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                ),
                phone_number=cognito.StandardAttribute(
                    required=False,
                    mutable=True
                )
            ),
            custom_attributes={
                "user_type": cognito.StringAttribute(
                    min_len=1,
                    max_len=20,
                    mutable=True
                ),
                "organization": cognito.StringAttribute(
                    min_len=1,
                    max_len=100,
                    mutable=True
                ),
                "license_number": cognito.StringAttribute(
                    min_len=1,
                    max_len=50,
                    mutable=True
                ),
                "specialty": cognito.StringAttribute(
                    min_len=1,
                    max_len=50,
                    mutable=True
                )
            },
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            lambda_triggers=cognito.UserPoolTriggers(
                pre_sign_up=pre_signup_trigger,
                post_confirmation=post_confirmation_trigger
            ),
            removal_policy=self.get_removal_policy(),
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=True,
                otp=True
            ),
            device_tracking=cognito.DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=True
            )
        )
        
        # Create User Pool Domain
        self.user_pool_domain = cognito.UserPoolDomain(
            self, "UserPoolDomain",
            user_pool=self.user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"healthconnect-{self.env_name}"
            )
        )
        
        # Create User Pool Clients
        
        # Web App Client
        self.web_app_client = cognito.UserPoolClient(
            self, "WebAppClient",
            user_pool=self.user_pool,
            user_pool_client_name=f"healthconnect-web-{self.env_name}",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                custom=True,
                admin_user_password=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE
                ],
                callback_urls=[
                    f"https://healthconnect-{self.env_name}.com/callback",
                    "http://localhost:3000/callback"
                ],
                logout_urls=[
                    f"https://healthconnect-{self.env_name}.com/logout",
                    "http://localhost:3000/logout"
                ]
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            read_attributes=cognito.ClientAttributes(
                email=True,
                given_name=True,
                family_name=True,
                phone_number=True,
                custom_attributes=["user_type", "organization", "specialty"]
            ),
            write_attributes=cognito.ClientAttributes(
                email=True,
                given_name=True,
                family_name=True,
                phone_number=True,
                custom_attributes=["user_type", "organization", "specialty"]
            ),
            token_validity=cognito.TokenValidity(
                access_token=Duration.hours(1),
                id_token=Duration.hours(1),
                refresh_token=Duration.days(30)
            ),
            refresh_token_validity=Duration.days(30),
            prevent_user_existence_errors=True
        )
        
        # Mobile App Client
        self.mobile_app_client = cognito.UserPoolClient(
            self, "MobileAppClient",
            user_pool=self.user_pool,
            user_pool_client_name=f"healthconnect-mobile-{self.env_name}",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                custom=True
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            token_validity=cognito.TokenValidity(
                access_token=Duration.hours(1),
                id_token=Duration.hours(1),
                refresh_token=Duration.days(30)
            ),
            prevent_user_existence_errors=True
        )
        
        # Admin Client (with client secret)
        self.admin_client = cognito.UserPoolClient(
            self, "AdminClient",
            user_pool=self.user_pool,
            user_pool_client_name=f"healthconnect-admin-{self.env_name}",
            generate_secret=True,
            auth_flows=cognito.AuthFlow(
                admin_user_password=True,
                custom=True
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            token_validity=cognito.TokenValidity(
                access_token=Duration.minutes(30),
                id_token=Duration.minutes(30),
                refresh_token=Duration.hours(8)
            ),
            prevent_user_existence_errors=True
        )
    
    def create_identity_pool(self):
        """Create Cognito Identity Pool for AWS resource access"""
        
        # Create Identity Pool
        self.identity_pool = cognito.CfnIdentityPool(
            self, "IdentityPool",
            identity_pool_name=f"healthconnect_identity_pool_{self.env_name}",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.web_app_client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name
                ),
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.mobile_app_client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name
                )
            ]
        )
        
        # Create IAM roles for authenticated users
        
        # Patient Role
        patient_role = iam.Role(
            self, "PatientRole",
            role_name=f"HealthConnect-Patient-{self.env_name}",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            ),
            inline_policies={
                "PatientPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject"
                            ],
                            resources=[
                                f"arn:aws:s3:::healthconnect-*/{self.env_name}/patients/${{cognito-identity.amazonaws.com:sub}}/*"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "execute-api:Invoke"
                            ],
                            resources=[
                                f"arn:aws:execute-api:{self.region}:{self.account}:*/*/GET/health/*",
                                f"arn:aws:execute-api:{self.region}:{self.account}:*/*/POST/health/*",
                                f"arn:aws:execute-api:{self.region}:{self.account}:*/*/GET/consultation/*",
                                f"arn:aws:execute-api:{self.region}:{self.account}:*/*/POST/consultation/*"
                            ]
                        )
                    ]
                )
            }
        )
        
        # Provider Role
        provider_role = iam.Role(
            self, "ProviderRole",
            role_name=f"HealthConnect-Provider-{self.env_name}",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            ),
            inline_policies={
                "ProviderPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                f"arn:aws:s3:::healthconnect-*/{self.env_name}/providers/${{cognito-identity.amazonaws.com:sub}}/*",
                                f"arn:aws:s3:::healthconnect-*/{self.env_name}/shared/*"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "execute-api:Invoke"
                            ],
                            resources=[
                                f"arn:aws:execute-api:{self.region}:{self.account}:*/*/*"
                            ]
                        )
                    ]
                )
            }
        )
        
        # Admin Role
        admin_role = iam.Role(
            self, "AdminRole",
            role_name=f"HealthConnect-Admin-{self.env_name}",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("PowerUserAccess")
            ]
        )
        
        # Attach roles to Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(
            self, "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={
                "authenticated": patient_role.role_arn
            },
            role_mappings={
                self.user_pool.user_pool_provider_name: cognito.CfnIdentityPoolRoleAttachment.RoleMappingProperty(
                    type="Rules",
                    ambiguous_role_resolution="AuthenticatedRole",
                    rules_configuration=cognito.CfnIdentityPoolRoleAttachment.RulesConfigurationProperty(
                        rules=[
                            cognito.CfnIdentityPoolRoleAttachment.MappingRuleProperty(
                                claim="custom:user_type",
                                match_type="Equals",
                                value="patient",
                                role_arn=patient_role.role_arn
                            ),
                            cognito.CfnIdentityPoolRoleAttachment.MappingRuleProperty(
                                claim="custom:user_type",
                                match_type="Equals",
                                value="provider",
                                role_arn=provider_role.role_arn
                            ),
                            cognito.CfnIdentityPoolRoleAttachment.MappingRuleProperty(
                                claim="custom:user_type",
                                match_type="Equals",
                                value="admin",
                                role_arn=admin_role.role_arn
                            )
                        ]
                    )
                )
            }
        )
    
    def create_user_groups(self):
        """Create Cognito User Pool Groups"""
        
        # Patients Group
        cognito.CfnUserPoolGroup(
            self, "PatientsGroup",
            group_name="HealthConnect-Patients",
            user_pool_id=self.user_pool.user_pool_id,
            description="Group for patient users",
            precedence=3
        )
        
        # Providers Group
        cognito.CfnUserPoolGroup(
            self, "ProvidersGroup",
            group_name="HealthConnect-Providers",
            user_pool_id=self.user_pool.user_pool_id,
            description="Group for healthcare provider users",
            precedence=2
        )
        
        # Admins Group
        cognito.CfnUserPoolGroup(
            self, "AdminsGroup",
            group_name="HealthConnect-Admins",
            user_pool_id=self.user_pool.user_pool_id,
            description="Group for administrator users",
            precedence=1
        )
    
    def create_lambda_triggers(self):
        """Create additional Lambda triggers for Cognito"""
        
        # Pre-authentication trigger for additional security
        pre_auth_trigger = lambda_.Function(
            self, "PreAuthTrigger",
            function_name=f"healthconnect-pre-auth-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Pre-authentication trigger: {json.dumps(event)}")
    
    # Add custom authentication logic here
    # For example, check if user account is active
    
    # Log authentication attempt
    username = event['userName']
    client_id = event['callerContext']['clientId']
    source_ip = event['request']['userContextData']['ipAddress']
    
    logger.info(f"Authentication attempt: user={username}, client={client_id}, ip={source_ip}")
    
    return event
            """),
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Add trigger to user pool (would need to be done via console or CLI)
        # as CDK doesn't support all trigger types yet
    
    def get_removal_policy(self):
        """Get removal policy based on environment"""
        if self.env_name == "prod":
            return RemovalPolicy.RETAIN
        else:
            return RemovalPolicy.DESTROY
    
    @property
    def account(self) -> str:
        """Get AWS account ID"""
        return Stack.of(self).account
    
    @property
    def region(self) -> str:
        """Get AWS region"""
        return Stack.of(self).region
