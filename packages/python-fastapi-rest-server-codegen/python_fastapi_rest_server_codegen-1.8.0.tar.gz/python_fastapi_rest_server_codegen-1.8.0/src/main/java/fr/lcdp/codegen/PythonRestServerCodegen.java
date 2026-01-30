package fr.lcdp.codegen;

import io.swagger.v3.oas.models.media.Schema;
import org.apache.commons.lang3.StringUtils;
import org.openapitools.codegen.CodegenProperty;
import org.openapitools.codegen.CodegenResponse;
import org.openapitools.codegen.CodegenType;
import org.openapitools.codegen.SupportingFile;
import org.openapitools.codegen.languages.PythonFastAPIServerCodegen;
import org.openapitools.codegen.model.ModelMap;
import org.openapitools.codegen.model.OperationsMap;
import org.openapitools.codegen.utils.ModelUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.List;

public class PythonRestServerCodegen extends PythonFastAPIServerCodegen {

    private static final Logger LOGGER = LoggerFactory.getLogger(PythonRestServerCodegen.class);

    public static final String COMMON_PACKAGE_NAME = "commonPackageName";

    private static final String BASE_CLASS_SUFFIX = "base";

    private String commonPackage = "common";

    /**
     * Constructor
     */
    public PythonRestServerCodegen(){
        super();

        // Do not add 'src' as source folder in the tree
        additionalProperties.put("sourceFolder", ".");

        LOGGER.info("Start PythonRestServerCodegen");
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
        return "python-fastapi-rest-server-codegen";
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

    @Override
    public void processOpts() {
        super.processOpts();

        if (additionalProperties.containsKey(COMMON_PACKAGE_NAME)) {
            commonPackage = (String) additionalProperties.get(COMMON_PACKAGE_NAME);
        }

        supportingFiles.add(new SupportingFile("python-fastapi-rest-server/health.mustache", StringUtils.substringAfter(commonPackageFileFolder(), outputFolder), "health.py"));

        this.removeSupportingFile("security_api.mustache");
        supportingFiles.add(new SupportingFile("python-fastapi-rest-server/security_api.mustache", StringUtils.substringAfter(packageFileFolder(), outputFolder), "security_api.py"));
        supportingFiles.add(new SupportingFile("python-fastapi-rest-server/token.mustache", StringUtils.substringAfter(packageFileFolder(), outputFolder), "token.py"));
        supportingFiles.add(new SupportingFile("python-fastapi-rest-server/context.mustache", StringUtils.substringAfter(packageFileFolder(), outputFolder), "context.py"));

        // Remove useless files
        this.removeSupportingFile("gitignore.mustache");
        this.removeSupportingFile(".flake8.mustache");
        this.removeSupportingFile("docker-compose.mustache");
        this.removeSupportingFile("openapi.mustache");
        this.removeSupportingFile("poetry.mustache");
        this.removeSupportingFile("requirements.mustache");
        this.removeSupportingFile("setup_cfg.mustache");
        this.removeSupportingFile("conftest.mustache");
        this.removeSupportingFile("Dockerfile.mustache");
        this.removeSupportingFile("pyproject_toml.mustache");
        this.removeSupportingFile("README.mustache");

        supportingFiles.removeIf(supportingFile ->
            supportingFile.getTemplateFile().equals("__init__.mustache")
                    &&
            supportingFile.getFolder().equals(StringUtils.substringAfter(apiImplFileFolder(), outputFolder))
        );

        // Remove API test templates
        apiTestTemplateFiles.clear();
        modelTestTemplateFiles.clear();

        apiTemplateFiles.remove("api.mustache");
        apiTemplateFiles.put("python-fastapi-rest-server/api.mustache", ".py");

        apiTemplateFiles.remove("base_api.mustache");
        apiTemplateFiles.put("python-fastapi-rest-server/base_api.mustache", "_".concat(BASE_CLASS_SUFFIX).concat(".py"));

        modelTemplateFiles.remove("model.mustache");
        modelTemplateFiles.put("python-fastapi-rest-server/model.mustache", ".py");
    }

    private void removeSupportingFile(String templateName)
    {
        supportingFiles.removeIf(supportingFile -> {
            return supportingFile.getTemplateFile().equals(templateName);
        });
    }

    public String commonPackageFileFolder() {
        return String.join(File.separator, new String[]{outputFolder, sourceFolder, commonPackage.replace('.', File.separatorChar)});
    }

    public String packageFileFolder() {
        return String.join(File.separator, new String[]{outputFolder, sourceFolder, packageName.replace('.', File.separatorChar)});
    }



    @Override
    public void postProcessResponseWithProperty(CodegenResponse response, CodegenProperty property) {
        /**
         * LDS-3925 : By default nullable response is not taken into account resulting in missing Optional.
         * If response is nullable, then wrap in optional
         */
        if (property.isNullable) {
            property.setDataType("Optional[" + property.getDataType() + "]");
            response.setDataType("Optional[" + response.getDataType() + "]");
        }
    }
}
