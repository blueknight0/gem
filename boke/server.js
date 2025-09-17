import express from "express";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
import cors from "cors";
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

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

const ipBuckets = new Map(); // ip -> { minuteStart: number, minuteCount: number, dayDate: string, dayCount: number }

function rateLimitMiddleware(req, res, next) {
	const ip = req.headers["x-forwarded-for"]?.toString().split(",")[0].trim() || req.socket.remoteAddress || "unknown";
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

function rollVisitorsDateIfNeeded() {
	const d = new Date().toISOString().slice(0, 10);
	if (visitors.date !== d) {
		visitors.date = d;
		visitors.today = 0;
		visitors.seenToday = new Set();
	}
}

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

// --- Famous figures loader
let FAMOUS_FIGURES = [];
function loadFamousFigures() {
	try {
		const mdPath = path.join(__dirname, "famous_historical_figures.md");
		if (!fs.existsSync(mdPath)) return;
		const text = fs.readFileSync(mdPath, "utf-8");
		const lines = text.split(/\r?\n/);
		const re = /^\s*(\d+)\.\s+(.+?)\s+\((.+?)\)\s*$/;
		const arr = [];
		for (const line of lines) {
			const m = line.match(re);
			if (m) {
				const idx = Number(m[1]);
				const name = m[2].trim();
				const era = m[3].trim();
				arr.push({ index: idx, name, era });
			}
		}
		if (arr.length) FAMOUS_FIGURES = arr;
	} catch {}
}
loadFamousFigures();
function pickRandomFigure() {
	if (!FAMOUS_FIGURES.length) return null;
	return FAMOUS_FIGURES[Math.floor(Math.random() * FAMOUS_FIGURES.length)];
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

// API endpoints
app.get("/api/boke", rateLimitMiddleware, async (_req, res) => {
	try {
		const figure = pickRandomFigure();
		const figureName = figure?.name || null;
		const figureEra = figure?.era || null;
		const instruction = [
			"당신은 '쓸데없는 명언 짤' 생성기 기획자입니다. 아래 조건을 만족하는 한 개의 결과를 JSON으로 만드세요.",
			figureName ? `지정 인물: ${figureName} (${figureEra || '시대/연도 미상'})` : "지정 인물: (무작위)",
			"목표: 위 인물의 '그 사람이 하지 않을 법한' 내용을, 명언처럼 보이지만 역설적인 한국어 1~2문장으로 만듭니다.",
			"캡션 형식: 인물명 (생년~사망년|현재)\\n명언문",
			"이미지 연출: 해당 인물을 대표할 법한 배경에서, 반신이 보이는 half-length portrait. 현실감 있는 사진/그림 룩 중 하나. 텍스트는 이미지에 렌더링하지 않습니다(캡션은 별도 오버레이).",
			"품질: 너무 장황하지 말고 간결하게.",
			"반환(JSON) 키: person_ko, birth_year, death_year_or_present, quote_ko, image_prompt, why_ironic_ko",
			"- person_ko: 인물 한국어 이름 (반드시 지정 인물과 동일하게)",
			"- birth_year: 4자리 연도(모르면 대략 추정치도 허용)",
			"- death_year_or_present: 사망년 4자리 또는 '현재'",
			"- quote_ko: 그 인물이 하지 않을 법한, 그러나 명언처럼 보이는 1~2문장. 너무 길지 않게",
			"- image_prompt: 영어로 작성. representative background, half-length portrait, realistic photo or painterly look, candid/portrait framing, no text, no watermark",
			"- why_ironic_ko: 왜 그 인물과 어울리지 않아 웃긴지 1문장 설명",
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
		const person = figureName || obj.person_ko || null;
		const years = (obj.birth_year ? String(obj.birth_year) : "") + "~" + (obj.death_year_or_present ? String(obj.death_year_or_present) : "");
		const paren = years.trim() !== "~" ? `(${years})` : (figureEra ? `(${figureEra})` : null);
		const caption = [
			person ? String(person) : null,
			paren,
		].filter(Boolean).join(" ") + (obj.quote_ko ? "\n" + String(obj.quote_ko) : "");
		return res.json({
			scenario: {
				person: person,
				birthYear: obj.birth_year || null,
				deathYear: obj.death_year_or_present || null,
				quote: obj.quote_ko || null,
			},
			prompt: diversifiedPrompt,
			humor: caption || null,
			caption: caption || null,
			whyFunny: obj.why_ironic_ko || null,
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

const PORT = process.env.PORT || 5173;
app.listen(PORT, () => console.log(`server on http://localhost:${PORT}`));


