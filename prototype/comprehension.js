const MAX_README_CHARS = 180_000;
const MAX_LINKS = 240;
const MAX_EVIDENCE = 10;

const LANGUAGE_HELP = {
  Python: "Python is used for step-by-step computer instructions, automation, data work and web services.",
  JavaScript: "JavaScript is commonly used to make web pages and applications respond to people.",
  TypeScript: "TypeScript adds extra checks to JavaScript code so some mistakes can be found earlier.",
  HTML: "HTML describes the headings, text, links, controls and other content on a web page.",
  CSS: "CSS controls the visible layout and appearance of web pages.",
  Shell: "Shell scripts automate command-line tasks.",
  PowerShell: "PowerShell scripts automate computer and administrative tasks.",
  "C++": "C++ is often used where software needs close control of performance, memory or hardware.",
  C: "C is often used for operating systems, embedded devices and performance-sensitive software.",
  Rust: "Rust is designed for fast software with strong checks against some memory errors.",
  Java: "Java is used for applications that run through the Java platform.",
  Kotlin: "Kotlin is commonly used for Android applications and Java-platform software.",
  Swift: "Swift is mainly used to build applications for Apple devices.",
  PHP: "PHP is commonly used by web servers to build pages and work with stored information.",
  Ruby: "Ruby is often used for web applications and automation.",
  Go: "Go is often used for network services and command-line tools.",
  SourcePawn: "SourcePawn is used to make plugins for Source-engine game servers.",
  Pawn: "Pawn is used in some games and embedded systems."
};

const TYPE_RULES = [
  {
    id: "curriculum",
    label: "Learning course or curriculum",
    patterns: [
      [/\b(?:curriculum|course syllabus|learning path)\b/gi, 7],
      [/\b(?:lessons?|quizzes?|labs?|course setup|what you will learn)\b/gi, 3],
      [/\b(?:week|weeks)\b/gi, 2],
      [/\b(?:for beginners?|beginner-friendly)\b/gi, 4]
    ]
  },
  {
    id: "application",
    label: "Application or product",
    patterns: [
      [/\b(?:app store|download (?:the )?app|get app|playable app)\b/gi, 8],
      [/\b(?:iphone|ipad|android app|desktop app|mobile app)\b/gi, 4],
      [/\b(?:web application|software application|synthesizer app)\b/gi, 5],
      [/\bapp\b/gi, 1]
    ]
  },
  {
    id: "library",
    label: "Library or framework",
    patterns: [
      [/\b(?:software library|framework|sdk|developer library)\b/gi, 6],
      [/\b(?:package|module|api)\b/gi, 1]
    ]
  },
  {
    id: "command-line",
    label: "Command-line tool",
    patterns: [
      [/\b(?:command-line|command line|cli|terminal tool)\b/gi, 7],
      [/\busage:\s*\w+/gi, 3]
    ]
  },
  {
    id: "website",
    label: "Website or web application",
    patterns: [
      [/\b(?:live website|live demo|web app|website)\b/gi, 5],
      [/\b(?:open in your browser|deployed at)\b/gi, 3]
    ]
  },
  {
    id: "documentation",
    label: "Documentation or reference collection",
    patterns: [
      [/\b(?:documentation site|reference collection|handbook|knowledge base)\b/gi, 7],
      [/\b(?:documentation|reference guide|guide collection)\b/gi, 3]
    ]
  },
  {
    id: "template",
    label: "Template or starter project",
    patterns: [
      [/\b(?:starter project|project template|boilerplate|scaffold|starter kit)\b/gi, 7],
      [/\btemplate\b/gi, 4]
    ]
  },
  {
    id: "research",
    label: "Research or dataset repository",
    patterns: [
      [/\b(?:research dataset|dataset repository|corpus|benchmark dataset)\b/gi, 7],
      [/\b(?:research paper|experimental results|benchmark)\b/gi, 3]
    ]
  }
];

function normaliseSpace(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function decodeEntities(value) {
  return String(value || "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ");
}

export function cleanMarkdown(value) {
  return normaliseSpace(
    decodeEntities(String(value || "")
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/~~~[\s\S]*?~~~/g, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/^\s*(?:[-*+]|\d+[.)]|✓)\s+/gm, "")
      .replace(/[>*_~|]/g, " "))
  );
}

function sentenceCase(value) {
  const text = normaliseSpace(value);
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function clip(value, limit = 220) {
  const text = normaliseSpace(value);
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit - 1).replace(/\s+\S*$/, "").trim();
  return `${cut}…`;
}

function parseSections(readme) {
  const text = String(readme || "").slice(0, MAX_README_CHARS).replace(/\r\n?/g, "\n");
  const lines = text.split("\n");
  const sections = [];
  let current = { heading: "Overview", level: 0, lines: [] };

  for (const line of lines) {
    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (heading) {
      sections.push(current);
      current = {
        heading: clip(cleanMarkdown(heading[2]), 120) || "Untitled section",
        level: heading[1].length,
        lines: []
      };
    } else {
      current.lines.push(line);
    }
  }
  sections.push(current);

  return sections
    .map(section => {
      const raw = section.lines.join("\n");
      const paragraphs = raw
        .split(/\n\s*\n/)
        .map(cleanMarkdown)
        .filter(item => item.length >= 16);
      const bullets = section.lines
        .filter(line => /^\s*(?:[-*+]|\d+[.)]|✓)\s+/.test(line))
        .map(cleanMarkdown)
        .filter(item => item.length >= 3);
      return {
        ...section,
        raw,
        text: cleanMarkdown(raw),
        paragraphs,
        bullets
      };
    })
    .filter(section => section.heading !== "Overview" || section.text);
}

function sectionCorpus(sections, limit = 18_000) {
  return sections.map(section => `${section.heading}\n${section.text}`).join("\n").slice(0, limit);
}

function countMatches(text, pattern) {
  const matches = text.match(pattern);
  return matches ? matches.length : 0;
}

function typeScores(sections, repo) {
  const early = sections.slice(0, 8).map(section => `${section.heading} ${section.text}`).join(" ");
  const corpus = `${repo?.name || ""} ${repo?.description || ""} ${early}`;
  const scores = TYPE_RULES.map(rule => ({
    id: rule.id,
    label: rule.label,
    score: rule.patterns.reduce((total, [pattern, weight]) => total + countMatches(corpus, pattern) * weight, 0)
  }));

  const curriculum = scores.find(item => item.id === "curriculum");
  const application = scores.find(item => item.id === "application");
  if (curriculum && /\b(?:curriculum|course syllabus|learning path)\b/i.test(corpus)) curriculum.score += 8;
  if (application && /\b(?:app store|download (?:the )?app|get app)\b/i.test(corpus)) application.score += 8;

  scores.sort((a, b) => b.score - a.score || a.label.localeCompare(b.label));
  return scores;
}

function containsOpenSourceCode(corpus) {
  return /\b(?:open[- ]source(?:d)? (?:the )?code|source code|modify (?:the )?code|contribute (?:code|to (?:the )?project)|code usage)\b/i.test(corpus);
}

export function classifyProject(repo, readme) {
  const sections = parseSections(readme);
  const scores = typeScores(sections, repo);
  const top = scores[0];
  const second = scores[1];
  const corpus = sectionCorpus(sections);
  const hasCodebase = containsOpenSourceCode(corpus);

  if (!top || top.score < 6) {
    return { id: "unknown", label: "Mixed or unclear project", confidence: "low", scores, hasCodebase };
  }

  const closeSecond = second && second.score >= 6 && second.score >= top.score * 0.84;
  if (top.id === "application" && hasCodebase) {
    return { id: "application", label: "Application and open-source codebase", confidence: "high", scores, hasCodebase };
  }
  if (closeSecond && !["curriculum", "application"].includes(top.id)) {
    return { id: "mixed", label: `${top.label} with ${second.label.toLowerCase()}`, confidence: "medium", scores, hasCodebase };
  }
  return { id: top.id, label: top.label, confidence: top.score >= 14 ? "high" : "medium", scores, hasCodebase };
}

function findSection(sections, pattern) {
  return sections.find(section => pattern.test(section.heading) || pattern.test(section.text));
}

function findEvidence(sections, keywords, fallbackHeading = "README") {
  const lowerKeywords = keywords.map(item => item.toLowerCase());
  for (const section of sections) {
    const candidates = [...section.paragraphs, ...section.bullets];
    for (const candidate of candidates) {
      const lower = candidate.toLowerCase();
      if (lowerKeywords.some(keyword => lower.includes(keyword))) {
        return { source: section.heading || fallbackHeading, excerpt: clip(candidate, 190) };
      }
    }
  }
  return null;
}

function addEvidence(evidence, statement, found) {
  if (!statement || !found || evidence.length >= MAX_EVIDENCE) return;
  const key = `${statement}|${found.source}|${found.excerpt}`;
  if (evidence.some(item => `${item.statement}|${item.source}|${item.excerpt}` === key)) return;
  evidence.push({ statement, source: found.source, excerpt: found.excerpt });
}

function subjectFromReadme(repo, sections) {
  const headingText = sections.slice(0, 3).map(section => section.heading).join(" ");
  if (/artificial intelligence/i.test(headingText) || /\bAI for beginners\b/i.test(headingText)) return "artificial intelligence";
  const forBeginners = headingText.match(/(.{2,70}?)\s+for beginners/i);
  if (forBeginners) return cleanMarkdown(forBeginners[1]).toLowerCase();
  const corpus = sectionCorpus(sections, 5_000);
  const learn = corpus.match(/(?:curriculum|course)\s+(?:for|about)\s+(?:learning\s+)?([^.!?]{3,80})/i);
  if (learn) return cleanMarkdown(learn[1]).toLowerCase();
  const name = String(repo?.name || "").replace(/[-_]+/g, " ").replace(/\bfor beginners\b/i, "").trim();
  return name ? name.toLowerCase() : "the subject";
}

function countFact(corpus, unit) {
  const pattern = new RegExp(`\\b(\\d{1,3})[ -]?${unit}s?\\b`, "i");
  const match = corpus.match(pattern);
  return match ? Number(match[1]) : null;
}

function platformFact(corpus) {
  if (/\b(?:universal for )?iphone\s*\/\s*ipad\b/i.test(corpus)) {
    return ["iPhone", "iPad"];
  }
  const platforms = [];
  if (/\biphone\b/i.test(corpus)) platforms.push("iPhone");
  if (/\bipad\b/i.test(corpus)) platforms.push("iPad");
  if (/\bandroid\b/i.test(corpus)) platforms.push("Android");
  if (/\bwindows\b/i.test(corpus)) platforms.push("Windows");
  if (/\bmac(?:os)?\b/i.test(corpus)) platforms.push("Mac");
  if (/\blinux\b/i.test(corpus)) platforms.push("Linux");
  return [...new Set(platforms)].slice(0, 3);
}

function extractMarkdownLinks(readme, repo) {
  const text = String(readme || "").slice(0, MAX_README_CHARS);
  const links = [];
  const pattern = /(?<!!)\[([^\]]{1,180})\]\(([^)\s]+)(?:\s+["'][^"']*["'])?\)/g;
  let match;
  while ((match = pattern.exec(text)) && links.length < MAX_LINKS) {
    const label = clip(cleanMarkdown(match[1]), 120);
    const href = match[2].trim().replace(/^<|>$/g, "");
    if (!label || !href || href.startsWith("#") || /^(?:mailto|javascript|data):/i.test(href)) continue;
    const url = resolveReadmeUrl(repo, href);
    if (!url) continue;
    const before = text.slice(0, match.index);
    const sectionMatch = [...before.matchAll(/^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$/gm)].pop();
    const section = sectionMatch ? clip(cleanMarkdown(sectionMatch[1]), 100) : "README";
    links.push({ label, url, section });
  }
  return links;
}

export function safePublicUrl(value) {
  try {
    const url = new URL(String(value || ""));
    if (url.protocol !== "https:" || url.username || url.password) return null;
    return url.href;
  } catch {
    return null;
  }
}

function resolveReadmeUrl(repo, href) {
  try {
    if (/^https?:\/\//i.test(href)) {
      const url = new URL(href);
      if (url.protocol === "http:") url.protocol = "https:";
      return safePublicUrl(url.href);
    }
    const fullName = repo?.full_name;
    const branch = repo?.default_branch;
    if (!fullName || !branch) return null;
    if (href.startsWith("/")) return safePublicUrl(`https://github.com${href}`);
    const base = `https://github.com/${fullName}/blob/${encodeURIComponent(branch)}/`;
    return safePublicUrl(new URL(href, base).href);
  } catch {
    return null;
  }
}

function actionScore(link, type) {
  const text = `${link.label} ${link.url} ${link.section}`.toLowerCase();
  if (/app store|itunes\.apple\.com|download (?:in|from)? ?app|\bget app\b/.test(text)) return 120;
  if (/course setup|start (?:the )?course|getting started|first lesson/.test(text)) return 115;
  if (type === "curriculum" && /lesson|curriculum|course/.test(text)) return 92;
  if (/live demo|try it|open app|launch/.test(text)) return 100;
  if (/features|learn more about this project/.test(text)) return 85;
  if (/documentation|\bdocs\b|guide/.test(text)) return 78;
  if (/install|setup/.test(text)) return 68;
  if (/contribut|pull request/.test(text)) return 58;
  return 20;
}

function actionLabel(link, type) {
  const text = `${link.label} ${link.url}`.toLowerCase();
  if (/app store|itunes\.apple\.com|download (?:in|from)? ?app|\bget app\b/.test(text)) return "Get or open the app";
  if (/course setup|getting started/.test(text)) return "Start with the course setup";
  if (type === "curriculum" && /lesson/.test(text)) return `Open ${link.label.toLowerCase()}`;
  if (/live demo|try it|launch/.test(text)) return "Open the live project";
  if (/features/.test(text)) return "See the project features";
  if (/documentation|\bdocs\b/.test(text)) return "Read the documentation";
  if (/contribut/.test(text)) return "See how to contribute";
  return sentenceCase(link.label);
}

function extractActions(repo, readme, sections, type) {
  const links = extractMarkdownLinks(readme, repo, sections)
    .map(link => ({ ...link, score: actionScore(link, type), actionLabel: actionLabel(link, type) }))
    .sort((a, b) => b.score - a.score || a.actionLabel.localeCompare(b.actionLabel));

  const actions = [];
  for (const link of links) {
    if (link.score < 55) continue;
    if (actions.some(item => item.url === link.url || item.label === link.actionLabel)) continue;
    actions.push({ label: link.actionLabel, url: link.url, source: link.section });
    if (actions.length >= 4) break;
  }

  const homepage = safePublicUrl(repo?.homepage);
  if (homepage && !actions.some(item => item.url === homepage)) {
    actions.push({ label: "Open the project website", url: homepage, source: "Repository metadata" });
  }
  const repoUrl = safePublicUrl(repo?.html_url);
  if (repoUrl && !actions.some(item => item.url === repoUrl)) {
    actions.push({ label: "Open the source repository", url: repoUrl, source: "Repository metadata" });
  }
  return actions.slice(0, 5);
}

function meaningfulOverview(sections, repo) {
  const blocked = /^(?:installation|usage|licen[cs]e|contents|table of contents|contributing|requirements|badges?)$/i;
  for (const section of sections.slice(0, 8)) {
    if (blocked.test(section.heading)) continue;
    const candidate = section.paragraphs.find(item => item.length >= 35 && !/^build status|^github (?:license|contributors|issues)/i.test(item));
    if (candidate) return clip(candidate, 330);
  }
  return clip(repo?.description || "The README does not provide a clear ordinary-language purpose.", 260);
}

function curriculumPurpose(repo, sections, corpus, evidence) {
  const subject = subjectFromReadme(repo, sections);
  const weeks = countFact(corpus, "week");
  const lessons = countFact(corpus, "lesson");
  const practical = [];
  if (/\bquizzes?\b/i.test(corpus)) practical.push("quizzes");
  if (/\b(?:practical )?labs?\b/i.test(corpus)) practical.push("practical labs");
  if (/\bnotebooks?\b/i.test(corpus)) practical.push("notebooks");
  const first = `This is a freely available beginner curriculum for learning ${subject}.`;
  const countParts = [];
  if (lessons) countParts.push(`${lessons} lessons`);
  if (weeks) countParts.push(`designed for about ${weeks} weeks`);
  if (practical.length) countParts.push(`with ${practical.slice(0, 2).join(" and ")}`);
  const second = countParts.length ? `It contains ${countParts.join(", ")}.` : "It is organised as lessons with practical learning material.";
  addEvidence(evidence, first, findEvidence(sections, ["curriculum", "for beginners", "beginner-friendly"]));
  addEvidence(evidence, second, findEvidence(sections, ["lesson", "week", "quizzes", "labs"]));
  return `${first} ${second}`;
}

function applicationPurpose(repo, sections, corpus, classification, evidence) {
  const platforms = platformFact(corpus);
  const name = cleanMarkdown(repo?.name || "The project").replace(/[-_]+/g, " ");
  const isSynth = /\bsynth(?:esizer)?\b/i.test(corpus) || /synth/i.test(name);
  const product = isSynth ? "synthesizer app" : "software application";
  const platformText = platforms.length ? ` for ${platforms.join(" and ")}` : "";
  const first = `This is a ${/open[- ]source/i.test(corpus) || classification.hasCodebase ? "playable open-source " : ""}${product}${platformText}.`;
  const second = classification.hasCodebase
    ? "The repository also contains source code that developers can study, change and contribute to."
    : "The repository contains the files used to build and maintain it.";
  addEvidence(evidence, first, findEvidence(sections, ["app", "iphone", "ipad", "synthesizer"]));
  addEvidence(evidence, second, findEvidence(sections, ["open-sourced the code", "source code", "contribute"]));
  return `${first} ${second}`;
}

function genericPurpose(repo, sections, classification, evidence) {
  const overview = meaningfulOverview(sections, repo);
  const name = cleanMarkdown(repo?.name || "This project").replace(/[-_]+/g, " ");
  let prefix;
  switch (classification.id) {
    case "library": prefix = `${name} is a software library or framework.`; break;
    case "command-line": prefix = `${name} is a command-line tool.`; break;
    case "website": prefix = `${name} is a website or web application.`; break;
    case "documentation": prefix = `${name} is a documentation or reference collection.`; break;
    case "template": prefix = `${name} is a template or starter project.`; break;
    case "research": prefix = `${name} is a research or dataset repository.`; break;
    default: prefix = "This repository contains a project whose exact type is not completely clear from the available public evidence.";
  }
  const purpose = `${prefix} ${overview}`;
  addEvidence(evidence, purpose, findEvidence(sections, overview.split(" ").slice(0, 4).map(item => item.toLowerCase())));
  return clip(purpose, 430);
}

function audienceFor(type, corpus, subject, evidence, sections) {
  let audience;
  if (type === "curriculum") {
    audience = `It is aimed at beginners learning ${subject}. Some lessons may involve code, notebooks or practical exercises.`;
    addEvidence(evidence, audience, findEvidence(sections, ["for beginners", "beginner-friendly", "practical lessons"]));
    return audience;
  }
  if (type === "application" && /\bmusicians?\b/i.test(corpus) && /\bdevelopers?|programming|contribut/i.test(corpus)) {
    audience = "It is for musicians who want to use the synthesizer and for developers who want to learn from, modify or contribute to its code.";
    addEvidence(evidence, audience, findEvidence(sections, ["musicians", "audio development", "contribute"]));
    return audience;
  }

  const groups = [];
  if (/\bbeginners?\b/i.test(corpus)) groups.push("beginners");
  if (/\bstudents?\b/i.test(corpus)) groups.push("students");
  if (/\bteachers?|educators?\b/i.test(corpus)) groups.push("teachers");
  if (/\bresearchers?\b/i.test(corpus)) groups.push("researchers");
  if (/\bdevelopers?|programmers?\b/i.test(corpus)) groups.push("developers");
  if (/\bmusicians?\b/i.test(corpus)) groups.push("musicians");
  if (!groups.length) return "The README does not clearly state who the project is for.";
  audience = `The README appears to address ${[...new Set(groups)].slice(0, 3).join(", ")}.`;
  addEvidence(evidence, audience, findEvidence(sections, groups));
  return audience;
}

function curriculumCapabilities(sections, corpus, evidence) {
  const items = [];
  const weeks = countFact(corpus, "week");
  const lessons = countFact(corpus, "lesson");
  if (lessons || weeks) {
    const parts = [];
    if (lessons) parts.push(`${lessons} lessons`);
    if (weeks) parts.push(`a suggested ${weeks}-week path`);
    const text = `The course provides ${parts.join(" and ")}.`;
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, ["lesson", "week"]));
  }
  if (/\bquizzes?\b/i.test(corpus) || /\blabs?\b/i.test(corpus)) {
    const text = "It includes quizzes and practical labs rather than only explanatory text.";
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, ["quizzes", "labs"]));
  }
  const topicMap = [
    ["symbolic artificial intelligence", /symbolic (?:artificial intelligence|ai)/i],
    ["neural networks", /neural networks?/i],
    ["deep learning", /deep learning/i],
    ["computer vision", /computer vision/i],
    ["genetic algorithms", /genetic algorithms?/i],
    ["multi-agent systems", /multi-agent systems?/i]
  ];
  const topics = topicMap.filter(([, pattern]) => pattern.test(corpus)).map(([label]) => label).slice(0, 4);
  if (topics.length) {
    const text = `Topics include ${topics.join(", ")}.`;
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, topics));
  }
  if (/multi-language support|translations?/i.test(corpus)) {
    const text = "The course is available in many translated versions.";
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, ["multi-language support", "translations"]));
  }
  if (/\bnotebooks?\b/i.test(corpus)) {
    const text = "Practical work includes runnable notebooks or worked code examples.";
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, ["notebook"]));
  }
  return items.slice(0, 5);
}

function applicationCapabilities(sections, corpus, evidence) {
  const items = [];
  const platforms = platformFact(corpus);
  if (platforms.length) {
    const text = `The README says the app supports ${platforms.join(" and ")}.`;
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, platforms.map(item => item.toLowerCase())));
  }
  const synthParts = ["oscillators", "filters", "reverbs", "effects"].filter(item => new RegExp(`\\b${item}\\b`, "i").test(corpus));
  if (synthParts.length >= 3) {
    const text = `The source includes synthesizer building blocks such as ${synthParts.join(", ")}.`;
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, synthParts));
  }
  const doneLines = sections.flatMap(section => section.raw.split("\n").filter(line => /✓\s*DONE/i.test(line)).map(cleanMarkdown));
  if (doneLines.length) {
    const compact = doneLines.slice(0, 2).map(item => item.replace(/^DONE:\s*/i, "").replace(/Thanks.*$/i, "").trim()).filter(Boolean);
    if (compact.length) {
      const text = `The README marks completed work including ${compact.join(" and ")}.`;
      items.push(clip(text, 250));
      addEvidence(evidence, text, { source: "Opportunities for Contributing", excerpt: clip(doneLines.join(" "), 190) });
    }
  }
  if (/repository builds and runs without modification/i.test(corpus)) {
    const text = "The README says the main project builds and runs without modification, although one optional integration needs extra files.";
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, ["builds and runs without modification"]));
  }
  return items.slice(0, 5);
}

function genericCapabilities(sections, evidence) {
  const candidates = [];
  const usefulHeading = /features?|capabilities|what you will learn|what it does|content|included|highlights/i;
  for (const section of sections) {
    if (!usefulHeading.test(section.heading)) continue;
    for (const item of [...section.bullets, ...section.paragraphs]) {
      const clean = clip(item, 180);
      if (clean.length < 12 || candidates.includes(clean)) continue;
      candidates.push(sentenceCase(clean));
      addEvidence(evidence, clean, { source: section.heading, excerpt: clean });
      if (candidates.length >= 5) return candidates;
    }
  }
  return candidates;
}

function unfinishedFromReadme(sections, corpus, type, evidence) {
  const items = [];
  if (type === "application" && /\bauv3\b/i.test(corpus) && /\bmpe\b/i.test(corpus)) {
    const text = "The README lists AUv3 plug-in support and MPE as planned major updates.";
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, ["auv3", "mpe"]));
  }
  if (type === "application" && /link functionality will be missing/i.test(corpus)) {
    const text = "One optional Link feature needs a separately supplied software kit before it works.";
    items.push(text);
    addEvidence(evidence, text, findEvidence(sections, ["link functionality will be missing"]));
  }
  if (type === "curriculum" && /what we will not cover/i.test(corpus)) {
    const limitations = findSection(sections, /what we will not cover/i);
    const named = limitations?.bullets.slice(0, 4).map(item => item.replace(/\.$/, "")) || [];
    const text = named.length
      ? `The course explicitly leaves some subjects to other resources, including ${named.join(", ")}.`
      : "The course explicitly lists subjects that it does not cover in depth.";
    items.push(clip(text, 260));
    addEvidence(evidence, text, limitations ? { source: limitations.heading, excerpt: clip(limitations.bullets.join(" "), 190) } : null);
  }

  const headings = /roadmap|future|planned|to do|todo|opportunities for contributing|known issues|limitations|missing|not included/i;
  for (const section of sections) {
    if (!headings.test(section.heading)) continue;
    const bullets = section.bullets.filter(item => !/✓\s*done/i.test(item)).slice(0, 4);
    if (!bullets.length) continue;
    if (type === "application" && /opportunities for contributing/i.test(section.heading)) {
      const selected = bullets.slice(0, 3).map(item => item.replace(/\.$/, ""));
      const text = `The README invites further work such as ${selected.join(", ")}.`;
      if (!items.some(item => item.includes(selected[0]))) {
        items.push(clip(text, 250));
        addEvidence(evidence, text, { source: section.heading, excerpt: clip(bullets.join(" "), 190) });
      }
    } else if (items.length < 4) {
      const text = sentenceCase(clip(bullets[0], 190));
      if (!items.includes(text)) {
        items.push(text);
        addEvidence(evidence, text, { source: section.heading, excerpt: clip(bullets[0], 190) });
      }
    }
    if (items.length >= 4) break;
  }
  return items.slice(0, 4);
}

export function validProgress(value) {
  return value && typeof value === "object" && !Array.isArray(value) && Array.isArray(value.stages);
}

export function progressSummary(progress) {
  if (!validProgress(progress)) {
    return {
      done: [],
      remaining: [],
      completion: null,
      completionReason: "No recognised owner progress record was found.",
      allComplete: false
    };
  }
  const stages = progress.stages.filter(stage =>
    stage && typeof stage.label === "string" && Number.isFinite(stage.completed) &&
    Number.isFinite(stage.total) && stage.total > 0 && stage.completed >= 0
  );
  const done = stages.filter(stage => stage.completed >= stage.total).map(stage => stage.label);
  const remaining = stages.filter(stage => stage.completed < stage.total).map(stage => stage.label);
  const total = stages.reduce((sum, stage) => sum + stage.total, 0);
  const completed = stages.reduce((sum, stage) => sum + Math.min(stage.completed, stage.total), 0);
  const explicitlyDisabled = progress.overall && progress.overall.enabled === false;
  const completion = total > 0 && !explicitlyDisabled ? Math.round((completed / total) * 100) : null;
  const completionReason = explicitlyDisabled
    ? "The owner progress record explicitly disables an overall percentage."
    : total > 0
      ? `Based only on ${stages.length} owner-defined stage${stages.length === 1 ? "" : "s"}.`
      : "The progress record contains no usable numeric stages.";
  return { done, remaining, completion, completionReason, allComplete: stages.length > 0 && remaining.length === 0 };
}

export function languageRows(languages) {
  const entries = Object.entries(languages || {})
    .filter(([, bytes]) => Number.isFinite(bytes) && bytes > 0)
    .sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, bytes]) => sum + bytes, 0);
  if (!total) return [];
  return entries
    .map(([name, bytes]) => ({
      name,
      percentage: Math.round((bytes / total) * 1000) / 10,
      help: LANGUAGE_HELP[name] || null
    }))
    .filter(item => item.percentage >= 0.1)
    .slice(0, 12);
}

function bestStart(actions, type) {
  if (!actions.length) return null;
  if (type === "curriculum") {
    return actions.find(item => /course setup|lesson|course/i.test(item.label)) || actions[0];
  }
  if (type === "application") {
    return actions.find(item => /app/i.test(item.label)) || actions[0];
  }
  return actions[0];
}

export function buildComprehension(repo, readme, progress = null, languages = {}) {
  const sections = parseSections(readme);
  const corpus = sectionCorpus(sections);
  const classification = classifyProject(repo, readme);
  const evidence = [];
  const subject = subjectFromReadme(repo, sections);
  let purpose;
  if (classification.id === "curriculum") {
    purpose = curriculumPurpose(repo, sections, corpus, evidence);
  } else if (classification.id === "application") {
    purpose = applicationPurpose(repo, sections, corpus, classification, evidence);
  } else {
    purpose = genericPurpose(repo, sections, classification, evidence);
  }

  const audience = audienceFor(classification.id, corpus, subject, evidence, sections);
  const actions = extractActions(repo, readme, sections, classification.id);
  let capabilities;
  if (classification.id === "curriculum") {
    capabilities = curriculumCapabilities(sections, corpus, evidence);
  } else if (classification.id === "application") {
    capabilities = applicationCapabilities(sections, corpus, evidence);
  } else {
    capabilities = genericCapabilities(sections, evidence);
  }
  if (!capabilities.length) {
    capabilities = ["The README does not provide a concise, clearly labelled list of delivered capabilities."];
  }

  const status = progressSummary(progress);
  const unfinished = [...status.remaining, ...unfinishedFromReadme(sections, corpus, classification.id, evidence)];
  const uniqueUnfinished = [...new Set(unfinished)].slice(0, 5);
  if (!uniqueUnfinished.length) {
    uniqueUnfinished.push("The README does not provide a complete plan of remaining work.");
  }
  if (status.completion === null) {
    uniqueUnfinished.push("Overall completion remains unknown because no recognised owner-defined completion measure is available.");
  }

  return {
    classification,
    purpose,
    audience,
    actions,
    capabilities: [...new Set(capabilities)].slice(0, 5),
    unfinished: [...new Set(uniqueUnfinished)].slice(0, 6),
    start: bestStart(actions, classification.id),
    progress: status,
    languages: languageRows(languages),
    evidence: evidence.slice(0, MAX_EVIDENCE),
    readmeAvailable: Boolean(readme),
    sectionsRead: sections.length
  };
}
