# OpenAPI Generator for the python-flask-rest-server-codegen library

## Overview
This is a boiler-plate project to generate your own project derived from an OpenAPI specification.

## What's OpenAPI
The goal of OpenAPI is to define a standard, language-agnostic interface to REST APIs which allows both humans and computers to discover and understand the capabilities of the service without access to source code, documentation, or through network traffic inspection.
When properly described with OpenAPI, a consumer can understand and interact with the remote service with a minimal amount of implementation logic.
Similar to what interfaces have done for lower-level programming, OpenAPI removes the guesswork in calling the service.

Check out [OpenAPI-Spec](https://github.com/OAI/OpenAPI-Specification) for additional information about the OpenAPI project, including additional libraries with support for other languages and more. 

## How do I use this?
At this point, you've likely generated a server setup.  It will include something along these lines:

```
.
|- README.md    // this file
|- pom.xml      // build script
|-- src
|--- main
|---- java
|----- fr.lcdp.codegen.PythonRestServerCodegen.java // generator file
|---- resources
|----- python.lcdp // template files
```


Templates in this folder:

`src/main/resources/python/lcdp`

Once modified, you can run this:

```
mvn package
```

In your generator project. A single jar file will be produced in `target`. You can now use that with [OpenAPI Generator](https://openapi-generator.tech):

For mac/linux:
```
java -cp /path/to/openapi-generator-cli.jar:/path/to/your.jar org.openapitools.codegen.OpenAPIGenerator generate -g python-rest-client-codegen -i /path/to/openapi.yaml -o ./test
```
(Do not forget to replace the values `/path/to/openapi-generator-cli.jar`, `/path/to/your.jar` and `/path/to/openapi.yaml` in the previous command)

For Windows users, you will need to use `;` instead of `:` in the classpath, e.g.
```
java -cp /path/to/openapi-generator-cli.jar;/path/to/your.jar org.openapitools.codegen.OpenAPIGenerator generate -g python-rest-client-codegen -i /path/to/openapi.yaml -o ./test
```

Now your templates are available to the server generator and you can write output values

## Debugging

You can execute the `java` command from above while passing different debug flags to show
the object you have available during server generation:

```
# The following additional debug options are available for all codegen targets:
# -DdebugOpenAPI prints the OpenAPI Specification as interpreted by the codegen
# -DdebugModels prints models passed to the template engine
# -DdebugOperations prints operations passed to the template engine
# -DdebugSupportingFiles prints additional data passed to the template engine

java -DdebugOperations -cp /path/to/openapi-generator-cli.jar:/path/to/your.jar org.openapitools.codegen.OpenAPIGenerator generate -g python-rest-client-codegen -i /path/to/openapi.yaml -o ./test
```

Will, for example, output the debug info for operations.
You can use this info in the `api.mustache` file.