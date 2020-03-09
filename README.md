# nb_to_html

nb_to_html is a web application that creates on-demand dynamic HTML reports powered by Jupyter Notebooks.

This is quite a powerful concept as it allows the data scientist to really quickly generate HTML reports that could be sent out as simple URLs.

It does so simply by receiving a path to Notebook to be run (which could be a public or private GitHub repo) and a collection of optional runtimes parameters for the Notebook. Once the notebook finishes execution, its contents is convered to HTML and rendered to the client.

## example

Suppose you have a simple notebook that plots data for a stock symbol. In its cleared state, the notebook looks like this: https://github.com/skyline-ai/stocks_demo/blob/master/stocks_demo.ipynb

This is how you would get an HTML report of the execution result for different stock symbols:

AAPL (Apple):
http://localhost:8080/nb_to_html?org=skyline-ai&repo=stocks_demo&nb_path=stocks_demo.ipynb&params={"target_stock_symbol":"AAPL"}

![Alt text](/img/AAPL.jpg?raw=true "AAPL")

MSFT (Microsoft):
http://localhost:8080/nb_to_html?org=skyline-ai&repo=stocks_demo&nb_path=stocks_demo.ipynb&params={"target_stock_symbol":"MSFT"}

![Alt text](/img/MSFT.jpg?raw=true "MSFT")

For each request, nb_to_html downloads the notebook, sets its parameters, executes it, converts the results to HTML and renders it to the client.

Note the parameters in this case were:
- org = skyline-ai (the GitHub organization)
- repo = stocks_demo (repo name on GitHub)
- nb_path = stocks_demo.ipynb (the full path to the notebook on GitHub)
- params={"target_stock_symbol":"MSFT"} (the optional params argument containing the name of the variable to inject). Fo this to work, you must tag your notebook cell with "parameters" (see [papermill](https://github.com/nteract/papermill) docs)

## under-the-hood

Under-the-hood, nb_to_html uses [papermill](https://github.com/nteract/papermill) to execute the notebook and nbconvert to convert the result to HTML.

## accessing notebooks on private repos

The application supports accessing private repos by setting the `GITHUB_TOKEN` env variable.

## configuration, deployment

You could deploy the application using Docker to anywhere you want. For example, if the application is deployed to AWS Farget + ECS, to create a new revision:
1. Push to ECR:
```
aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {REPO}.dkr.ecr.{REGION}.amazonaws.com/nb_to_html

docker build -t nb_to_html .

docker tag nb_to_html:latest {REPO}.{REGION}.amazonaws.com/nb_to_html:latest

docker push {REPO}.{REGION}.amazonaws.com/nb_to_html:latest
```

2. Create a new revision on Fargate:
https://console.aws.amazon.com/ecs/home?region={REGION}#/clusters/default-nb-to-html-server/services (select the service and click on update)

