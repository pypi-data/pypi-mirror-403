package fr.lcdp.codegen;

import org.openapitools.codegen.*;
import org.openapitools.codegen.languages.PythonClientCodegen;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;


public class PythonRestClientCodegen extends PythonClientCodegen {

    private final Logger LOGGER = LoggerFactory.getLogger(PythonRestClientCodegen.class);

    public static final String API_DOC_PATH= "apiDocPath";
    public static final String MODEL_DOC_PATH= "modelDocPath";

    /**
     * Constructor
     */
    public PythonRestClientCodegen(){
        super();
    }
    /**
     * Configures the type of generator.
     *
     * @return  the CodegenType for this generator
     * @see     org.openapitools.codegen.CodegenType
     */
    public CodegenType getTag() {
        return CodegenType.CLIENT;
    }

    /**
     * Configures a friendly name for the generator.  This will be used by the generator
     * to select the library with the -g flag.
     *
     * @return the friendly name for the generator
     */
    public String getName() {
        return "python-rest-client-codegen";
    }

    /**
     * Returns human-friendly help for the generator.  Provide the consumer with help
     * tips, parameters here
     *
     * @return A string value for the help message
     */
    public String getHelp() {
        return "Generates a python-lcdp-client.";
    }

    public void preProcessOpts() {
        this.additionalProperties.put(CodegenConstants.SOURCECODEONLY_GENERATION, "true");
        // Doc package
        if (!this.additionalProperties.containsKey(API_DOC_PATH)) {
            this.additionalProperties.put(API_DOC_PATH, "/docs");
        }
        this.apiDocPath = this.additionalProperties.get(API_DOC_PATH).toString();

        if (!this.additionalProperties.containsKey(MODEL_DOC_PATH)) {
            this.additionalProperties.put(MODEL_DOC_PATH, "/docs");
        }
        this.modelDocPath = this.additionalProperties.get(MODEL_DOC_PATH).toString();
    }

    @Override
    public void processOpts() {
        this.preProcessOpts();

        // Use discriminator value for class lookup
        this.setUseOneOfDiscriminatorLookup(true);

        super.processOpts();

        // remove unused files
        this.removeSupportingFile("gitlab-ci.mustache");

        this.removeSupportingFile("README_onlypackage.mustache");

        // move configuration.mustache and add configuration builder
        this.supportingFiles.add(new SupportingFile("lcdp/configuration_builder.mustache", this.packagePath(), "configuration_builder.py"));

        // api client utils
        supportingFiles.add(new SupportingFile("lcdp/api_client_utils.mustache", this.packagePath(), "api_client_utils.py"));

        // Fix for https://github.com/OpenAPITools/openapi-generator/issues/3285
        String apiPath = apiPackage.replace('.', File.separatorChar);
        this.removeSupportingFile("__init__api.mustache");
        this.supportingFiles.add(new SupportingFile("lcdp/__init__api.mustache", apiPath, "__init__.py"));
        this.removeSupportingFile("__init__package.mustache");
        supportingFiles.add(new SupportingFile("lcdp/__init__package.mustache", packagePath(), "__init__.py"));

        // Override model.mustache to serialize ISO8601 in milliseconds instead of microseconds
        modelTemplateFiles.remove("model.mustache");
        modelTemplateFiles.put("lcdp/model.mustache", ".py");
        this.removeSupportingFile("api_client.mustache");
        supportingFiles.add(new SupportingFile("lcdp/api_client.mustache", packagePath(), "api_client.py"));

        apiTemplateFiles.remove("api.mustache");
        apiTemplateFiles.put("lcdp/api.mustache", ".py");
    }

    private void removeSupportingFile(String templateName)
    {
        supportingFiles.removeIf(supportingFile -> {
            return supportingFile.getTemplateFile().equals(templateName);
        });
    }
}
