import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { buildComprehension, classifyProject, languageRows, safePublicUrl } from "../prototype/comprehension.js";
import { polishReading } from "../prototype/polish.js";

const fixtureUrl = new URL("./fixtures/browser_comprehension.json", import.meta.url);
const fixtures = JSON.parse(await readFile(fixtureUrl, "utf8"));

function readFixture(fixture) {
  return polishReading(
    buildComprehension(fixture.repo, fixture.readme, null, fixture.languages),
    fixture.repo,
    fixture.readme
  );
}

const synth = readFixture(fixtures.synth);
assert.equal(synth.classification.id, "application");
assert.match(synth.classification.label, /open-source codebase/i);
assert.match(synth.purpose, /playable open-source synthesizer app for iPhone and iPad/i);
assert.match(synth.purpose, /study, change and contribute/i);
assert.match(synth.audience, /musicians/i);
assert.match(synth.audience, /developers/i);
assert.ok(synth.actions.some(action => /app/i.test(action.label) && action.url.startsWith("https://itunes.apple.com/")));
assert.ok(synth.actions.some(action => /features/i.test(action.label)));
assert.ok(synth.actions.some(action => action.label === "Study or change the source code"));
assert.ok(synth.actions.every(action => !/sdk|locali[sz]ation/i.test(`${action.label} ${action.source}`)));
assert.ok(synth.capabilities.some(item => /oscillators, filters, reverbs and effects/i.test(item)));
assert.ok(synth.capabilities.some(item => /iPhone\/Universal version and accessibility support/i.test(item)));
assert.ok(synth.unfinished.some(item => /AUv3/i.test(item) && /MPE/i.test(item)));
assert.ok(synth.unfinished.some(item => /preset search, a MIDI learn matrix and assignable touchpads/i.test(item)));
assert.equal(synth.progress.completion, null);
assert.ok(synth.evidence.length >= 4);

const course = readFixture(fixtures.course);
assert.equal(course.classification.id, "curriculum");
assert.match(course.purpose, /beginner curriculum for learning artificial intelligence/i);
assert.match(course.purpose, /24 lessons/i);
assert.match(course.purpose, /12 weeks/i);
assert.match(course.purpose, /quizzes and practical labs/i);
assert.match(course.audience, /beginners/i);
assert.ok(course.actions.some(action => action.label === "Start with the course setup"));
assert.ok(course.actions.some(action => action.label === "Browse the course lessons"));
assert.ok(course.actions.every(action => !/^@|Machine Learning for Beginners/i.test(action.label)));
assert.ok(course.capabilities.some(item => /symbolic artificial intelligence/i.test(item)));
assert.ok(course.capabilities.some(item => /translated versions/i.test(item)));
assert.ok(course.unfinished.some(item => /business uses of AI/i.test(item)));
assert.ok(course.unfinished.some(item => /deeper mathematics of deep learning/i.test(item)));
assert.equal(course.progress.completion, null);
assert.ok(course.evidence.every(record => !/sketchnote|:---:|@girlie/i.test(record.excerpt)));

assert.notEqual(synth.purpose, fixtures.synth.repo.description);
assert.notEqual(course.purpose, fixtures.course.repo.description);
assert.notEqual(synth.purpose, course.purpose);

const unknown = readFixture(fixtures.unknown);
assert.equal(classifyProject(fixtures.unknown.repo, fixtures.unknown.readme).id, "unknown");
assert.equal(unknown.progress.completion, null);
assert.ok(!JSON.stringify(unknown).includes("coding or markup language"));
assert.ok(unknown.languages.every(item => item.percentage >= 0.1));
assert.equal(unknown.languages.find(item => item.name === "MadeUpLanguage")?.help, null);

assert.equal(safePublicUrl("javascript:alert(1)"), null);
assert.equal(safePublicUrl("http://example.com"), null);
assert.equal(safePublicUrl("https://example.com/path"), "https://example.com/path");

const tiny = languageRows({ Large: 9999, Tiny: 1 });
assert.deepEqual(tiny.map(item => item.name), ["Large"]);

console.log("browser-comprehension-contract=pass");
