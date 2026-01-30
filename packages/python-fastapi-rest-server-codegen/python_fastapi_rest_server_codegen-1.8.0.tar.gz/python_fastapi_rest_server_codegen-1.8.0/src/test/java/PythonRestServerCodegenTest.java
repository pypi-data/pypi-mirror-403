import org.junit.Assert;
import org.junit.runner.RunWith;
import org.junit.runners.Parameterized;
import org.openapitools.codegen.ClientOptInput;
import org.openapitools.codegen.DefaultGenerator;
import org.junit.Test;
import org.openapitools.codegen.config.CodegenConfigurator;
import java.io.File;
import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

@RunWith(Parameterized.class)
public class PythonRestServerCodegenTest {
    @Parameterized.Parameters(name = "{index} : {0}")
    public static Collection<Object[]> data() {
        return Arrays.asList(new Object[][] {
                {"test/resources/petStore", "petstore"},
                {"test/resources/codeWithInheritance", "openapi"},
                {"test/resources/enumPathParam", "openapi"},
                {"test/resources/simpleCode", "openapi"},
                {"test/resources/apiKey", "openapi"},
                {"test/resources/arrayOfReferencedEnum", "openapi"},
                {"test/resources/multipleOneOfWithDiscriminator", "openapi"},
                {"test/resources/nullableRef", "openapi"},
                {"test/resources/oneOfWithDiscriminator", "openapi"},
                {"test/resources/orderedTags", "openapi"},
                {"test/resources/xRestrict", "openapi"},
                {"test/resources/productApi", "product"},
        });
    }

    private final String filePath;
    private final String yamlName;

    public PythonRestServerCodegenTest(String filePath, String yamlName) {
        this.filePath = filePath;
        this.yamlName = yamlName;
    }

    @Test
    public void generateCodegen() throws IOException {
        File tempDirectory = Files.createTempDirectory("test").toFile();
        Path outputPath = Files.createDirectory(tempDirectory.toPath().resolve("myModule"));

        Map<String, Object> properties = new HashMap<>();
        properties.put("hideGenerationTimestamp", true);

        Path inputPath = FileSystems.getDefault().getPath(".")
                .toAbsolutePath()
                .getParent()
                .getParent()
                .toAbsolutePath();

        boolean setupTestResults = false;
        if (setupTestResults) {
            outputPath = FileSystems.getDefault().getPath(".")
                    .toAbsolutePath()
                    .getParent()
                    .resolve("src/" + this.filePath);
        }

        final CodegenConfigurator configurator = new CodegenConfigurator()
                .setGeneratorName("python-fastapi-rest-server-codegen")
                .setAdditionalProperties(properties)
                .setInputSpec(inputPath.toString()+"/"+this.filePath+"/"+this.yamlName+".yaml")
                .setOutputDir(outputPath.toString().replace("\\", "/"));

        DefaultGenerator generator = new DefaultGenerator();
        final ClientOptInput clientOptInput = configurator.toClientOptInput();
        generator.setGenerateMetadata(false); // Avoid generating metadata as they are platform line ending dependent
        generator.opts(clientOptInput).generate();

        Path expectedContent = Paths.get("src/"+this.filePath);
        Files.createDirectories(expectedContent);
        Assert.assertTrue("Generated code and expected one are not similar. Look : " + outputPath.toString(), DirectoryUtils.isEqual(expectedContent, outputPath, true));
    }
}
