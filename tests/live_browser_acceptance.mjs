import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { buildComprehension } from "../prototype/comprehension.js";

const token = process.env.GITHUB_TOKEN || process.env.PROJECT_READER_GITHUB_TOKEN || "";
const headers = {
  Accept: "application/vnd.github+json",
  "X-GitHub-Api-Version": "2022-11-28",
  ...(token ? { Authorization: `Bearer ${token}` } : {})
};

async function github(path, missing = false) {
  const response = await fetch(`https://api.github.com${path}`, { headers });
  if (missing && response.status === 404) return null;
  if (!response.ok) throw new Error(`GitHub ${response.status} for ${path}`);
  return response.json();
}

function decode(payload) {
  if (!payload?.content) return null;
  return Buffer.from(payload.content.replace(/\s/g, ""), "base64").toString("utf8");
}

async function read(fullName) {
  const [owner, name] = fullName.split("/");
  const repo = await github(`/repos/${owner}/${name}`);
  const branch = encodeURIComponent(repo.default_branch);
  const [readmePayload, progressPayload, languages] = await Promise.all([
    github(`/repos/${owner}/${name}/readme?ref=${branch}`),
    github(`/repos/${owner}/${name}/contents/.project/progress.json?ref=${branch}`, true),
    github(`/repos/${owner}/${name}/languages`)
  ]);
  let progress = null;
  if (progressPayload) {
    try { progress = JSON.parse(decode(progressPayload)); } catch { progress = null; }
  }
  return { repo, readme: decode(readmePayload), progress, languages };
}

const synthSource = await read("AudioKit/AudioKitSynthOne");
const synth = buildComprehension(synthSource.repo, synthSource.readme, synthSource.progress, synthSource.languages);
assert.equal(synth.classification.id, "application");
assert.match(synth.purpose, /synthesizer app/i);
assert.match(synth.purpose, /iPhone and iPad/i);
assert.match(synth.purpose, /source code/i);
assert.match(synth.audience, /musicians/i);
assert.match(synth.audience, /developers/i);
assert.ok(synth.actions.some(action => /app/i.test(action.label)));
assert.ok(synth.actions.some(action => /features/i.test(action.label)));
assert.ok(synth.capabilities.some(item => /oscillators/i.test(item) && /filters/i.test(item)));
assert.ok(synth.unfinished.some(item => /AUv3/i.test(item) && /MPE/i.test(item)));
assert.equal(synth.progress.completion, null);

const courseSource = await read("microsoft/AI-For-Beginners");
const course = buildComprehension(courseSource.repo, courseSource.readme, courseSource.progress, courseSource.languages);
assert.equal(course.classification.id, "curriculum");
assert.match(course.purpose, /beginner curriculum/i);
assert.match(course.purpose, /artificial intelligence/i);
assert.match(course.purpose, /24 lessons/i);
assert.match(course.purpose, /12 weeks/i);
assert.match(course.purpose, /quizzes/i);
assert.match(course.purpose, /labs/i);
assert.ok(course.actions.some(action => /course setup|lesson/i.test(action.label)));
assert.ok(course.capabilities.some(item => /neural networks/i.test(item)));
assert.ok(course.capabilities.some(item => /computer vision/i.test(item)));
assert.ok(course.capabilities.some(item => /translated versions/i.test(item)));
assert.equal(course.progress.completion, null);

assert.notEqual(synth.purpose, synthSource.repo.description);
assert.notEqual(course.purpose, courseSource.repo.description);
assert.notEqual(synth.purpose, course.purpose);
assert.ok([...synth.languages, ...course.languages].every(item => item.percentage >= 0.1));
assert.ok(!JSON.stringify({ synth, course }).includes("coding or markup language"));

const report = {
  schema_version: 1,
  checked_repositories: {
    "AudioKit/AudioKitSynthOne": synth,
    "microsoft/AI-For-Beginners": course
  }
};
const output = process.env.PROJECT_READER_ACCEPTANCE_OUTPUT;
if (output) await writeFile(output, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log("live-browser-acceptance=pass");
