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

## development

In dev, run the app with docker:

```
docker run --rm -ti -p 8080:8080 -e GITHUB_TOKEN -e GOOGLE_APPLICATION_CREDENTIALS_JSON -e PORT -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e S3_BUCKET -e REDIS_PASSWORD -e REDIS_HOST -e REDIS_PORT nb_to_html
```

## adding dependencies
To add dependencies (e.g. a python library you need in your notebook), either pip install it via a notebook cell like so:

```
!pip install bokeh
```

Or, you could add it to the `requirements.txt` file, that already contains a few commonly used libraries (pandas, numpy, boto3, seaborn, etc.).


## server-side caching

The server supports caching the results of notebook execution on redis. If you choose to set up the redis configuruation as explained below, the server will hash the contents of the notebook in combination with the runtime parameters and use this hash as a cache key to use a previous execution.

### Env vars / server configuration

All configuration values are *optional*:
- GITHUB_TOKEN (optional, a GitHub API access token to access private repos)
- GOOGLE_APPLICATION_CREDENTIALS_JSON (optional, if your notebook talks to a GCP service like Google BigQuery). Setting this varaible with the contents of the GOOGLE_APPLICATION_CREDENTIALS file will allow you to read those credentials from notebooks without having to store the credentials anywhere else
- S3_Bucket (optional, an S3 bucket name). If supplied, every report will be saved on the bucket under the following format: s3://<S3_BUCKET>/nb_to_html/<yyyy>/<MM>/report_name_yyyy_mm_dd_hh:ss.html
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (optional, AWS credentials if S3 storage is desired)
- REDIS_PASSWORD, REDIS_HOST and REDIS_PORT if redis caching is desired

## Building the project with Docker
To speed up development, there is a base docker image containing the pip install stage. This means that code
changes can be tested quickly by building a dockerfile that only copies the app and runs it after all deps
have already been installed.

Edit dependencies on the `BaseDockerFile` and build it like so:

```
docker build -t nb_to_html_base -f BaseDockerfile .
```

Then, after any code change, build just the project, without having to wait for the pip install step:

```
docker build -t nb_to_html .
```

And run the app using the docker run command above.

## deployment

The application is deployed to AWS Farget. To create a new revision:
1. Push to ECR:
```
aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {REPO}.dkr.ecr.{REGION}.amazonaws.com/nb_to_html

docker build -t nb_to_html .

docker tag nb_to_html:latest {REPO}.{REGION}.amazonaws.com/nb_to_html:latest

docker push {REPO}.{REGION}.amazonaws.com/nb_to_html:latest
```

2. Create a new revision on Fargate:
https://console.aws.amazon.com/ecs/home?region={REGION}#/clusters/default-nb-to-html-server/services (select the service and click on update)

