#!/bin/bash

awslocal ssm put-parameter \
    --name "/emol/django_settings_module" \
    --value "emol.settings.dev" \
    --type "SecureString" \
    --endpoint-url "http://localstack:4566" \
    --overwrite >/dev/null

awslocal ssm put-parameter \
    --name "/emol/oauth_client_id" \
    --value "mock-client-id" \
    --type "SecureString" \
    --endpoint-url "http://localstack:4566" \
    --overwrite >/dev/null

awslocal ssm put-parameter \
    --name "/emol/oauth_client_secret" \
    --value "mock-client-secret" \
    --type "SecureString" \
    --endpoint-url "http://localstack:4566" \
    --overwrite >/dev/null

awslocal ssm put-parameter \
    --name "/emol/db_host" \
    --value "db" \
    --type "SecureString" \
    --endpoint-url "http://localstack:4566" \
    --overwrite >/dev/null

awslocal ssm put-parameter \
    --name "/emol/db_name" \
    --value "emol" \
    --type "SecureString" \
    --endpoint-url "http://localstack:4566" \
    --overwrite >/dev/null

awslocal ssm put-parameter \
    --name "/emol/db_user" \
    --value "emol_db_user" \
    --type "SecureString" \
    --endpoint-url "http://localstack:4566" \
    --overwrite >/dev/null

awslocal ssm put-parameter \
    --name "/emol/db_password" \
    --value "emol_db_password" \
    --type "SecureString" \
    --endpoint-url "http://localstack:4566" \
    --overwrite >/dev/null
