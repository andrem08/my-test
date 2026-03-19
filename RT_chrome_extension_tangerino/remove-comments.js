const fs = require('fs');
const ts = require('typescript');

const files = process.argv.slice(2);

files.forEach(file => {
  try {
    const sourceCode = fs.readFileSync(file, 'utf8');
    const sourceFile = ts.createSourceFile(
      file,
      sourceCode,
      ts.ScriptTarget.Latest,
      true
    );

    const printer = ts.createPrinter({ removeComments: true });
    const result = printer.printFile(sourceFile);

    fs.writeFileSync(file, result, 'utf8');
    console.log(`Comments removed from ${file}`);
  } catch (error) {
    console.error(`Error processing file ${file}: ${error.message}`);
  }
});