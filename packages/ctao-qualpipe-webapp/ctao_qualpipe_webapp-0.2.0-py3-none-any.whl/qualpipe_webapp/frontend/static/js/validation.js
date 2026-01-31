import { metadataSchemaPath, criteriaSchemaPath } from "./config.js";

async function isValidMetadata(metadata, id) {
  // load each schema (metadata + criteria)
  const [metaResp, critResp] = await Promise.all([
    fetch(metadataSchemaPath),
    fetch(criteriaSchemaPath),
  ]);

  const metadataSchemaName = metadataSchemaPath.split("/").pop();
  const criteriaSchemaName = criteriaSchemaPath.split("/").pop();

  if (!metaResp.ok) {
    console.error(
      `'${metadataSchemaName}' not found (status:",
      metaResp.status,
      ")`
    );
    return false;
  }
  if (!critResp.ok) {
    console.error(
      `'${criteriaSchemaName}' not found (status:",
      critResp.status,
      ")`
    );
    return false;
  }

  const [metaTxt, critTxt] = await Promise.all([
    metaResp.text(),
    critResp.text(),
  ]);

  // js-yaml must be loaded (as a UMD build and available on window.jsyaml)
  const YAML = window.jsyaml;
  if (typeof YAML === "undefined") {
    console.error("js-yaml library is not loaded on window (window.jsyaml).");
    return false;
  }

  const meta = YAML.load(metaTxt);
  const crit = YAML.load(critTxt);

  const AjvConstructor = window.Ajv;

  if (typeof AjvConstructor !== "function") {
    console.error("Ajv constructor not found on window.");
    return false;
  }

  const ajv = new AjvConstructor({ allErrors: true });

  // register "criteria" schema to allow resolving $ref
  let candidateIds = [criteriaSchemaName].filter(Boolean);

  // remove duplicates (useful only if we combine more schemas automatically)
  candidateIds = [...new Set(candidateIds)];

  for (const sid of candidateIds) {
    try {
      ajv.addSchema(crit, sid);
      console.debug(
        `OK: Schema with id '${sid}' added to Ajv instance. ajv:`,
        ajv
      );
    } catch (e) {
      console.warn(`ERR: Schema with id '${sid}' could not be added:`, e);
    }
  }

  // compile and validate metadata (all $ref should now be resolved)
  const validate = ajv.compile(meta);
  if (!validate(metadata)) {
    console.error(
      "Validation error: Metadata for " + id + " are not valid",
      validate.errors
    );
    return false;
  }

  console.debug("Received 'metadata' for '" + id + "' are valid.");
  return true;
}

async function isValidData(data, id, elementId, plotType) {
  let response;
  try {
    response = await fetch(`/static/data_schema_${plotType}.yaml`);
    if (!response.ok) {
      console.error(
        `Schema file '/static/data_schema_${plotType}.yaml' not found
        (status: ${response.status}) for elementId: ${elementId}`
      );
      return false;
    } else {
      console.debug(
        `Schema file '/static/data_schema_${plotType}.yaml' loaded successfully.`
      );
    }
  } catch (error) {
    console.error(`${error} for '${elementId}`);
    return false;
  }
  const schemaYaml = await response.text();
  // use js-yaml to convert YAML in JS object
  if (typeof window.jsyaml === "undefined") {
    console.error("js-yaml library is not loaded.");
    return false;
  }
  const schema = window.jsyaml.load(schemaYaml);
  const ajv = new window.Ajv();
  const validate = ajv.compile(schema);
  console.debug(
    `Validating 'data' of '${id}' against 'data_schema_${plotType}.yaml'...`
  );
  if (!validate(data)) {
    console.error(
      `Validation error: Data for ${id} are not valid`,
      validate.errors
    );
    return false;
  }
  console.debug(`Received 'data' for '${id}' are valid.`);
  return true;
}

export { isValidMetadata, isValidData };
