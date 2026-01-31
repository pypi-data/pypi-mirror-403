r'''
# aws-lambda-textract module

<!--BEGIN STABILITY BANNER-->---


![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

---
<!--END STABILITY BANNER-->

| **Reference Documentation**:| <span style="font-weight: normal">https://docs.aws.amazon.com/solutions/latest/constructs/</span>|
|:-------------|:-------------|

<div style="height:8px"></div>

| Language | Package |
|:---------|---------|
|![Python Logo](https://docs.aws.amazon.com/cdk/api/latest/img/python32.png) Python|`aws_solutions_constructs.aws_lambda_textract`|
|![Typescript Logo](https://docs.aws.amazon.com/cdk/api/latest/img/typescript32.png) Typescript|`@aws-solutions-constructs/aws-lambda-textract`|
|![Java Logo](https://docs.aws.amazon.com/cdk/api/latest/img/java32.png) Java|`software.amazon.awsconstructs.services.lambdatextract`|

## Overview

This AWS Solutions Construct implements an AWS Lambda function connected to Amazon Textract service. For asynchronous document analysis jobs, the construct can optionally create source and destination S3 buckets with appropriate IAM permissions for the Lambda function to interact with both buckets and Amazon Textract service.

For full documentation, see the [README.adoc](README.adoc) file.

---


© Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import aws_cdk.aws_sns as _aws_cdk_aws_sns_ceddda9d
import constructs as _constructs_77d1e7e8


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-textract.EnvironmentVariableDefinition",
    jsii_struct_bases=[],
    name_mapping={
        "default_name": "defaultName",
        "value": "value",
        "client_name_override": "clientNameOverride",
    },
)
class EnvironmentVariableDefinition:
    def __init__(
        self,
        *,
        default_name: builtins.str,
        value: builtins.str,
        client_name_override: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param default_name: -
        :param value: -
        :param client_name_override: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e068a91f4a013b176c445ecbe1a13bc6abf36eddb52b905fff7a3e8524e6954e)
            check_type(argname="argument default_name", value=default_name, expected_type=type_hints["default_name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument client_name_override", value=client_name_override, expected_type=type_hints["client_name_override"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "default_name": default_name,
            "value": value,
        }
        if client_name_override is not None:
            self._values["client_name_override"] = client_name_override

    @builtins.property
    def default_name(self) -> builtins.str:
        result = self._values.get("default_name")
        assert result is not None, "Required property 'default_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def client_name_override(self) -> typing.Optional[builtins.str]:
        result = self._values.get("client_name_override")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EnvironmentVariableDefinition(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class LambdaToTextract(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-textract.LambdaToTextract",
):
    '''
    :summary: The LambdaToTextract class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        async_jobs: typing.Optional[builtins.bool] = None,
        create_customer_managed_output_bucket: typing.Optional[builtins.bool] = None,
        data_access_role_arn_environment_variable_name: typing.Optional[builtins.str] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        destination_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
        destination_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        destination_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        enable_notification_topic_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        existing_destination_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_notification_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        existing_notification_topic_obj: typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic] = None,
        existing_source_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_destination_s3_access_logs: typing.Optional[builtins.bool] = None,
        log_source_s3_access_logs: typing.Optional[builtins.bool] = None,
        notification_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        notification_topic_encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        notification_topic_props: typing.Optional[typing.Union[_aws_cdk_aws_sns_ceddda9d.TopicProps, typing.Dict[builtins.str, typing.Any]]] = None,
        sns_notification_topic_arn_environment_variable_name: typing.Optional[builtins.str] = None,
        source_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
        source_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        source_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        use_same_bucket: typing.Optional[builtins.bool] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param async_jobs: Whether to enable asynchronous document analysis jobs. When true, source and destination S3 buckets will be created and the Lambda function will be granted permissions to start and get status of document analysis jobs. Default: - false
        :param create_customer_managed_output_bucket: Whether to create a bucket to receive the output of Textract batch jobs. If this is yes, the construct will set up an S3 bucket for output, if this is false, then Textract jobs will send their output to an AWS managed S3 bucket. Default: - true
        :param data_access_role_arn_environment_variable_name: Optional Name for the Lambda function environment variable set to the ARN of the IAM role used for asynchronous document analysis jobs. Only valid when asyncJobs is true. Default: - SNS_ROLE_ARN
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param destination_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the destination bucket. Only valid when asyncJobs is true. Default: - DESTINATION_BUCKET_NAME
        :param destination_bucket_props: Optional user provided props to override the default props for the destination S3 Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param destination_logging_bucket_props: Optional user provided props to override the default props for the destination S3 Logging Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param enable_notification_topic_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the SNS Topic is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: topicProps.masterKey, encryptionKey or encryptionKeyProps. Only valid when asyncJobs is true. Default: - None
        :param existing_destination_bucket_obj: Existing instance of S3 Bucket object for analysis results, providing both this and ``destinationBucketProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_notification_topic_encryption_key: If an existing topic is provided in the ``existingTopicObj`` property, and that topic is encrypted with a customer managed KMS key, this property must specify that key. Only valid when asyncJobs is true. Default: - None
        :param existing_notification_topic_obj: Optional - existing instance of SNS topic object, providing both this and ``topicProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_source_bucket_obj: Existing instance of S3 Bucket object for source documents, providing both this and ``sourceBucketProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` causes an error. Functon will have these Textract permissions: ['textract:DetectDocumentText', 'textract:AnalyzeDocument', 'textract:AnalyzeExpense', 'textract:AnalyzeID']. When asyncJobs is true, ['textract:Start/GetDocumentTextDetection', 'textract:Start/GetDocumentAnalysis', 'textract:Start/GetDocumentAnalysis', 'textract:Start/GetLendingAnalysis' ] Default: - Default properties are used.
        :param log_destination_s3_access_logs: Whether to turn on Access Logs for the destination S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Only valid when asyncJobs is true. Default: - true
        :param log_source_s3_access_logs: Whether to turn on Access Logs for the source S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Only valid when asyncJobs is true. Default: - true
        :param notification_topic_encryption_key: An optional, imported encryption key to encrypt the SNS Topic with. Only valid when asyncJobs is true. Default: - not specified.
        :param notification_topic_encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SNS Topic with. Only valid when asyncJobs is true. Default: - None
        :param notification_topic_props: Optional - user provided properties to override the default properties for the SNS topic. Providing both this and ``existingTopicObj`` causes an error. Only valid when asyncJobs is true. Default: - Default properties are used.
        :param sns_notification_topic_arn_environment_variable_name: Optional Name for the Lambda function environment variable set to the ARN of the SNS topic used for asynchronous job completion notifications. Only valid when asyncJobs is true. Default: - SNS_TOPIC_ARN
        :param source_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the source bucket. Only valid when asyncJobs is true. Default: - SOURCE_BUCKET_NAME
        :param source_bucket_props: Optional user provided props to override the default props for the source S3 Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param source_logging_bucket_props: Optional user provided props to override the default props for the source S3 Logging Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param use_same_bucket: Whether to use the same S3 bucket for both source and destination files. When true, only the source bucket will be created and used for both purposes. Only valid when asyncJobs is true. Default: - false
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :access: public
        :summary: Constructs a new instance of the LambdaToTextract class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__17950614c4f48d264a59570aaba598954199422d2cff90f6e1f26ba4d9625c52)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToTextractProps(
            async_jobs=async_jobs,
            create_customer_managed_output_bucket=create_customer_managed_output_bucket,
            data_access_role_arn_environment_variable_name=data_access_role_arn_environment_variable_name,
            deploy_vpc=deploy_vpc,
            destination_bucket_environment_variable_name=destination_bucket_environment_variable_name,
            destination_bucket_props=destination_bucket_props,
            destination_logging_bucket_props=destination_logging_bucket_props,
            enable_notification_topic_encryption_with_customer_managed_key=enable_notification_topic_encryption_with_customer_managed_key,
            existing_destination_bucket_obj=existing_destination_bucket_obj,
            existing_lambda_obj=existing_lambda_obj,
            existing_notification_topic_encryption_key=existing_notification_topic_encryption_key,
            existing_notification_topic_obj=existing_notification_topic_obj,
            existing_source_bucket_obj=existing_source_bucket_obj,
            existing_vpc=existing_vpc,
            lambda_function_props=lambda_function_props,
            log_destination_s3_access_logs=log_destination_s3_access_logs,
            log_source_s3_access_logs=log_source_s3_access_logs,
            notification_topic_encryption_key=notification_topic_encryption_key,
            notification_topic_encryption_key_props=notification_topic_encryption_key_props,
            notification_topic_props=notification_topic_props,
            sns_notification_topic_arn_environment_variable_name=sns_notification_topic_arn_environment_variable_name,
            source_bucket_environment_variable_name=source_bucket_environment_variable_name,
            source_bucket_props=source_bucket_props,
            source_logging_bucket_props=source_logging_bucket_props,
            use_same_bucket=use_same_bucket,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="destinationBucket")
    def destination_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "destinationBucket"))

    @builtins.property
    @jsii.member(jsii_name="destinationBucketInterface")
    def destination_bucket_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], jsii.get(self, "destinationBucketInterface"))

    @builtins.property
    @jsii.member(jsii_name="destinationLoggingBucket")
    def destination_logging_bucket(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "destinationLoggingBucket"))

    @builtins.property
    @jsii.member(jsii_name="notificationTopicEncryptionKey")
    def notification_topic_encryption_key(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "notificationTopicEncryptionKey"))

    @builtins.property
    @jsii.member(jsii_name="snsNotificationTopic")
    def sns_notification_topic(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic]:
        return typing.cast(typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic], jsii.get(self, "snsNotificationTopic"))

    @builtins.property
    @jsii.member(jsii_name="sourceBucket")
    def source_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "sourceBucket"))

    @builtins.property
    @jsii.member(jsii_name="sourceBucketInterface")
    def source_bucket_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], jsii.get(self, "sourceBucketInterface"))

    @builtins.property
    @jsii.member(jsii_name="sourceLoggingBucket")
    def source_logging_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "sourceLoggingBucket"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-textract.LambdaToTextractProps",
    jsii_struct_bases=[],
    name_mapping={
        "async_jobs": "asyncJobs",
        "create_customer_managed_output_bucket": "createCustomerManagedOutputBucket",
        "data_access_role_arn_environment_variable_name": "dataAccessRoleArnEnvironmentVariableName",
        "deploy_vpc": "deployVpc",
        "destination_bucket_environment_variable_name": "destinationBucketEnvironmentVariableName",
        "destination_bucket_props": "destinationBucketProps",
        "destination_logging_bucket_props": "destinationLoggingBucketProps",
        "enable_notification_topic_encryption_with_customer_managed_key": "enableNotificationTopicEncryptionWithCustomerManagedKey",
        "existing_destination_bucket_obj": "existingDestinationBucketObj",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_notification_topic_encryption_key": "existingNotificationTopicEncryptionKey",
        "existing_notification_topic_obj": "existingNotificationTopicObj",
        "existing_source_bucket_obj": "existingSourceBucketObj",
        "existing_vpc": "existingVpc",
        "lambda_function_props": "lambdaFunctionProps",
        "log_destination_s3_access_logs": "logDestinationS3AccessLogs",
        "log_source_s3_access_logs": "logSourceS3AccessLogs",
        "notification_topic_encryption_key": "notificationTopicEncryptionKey",
        "notification_topic_encryption_key_props": "notificationTopicEncryptionKeyProps",
        "notification_topic_props": "notificationTopicProps",
        "sns_notification_topic_arn_environment_variable_name": "snsNotificationTopicArnEnvironmentVariableName",
        "source_bucket_environment_variable_name": "sourceBucketEnvironmentVariableName",
        "source_bucket_props": "sourceBucketProps",
        "source_logging_bucket_props": "sourceLoggingBucketProps",
        "use_same_bucket": "useSameBucket",
        "vpc_props": "vpcProps",
    },
)
class LambdaToTextractProps:
    def __init__(
        self,
        *,
        async_jobs: typing.Optional[builtins.bool] = None,
        create_customer_managed_output_bucket: typing.Optional[builtins.bool] = None,
        data_access_role_arn_environment_variable_name: typing.Optional[builtins.str] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        destination_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
        destination_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        destination_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        enable_notification_topic_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        existing_destination_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_notification_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        existing_notification_topic_obj: typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic] = None,
        existing_source_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_destination_s3_access_logs: typing.Optional[builtins.bool] = None,
        log_source_s3_access_logs: typing.Optional[builtins.bool] = None,
        notification_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        notification_topic_encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        notification_topic_props: typing.Optional[typing.Union[_aws_cdk_aws_sns_ceddda9d.TopicProps, typing.Dict[builtins.str, typing.Any]]] = None,
        sns_notification_topic_arn_environment_variable_name: typing.Optional[builtins.str] = None,
        source_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
        source_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        source_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        use_same_bucket: typing.Optional[builtins.bool] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param async_jobs: Whether to enable asynchronous document analysis jobs. When true, source and destination S3 buckets will be created and the Lambda function will be granted permissions to start and get status of document analysis jobs. Default: - false
        :param create_customer_managed_output_bucket: Whether to create a bucket to receive the output of Textract batch jobs. If this is yes, the construct will set up an S3 bucket for output, if this is false, then Textract jobs will send their output to an AWS managed S3 bucket. Default: - true
        :param data_access_role_arn_environment_variable_name: Optional Name for the Lambda function environment variable set to the ARN of the IAM role used for asynchronous document analysis jobs. Only valid when asyncJobs is true. Default: - SNS_ROLE_ARN
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param destination_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the destination bucket. Only valid when asyncJobs is true. Default: - DESTINATION_BUCKET_NAME
        :param destination_bucket_props: Optional user provided props to override the default props for the destination S3 Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param destination_logging_bucket_props: Optional user provided props to override the default props for the destination S3 Logging Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param enable_notification_topic_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the SNS Topic is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: topicProps.masterKey, encryptionKey or encryptionKeyProps. Only valid when asyncJobs is true. Default: - None
        :param existing_destination_bucket_obj: Existing instance of S3 Bucket object for analysis results, providing both this and ``destinationBucketProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_notification_topic_encryption_key: If an existing topic is provided in the ``existingTopicObj`` property, and that topic is encrypted with a customer managed KMS key, this property must specify that key. Only valid when asyncJobs is true. Default: - None
        :param existing_notification_topic_obj: Optional - existing instance of SNS topic object, providing both this and ``topicProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_source_bucket_obj: Existing instance of S3 Bucket object for source documents, providing both this and ``sourceBucketProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` causes an error. Functon will have these Textract permissions: ['textract:DetectDocumentText', 'textract:AnalyzeDocument', 'textract:AnalyzeExpense', 'textract:AnalyzeID']. When asyncJobs is true, ['textract:Start/GetDocumentTextDetection', 'textract:Start/GetDocumentAnalysis', 'textract:Start/GetDocumentAnalysis', 'textract:Start/GetLendingAnalysis' ] Default: - Default properties are used.
        :param log_destination_s3_access_logs: Whether to turn on Access Logs for the destination S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Only valid when asyncJobs is true. Default: - true
        :param log_source_s3_access_logs: Whether to turn on Access Logs for the source S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Only valid when asyncJobs is true. Default: - true
        :param notification_topic_encryption_key: An optional, imported encryption key to encrypt the SNS Topic with. Only valid when asyncJobs is true. Default: - not specified.
        :param notification_topic_encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SNS Topic with. Only valid when asyncJobs is true. Default: - None
        :param notification_topic_props: Optional - user provided properties to override the default properties for the SNS topic. Providing both this and ``existingTopicObj`` causes an error. Only valid when asyncJobs is true. Default: - Default properties are used.
        :param sns_notification_topic_arn_environment_variable_name: Optional Name for the Lambda function environment variable set to the ARN of the SNS topic used for asynchronous job completion notifications. Only valid when asyncJobs is true. Default: - SNS_TOPIC_ARN
        :param source_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the source bucket. Only valid when asyncJobs is true. Default: - SOURCE_BUCKET_NAME
        :param source_bucket_props: Optional user provided props to override the default props for the source S3 Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param source_logging_bucket_props: Optional user provided props to override the default props for the source S3 Logging Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param use_same_bucket: Whether to use the same S3 bucket for both source and destination files. When true, only the source bucket will be created and used for both purposes. Only valid when asyncJobs is true. Default: - false
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :summary: The properties for the LambdaToTextract class.
        '''
        if isinstance(destination_bucket_props, dict):
            destination_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**destination_bucket_props)
        if isinstance(destination_logging_bucket_props, dict):
            destination_logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**destination_logging_bucket_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(notification_topic_encryption_key_props, dict):
            notification_topic_encryption_key_props = _aws_cdk_aws_kms_ceddda9d.KeyProps(**notification_topic_encryption_key_props)
        if isinstance(notification_topic_props, dict):
            notification_topic_props = _aws_cdk_aws_sns_ceddda9d.TopicProps(**notification_topic_props)
        if isinstance(source_bucket_props, dict):
            source_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**source_bucket_props)
        if isinstance(source_logging_bucket_props, dict):
            source_logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**source_logging_bucket_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bcb2f09b176f317eb5f8bad81ac079e56df2df6326e32f49ff4a08e8b4420b2b)
            check_type(argname="argument async_jobs", value=async_jobs, expected_type=type_hints["async_jobs"])
            check_type(argname="argument create_customer_managed_output_bucket", value=create_customer_managed_output_bucket, expected_type=type_hints["create_customer_managed_output_bucket"])
            check_type(argname="argument data_access_role_arn_environment_variable_name", value=data_access_role_arn_environment_variable_name, expected_type=type_hints["data_access_role_arn_environment_variable_name"])
            check_type(argname="argument deploy_vpc", value=deploy_vpc, expected_type=type_hints["deploy_vpc"])
            check_type(argname="argument destination_bucket_environment_variable_name", value=destination_bucket_environment_variable_name, expected_type=type_hints["destination_bucket_environment_variable_name"])
            check_type(argname="argument destination_bucket_props", value=destination_bucket_props, expected_type=type_hints["destination_bucket_props"])
            check_type(argname="argument destination_logging_bucket_props", value=destination_logging_bucket_props, expected_type=type_hints["destination_logging_bucket_props"])
            check_type(argname="argument enable_notification_topic_encryption_with_customer_managed_key", value=enable_notification_topic_encryption_with_customer_managed_key, expected_type=type_hints["enable_notification_topic_encryption_with_customer_managed_key"])
            check_type(argname="argument existing_destination_bucket_obj", value=existing_destination_bucket_obj, expected_type=type_hints["existing_destination_bucket_obj"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_notification_topic_encryption_key", value=existing_notification_topic_encryption_key, expected_type=type_hints["existing_notification_topic_encryption_key"])
            check_type(argname="argument existing_notification_topic_obj", value=existing_notification_topic_obj, expected_type=type_hints["existing_notification_topic_obj"])
            check_type(argname="argument existing_source_bucket_obj", value=existing_source_bucket_obj, expected_type=type_hints["existing_source_bucket_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument log_destination_s3_access_logs", value=log_destination_s3_access_logs, expected_type=type_hints["log_destination_s3_access_logs"])
            check_type(argname="argument log_source_s3_access_logs", value=log_source_s3_access_logs, expected_type=type_hints["log_source_s3_access_logs"])
            check_type(argname="argument notification_topic_encryption_key", value=notification_topic_encryption_key, expected_type=type_hints["notification_topic_encryption_key"])
            check_type(argname="argument notification_topic_encryption_key_props", value=notification_topic_encryption_key_props, expected_type=type_hints["notification_topic_encryption_key_props"])
            check_type(argname="argument notification_topic_props", value=notification_topic_props, expected_type=type_hints["notification_topic_props"])
            check_type(argname="argument sns_notification_topic_arn_environment_variable_name", value=sns_notification_topic_arn_environment_variable_name, expected_type=type_hints["sns_notification_topic_arn_environment_variable_name"])
            check_type(argname="argument source_bucket_environment_variable_name", value=source_bucket_environment_variable_name, expected_type=type_hints["source_bucket_environment_variable_name"])
            check_type(argname="argument source_bucket_props", value=source_bucket_props, expected_type=type_hints["source_bucket_props"])
            check_type(argname="argument source_logging_bucket_props", value=source_logging_bucket_props, expected_type=type_hints["source_logging_bucket_props"])
            check_type(argname="argument use_same_bucket", value=use_same_bucket, expected_type=type_hints["use_same_bucket"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if async_jobs is not None:
            self._values["async_jobs"] = async_jobs
        if create_customer_managed_output_bucket is not None:
            self._values["create_customer_managed_output_bucket"] = create_customer_managed_output_bucket
        if data_access_role_arn_environment_variable_name is not None:
            self._values["data_access_role_arn_environment_variable_name"] = data_access_role_arn_environment_variable_name
        if deploy_vpc is not None:
            self._values["deploy_vpc"] = deploy_vpc
        if destination_bucket_environment_variable_name is not None:
            self._values["destination_bucket_environment_variable_name"] = destination_bucket_environment_variable_name
        if destination_bucket_props is not None:
            self._values["destination_bucket_props"] = destination_bucket_props
        if destination_logging_bucket_props is not None:
            self._values["destination_logging_bucket_props"] = destination_logging_bucket_props
        if enable_notification_topic_encryption_with_customer_managed_key is not None:
            self._values["enable_notification_topic_encryption_with_customer_managed_key"] = enable_notification_topic_encryption_with_customer_managed_key
        if existing_destination_bucket_obj is not None:
            self._values["existing_destination_bucket_obj"] = existing_destination_bucket_obj
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_notification_topic_encryption_key is not None:
            self._values["existing_notification_topic_encryption_key"] = existing_notification_topic_encryption_key
        if existing_notification_topic_obj is not None:
            self._values["existing_notification_topic_obj"] = existing_notification_topic_obj
        if existing_source_bucket_obj is not None:
            self._values["existing_source_bucket_obj"] = existing_source_bucket_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if log_destination_s3_access_logs is not None:
            self._values["log_destination_s3_access_logs"] = log_destination_s3_access_logs
        if log_source_s3_access_logs is not None:
            self._values["log_source_s3_access_logs"] = log_source_s3_access_logs
        if notification_topic_encryption_key is not None:
            self._values["notification_topic_encryption_key"] = notification_topic_encryption_key
        if notification_topic_encryption_key_props is not None:
            self._values["notification_topic_encryption_key_props"] = notification_topic_encryption_key_props
        if notification_topic_props is not None:
            self._values["notification_topic_props"] = notification_topic_props
        if sns_notification_topic_arn_environment_variable_name is not None:
            self._values["sns_notification_topic_arn_environment_variable_name"] = sns_notification_topic_arn_environment_variable_name
        if source_bucket_environment_variable_name is not None:
            self._values["source_bucket_environment_variable_name"] = source_bucket_environment_variable_name
        if source_bucket_props is not None:
            self._values["source_bucket_props"] = source_bucket_props
        if source_logging_bucket_props is not None:
            self._values["source_logging_bucket_props"] = source_logging_bucket_props
        if use_same_bucket is not None:
            self._values["use_same_bucket"] = use_same_bucket
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def async_jobs(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable asynchronous document analysis jobs.

        When true, source and destination S3 buckets will be created and the Lambda function
        will be granted permissions to start and get status of document analysis jobs.

        :default: - false
        '''
        result = self._values.get("async_jobs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def create_customer_managed_output_bucket(self) -> typing.Optional[builtins.bool]:
        '''Whether to create a bucket to receive the output of Textract batch jobs.

        If this is yes, the construct will set up an S3 bucket for
        output, if this is false, then Textract jobs will send their output to an AWS managed S3 bucket.

        :default: - true
        '''
        result = self._values.get("create_customer_managed_output_bucket")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def data_access_role_arn_environment_variable_name(
        self,
    ) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the ARN of the IAM role used for asynchronous document analysis jobs.

        Only valid when asyncJobs is true.

        :default: - SNS_ROLE_ARN
        '''
        result = self._values.get("data_access_role_arn_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def deploy_vpc(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a new VPC.

        :default: - false
        '''
        result = self._values.get("deploy_vpc")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def destination_bucket_environment_variable_name(
        self,
    ) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the name of the destination bucket.

        Only valid when asyncJobs is true.

        :default: - DESTINATION_BUCKET_NAME
        '''
        result = self._values.get("destination_bucket_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the destination S3 Bucket.

        Only valid when asyncJobs is true.

        :default: - Default props are used
        '''
        result = self._values.get("destination_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def destination_logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the destination S3 Logging Bucket.

        Only valid when asyncJobs is true.

        :default: - Default props are used
        '''
        result = self._values.get("destination_logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def enable_notification_topic_encryption_with_customer_managed_key(
        self,
    ) -> typing.Optional[builtins.bool]:
        '''If no key is provided, this flag determines whether the SNS Topic is encrypted with a new CMK or an AWS managed key.

        This flag is ignored if any of the following are defined: topicProps.masterKey, encryptionKey or encryptionKeyProps.
        Only valid when asyncJobs is true.

        :default: - None
        '''
        result = self._values.get("enable_notification_topic_encryption_with_customer_managed_key")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def existing_destination_bucket_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Existing instance of S3 Bucket object for analysis results, providing both this and ``destinationBucketProps`` will cause an error.

        Only valid when asyncJobs is true.

        :default: - None
        '''
        result = self._values.get("existing_destination_bucket_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], result)

    @builtins.property
    def existing_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def existing_notification_topic_encryption_key(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''If an existing topic is provided in the ``existingTopicObj`` property, and that topic is encrypted with a customer managed KMS key, this property must specify that key.

        Only valid when asyncJobs is true.

        :default: - None
        '''
        result = self._values.get("existing_notification_topic_encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def existing_notification_topic_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic]:
        '''Optional - existing instance of SNS topic object, providing both this and ``topicProps`` will cause an error.

        Only valid when asyncJobs is true.

        :default: - None
        '''
        result = self._values.get("existing_notification_topic_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic], result)

    @builtins.property
    def existing_source_bucket_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Existing instance of S3 Bucket object for source documents, providing both this and ``sourceBucketProps`` will cause an error.

        Only valid when asyncJobs is true.

        :default: - None
        '''
        result = self._values.get("existing_source_bucket_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC for the construct to use (construct will NOT create a new VPC in this case).'''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the Lambda function.

        Providing both this and ``existingLambdaObj``
        causes an error.

        Functon will have these Textract permissions: ['textract:DetectDocumentText', 'textract:AnalyzeDocument', 'textract:AnalyzeExpense',
        'textract:AnalyzeID']. When asyncJobs is true, ['textract:Start/GetDocumentTextDetection', 'textract:Start/GetDocumentAnalysis',
        'textract:Start/GetDocumentAnalysis', 'textract:Start/GetLendingAnalysis' ]

        :default: - Default properties are used.
        '''
        result = self._values.get("lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def log_destination_s3_access_logs(self) -> typing.Optional[builtins.bool]:
        '''Whether to turn on Access Logs for the destination S3 bucket with the associated storage costs.

        Enabling Access Logging is a best practice.
        Only valid when asyncJobs is true.

        :default: - true
        '''
        result = self._values.get("log_destination_s3_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def log_source_s3_access_logs(self) -> typing.Optional[builtins.bool]:
        '''Whether to turn on Access Logs for the source S3 bucket with the associated storage costs.

        Enabling Access Logging is a best practice.
        Only valid when asyncJobs is true.

        :default: - true
        '''
        result = self._values.get("log_source_s3_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def notification_topic_encryption_key(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''An optional, imported encryption key to encrypt the SNS Topic with.

        Only valid when asyncJobs is true.

        :default: - not specified.
        '''
        result = self._values.get("notification_topic_encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def notification_topic_encryption_key_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps]:
        '''Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SNS Topic with.

        Only valid when asyncJobs is true.

        :default: - None
        '''
        result = self._values.get("notification_topic_encryption_key_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps], result)

    @builtins.property
    def notification_topic_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sns_ceddda9d.TopicProps]:
        '''Optional - user provided properties to override the default properties for the SNS topic.

        Providing both this and ``existingTopicObj`` causes an error. Only valid when asyncJobs is true.

        :default: - Default properties are used.
        '''
        result = self._values.get("notification_topic_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sns_ceddda9d.TopicProps], result)

    @builtins.property
    def sns_notification_topic_arn_environment_variable_name(
        self,
    ) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the ARN of the SNS topic used for asynchronous job completion notifications.

        Only valid when asyncJobs is true.

        :default: - SNS_TOPIC_ARN
        '''
        result = self._values.get("sns_notification_topic_arn_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def source_bucket_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the name of the source bucket.

        Only valid when asyncJobs is true.

        :default: - SOURCE_BUCKET_NAME
        '''
        result = self._values.get("source_bucket_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def source_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the source S3 Bucket.

        Only valid when asyncJobs is true.

        :default: - Default props are used
        '''
        result = self._values.get("source_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def source_logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the source S3 Logging Bucket.

        Only valid when asyncJobs is true.

        :default: - Default props are used
        '''
        result = self._values.get("source_logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def use_same_bucket(self) -> typing.Optional[builtins.bool]:
        '''Whether to use the same S3 bucket for both source and destination files.

        When true, only the source bucket will be created and used
        for both purposes. Only valid when asyncJobs is true.

        :default: - false
        '''
        result = self._values.get("use_same_bucket")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Properties to override default properties if deployVpc is true.'''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LambdaToTextractProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "EnvironmentVariableDefinition",
    "LambdaToTextract",
    "LambdaToTextractProps",
]

publication.publish()

def _typecheckingstub__e068a91f4a013b176c445ecbe1a13bc6abf36eddb52b905fff7a3e8524e6954e(
    *,
    default_name: builtins.str,
    value: builtins.str,
    client_name_override: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__17950614c4f48d264a59570aaba598954199422d2cff90f6e1f26ba4d9625c52(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    async_jobs: typing.Optional[builtins.bool] = None,
    create_customer_managed_output_bucket: typing.Optional[builtins.bool] = None,
    data_access_role_arn_environment_variable_name: typing.Optional[builtins.str] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    destination_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
    destination_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    destination_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_notification_topic_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    existing_destination_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_notification_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    existing_notification_topic_obj: typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic] = None,
    existing_source_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_destination_s3_access_logs: typing.Optional[builtins.bool] = None,
    log_source_s3_access_logs: typing.Optional[builtins.bool] = None,
    notification_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    notification_topic_encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    notification_topic_props: typing.Optional[typing.Union[_aws_cdk_aws_sns_ceddda9d.TopicProps, typing.Dict[builtins.str, typing.Any]]] = None,
    sns_notification_topic_arn_environment_variable_name: typing.Optional[builtins.str] = None,
    source_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
    source_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    source_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    use_same_bucket: typing.Optional[builtins.bool] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bcb2f09b176f317eb5f8bad81ac079e56df2df6326e32f49ff4a08e8b4420b2b(
    *,
    async_jobs: typing.Optional[builtins.bool] = None,
    create_customer_managed_output_bucket: typing.Optional[builtins.bool] = None,
    data_access_role_arn_environment_variable_name: typing.Optional[builtins.str] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    destination_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
    destination_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    destination_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_notification_topic_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    existing_destination_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_notification_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    existing_notification_topic_obj: typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic] = None,
    existing_source_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_destination_s3_access_logs: typing.Optional[builtins.bool] = None,
    log_source_s3_access_logs: typing.Optional[builtins.bool] = None,
    notification_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    notification_topic_encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    notification_topic_props: typing.Optional[typing.Union[_aws_cdk_aws_sns_ceddda9d.TopicProps, typing.Dict[builtins.str, typing.Any]]] = None,
    sns_notification_topic_arn_environment_variable_name: typing.Optional[builtins.str] = None,
    source_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
    source_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    source_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    use_same_bucket: typing.Optional[builtins.bool] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
