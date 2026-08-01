import { cleanMarkdown, safePublicUrl } from "./comprehension.js";

function unique(items, key) {
  const seen = new Set();
  return items.filter(item => {
    const value = key(item);
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

function sourceAction(repo, label = "Open the source repository") {
  const url = safePublicUrl(repo?.html_url);
  return url ? { label, url, source: "Repository" } : null;
}

function anchoredAction(repo, label, anchor, source) {
  const base = safePublicUrl(repo?.html_url);
  if (!base) return null;
  return {
    label,
    url: `${base.replace(/\/$/, "")}#${anchor}`,
    source
  };
}

function resolveReadmeLink(repo, href) {
  try {
    if (/^https?:\/\//i.test(href)) {
      const url = new URL(href);
      if (url.protocol === "http:") url.protocol = "https:";
      return safePublicUrl(url.href);
    }
    const fullName = repo?.full_name;
    const branch = repo?.default_branch;
    if (!fullName || !branch || href.startsWith("#")) return null;
    if (href.startsWith("/")) return safePublicUrl(`https://github.com${href}`);
    return safePublicUrl(
      new URL(
        href,
        `https://github.com/${fullName}/blob/${encodeURIComponent(branch)}/`
      ).href
    );
  } catch {
    return null;
  }
}

function findReadmeAction(readme, repo, labelPattern, label, source) {
  const pattern = /(?<!!)\[([^\]]{1,180})\]\(([^)\s]+)(?:\s+["'][^"']*["'])?\)/g;
  let match;
  const text = String(readme || "");
  while ((match = pattern.exec(text))) {
    const linkLabel = cleanMarkdown(match[1]);
    if (!labelPattern.test(linkLabel)) continue;
    const url = resolveReadmeLink(repo, match[2].trim().replace(/^<|>$/g, ""));
    if (url) return { label, url, source };
  }
  return null;
}

function filterActions(reading, repo, readme) {
  const type = reading.classification.id;
  const ownRepository = String(repo?.html_url || "").toLowerCase().replace(/\/$/, "");
  let actions = reading.actions.filter(action => {
    const label = action.label.toLowerCase();
    const source = String(action.source || "").toLowerCase();
    const url = action.url.toLowerCase();
    if (/^@|twitter|discord|watch|fork|star|badge|sponsor/.test(label)) return false;
    if (/locali[sz]ation|ableton link sdk|sign up/.test(`${label} ${source}`)) return false;
    if (type === "curriculum" && url.includes("github.com/") && !url.startsWith(ownRepository)) return false;
    return true;
  });

  if (type === "application") {
    actions = actions.filter(action => /app|feature|project website|source|contribut/i.test(action.label));
    const source = sourceAction(repo, "Study or change the source code");
    const contribute = anchoredAction(repo, "See contribution ideas", "opportunities-for-contributing", "README contribution section");
    if (source) actions.push(source);
    if (contribute) actions.push(contribute);
    const order = [/get or open the app/i, /project features/i, /study or change/i, /contribution ideas/i];
    actions.sort((a, b) => {
      const rank = item => {
        const index = order.findIndex(pattern => pattern.test(item.label));
        return index === -1 ? order.length : index;
      };
      return rank(a) - rank(b);
    });
  } else if (type === "curriculum") {
    actions = actions.filter(action => /course setup|lesson|course resources|microsoft learn|source repository/i.test(action.label));
    const setup = findReadmeAction(
      readme,
      repo,
      /^course setup$/i,
      "Start with the course setup",
      "README course contents"
    );
    const lessons = anchoredAction(repo, "Browse the course lessons", "content", "README course contents");
    const source = sourceAction(repo);
    if (setup) actions.push(setup);
    if (lessons) actions.push(lessons);
    if (source) actions.push(source);
    const order = [/course setup/i, /course lessons/i, /course resources|microsoft learn/i, /source repository/i];
    actions.sort((a, b) => {
      const rank = item => {
        const index = order.findIndex(pattern => pattern.test(item.label));
        return index === -1 ? order.length : index;
      };
      return rank(a) - rank(b);
    });
  } else {
    const source = sourceAction(repo);
    if (source) actions.push(source);
  }

  return unique(actions, action => `${action.label}|${action.url}`).slice(0, 4);
}

function polishCapabilities(reading) {
  return reading.capabilities.map(item => {
    if (/synthesizer building blocks/i.test(item)) {
      return item.replace(/oscillators, filters, reverbs, effects/i, "oscillators, filters, reverbs and effects");
    }
    if (/marks completed work/i.test(item) && /iphone\/?universal/i.test(item) && /accessibility/i.test(item)) {
      return "The README marks the iPhone/Universal version and accessibility support as completed work.";
    }
    return item.replace(/\.\./g, ".").replace(/\s+\./g, ".");
  });
}

function extractLimitations(readme) {
  const text = String(readme || "").replace(/\r\n?/g, "\n");
  const start = text.search(/what we will not cover in this curriculum/i);
  if (start < 0) return null;
  const tail = text.slice(start);
  const endMatch = tail.slice(40).search(/\n#{1,6}\s+content\b|\nfor a gentle introduction\b/i);
  const section = endMatch >= 0 ? tail.slice(0, endMatch + 40) : tail.slice(0, 4500);
  const clean = cleanMarkdown(section);
  const topics = [];
  if (/business cases|ai in business/i.test(clean)) topics.push("business uses of AI");
  if (/classic machine learning/i.test(clean)) topics.push("classic machine learning");
  if (/conversational ai|chat bots?/i.test(clean)) topics.push("conversational AI");
  if (/deep mathematics/i.test(clean)) topics.push("the deeper mathematics of deep learning");
  if (!topics.length) return {
    statement: "The README has a separate section describing subjects that the course does not cover in depth and points readers to other resources.",
    excerpt: clean.slice(0, 220)
  };
  return {
    statement: `The course does not cover ${topics.join(", ")} in depth; the README points to other resources for those subjects.`,
    excerpt: clean.slice(0, 260)
  };
}

function polishUnfinished(reading, readme) {
  const type = reading.classification.id;
  let items = reading.unfinished.filter(item => !/^The course explicitly leaves some subjects/i.test(item));

  if (type === "application") {
    items = items.map(item => {
      if (/invites further work/i.test(item) && /search presets/i.test(item)) {
        return "The README suggests future improvements including preset search, a MIDI learn matrix and assignable touchpads.";
      }
      return item;
    });
  }

  if (type === "curriculum") {
    const limitation = extractLimitations(readme);
    if (limitation) items.unshift(limitation.statement);
  }

  return unique(items, item => item).slice(0, 6);
}

function goodExcerpt(record) {
  return record && record.excerpt && !/:---:|sketchnote|@girlie|github (?:license|contributors|issues|pull-requests)/i.test(record.excerpt);
}

function bestEvidence(reading, pattern) {
  return reading.evidence.find(record => pattern.test(`${record.statement} ${record.excerpt}`) && goodExcerpt(record));
}

function polishEvidence(reading, readme) {
  const evidence = reading.evidence
    .filter(goodExcerpt)
    .filter(record => !/^The course explicitly leaves some subjects/i.test(record.statement));

  if (reading.classification.id === "curriculum") {
    const curriculum = bestEvidence(reading, /12-week|24-lesson|curriculum.*quizzes|practical lessons/i);
    if (curriculum) {
      for (const statement of [reading.purpose, reading.audience]) {
        if (!evidence.some(record => record.statement === statement)) {
          evidence.unshift({ statement, source: curriculum.source, excerpt: curriculum.excerpt });
        }
      }
    }
    const limitation = extractLimitations(readme);
    if (limitation && !evidence.some(record => record.statement === limitation.statement)) {
      evidence.push({
        statement: limitation.statement,
        source: "What we will not cover in this curriculum",
        excerpt: limitation.excerpt
      });
    }
  }

  if (reading.classification.id === "application") {
    const product = bestEvidence(reading, /open-sourced the code|Universal for iPhone\/iPad|synthesizer/i);
    if (product && !evidence.some(record => record.statement === reading.purpose)) {
      evidence.unshift({ statement: reading.purpose, source: product.source, excerpt: product.excerpt });
    }
  }

  return unique(evidence, record => `${record.statement}|${record.source}|${record.excerpt}`).slice(0, 10);
}

export function polishReading(reading, repo, readme) {
  const actions = filterActions(reading, repo, readme);
  return {
    ...reading,
    actions,
    start: actions[0] || reading.start,
    capabilities: polishCapabilities(reading),
    unfinished: polishUnfinished(reading, readme),
    evidence: polishEvidence(reading, readme)
  };
}
