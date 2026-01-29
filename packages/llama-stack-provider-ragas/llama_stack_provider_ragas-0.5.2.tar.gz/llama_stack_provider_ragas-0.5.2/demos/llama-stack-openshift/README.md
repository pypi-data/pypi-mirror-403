# Deploying Llama Stack on OpenShift AI with the remote Ragas eval provider

## Prerequisites
* OpenShift cluster with admin privileges
* Data Science Pipeline Server configured
* Llama Stack Operator installed
* A VLLM hosted Model either through Kserve or MaaS. You can follow these [docs](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_cloud_service/1/html/working_with_rag/deploying-a-rag-stack-in-a-data-science-project_rag#Deploying-a-llama-model-with-kserve_rag) until step 3.4

## Installing Open Data Hub

If you don't have OpenShift AI or Open Data Hub installed, you can install it using the provided YAML files:

```bash
# Install the Open Data Hub operator (wait for it to be ready)
oc apply -f deployment/01-opendatahub-operator-subscription.yaml

# Wait for the operator to be installed
oc get csv -n openshift-operators | grep opendatahub

# Create the DSC Initialization (wait for operator to be ready first)
oc apply -f deployment/02-dsc-initialization.yaml

# Create the Data Science Cluster
oc apply -f deployment/03-datasciencecluster.yaml
```

You can check the status of your installation with:
```bash
oc get dsc
oc get dsci
oc get route -n opendatahub
```

## Setting up the Data Science Pipeline

Create the data science project and pipeline:
```bash
# Create the project/namespace
oc new-project ragas-eval-pipeline

# Create AWS credentials secret for S3 storage
oc create secret generic aws-credentials \
  --from-literal=AWS_ACCESS_KEY_ID=your-access-key \
  --from-literal=AWS_SECRET_ACCESS_KEY=your-secret-key \
  --from-literal=AWS_DEFAULT_REGION=us-east-1 \
  -n ragas-eval-pipeline

# Deploy the Data Science Pipeline Application
oc apply -f deployment/04-datasciencepipeline.yaml
```

Check the pipeline status:
```bash
oc get dspa -n ragas-eval-pipeline
oc get pods -n ragas-eval-pipeline
```

## Setup
Create a secret for storing your model's information.
```
export INFERENCE_MODEL="llama-3-2-3b"
export VLLM_URL="https://llama-32-3b-instruct-predictor:8443/v1"
export VLLM_TLS_VERIFY="false" # Use "true" in production!
export VLLM_API_TOKEN="<token identifier>"

oc create secret generic llama-stack-inference-model-secret \
  --from-literal INFERENCE_MODEL="$INFERENCE_MODEL" \
  --from-literal VLLM_URL="$VLLM_URL" \
  --from-literal VLLM_TLS_VERIFY="$VLLM_TLS_VERIFY" \
  --from-literal VLLM_API_TOKEN="$VLLM_API_TOKEN"
```

## Setup Deployment files
### Configuring the `kubeflow-ragas-config` ConfigMap
Update the [kubeflow-ragas-config](deployment/kubeflow-ragas-config.yaml) with the following data:
``` bash
# See project README for more details
EMBEDDING_MODEL=all-MiniLM-L6-v2
KUBEFLOW_LLAMA_STACK_URL=<your-llama-stack-url>
KUBEFLOW_PIPELINES_ENDPOINT=<your-kfp-endpoint>
KUBEFLOW_NAMESPACE=<your-namespace>
KUBEFLOW_BASE_IMAGE=quay.io/diegosquayorg/my-ragas-provider-image:latest
KUBEFLOW_RESULTS_S3_PREFIX=s3://my-bucket/ragas-results
KUBEFLOW_S3_CREDENTIALS_SECRET_NAME=<secret-name>
```

> [!NOTE]
> The `KUBEFLOW_LLAMA_STACK_URL` must be an external route.

### Configuring the `pipelines_token` Secret
Unfortunately the Llama Stack distribution service account does not have privilages to create pipeline runs. In order to work around this we must provide a user token as a secret to the Llama Stack Distribution.

Create the secret with:
``` bash
# Gather your token with `oc whoami -t`
kubectl create secret generic kubeflow-pipelines-token \
  --from-literal=KUBEFLOW_PIPELINES_TOKEN=<your-pipelines-token>
```

## Deploy Llama Stack on OpenShift
You can now deploy the configuration files and the Llama Stack distribution with `oc apply -f deployment/kubeflow-ragas-config.yaml` and `oc apply -f deployment/llama-stack-distribution.yaml`

You should now have a Llama Stack server on OpenShift with the remote ragas eval provider configured.
You can now follow the remote instructions of the [basic_demo.ipynb](../../demos/basic_demo.ipynb) demo but ensure you are running it in a Data Science workbench and use the `LLAMA_STACK_URL` defined earlier. Alternatively you can run it locally if you create a Route.
