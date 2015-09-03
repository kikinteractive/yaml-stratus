# YAML Stratus

This was developed originally to ease the use of [AWS CloudFormation](http://aws.amazon.com/cloudformation/aws-cloudformation-templates/) templates. CloudFormation templates are described using JSON, but standard
JSON allows neither comments nor back references and is difficult to read. [YAML](http://en.wikipedia.org/wiki/YAML), on the other hand, allows comments and is
extendable using the '!' notation. Most importantly, YAML can be easily converted to JSON.

YAML Stratus provides extensions to YAML that make it amenable to use with AWS CloudFormation, as well as a python binding,
and a tool for converting to the standard JSON used by CloudFormation.

We were able to specify 943,762 bytes of JSON templates containing 24,243 lines using just 194,647 bytes of YAML templates
containing 4,867 lines. That is a reduction of 79%. And it should be taken into account that roughly 10% of the YAML
included comments, that were impossible to include in JSON.

### Standard YAML capabilities not part of JSON:

* comments
* back references
* embedded declarations using indentation rather than the brace brackets and quotations required by JSON
* block literals

Note also that JSON is YAML, so familiar JSON data can be embedded within YAML.

### Extensions to YAML provided by YAML Stratus:

* !include - YAML files can include other YAML files, allowing sharing of common data
* !include-base64 - Base 64 encodings of other files can be embedded in JSON output
* !param - YAML files can include parameters that can be replaced with values during JSON generation
* !merge - Allows the merging of data from two source data hierarchies
* !remove - Used in conjunction with !merge to remove selected data during the merge process
* !replace - Used in conjunction with !merge to replace selected data during the merge process
* !jtext - Friendlier way to work with CloudFormation Fn::Join

## Installation

To install from project directory

`pip install -e .`

To install via [pip](https://pypi.python.org/pypi) simply:

`pip install yamlstratus`

## Usage

### Processing a YAML template using script

```
usage: ystratus.py [-h] [-i INCLUDE_DIRS] [-r ROOT_TAG] [-o OUTPUT_DIR]
                   [-P PARAM]
                   src

Convert YAML Stratus format to json

positional arguments:
  src                   the name of the source file

optional arguments:
  -h, --help            show this help message and exit
  -i INCLUDE_DIRS, --include-dirs INCLUDE_DIRS
                        the search path of include files
  -r ROOT_TAG, --root-tag ROOT_TAG
                        the source tag that forms the root of the returned
                        document
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        the destination directory of generated file
  -P PARAM, --param PARAM
                        Parameter to set. Ex -P LoadBalancerDnsWeight=5
```

#### LAMP Example:

Using `ystratus` to create a CloudFormation template of a typical LAMP stack:

```
ystratus.py example/ec2/LampInstance.yaml
```

#### Data Pipeline Example:

Using `ystratus` to create a [Data Pipeline](http://docs.aws.amazon.com/datapipeline/latest/DeveloperGuide/dp-writing-pipeline-definition.html) for searching an S3 bucket:

```
ystratus.py example/data-pipeline/ShellCommand.yaml -P inputBucket=myinputbucket -P outputBucket=myoutputbucket -P cmd="grep abc *"
```

### Processing a YAML template from python

#### LAMP Example

Using `python` to create a CloudFormation template of a typical LAMP stack:

```
>>> import yamlstratus
>>> with open('example/ec2/LampInstance.yaml', 'r') as f:
...     with open('LampInstance.json', 'w') as out:
...         out.write(yamlstratus.load_as_json(f, include_dirs=['example/ec2']))
```

#### Data Pipeline Example:

Using `python` to create a Data Pipeline for searching an S3 bucket:

```
>>> import yamlstratus
>>> with open('example/data-pipeline/ShellCommand.yaml', 'r') as f:
...     with open('ShellCommand.json', 'w') as out:
...         out.write(yamlstratus.load_as_json(f, include_dirs=['example/data-pipeline'], params={
...             "inputBucket": "myinputbucket",
...             "outputBucket": "myoutputbucket",
...             "cmd": "grep abc *"
...         }))
```

## Extensions

YAML Stratus provides a suite of extensions, easing the creation of JSON templates for the likes of AWS CloudFormation and [AWS Data PipeLine](http://aws.amazon.com/datapipeline/).

### Including files using `!include`

YAML files can include other YAML files, allowing sharing of common data. Ex.

```
main:
    Properties: !include filename
```

The `filename` argument can optionally exclude any `.yaml` or `.yml` suffix.

By default, the entire file is included. If you only want a particular node within the file, you
can specify that node using a `.` delimiter. Ex.

```
main:
    Properties: !include filename.TomcatProperties
```

`filename.yaml`:

```
ApacheProperties:
     http_port: 80
     https_port: 443
TomcatProperties:
     http_port: 8080
     https_port: 8443
```

The delimiter can be used for multiple levels.  Ex.

```
main:
    Properties:
        http_port: !include filename.ApacheProperties.http_port
```

`filename.yaml`:

```
ApacheProperties:
     http_port: 80
     https_port: 443
TomcatProperties:
     http_port: 8080
     https_port: 8443
```

### Parameterizing using `!param`

YAML files can include parameters that can be replaced with values during JSON generation. Ex.

yaml:
```
main:
    Properties:
        http_port: !param port "80"
```

python:
```
    import yamlstratus
    ...
    json = yamlstratus.load_as_json(input, params={'port': '8000'})
```

The second parameter to the `!param` extension is the default value. It does not have to be specified.

### Inheritance using `!merge`

Allows the merging of data from two source data hierarchies. This is the heart of `yamlstratus` allowing
a kind of inheritance. Ex.

yaml:
```

define: &HttpTomcatSecurityGroup
    Type: "AWS::EC2::SecurityGroup"
    Properties:
        SecurityGroupIngress:
            - CidrIp: "0.0.0.0/0"
              FromPort: 8080
              ToPort: 8080

...
    MyInstanceSecurityGroup: !merge
        startingFrom: *HttpTomcatSecurityGroup
        mergeWith:
            Properties:
                GroupDescription: Example http/https security group for an instance hosting tomcat
                SecurityGroupIngress:
                    - CidrIp: "0.0.0.0/0"
                      FromPort: 8443
                      ToPort: 8443

```
Output:
```

...
""MyInstanceSecurityGroup": {
    "Type": "AWS::EC2::SecurityGroup",
    "Properties": {
        "GroupDescription": "Example http/https security group for an instance hosting tomcat",
        "SecurityGroupIngress": [
            { "CidrIp" : "0.0.0.0/0", "FromPort": "8080", "ToPort" : "8080"},
            { "CidrIp" : "0.0.0.0/0", "FromPort": "8443", "ToPort" : "8443"}
        ]
    }
}


```
### `!remove`

Used in conjunction with !merge to remove selected data during the merge process.

yaml:
```

define: &LoadBalancerDns
    Type: "AWS::Route53::RecordSet"
    Properties:
        HostedZoneName: "example.com."
        Type: A
        AliasTarget:
            HostedZoneId:
                "Fn::GetAtt": [LoadBalancer, CanonicalHostedZoneNameID]
            DNSName:
                "Fn::GetAtt": [LoadBalancer, CanonicalHostedZoneName]

...
    MyLoadBalancerDns: !merge
        startingFrom: *LoadBalancerDns
        mergeWith:
            Properties:
                Type: CNAME
                TTL: 300
                ResourceRecords:
                    - "Fn::GetAtt":
                          - LoadBalancer
                          - DNSName
                AliasTarget: !remove

```
Output:
```

...
""MyLoadBalancerDns": {
    "Type": "AWS::Route53::RecordSet",
    "Properties": {
        "HostedZoneName": "example.com.",
        "Type": "CNAME",
        "TTL": "300",
        "ResourceRecords": {"Fn::GetAtt": ["LoadBalancer" , "DNSName"]},
    }
}


```


### Overriding using `!replace`

Used in conjunction with !merge to replace selected data during the merge process.

yaml:
```

define: &LoadBalancerSecurityGroup
    Type: "AWS::EC2::SecurityGroup"
    Properties:
        GroupDescription: Tomcat load balancer access
        SecurityGroupIngress:
            - IpProtocol: tcp
              FromPort: 443
              ToPort: 443
              CidrIp: "0.0.0.0/0"
        SecurityGroupEgress:
            # To tomcat
            - IpProtocol: tcp
              FromPort: 8080
              ToPort: 8080
              CidrIp: "0.0.0.0/0"

...
    MyLoadBalancerSecurityGroup: !merge
        startingFrom: *LoadBalancerSecurityGroup
        mergeWith:
            Properties:
                SecurityGroupIngress: !replace
                    # Https from particular source
                    - IpProtocol: tcp
                      FromPort: 443
                      ToPort: 443
                      CidrIp: "93.184.216.34/32"

```
Output:
```

...
""MyLoadBalancerSecurityGroup": {
    "Type": "AWS::EC2::SecurityGroup",
    "Properties": {
        "GroupDescription": "Tomcat load balancer access",
        "SecurityGroupIngress": [{
            "IpProtocol": "tcp",
              "FromPort": "443",
              "ToPort": "443",
              "CidrIp": "93.184.216.34/32"
        }],
        "SecurityGroupEgress": [{
            "IpProtocol": "tcp",
              "FromPort": "8080",
              "ToPort": "8080",
              "CidrIp": "0.0.0.0/0"
        }]
    }
}
```

### Embedding elements in text using `!jtext`

When specifically working with CloudFormation templates, the `jtext` plugin allows more seamless joining of
text with elements via `Fn::Join`.

yaml:
```
    "/tmp/setup.mysql":
        content: !jtext |
            CREATE DATABASED !{Ref: DBName!};
            GRANT ALL ON !{Ref: DBName!}.* TO '!{Ref: DBUsername!}'@'localhost' IDENTIFIED BY '!{Ref : DBPassword!}';
        mode : 000400
        owner: root
        group: root

```
Output:
```
    "/tmp/setup.mysql": {
        "content": {
            "Fn:Join": [
                "",
                [
                    "CREATE DATABASE ",
                    {
                        "Ref": "DBName"
                    },
                    ";\nGRANT ALL ON ",
                    {
                        "Ref": "DBName"
                    },
                    ".* TO '",
                    {
                        "Ref": "DBUsername"
                    },
                    "'@'localhost' IDENTIFIED BY '",
                    {
                        "Ref": "DBPassword"
                    },
                    "';\n"
                ]
            ]
        },
        "owner": "root",
        "group": "root",
        "mode": 256
    }
```
## Author

Kik Interactive

## License

Use of YAML Stratus is subject to the Terms & Conditions and the Acceptable Use Policy.

The source for YAML Stratus is available under the Apache 2.0 license. See the LICENSE.txt file for details.
