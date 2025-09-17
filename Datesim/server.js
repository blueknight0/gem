import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
import cors from "cors";
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.set("trust proxy", 1);
app.use(cors());
app.use(express.json({ limit: "200kb" }));

// Static
app.use(express.static(path.join(__dirname, "public")));

// Health
app.get("/api/health", (_req, res) => {
	res.json({ ok: true });
});

// --- Gemini config
const GENAI_BASE = process.env.GENAI_BASE || "https://generativelanguage.googleapis.com";
const GENAI_TEXT_MODEL = process.env.GENAI_TEXT_MODEL || "gemini-2.5-flash-lite";
const GENAI_IMAGE_MODEL = process.env.GENAI_IMAGE_MODEL || "gemini-2.5-flash-image-preview";
// Story pacing
const TOTAL_DAYS = 30;
const TURNS_PER_DAY = 10;

// --- Usage counters (in-memory)
let usage = {
	total: 0,
	today: 0,
	date: new Date().toISOString().slice(0, 10),
};

function rollUsageDateIfNeeded() {
	const d = new Date().toISOString().slice(0, 10);
	if (usage.date !== d) {
		usage.date = d;
		usage.today = 0;
	}
}

// --- Simple rate limit per IP (in-memory)
const RATE_LIMIT_PER_MIN = Number(process.env.RATE_LIMIT_PER_MIN || 20);
const RATE_LIMIT_PER_DAY = Number(process.env.RATE_LIMIT_PER_DAY || 200);
// In-memory guardrails
const MAX_IP_BUCKETS = Number(process.env.MAX_IP_BUCKETS || 5000);
const IP_BUCKET_TTL_MS = Number(process.env.IP_BUCKET_TTL_MS || 10 * 60 * 1000);

const ipBuckets = new Map(); // ip -> { minuteStart: number, minuteCount: number, dayDate: string, dayCount: number }

function maybeCleanupIpBuckets() {
	const now = Date.now();
	// TTL cleanup
	for (const [ip, rec] of ipBuckets.entries()) {
		if ((now - rec.minuteStart) > IP_BUCKET_TTL_MS) {
			ipBuckets.delete(ip);
		}
	}
	// Size cap cleanup (best-effort: drop oldest minuteStart first)
	if (ipBuckets.size > MAX_IP_BUCKETS) {
		const arr = Array.from(ipBuckets.entries());
		arr.sort((a, b) => a[1].minuteStart - b[1].minuteStart);
		for (let i = 0; i < arr.length && ipBuckets.size > MAX_IP_BUCKETS; i++) {
			ipBuckets.delete(arr[i][0]);
		}
	}
}

function rateLimitMiddleware(req, res, next) {
	const ip = req.ip || req.socket.remoteAddress || "unknown";
	const now = Date.now();
	let rec = ipBuckets.get(ip);
	const currentMinuteStart = now - (now % 60000);
	const currentDay = new Date().toISOString().slice(0, 10);
	if (!rec) {
		rec = { minuteStart: currentMinuteStart, minuteCount: 0, dayDate: currentDay, dayCount: 0 };
		ipBuckets.set(ip, rec);
	}
	// rollover minute window
	if (rec.minuteStart !== currentMinuteStart) {
		rec.minuteStart = currentMinuteStart;
		rec.minuteCount = 0;
	}
	// rollover day window
	if (rec.dayDate !== currentDay) {
		rec.dayDate = currentDay;
		rec.dayCount = 0;
	}
	if (rec.minuteCount >= RATE_LIMIT_PER_MIN) {
		const retryAfter = Math.ceil((rec.minuteStart + 60000 - now) / 1000);
		return res.status(429).json({ error: "rate_limited_minute", retryAfterSeconds: retryAfter });
	}
	if (rec.dayCount >= RATE_LIMIT_PER_DAY) {
		return res.status(429).json({ error: "rate_limited_day" });
	}
	// tentatively increment; on error paths we won't decrement (acceptable for simplicity)
	rec.minuteCount += 1;
	rec.dayCount += 1;
	// occasional cleanup
	if (Math.random() < 0.01) maybeCleanupIpBuckets();
	return next();
}

// --- Visitor counters (in-memory unique by client-provided vid)
let visitors = {
	date: new Date().toISOString().slice(0, 10),
	today: 0, // unique visitors today
	seenToday: new Set(),
	total: 0, // lifetime unique visitors
	seenEver: new Set(),
};

const VISITORS_SEEN_EVER_MAX = Number(process.env.VISITORS_SEEN_EVER_MAX || 100000);

function rollVisitorsDateIfNeeded() {
	const d = new Date().toISOString().slice(0, 10);
	if (visitors.date !== d) {
		visitors.date = d;
		visitors.today = 0;
		visitors.seenToday = new Set();
	}
}

// --- Sessions TTL and bounds
const MAX_SESSIONS = Number(process.env.MAX_SESSIONS || 10000);
const SESSIONS_TTL_MS = Number(process.env.SESSIONS_TTL_MS || 24 * 60 * 60 * 1000);

// --- Style diversification helpers
function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function pickSome(arr, n) {
	const copy = arr.slice();
	for (let i = copy.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[copy[i], copy[j]] = [copy[j], copy[i]];
	}
	return copy.slice(0, Math.max(0, Math.min(n, copy.length)));
}

const STYLE_TIME = ["early morning", "noon", "golden hour", "blue hour", "overcast afternoon", "rainy evening", "late night indoors"];
const STYLE_WEATHER = ["clear", "light rain", "misty", "snow flurries", "humid air", "after-rain puddles"];
const STYLE_ANGLE = ["eye-level", "slightly low-angle", "slightly high-angle", "over-the-shoulder", "candid street-level", "three-quarter view"];
const STYLE_LENS = ["24mm wide", "35mm", "50mm", "85mm", "105mm telephoto"];
const STYLE_LIGHTING = [
	"soft natural window light",
	"diffused overcast light",
	"fluorescent indoor lighting",
	"subway station lighting",
	"store aisle lighting",
	"mixed temperature practical lights"
];
const STYLE_COLOR = ["neutral realistic colors", "muted pastel palette", "warm amber tint", "cool bluish tint", "film-like subdued colors"];
const STYLE_COMPOSITION = ["rule-of-thirds composition", "centered symmetrical framing", "off-center candid framing", "slight dutch tilt"];

function buildStyleHint() {
	const t = pickRandom(STYLE_TIME);
	const w = pickRandom(STYLE_WEATHER);
	const a = pickRandom(STYLE_ANGLE);
	const l = pickRandom(STYLE_LENS);
	const li = pickRandom(STYLE_LIGHTING);
	const c = pickRandom(STYLE_COLOR);
	const comp = pickRandom(STYLE_COMPOSITION);
	const extras = pickSome(["hand-held feel", "shallow depth of field", "subtle grain", "ambient reflections", "slight motion blur"], 2);
	return [
		`Style variation: ${a} angle, ${l} lens, ${comp}.`,
		`Time/Weather: ${t}, ${w}.`,
		`Lighting: ${li}.`,
		`Color: ${c}.`,
		extras.length ? `Extra: ${extras.join(", ")}.` : null,
		"Keep it realistic and candid. Do not render any text in the image."
	].filter(Boolean).join(" ");
}

async function callGeminiText(prompt) {
	const apiKey = process.env.GEMINI_API_KEY;
	if (!apiKey) throw new Error("Server missing GEMINI_API_KEY");
	const url = `${GENAI_BASE}/v1beta/models/${GENAI_TEXT_MODEL}:generateContent?key=${encodeURIComponent(apiKey)}`;
	const resp = await fetch(url, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			contents: [ { parts: [ { text: prompt } ] } ],
			generationConfig: {
				responseMimeType: "application/json",
				temperature: 1.3,
				topP: 0.95,
				topK: 64
			}
		}),
	});
	if (!resp.ok) {
		const t = await resp.text();
		throw new Error(`Gemini text error ${resp.status}: ${t}`);
	}
	const data = await resp.json();
	const text = data?.candidates?.[0]?.content?.parts?.map(p => p.text).join("\n") ?? "";
	return text;
}

function extractJsonObjectFromText(text) {
	// Try to extract JSON object even if wrapped in code fences or extra text
	const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
	const raw = fenceMatch ? fenceMatch[1] : text;
	const start = raw.indexOf("{");
	const end = raw.lastIndexOf("}");
	if (start >= 0 && end > start) {
		const slice = raw.slice(start, end + 1);
		try { return JSON.parse(slice); } catch {}
	}
	return null;
}

// --- DateSim in-memory sessions (per vid)
const sessions = new Map(); // vid -> { profile, rerollsUsed, confirmed, step, lastActive, lastImageBase64, day, turnInDay, imagesToday, ended, affinity, storyLog, userChoicesCount }

function getSession(vid) {
	let s = sessions.get(vid);
	if (!s) {
		s = { profile: null, rerollsUsed: 0, confirmed: false, step: 0, lastActive: Date.now(), lastImageBase64: null, day: 0, turnInDay: 0, imagesToday: 0, ended: false, affinity: 0, storyLog: [], userChoicesCount: 0 };
		sessions.set(vid, s);
	}
	s.lastActive = Date.now();
	// enforce rough cap lazily
	if (sessions.size > MAX_SESSIONS) {
		const arr = Array.from(sessions.entries());
		arr.sort((a, b) => (a[1].lastActive || 0) - (b[1].lastActive || 0));
		for (let i = 0; i < arr.length && sessions.size > MAX_SESSIONS; i++) {
			sessions.delete(arr[i][0]);
		}
	}
	return s;
}

function cleanupSessions() {
	const now = Date.now();
	for (const [vid, s] of sessions.entries()) {
		if (!s.lastActive || (now - s.lastActive) > SESSIONS_TTL_MS) {
			sessions.delete(vid);
		}
	}
	if (sessions.size > MAX_SESSIONS) {
		const arr = Array.from(sessions.entries());
		arr.sort((a, b) => (a[1].lastActive || 0) - (b[1].lastActive || 0));
		for (let i = 0; i < arr.length && sessions.size > MAX_SESSIONS; i++) {
			sessions.delete(arr[i][0]);
		}
	}
}

setInterval(cleanupSessions, 10 * 60 * 1000).unref?.();

function buildCharacterCore(profile) {
	const {
		dimension = "3D",
		name = "",
		species = "human",
		race = "",
		gender = "",
		extra = "",
	} = profile || {};
	const baseDesc = [
		(species ? `${species}` : null),
		(race ? `${race}` : null),
		(gender ? `${gender}` : null),
	].filter(Boolean).join(", ");
	const style = (String(dimension).toUpperCase() === "2D")
		? "Anime-inspired 2D illustration, clean cel shading, soft lighting, detailed character design, do not render any text."
		: "Realistic candid photo style, natural skin texture, shallow depth of field when appropriate, do not render any text.";
	const nameLine = name ? `Depict a person named ${name}.` : "";
	const extras = extra ? `Preferences: ${extra}.` : "";
	return [
		`Dating sim partner portrait. ${nameLine}`,
		`Appearance: ${baseDesc || "human"}.`,
		style,
		extras,
	].filter(Boolean).join(" \n");
}

function buildCharacterImagePrompt(profile) {
	// Introduction portrait: neutral background is desired
	return [
		buildCharacterCore(profile),
		buildStyleHint(),
		"Framing waist-up or portrait. Neutral background suitable for profile introduction.",
		"Do not place any text in the image."
	].filter(Boolean).join(" \n");
}

function buildSceneImagePrompt(profile, sceneHint) {
	// Scene update: keep identity but explicitly set location and environmental cues
	const core = buildCharacterCore(profile);
	const locationLine = sceneHint ? `Set the scene/location explicitly to: ${sceneHint}.` : "Set the scene to a realistic everyday location.";
	const constraints = [
		"Ensure clear environmental cues that unmistakably match the location (e.g., park walkway, trees, benches; subway platform, rails, signage).",
		"Do not use a neutral or generic background."
	];
	return [
		core,
		locationLine,
		constraints.join(" "),
		buildStyleHint(),
		"Do not place any text in the image."
	].filter(Boolean).join(" \n");
}

// --- DateSim endpoints
app.post("/api/datesim/setup", rateLimitMiddleware, async (req, res) => {
	try {
		const vid = (req.body && typeof req.body.vid === "string") ? req.body.vid : null;
		if (!vid) return res.status(400).json({ error: "vid_required" });
		const profile = req.body && req.body.profile ? req.body.profile : null;
		const isReroll = Boolean(req.body && req.body.reroll);
		const session = getSession(vid);
		if (isReroll) {
			if (session.rerollsUsed >= 2) {
				return res.status(400).json({ error: "reroll_limit" });
			}
			session.rerollsUsed += 1;
		}
		if (profile) {
			session.profile = profile;
			session.confirmed = false;
			session.step = 0;
		}
		if (!session.profile) return res.status(400).json({ error: "profile_required" });
		const prompt = buildCharacterImagePrompt(session.profile);
		const apiKey = process.env.GEMINI_API_KEY;
		if (!apiKey) return res.status(500).json({ error: "Server missing GEMINI_API_KEY" });
		const url = `${GENAI_BASE}/v1beta/models/${GENAI_IMAGE_MODEL}:generateContent?key=${encodeURIComponent(apiKey)}`;
		const resp = await fetch(url, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ contents: [ { parts: [ { text: prompt } ] } ] })
		});
		let warning = null;
		let b64 = null;
		if (!resp.ok) {
			warning = `Gemini image error ${resp.status}`;
		} else {
			const data = await resp.json();
			b64 = data?.candidates?.[0]?.content?.parts?.find(p => p.inlineData)?.inlineData?.data
				|| data?.generatedImages?.[0]?.b64Data
				|| data?.images?.[0]?.base64
				|| null;
			if (!b64) warning = "no_image_data";
		}
		if (b64) session.lastImageBase64 = b64;
		return res.json({ imageBase64: b64, warning, rerollsLeft: Math.max(0, 2 - session.rerollsUsed), profile: session.profile });
	} catch (e) {
		return res.status(500).json({ error: String(e?.message || e) });
	}
});

app.post("/api/datesim/confirm", (req, res) => {
	try {
		const vid = (req.body && typeof req.body.vid === "string") ? req.body.vid : null;
		if (!vid) return res.status(400).json({ error: "vid_required" });
		const session = getSession(vid);
		if (!session.profile) return res.status(400).json({ error: "profile_required" });
		session.confirmed = true;
		session.day = 1;
		session.turnInDay = 0;
		session.imagesToday = 0;
		session.ended = false;
		session.affinity = 0;
		session.storyLog = [];
		session.userChoicesCount = 0;
		return res.json({ ok: true, day: session.day, turnInDay: session.turnInDay });
	} catch (e) {
		return res.status(500).json({ error: "confirm_failed" });
	}
});

app.post("/api/datesim/choices", rateLimitMiddleware, async (req, res) => {
	try {
		const vid = (req.body && typeof req.body.vid === "string") ? req.body.vid : null;
		if (!vid) return res.status(400).json({ error: "vid_required" });
		const session = getSession(vid);
		if (!session.confirmed) return res.status(400).json({ error: "not_confirmed" });
		if (session.ended || session.day > TOTAL_DAYS) {
			return res.json({ ending: true, message: "엔딩에 도달했습니다.", choices: [] });
		}
		const clientHistory = Array.isArray(req.body?.history) ? req.body.history : [];
		// Incorporate new user choices from client history into server-side storyLog (dedup by count)
		if (clientHistory.length > session.userChoicesCount) {
			const newItems = clientHistory.slice(session.userChoicesCount);
			for (const it of newItems) {
				if (it && typeof it.choice === 'string') {
					session.storyLog.push({ type: 'user_choice', day: session.day, turn: session.turnInDay + 1, text: it.choice });
					session.userChoicesCount += 1;
				}
			}
		}
		const sys = [
			"You are a dating simulation director AI.",
			"Goal: continue a romantic slice-of-life date with natural Korean dialogue.",
			"Return JSON with keys: partner_reply_ko, narrative_ko, choices_ko (3 strings, short and mutually exclusive), emotion_delta (short), affinity_delta (integer -3..+3), scene_hint_en (short English).",
			"STRICT: The 3 choices must be mutually exclusive and lead to clearly different next scenes (no overlap, no repetition).",
			"STRICT: Ensure story progression. Do not get stuck. Avoid loops and dead-ends.",
			"Plot frame: 30-day relationship arc starting with a blind date on Day 1 (소개팅 시작일).",
			"Branch by current affinity: higher affinity unlocks more intimate/positive routes; low affinity can cause conflicts or cooling off; maintain realism.",
			"Keep each reply concise (1-2 sentences).",
			"For scene_hint_en, be explicit: include concrete location (e.g., city park walkway, riverside cafe terrace, subway platform), time of day, weather, and 1-2 distinctive objects/background cues.",
			"Never include any text to be rendered in images; scene_hint_en is for visuals only."
		].join("\n");
		const profileLine = session.profile ? `Profile: dimension=${session.profile.dimension||''}, name=${session.profile.name||''}, species=${session.profile.species||''}, race=${session.profile.race||''}, gender=${session.profile.gender||''}, extra=${session.profile.extra||''}. Player name: ${session.profile.playerName||''}.` : "";
		const progressLine = `Day ${session.day} / ${TOTAL_DAYS}, Turn ${session.turnInDay+1} / ${TURNS_PER_DAY}, Affinity ${session.affinity}.`;
		const storyContext = JSON.stringify(session.storyLog, null, 2);
		const prompt = [sys, profileLine, progressLine, "Full story so far (ordered log):", storyContext].filter(Boolean).join("\n\n");
		const text = await callGeminiText(prompt);
		const obj = extractJsonObjectFromText(text);
		if (!obj || !Array.isArray(obj.choices_ko) || obj.choices_ko.length < 3) {
			return res.status(502).json({ error: "invalid LLM response", raw: text });
		}
		session.step += 1;
		session.turnInDay += 1;
		let rolled = false;
		if (session.turnInDay >= TURNS_PER_DAY) {
			session.day += 1;
			session.turnInDay = 0;
			session.imagesToday = 0;
			rolled = true;
		}
		if (session.day > TOTAL_DAYS) {
			session.ended = true;
		}
		// Update affinity and story log
		const delta = Math.max(-3, Math.min(3, Number(obj.affinity_delta ?? 0) || 0));
		session.affinity = Math.max(-100, Math.min(100, (session.affinity || 0) + delta));
		session.storyLog.push({ type: 'ai', day: session.day, turn: session.turnInDay, partnerReply: obj.partner_reply_ko || '', narrative: obj.narrative_ko || '', emotionDelta: obj.emotion_delta || '', sceneHint: obj.scene_hint_en || '', affinityAfter: session.affinity });
		return res.json({
			partnerReply: obj.partner_reply_ko || "",
			narrative: obj.narrative_ko || "",
			choices: obj.choices_ko.slice(0,3),
			emotionDelta: obj.emotion_delta || "",
			sceneHint: obj.scene_hint_en || "",
			affinity: session.affinity,
			day: session.day,
			turnInDay: session.turnInDay,
			dayRolled: rolled,
			ended: session.ended
		});
	} catch (e) {
		return res.status(500).json({ error: String(e?.message || e) });
	}
});

app.post("/api/datesim/image", rateLimitMiddleware, async (req, res) => {
	try {
		const vid = (req.body && typeof req.body.vid === "string") ? req.body.vid : null;
		if (!vid) return res.status(400).json({ error: "vid_required" });
		const session = getSession(vid);
		if (!session.profile) return res.status(400).json({ error: "profile_required" });
		const sceneHint = typeof req.body?.sceneHint === "string" ? req.body.sceneHint : "";
		const prompt = buildSceneImagePrompt(session.profile, sceneHint);
		const apiKey = process.env.GEMINI_API_KEY;
		if (!apiKey) return res.status(500).json({ error: "Server missing GEMINI_API_KEY" });
		const url = `${GENAI_BASE}/v1beta/models/${GENAI_IMAGE_MODEL}:generateContent?key=${encodeURIComponent(apiKey)}`;

		// Prefer image-to-image by including last image when available
		const parts = [];
		if (session.lastImageBase64) {
			parts.push({ inlineData: { mimeType: "image/png", data: session.lastImageBase64 } });
		}
		const editHint = session.lastImageBase64 ? [
			"EDIT THE PROVIDED INPUT IMAGE IN-PLACE.",
			"Preserve identity strictly: face shape, facial features, skin tone, hairstyle, hair color, outfit silhouette and color.",
			"Do NOT change the person's identity. Only modify background/lighting/pose/props to match the scene hint.",
			"No text in the image."
		].join(" \n") : "";
		parts.push({ text: [prompt, editHint].filter(Boolean).join("\n\n") });

		const usedPrev = Boolean(session.lastImageBase64);
		const resp = await fetch(url, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ contents: [ { parts } ] })
		});
		if (!resp.ok) {
			const t = await resp.text();
			throw new Error(`Gemini image error ${resp.status}: ${t}`);
		}
		const data = await resp.json();
		let b64 = data?.candidates?.[0]?.content?.parts?.find(p => p.inlineData)?.inlineData?.data
			|| data?.generatedImages?.[0]?.b64Data
			|| data?.images?.[0]?.base64
			|| null;
		if (!b64) throw new Error("No image data in response");
		// Save as next baseline
		session.lastImageBase64 = b64;
		rollUsageDateIfNeeded();
		usage.today += 1;
		usage.total += 1;
		session.imagesToday = (session.imagesToday || 0) + 1;
		return res.json({ imageBase64: b64, usedPrevious: usedPrev });
	} catch (e) {
		console.error(e);
		// Do not return placeholder; signal client to retry on next branch/turn
		return res.status(200).json({ warning: String(e?.message || e), retryNext: true });
	}
});

// API endpoints
app.get("/api/boke", rateLimitMiddleware, async (_req, res) => {
	try {
		const instruction = [
			"당신은 '보케 시나리오 아키텍트'입니다. 밈 스타일의 보케(일본식 유머) 시나리오를 1개 생성하세요.",
			"목표: '장면 자체의 과한 황당함'이 아니라, 이미지와 한국어 한 줄 캡션(humor_ko) 사이의 아이러니에서 웃음을 만들어야 합니다.",
			"톤: 짧고 공감되는 유머.",
			"원칙: 약간 어긋났지만 가능한 행동. 풍부하고 다양한 상황과 장소.",
			"연출 기본: 현실 사진 룩, 캔디드·다큐 분위기. 자연스러운 색감(필요 시 필름 톤 OK).",
			"다양화 지침: 매 요청마다 배경/직업/역할/세대/시간대/날씨/마이크로-장소(편의점, 엘리베이터, 경로당, 공중화장실, 지하철 칸 등)를 바꾸고, 흔한 테마(사무실/컴퓨터/라면)는 남용하지 마세요.",
			"유머 스타일 다양화: 자조/현타/현실부정/쿨하고 건조한 한마디/과몰입/무덤덤한 보고체 등 중 하나를 임의로 선택.",
			"캡션 톤(한국 인터넷 밈 2023~2025): 짧고 강하며 이미지와 반대로 읽히는 아이러니. 예시는 참고만 하고 직접 문구는 새로 지을 것.",
			"반환(JSON) 키: title, subject, action, background, expression, image_prompt, humor_ko, why_funny_ko",
			"- title: 한국어 짧은 밈풍 제목(≤16자)",
			"- subject/action/background/expression: 영어, 간결하게",
			"- image_prompt: 영어로 자세히 작성(인물은 한국인, 현실 사진 룩, candid framing). 이미지에 텍스트를 넣지 말 것.",
			"- humor_ko: 한국어 한 줄 캡션(≤28자), 이미지와 의도적 아이러니",
			"- why_funny_ko: 한국어 한 줄로 이미지와 캡션 사이의 아이러니가 왜 웃긴지 설명(≤40자)",
		].join("\n");

		const text = await callGeminiText(instruction);
		const obj = extractJsonObjectFromText(text);
		if (!obj?.image_prompt) {
			return res.status(502).json({ error: "invalid LLM response", raw: text });
		}
		// 스타일 힌트를 덧붙여 시각 결과의 다양성을 높임
		const diversifiedPrompt = [obj.image_prompt, "\n\n", buildStyleHint()].join("");

		rollUsageDateIfNeeded();
		usage.today += 1;
		usage.total += 1;
		return res.json({
			scenario: {
				subject: obj.subject,
				action: obj.action,
				background: obj.background,
				expression: obj.expression,
				title: obj.title,
			},
			prompt: diversifiedPrompt,
			humor: obj.humor_ko || null,
			whyFunny: obj.why_funny_ko || null,
		});
	} catch (e) {
		console.error(e);
		return res.status(500).json({ error: String(e?.message || e) });
	}
});

app.post("/api/generate", rateLimitMiddleware, async (req, res) => {
	try {
		const { prompt, humor } = req.body ?? {};
		if (!prompt) return res.status(400).json({ error: "prompt is required" });
		const apiKey = process.env.GEMINI_API_KEY;
		if (!apiKey) return res.status(500).json({ error: "Server missing GEMINI_API_KEY" });

		// Use generateContent; image preview model may return inlineData with base64 image
		const url = `${GENAI_BASE}/v1beta/models/${GENAI_IMAGE_MODEL}:generateContent?key=${encodeURIComponent(apiKey)}`;
		const resp = await fetch(url, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				contents: [ { parts: [ { text: [
					prompt,
					"\n\nImportant: Do NOT render any text in the image. Use the following one-line humor only as mood/context (do not draw it):",
					(humor ? `Caption (Korean): ${humor}` : "")
				].filter(Boolean).join(" ") } ] } ]
			})
		});
		if (!resp.ok) {
			const t = await resp.text();
			throw new Error(`Gemini image error ${resp.status}: ${t}`);
		}
		const data = await resp.json();
		// Extract base64 image from common shapes
		let b64 = data?.candidates?.[0]?.content?.parts?.find(p => p.inlineData)?.inlineData?.data
			|| data?.generatedImages?.[0]?.b64Data
			|| data?.images?.[0]?.base64
			|| null;
		if (!b64) throw new Error("No image data in response");
		rollUsageDateIfNeeded();
		usage.today += 1;
		usage.total += 1;
		return res.json({ imageBase64: b64 });
	} catch (e) {
		console.error(e);
		// Non-fatal fallback to 1x1 png so UI continues to work
		const transparentPngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=";
		return res.status(200).json({ imageBase64: transparentPngBase64, warning: String(e?.message || e) });
	}
});

app.get("/api/stats", (_req, res) => {
	rollUsageDateIfNeeded();
	rollVisitorsDateIfNeeded();
	res.json({
		usage: { today: usage.today, total: usage.total, date: usage.date },
		rate: { perMinute: RATE_LIMIT_PER_MIN, perDay: RATE_LIMIT_PER_DAY },
		visitors: { today: visitors.today, total: visitors.total, date: visitors.date }
	});
});

// Track visitor unique id
app.post("/api/visit", (req, res) => {
	try {
		rollVisitorsDateIfNeeded();
		const vid = (req.body && typeof req.body.vid === 'string') ? req.body.vid : null;
		if (!vid) return res.status(400).json({ error: 'vid_required' });
		if (!visitors.seenEver.has(vid)) {
			// enforce cap on seenEver to avoid unbounded growth
			if (visitors.seenEver.size >= VISITORS_SEEN_EVER_MAX) {
				const first = visitors.seenEver.values().next().value;
				if (first !== undefined) visitors.seenEver.delete(first);
			}
			visitors.seenEver.add(vid);
			visitors.total += 1;
		}
		if (!visitors.seenToday.has(vid)) {
			visitors.seenToday.add(vid);
			visitors.today += 1;
		}
		return res.json({ ok: true, visitors: { today: visitors.today, total: visitors.total } });
	} catch (e) {
		return res.status(500).json({ error: 'visit_failed' });
	}
});

const PORT = process.env.PORT || 5174;
app.listen(PORT, () => console.log(`server on http://localhost:${PORT}`));


