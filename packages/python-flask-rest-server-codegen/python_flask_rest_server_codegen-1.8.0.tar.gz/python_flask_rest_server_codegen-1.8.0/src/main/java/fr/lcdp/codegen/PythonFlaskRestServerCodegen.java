package fr.lcdp.codegen;

import org.apache.commons.io.FilenameUtils;
import org.apache.commons.lang3.StringUtils;
import org.openapitools.codegen.CodegenType;
import org.openapitools.codegen.SupportingFile;
import org.openapitools.codegen.languages.PythonFlaskConnexionServerCodegen;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;

public class PythonFlaskRestServerCodegen extends PythonFlaskConnexionServerCodegen {

    private static final Logger LOGGER = LoggerFactory.getLogger(PythonFlaskRestServerCodegen.class);

    public static final String PACKAGE_NAME_IMPL = "packageNameImpl";

    public static final String API_DOC_PATH= "apiDocPath";
    public static final String MODEL_DOC_PATH= "modelDocPath";

    public static final String TEST_PACKAGE = "testPackage";

    private static final String LCDP_API_KEY_NAME = "apiKeyAuth";

    /**
     * Constructor
     */
    public PythonFlaskRestServerCodegen(){
        super();

        LOGGER.info("Start PythonFlaskRestServerCodegen");
    }

    /**
     * Configures the type of generator.
     *
     * @return  the CodegenType for this generator
     * @see     org.openapitools.codegen.CodegenType
     */
    public CodegenType getTag() {
        return CodegenType.SERVER;
    }

    /**
     * Configures a friendly name for the generator.  This will be used by the generator
     * to select the library with the -g flag.
     *
     * @return the friendly name for the generator
     */
    public String getName() {
        return "python-flask-rest-server-codegen";
    }

    /**
     * Returns human-friendly help for the generator.  Provide the consumer with help
     * tips, parameters here
     *
     * @return A string value for the help message
     */
    public String getHelp() {
        return "Generates a python-lcdp-server.";
    }


    public String getPackageNameImpl(){
        return (String) additionalProperties.get(PACKAGE_NAME_IMPL);
    }

    @Override
    protected void addSupportingFiles() {

        // Fix model to_dict
        this.modelTemplateFiles.remove("model.mustache");
        this.modelTemplateFiles.put("python-flask-rest-server/model.mustache", ".py");

        supportingFiles.add(new SupportingFile("python-flask-rest-server/context.mustache", packagePath(), "context.py"));
        supportingFiles.add(new SupportingFile("python-flask-rest-server/api_resolver.mustache", packagePath(), "api_resolver.py"));
        supportingFiles.add(new SupportingFile("python-flask-rest-server/token.mustache", packagePath(), "token.py"));
        supportingFiles.add(new SupportingFile("python-flask-rest-server/health.mustache", packagePath(), "health.py"));

        this.removeSupportingFile("security_controller_.mustache");
        supportingFiles.add(new SupportingFile("python-flask-rest-server/security_controller_.mustache", packagePath() + File.separatorChar + packageToPath(controllerPackage), "security_controller_.py"));

        this.removeSupportingFile("openapi.mustache");
        supportingFiles.add(new SupportingFile("openapi.mustache", packagePath() + File.separatorChar + "openapi", getModuleName() + ".yaml"));
    }

    private static String packageToPath(String pkg) {
        return pkg.replace(".", File.separator);
    }

    private String getModuleName(){
        return FilenameUtils.getBaseName(this.getInputSpec());
    }

    @Override
    public void processOpts() {
        super.processOpts();

       // Remove useless files
        this.removeSupportingFile("__main__.mustache");
        this.removeSupportingFile("dockerignore.mustache");
        this.removeSupportingFile("gitignore.mustache");
        this.removeSupportingFile("Dockerfile.mustache");
        this.removeSupportingFile("README.mustache");
        this.removeSupportingFile("requirements.mustache");
        this.removeSupportingFile("setup.mustache");
        this.removeSupportingFile("test-requirements.mustache");
        this.removeSupportingFile("git_push.sh.mustache");
        this.removeSupportingFile("gitlab-ci.mustache");
        this.removeSupportingFile("tox.mustache");
        this.removeSupportingFile("travis.mustache");

        // Remove API test templates
        apiTestTemplateFiles.clear();

        // Modify controller mustache to fix 'body' naming problem (See : https://github.com/OpenAPITools/openapi-generator/issues/1666)
        apiTemplateFiles.remove("controller.mustache");
        apiTemplateFiles.put("python-flask-rest-server/controller.mustache", ".py");

        // Assign package prefix for imports
        if (!this.additionalProperties.containsKey(PACKAGE_NAME_IMPL)) {
            this.additionalProperties.put(PACKAGE_NAME_IMPL, "impl");
        }

        // Doc package
        if (!this.additionalProperties.containsKey(API_DOC_PATH)) {
            this.additionalProperties.put(API_DOC_PATH, "docs/");
        }
        if (!this.additionalProperties.containsKey(MODEL_DOC_PATH)) {
            this.additionalProperties.put(MODEL_DOC_PATH, "docs/");
        }

        // Test package
        if (!this.additionalProperties.containsKey(TEST_PACKAGE)) {
            this.additionalProperties.put(TEST_PACKAGE, "tests");
        }
        this.testPackage = this.additionalProperties.get(TEST_PACKAGE).toString();

        // Get module name and assign it
        if(!additionalProperties.containsKey("moduleName"))
            additionalProperties.put("moduleName", getModuleName());

    }

    private void removeSupportingFile(String templateName)
    {
        supportingFiles.removeIf(supportingFile -> {
            return supportingFile.getTemplateFile().equals(templateName);
        });
    }

    @Override
    public String apiDocFileFolder() {
        return outputFolder + File.separator + this.additionalProperties.get(API_DOC_PATH);
    }

    @Override
    public String modelDocFileFolder() {
        return outputFolder + File.separator + this.additionalProperties.get(MODEL_DOC_PATH);
    }

    @Override
    public String toRegularExpression(String pattern) {
        pattern = super.toRegularExpression(pattern);

        if (StringUtils.isEmpty(pattern)) {
            return pattern;
        } else {
            // Default method to not replace '"' with '\"' which is required for ECMA 262 -> Python
            return pattern.replaceAll("\"", "\\\\\"");
        }
    }
}
