#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

async function main() {
  const [, , input, output] = process.argv;
  if (!input || !output) {
    console.error("Usage: node render_png.cjs <input.svg> <output.png>");
    process.exitCode = 2;
    return;
  }
  if (!fs.existsSync(input)) {
    console.error(`Input SVG not found: ${input}`);
    process.exitCode = 2;
    return;
  }
  let sharp;
  try {
    sharp = require("sharp");
  } catch (error) {
    console.error("PNG rendering requires the optional Node.js package 'sharp'. Keep the SVG output or install sharp.");
    process.exitCode = 3;
    return;
  }
  fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
  await sharp(input, { density: 144 }).png().toFile(output);
  process.stdout.write(`${path.resolve(output)}\n`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});

