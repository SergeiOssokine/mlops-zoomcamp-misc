# Deploying a streaming model to AWS
This folder contains configuration files and scripts to train a simple model to AWS.

The model predicts the duration of rides for the NYC Taxi service by using the pickup and drop off locations as features. It is built with `scikit-learn` using the Gradient Boosting Regression Tree algorithm. You can the code to train the model [here](./model_training/)



To deploy the model to AWS we employ several different approaches:

- AWS cli, as an intrdoction
- Different IaC tools:
    - AWS CloudFormation
    - Terraform
    - Pulumi

You can find the detailed description and instructions on how to use the code in the following sequence of blogs ([cli and CloudFormation](https://sergeiossokine.github.io/posts/streaming_deployment/streaming_example.html), [Terraform](https://sergeiossokine.github.io/posts/streaming_deployment_part2/stream_example_contd.html), [Pulumi](https://sergeiossokine.github.io/posts/streaming_deployment_part3/streaming_example_pulumi.html))