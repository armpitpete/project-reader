import { buildComprehension, safePublicUrl, validProgress } from "./comprehension.js";
import { correctNetworkServiceReading } from "./network-corrections.js";
import { polishReading } from "./polish.js";
import {
  fallbackNotice,
  fallbackRepository,
  fetchRawReadme,
  GitHubApiError,
  repositoryReference
} from "./resilience.js";

const GITHUB_API = "https://api.github.com";
const form = document.querySelector("#reader-form");
const input = document.querySelector("#repository");
const button = document.querySelector("#read-button");
const statusLine = document.querySelector("#status-line");
const result = document.querySelector("#reader-result");

function setStatus(message, tone = "") {
  statusLine.textContent = message;
  statusLine.dataset.tone = tone;
}

function setBusy(busy) {
  button.disabled = busy;
  input.disabled = busy;
  button.textContent = busy ? "Reading…" : "Read this project";
}

function clearResult() {
  result.replaceChildren();
  result.dataset.visible = "false";
}

function el(name, text = "", className = "") {
  const node = document.createElement(name);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function appendParagraph(parent, text, className = "") {
  parent.append(el("p", text, className));
}

function externalLink(text, href, className = "external-link") {
  const safeHref = safePublicUrl(href);
  if (!safeHref) throw new Error("A public link in the repository evidence was unsafe.");
  const link = el("a", text, className);
  link.href = safeHref;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function answerCard(title) {
  const card = el("section", "", "answer-card");
  card.append(el("h3", title));
  return card;
}

function addTextList(parent, items, emptyText) {
  if (!items.length) {
    appendParagraph(parent, emptyText, "muted");
    return;
  }
  const list = el("ul", "", "answer-list");
  for (const item of items) list.append(el("li", item));
  parent.append(list);
}

function addActionList(parent, actions) {
  if (!actions.length) {
    appendParagraph(parent, "No clear public action was found in the README.", "muted");
    return;
  }
  const list = el("ul", "", "action-list");
  for (const action of actions) {
    const item = el("li");
    item.append(externalLink(action.label, action.url));
    if (action.source) item.append(el("span", `From: ${action.source}`, "source-note"));
    list.append(item);
  }
  parent.append(list);
}

async function githubJson(path, allowMissing = false) {
  let response;
  try {
    response = await fetch(`${GITHUB_API}${path}`, {
      method: "GET",
      headers: {
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
      },
      cache: "no-store"
    });
  } catch {
    throw new GitHubApiError("GitHub's metadata service could not be reached.", { unavailable: true });
  }
  if (allowMissing && response.status === 404) return null;
  if (response.status === 404) {
    throw new GitHubApiError("GitHub could not find that public repository. Check the name and visibility.", { status: 404 });
  }
  if (response.status === 403 || response.status === 429) {
    throw new GitHubApiError("GitHub's public request allowance is unavailable.", {
      status: response.status,
      unavailable: true,
      rateLimited: true
    });
  }
  if (!response.ok) {
    throw new GitHubApiError("GitHub could not provide repository metadata right now.", {
      status: response.status,
      unavailable: response.status >= 500
    });
  }
  return response.json();
}

async function optionalGithubJson(path) {
  try {
    return { value: await githubJson(path, true), unavailable: false };
  } catch (error) {
    if (error instanceof GitHubApiError && error.unavailable) {
      return { value: null, unavailable: true };
    }
    throw error;
  }
}

function decodeFile(payload) {
  if (!payload || payload.type !== "file" || payload.encoding !== "base64" || typeof payload.content !== "string") return null;
  try {
    const binary = atob(payload.content.replace(/\s/g, ""));
    const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
    return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
  } catch {
    return null;
  }
}

function parseProgress(payload) {
  const text = decodeFile(payload);
  if (!text) return null;
  try {
    const candidate = JSON.parse(text);
    return validProgress(candidate) ? candidate : null;
  } catch {
    return null;
  }
}

async function readFallback(reference, { rateLimited = false, forced = false } = {}) {
  const raw = await fetchRawReadme(reference);
  return {
    repo: fallbackRepository(reference, raw.ref),
    readme: raw.text,
    progress: null,
    languages: {},
    checkedAt: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    context: {
      sourceMode: "readme-fallback",
      metadataAvailable: false,
      languageDataAvailable: false,
      rateLimited,
      notice: forced
        ? "README fallback mode was deliberately used for this proof. Repository metadata, licence, language totals and owner progress were not requested."
        : fallbackNotice(rateLimited)
    }
  };
}

export async function readRepository(referenceValue, { forceFallback = false } = {}) {
  const reference = repositoryReference(referenceValue);
  if (forceFallback) return readFallback(reference, { forced: true });

  let repo;
  try {
    repo = await githubJson(`/repos/${encodeURIComponent(reference.owner)}/${encodeURIComponent(reference.repo)}`);
  } catch (error) {
    if (error instanceof GitHubApiError && error.unavailable) {
      return readFallback(reference, { rateLimited: error.rateLimited });
    }
    throw error;
  }
  if (repo.private) throw new Error("Private repositories are not supported.");

  const base = `/repos/${encodeURIComponent(repo.owner.login)}/${encodeURIComponent(repo.name)}`;
  const branch = encodeURIComponent(repo.default_branch);
  const [rawResult, progressResult, languagesResult] = await Promise.all([
    fetchRawReadme(reference).catch(() => null),
    optionalGithubJson(`${base}/contents/.project/progress.json?ref=${branch}`),
    optionalGithubJson(`${base}/languages`)
  ]);

  let readme = rawResult?.text || null;
  let readmeApiUnavailable = false;
  if (!readme) {
    const readmeResult = await optionalGithubJson(`${base}/readme?ref=${branch}`);
    readme = decodeFile(readmeResult.value);
    readmeApiUnavailable = readmeResult.unavailable;
  }
  if (!readme) {
    if (progressResult.unavailable || languagesResult.unavailable || readmeApiUnavailable) {
      return readFallback(reference, { rateLimited: true });
    }
    throw new Error("The repository does not provide a readable public README.");
  }

  const partialMetadata = progressResult.unavailable || languagesResult.unavailable;
  return {
    repo,
    readme,
    progress: parseProgress(progressResult.value),
    languages: languagesResult.value || {},
    checkedAt: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    context: {
      sourceMode: partialMetadata ? "api-partial" : "api-enriched",
      metadataAvailable: true,
      languageDataAvailable: !languagesResult.unavailable,
      rateLimited: partialMetadata,
      notice: partialMetadata
        ? "The public README was read successfully, but some optional GitHub metadata was unavailable. The plain reading remains usable; missing technical details are labelled below."
        : ""
    }
  };
}

export function renderReading(repo, readme, progress, languages, checkedAt, context = {}) {
  const baseReading = polishReading(
    buildComprehension(repo, readme, progress, languages),
    repo,
    readme
  );
  const reading = correctNetworkServiceReading(baseReading, repo, readme);
  const article = el("article", "", "reader-result-content");

  if (context.notice) appendParagraph(article, context.notice, "notice");

  const header = el("header", "", "reading-header");
  header.append(el("p", reading.classification.label, "eyebrow"));
  header.append(el("h2", repo.full_name));
  appendParagraph(header, reading.purpose, "project-summary");
  const tags = el("div", "", "tag-row");
  if (context.metadataAvailable === false) {
    tags.append(el("span", "README-only reading", "tag"));
  } else {
    tags.append(el("span", repo.archived ? "Archived repository" : "Active repository", "tag"));
    if (repo.fork) tags.append(el("span", "Fork of another repository", "tag"));
    if (repo.license?.spdx_id) tags.append(el("span", `Licence: ${repo.license.spdx_id}`, "tag"));
  }
  header.append(tags);
  article.append(header);

  const simple = el("section", "", "simple-reading");
  simple.append(el("h2", "Plain reading"));

  let card = answerCard("What is this?");
  appendParagraph(card, reading.purpose);
  simple.append(card);

  card = answerCard("Who is it for?");
  appendParagraph(card, reading.audience);
  simple.append(card);

  card = answerCard("What can I do with it?");
  addActionList(card, reading.actions.slice(0, 4));
  simple.append(card);

  card = answerCard("What already exists?");
  addTextList(card, reading.capabilities, "No clearly delivered outcomes were found in the README.");
  simple.append(card);

  card = answerCard("What is unfinished or uncertain?");
  addTextList(card, reading.unfinished, "The public evidence does not clearly describe remaining work.");
  simple.append(card);

  card = answerCard("Where should I start?");
  if (reading.start) {
    appendParagraph(card, "This is the clearest public starting point found in the repository evidence.");
    card.append(externalLink(reading.start.label, reading.start.url, "primary-action external-link"));
  } else {
    appendParagraph(card, "No clear starting action was found. The repository itself is the safest next step.", "muted");
    card.append(externalLink("Open the source repository", repo.html_url));
  }
  simple.append(card);
  article.append(simple);

  const statusDetails = el("details");
  statusDetails.append(el("summary", "Project completion and uncertainty"));
  const statusGrid = el("div", "", "detail-grid");
  const completionText = reading.progress.completion === null
    ? "Unknown"
    : `${reading.progress.completion}% of the owner-defined stages`;
  appendParagraph(statusGrid, `Defined-stage completion: ${completionText}. ${reading.progress.completionReason}`);
  const likelihood = reading.progress.allComplete
    ? "The owner-defined stages are complete; a future completion forecast is not needed."
    : "Likelihood of finishing is unknown. Public repository files do not support a reliable prediction.";
  appendParagraph(statusGrid, likelihood);
  appendParagraph(statusGrid, "Open issues, recent activity, repository age and language amounts are not treated as completion evidence.");
  statusDetails.append(statusGrid);
  article.append(statusDetails);

  const evidenceDetails = el("details");
  evidenceDetails.append(el("summary", "Evidence behind the plain reading"));
  const evidenceGrid = el("div", "", "detail-grid");
  if (reading.evidence.length) {
    const evidenceList = el("ol", "", "evidence-list evidence-records");
    for (const record of reading.evidence) {
      const item = el("li");
      item.append(el("strong", record.statement));
      appendParagraph(item, `README section: ${record.source}`, "source-note");
      appendParagraph(item, `Evidence: ${record.excerpt}`, "evidence-excerpt");
      evidenceList.append(item);
    }
    evidenceGrid.append(evidenceList);
  } else {
    appendParagraph(evidenceGrid, "No short README passages could be linked to derived statements.", "muted");
  }
  evidenceDetails.append(evidenceGrid);
  article.append(evidenceDetails);

  const technical = el("details");
  technical.append(el("summary", "Technical sources and implementation details"));
  const technicalGrid = el("div", "", "detail-grid");
  if (context.metadataAvailable === false) {
    appendParagraph(technicalGrid, `README source reference: ${repo.default_branch}. Checked: ${checkedAt}. Repository metadata was unavailable.`, "small");
  } else {
    appendParagraph(technicalGrid, `Source branch: ${repo.default_branch}. Checked: ${checkedAt}.`, "small");
  }
  appendParagraph(technicalGrid, `Project type: ${reading.classification.label}. Classification confidence: ${reading.classification.confidence}.`, "small");

  const sourceList = el("ul", "", "evidence-list");
  const repoItem = el("li");
  repoItem.append(externalLink("Repository", repo.html_url));
  sourceList.append(repoItem);
  if (readme) {
    const readmeItem = el("li");
    readmeItem.append(externalLink("README", `${repo.html_url}#readme`));
    sourceList.append(readmeItem);
  }
  if (progress) {
    const progressItem = el("li");
    progressItem.append(externalLink("Owner progress record", `${repo.html_url}/blob/${encodeURIComponent(repo.default_branch)}/.project/progress.json`));
    sourceList.append(progressItem);
  }
  if (context.languageDataAvailable !== false) {
    const languagesItem = el("li");
    languagesItem.append(externalLink("GitHub language data", `${GITHUB_API}/repos/${repo.full_name}/languages`));
    sourceList.append(languagesItem);
  }
  technicalGrid.append(sourceList);

  if (reading.languages.length) {
    technicalGrid.append(el("h3", "Detected implementation languages"));
    const languageList = el("ul", "", "evidence-list");
    for (const language of reading.languages) {
      const text = language.help
        ? `${language.name}: ${language.percentage}% of language bytes. ${language.help}`
        : `${language.name}: ${language.percentage}% of language bytes reported by GitHub.`;
      languageList.append(el("li", text));
    }
    technicalGrid.append(languageList);
  } else if (context.languageDataAvailable === false) {
    appendParagraph(technicalGrid, "Implementation-language totals were not available in this reading mode.", "small muted");
  }

  appendParagraph(
    technicalGrid,
    context.sourceMode === "readme-fallback"
      ? "This reduced reading uses a public README fetched directly from GitHub's raw-content service. It does not use an account, token, server, repository clone or write access."
      : "This reading uses public GitHub responses in your browser. It does not clone the repository, run its code, inspect private data or write anything.",
    "small"
  );
  technical.append(technicalGrid);
  article.append(technical);

  return article;
}

async function runReading(reference, { forceFallback = false } = {}) {
  clearResult();
  setBusy(true);
  setStatus(forceFallback ? "Reading the public README in fallback mode…" : "Reading the README and public repository evidence…");
  try {
    const reading = await readRepository(reference, { forceFallback });
    result.append(renderReading(
      reading.repo,
      reading.readme,
      reading.progress,
      reading.languages,
      reading.checkedAt,
      reading.context
    ));
    result.dataset.visible = "true";
    setStatus(
      reading.context.sourceMode === "readme-fallback"
        ? "Reading complete using the public README fallback."
        : "Reading complete.",
      reading.context.sourceMode === "readme-fallback" ? "warning" : ""
    );
    result.focus({ preventScroll: true });
    result.scrollIntoView({ block: "start" });
    const url = new URL(window.location.href);
    url.searchParams.set("repo", reading.repo.full_name);
    url.searchParams.delete("autorun");
    history.replaceState(null, "", url);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Project Reader could not read that public repository.";
    setStatus(message, "error");
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  runReading(input.value);
});

const initialUrl = new URL(window.location.href);
const initial = initialUrl.searchParams.get("repo");
const forceFallback = initialUrl.searchParams.get("fallback") === "1";
if (initial) {
  input.value = initial;
  if (initialUrl.searchParams.get("autorun") === "1") runReading(initial, { forceFallback });
}
