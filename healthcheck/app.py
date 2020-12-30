import json
import sys
import urllib.request
import urllib.error
import boto3

cloudwatch_client = boto3.client('cloudwatch')

#ToDo: Pass this in via lambda function
json_sites_to_test = '''{ 
    "http-arcaidan.cloud": {
        "url": "http://arcadian.cloud",
        "desiredCode": "200"
    },
    "https - arcaidan.cloud": {
        "url": "https://arcadian.cloud",
        "desiredCode": "200"
    },
    "broken-test":{
        "url": "https://arcadian2.cloud",
        "desiredCode": "200"
    },
    "youtube.com":{
        "url": "https://youtube.com",
        "desiredCode": "200"
    }
}'''

#https://docs.python.org/3/howto/urllib2.html
def test_url(url):
    try:
        with urllib.request.urlopen(url) as response: 
            code = response.getcode()
        return code
    except urllib.error.URLError as e:
        print ("ERROR!")
        if hasattr(e, 'reason'):
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        elif hasattr(e, 'code'):
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
    except:
        return 0

def put_cloudwatch_test_result(metric_name, result):
    print ("Putting", metric_name, result)
    response = cloudwatch_client.put_metric_data(
    Namespace='Healthchecks',
    MetricData=[
        {
            'MetricName': metric_name,
            'Dimensions': [
                {
                    'Name': 'Label',
                    'Value': 'SuccessPercent'
                },
            ],
            'Value': result,
            'Unit': 'Percent'
        },
    ]
    )   


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    #Import data sites to test passed in from lambda call
    sites_to_test = json.loads(json_sites_to_test)

    test_results={}

    #Test all provided sites
    for site in sites_to_test:
        result = 0
        code = test_url(sites_to_test[site]['url'])
        desired_code = sites_to_test[site]['desiredCode']
        metric_name = site.replace(" ", "") #Catch anyone leaving whitespaces in the metric name ToDo: Trim all non-allowed characters
        # print("Testing:", sites_to_test[site]['url'])
        # print("Label:", site)
        # print("Status Code:", code)
        # print("desiredCode:", desired_code)

        if code:
            if int(code) == int(desired_code):
                #print ("Passed test")
                result = 100
            else:
                print ("WARNING:", metric_name, "Failed test with code:", code)
        else:
            print ("WARNING:", metric_name, "Failed test with no response")

        #Populate response Dict
        test_results[sites_to_test[site]['url']] = code

        #Put results into CloudWatch
        put_cloudwatch_test_result(metric_name, result)


    return {
        #"statusCode": 200,test_url('http://arcadian.cloud')
        "body": json.dumps({
            "message": test_results
        }),
    }
