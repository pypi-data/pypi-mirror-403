import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

// Import configuration file
const configPath = new URL("../static/js/config.js", import.meta.url);
const config = await import(configPath);

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Define paths
const templatePath = path.resolve(
  __dirname,
  "../static/template_metadata_schema.yaml"
);
const outPath = path.resolve(__dirname, "../static/metadata_schema.yaml");

// Get criteria schema name from config
const criteriaFilename = "./" + config.criteriaSchemaPath.split("/").pop();

const template = await fs.readFile(templatePath, "utf8");
const output = template
  .replace(/\{\{metadataSchemaName\}\}/g, config.metadataSchemaName)
  .replace(/\{\{criteriaSchemaRef\}\}/g, criteriaFilename);

// Write generated file
await fs.writeFile(outPath, output, "utf8");
console.log("✅ metadata_schema.yaml generated successfully");
console.log(`   Template: ${templatePath}`);
console.log(`   Output:   ${outPath}`);
console.log(`   Criteria ref: ${criteriaFilename}`);
