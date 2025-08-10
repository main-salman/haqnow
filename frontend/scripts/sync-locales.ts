import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

type Json = Record<string, any>;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const localesDir = path.resolve(__dirname, '../src/i18n/locales');
const enPath = path.join(localesDir, 'en.json');

function readJson(file: string): Json {
  return JSON.parse(fs.readFileSync(file, 'utf8')) as Json;
}

function writeJson(file: string, data: Json) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

function mergeMissingKeys(base: Json, target: Json): Json {
  // Recursively merge: keep target values; add missing from base
  const result: Json = Array.isArray(base) ? [] : {};
  for (const key of Object.keys(base)) {
    const baseVal = base[key];
    const targetHas = Object.prototype.hasOwnProperty.call(target, key);
    if (baseVal && typeof baseVal === 'object' && !Array.isArray(baseVal)) {
      const targetVal = targetHas && target[key] && typeof target[key] === 'object' ? target[key] : {};
      result[key] = mergeMissingKeys(baseVal, targetVal);
    } else {
      result[key] = targetHas ? target[key] : baseVal;
    }
  }
  // Preserve any extra keys in target not present in base
  for (const key of Object.keys(target)) {
    if (!Object.prototype.hasOwnProperty.call(base, key)) {
      result[key] = target[key];
    }
  }
  return result;
}

function main() {
  const en = readJson(enPath);
  const files = fs.readdirSync(localesDir).filter(f => f.endsWith('.json') && f !== 'en.json');
  let updated = 0;
  for (const file of files) {
    const p = path.join(localesDir, file);
    const data = readJson(p);
    const merged = mergeMissingKeys(en, data);
    writeJson(p, merged);
    updated += 1;
    console.log(`Synced locale: ${file}`);
  }
  console.log(`Done. Synced ${updated} locales to match en.json keys.`);
}

main();


