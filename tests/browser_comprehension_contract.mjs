import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { buildComprehension, classifyProject, languageRows, safePublicUrl } from "../prototype/comprehension.js";

const fixtureUrl = new URL("./fixtures/browser_comprehension.json", import.meta.url);
const fixtures = JSON.parse(await readFile(fixtureUrl, "utf8"));

const synth = buildComprehension(fixtures.synth.repo, fixtures.synth.readme, null, fixtures.synth.languages);
assert.equal(synth.classification.id, "application");
assert.match(synth.classification.label, /open-source codebase/i);
assert.match(synth.purpose, /playable open-source synthesizer app for iPhone and iPad/i);
assert.match(synth.purpose, /study, change and contribute/i);
assert.match(synth.audience, /musicians/i);
assert.match(synth.audience, /developers/i);
assert.ok(synth.actions.some(action => /app/i.test(action.label) && action.url.startsWith("https://itunes.apple.com/")));
assert.ok(synth.actions.some(action => /features/i.test(action.label)));
assert.ok(synth.capabilities.some(item => /oscillators, filters, reverbs, effects/i.test(item)));
assert.ok(synth.capabilities.some(item => /accessibility|Universal/i.test(item)));
assert.ok(synth.unfinished.some(item => /AUv3/i.test(item) && /MPE/i.test(item)));
assert.equal(synth.progress.completion, null);
assert.ok(synth.evidence.length >= 4);

const course = buildComprehension(fixtures.course.repo, fixtures.course.readme, null, fixtures.course.languages);
assert.equal(course.classification.id, "curriculum");
assert.match(course.purpose, /beginner curriculum for learning artificial intelligence/i);
assert.match(course.purpose, /24 lessons/i);
assert.match(course.purpose, /12 weeks/i);
assert.match(course.purpose, /quizzes and practical labs/i);
assert.match(course.audience, /beginners/i);
assert.ok(course.actions.some(action => action.label === "Start with the course setup"));
assert.ok(course.capabilities.some(item => /symbolic artificial intelligence/i.test(item)));
assert.ok(course.capabilities.some(item => /translated versions/i.test(item)));
assert.ok(course.unfinished.some(item => /does not cover|leaves some subjects/i.test(item)));
assert.equal(course.progress.completion, null);

assert.notEqual(synth.purpose, fixtures.synth.repo.description);
assert.notEqual(course.purpose, fixtures.course.repo.description);
assert.notEqual(synth.purpose, course.purpose);

const unknown = buildComprehension(fixtures.unknown.repo, fixtures.unknown.readme, null, fixtures.unknown.languages);
assert.equal(classifyProject(fixtures.unknown.repo, fixtures.unknown.readme).id, "unknown");
assert.equal(unknown.progress.completion, null);
assert.ok(!JSON.stringify(unknown).includes("coding or markup language"));
assert.ok(unknown.languages.every(item => item.percentage >= 0.1));
assert.equal(unknown.languages.find(item => item.name === "MadeUpLanguage")?.help, null);

assert.equal(safePublicUrl("javascript:alert(1)"), null);
assert.equal(safePublicUrl("http://example.com"), null);
assert.equal(safePublicUrl("https://example.com/path"), "https://example.com/path");

const tiny = languageRows({Large: 9999, Tiny: 1});
assert.deepEqual(tiny.map(item => item.name), ["Large"]);

console.log("browser-comprehension-contract=pass");
