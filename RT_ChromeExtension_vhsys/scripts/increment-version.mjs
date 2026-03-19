import fs from 'fs';
import path from 'path';

const versionFilePath = path.resolve(process.cwd(), 'version.ts');
const versionFileContent = fs.readFileSync(versionFilePath, 'utf-8');

const versionRegex = /export const updated_version = "(\d+)\.(\d+)\.(\d+)";/;
const match = versionFileContent.match(versionRegex);

if (match) {
  let [major, minor, patch] = match.slice(1).map(Number);
  patch++;
  const newVersion = `${major}.${minor}.${patch}`;
  const newContent = versionFileContent.replace(versionRegex, `export const updated_version = "${newVersion}";`);
  fs.writeFileSync(versionFilePath, newContent);
  console.log(`Version bumped to ${newVersion}`);
} else {
  console.error("Could not find version in version.ts");
  process.exit(1);
}
