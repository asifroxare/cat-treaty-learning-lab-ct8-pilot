import { readdirSync } from "node:fs";
import { extname, join, resolve } from "node:path";
import ts from "typescript";

const root = resolve(new URL("..", import.meta.url).pathname);
const arithmetic = new Set([
  ts.SyntaxKind.PlusToken, ts.SyntaxKind.MinusToken, ts.SyntaxKind.AsteriskToken,
  ts.SyntaxKind.SlashToken, ts.SyntaxKind.PercentToken, ts.SyntaxKind.AsteriskAsteriskToken,
]);
const numericCalls = new Set(["Number", "parseInt", "parseFloat"]);
const approvedGeometryReturns = ["CssPixel", "SvgCoordinate", "VisualizationExtent", "UnitInterval", "RecoveryBarGeometry", "TailPlotGeometry", "string"];

function filesUnder(directory) {
  const files = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...filesUnder(path));
    else if ([".ts", ".tsx"].includes(extname(path))) files.push(path);
  }
  return files;
}

function scan(rootNames, options, fixture = false) {
  const program = ts.createProgram(rootNames, { ...options, noEmit: true, skipLibCheck: true });
  const checker = program.getTypeChecker();
  const violations = [];
  const relevant = (file) => rootNames.includes(file.fileName);
  const typeName = (node) => checker.typeToString(checker.getTypeAtLocation(node));
  const authoritative = (node) => typeName(node).includes("AuthoritativeNumber");
  const geometry = (node) => /CssPixel|SvgCoordinate|VisualizationExtent|UnitInterval/.test(typeName(node));
  const checkedGeometryAdapter = (node) => {
    const signature = checker.getResolvedSignature(node);
    const declaration = signature?.declaration;
    if (!declaration) return false;
    const source = declaration.getSourceFile().fileName.replaceAll("\\", "/");
    return source.includes("/visualization/geometry/")
      && checker.typeToString(signature.getReturnType()) === "string";
  };

  for (const sourceFile of program.getSourceFiles().filter(relevant)) {
    const normalized = sourceFile.fileName.replaceAll("\\", "/");
    const isGeometryModule = normalized.includes("/visualization/geometry/");
    const report = (node, message) => {
      const position = sourceFile.getLineAndCharacterOfPosition(node.getStart());
      violations.push(`${normalized}:${position.line + 1}:${position.character + 1}: ${message}`);
    };
    const visit = (node) => {
      if (!isGeometryModule && ts.isBinaryExpression(node) && arithmetic.has(node.operatorToken.kind)
          && (authoritative(node.left) || authoritative(node.right))) {
        report(node, "arithmetic on AuthoritativeNumber is forbidden outside presentation geometry");
      }
      if (!isGeometryModule && (ts.isPrefixUnaryExpression(node) || ts.isPostfixUnaryExpression(node))
          && authoritative(node.operand)) report(node, "numeric mutation of AuthoritativeNumber is forbidden");
      if (ts.isCallExpression(node)) {
        const expressionText = node.expression.getText(sourceFile);
        const hasAuthoritativeArgument = node.arguments.some(authoritative);
        if (!isGeometryModule && hasAuthoritativeArgument
            && (expressionText.startsWith("Math.") || numericCalls.has(expressionText) || expressionText.endsWith(".reduce"))) {
          report(node, "numeric coercion or aggregation of AuthoritativeNumber is forbidden");
        }
        if (!isGeometryModule && node.arguments.some(geometry)
            && !checkedGeometryAdapter(node)) report(node, "presentation geometry cannot leak into application/display serialization");
      }
      if (!isGeometryModule && ts.isTemplateSpan(node) && geometry(node.expression)) {
        report(node, "presentation geometry cannot be interpolated outside the checked geometry adapter");
      }
      if (isGeometryModule && ts.isFunctionDeclaration(node) && node.name && node.type) {
        const declared = node.type.getText(sourceFile);
        if (!approvedGeometryReturns.some((name) => declared.includes(name))) report(node, "geometry exports require an approved branded/layout return type");
      }
      ts.forEachChild(node, visit);
    };
    visit(sourceFile);
  }
  const diagnostics = ts.getPreEmitDiagnostics(program).filter((item) => item.file && relevant(item.file));
  if (diagnostics.length && fixture) {
    violations.push(...diagnostics.map((item) => ts.flattenDiagnosticMessageText(item.messageText, " ")));
  }
  return violations;
}

const configPath = join(root, "tsconfig.app.json");
const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
const parsed = ts.parseJsonConfigFileContent(configFile.config, ts.sys, root);
const production = parsed.fileNames.filter((path) => !path.includes("/test/") && !path.includes("/api/generated/"));
const productionViolations = scan(production, parsed.options);

const fixtureRoot = join(root, "scripts", "fixtures");
const fixtureOptions = { strict: true, target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext, moduleResolution: ts.ModuleResolutionKind.Bundler };
const passing = scan([join(fixtureRoot, "visualization", "geometry", "passing.ts")], fixtureOptions, true);
const formulaFailure = scan([join(fixtureRoot, "failing-formula.ts")], fixtureOptions, true);
const leakageFailure = scan([join(fixtureRoot, "failing-geometry-leakage.ts")], fixtureOptions, true);

if (productionViolations.length || passing.length || formulaFailure.length === 0 || leakageFailure.length === 0) {
  const details = [
    ...productionViolations,
    ...passing.map((item) => `passing geometry fixture unexpectedly failed: ${item}`),
    ...(formulaFailure.length === 0 ? ["failing actuarial-formula fixture was not detected"] : []),
    ...(leakageFailure.length === 0 ? ["failing geometry-leakage fixture was not detected"] : []),
  ];
  throw new Error(`CT7 authoritative-number gate failed:\n${details.join("\n")}`);
}
console.log("CT7 type-aware calculation/geometry gate: PASS");
console.log(`Required fixtures: passing geometry PASS; actuarial formula rejected (${formulaFailure.length}); geometry leakage rejected (${leakageFailure.length})`);
