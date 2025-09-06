import express from "express";
import path from "path";
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
const GENAI_TEXT_MODEL = process.env.GENAI_TEXT_MODEL || "gemini-2.5-flash";
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

async function callGeminiText(prompt) {
	const apiKey = process.env.GEMINI_API_KEY;
	if (!apiKey) throw new Error("Server missing GEMINI_API_KEY");
	const url = `${GENAI_BASE}/v1beta/models/${GENAI_TEXT_MODEL}:generateContent?key=${encodeURIComponent(apiKey)}`;
	const resp = await fetch(url, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			contents: [ { parts: [ { text: prompt } ] } ],
			generationConfig: { responseMimeType: "application/json" }
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
		const instruction = [
			"당신은 '보케 시나리오 아키텍트'입니다. 밈 스타일의 보케(일본식 유머) 시나리오를 1개 생성하세요.",
			"목표: '장면 자체의 과한 황당함'이 아니라, 이미지와 한국어 한 줄 캡션(humor_ko) 사이의 아이러니에서 웃음을 만들어야 합니다.",
			"톤: 짧고 공감되는 유머.",
			"원칙: 약간 어긋났지만 가능한 행동. 풍부하고 다양한 상황과 장소",
			"연출: 자연광/현실적 색감/일반 카메라/캔디드·다큐 분위기. ",
			"캡션 톤(한국 인터넷 밈 2023~2025): 짧고 강하며 이미지와 반대로 읽히는 아이러니. 예시 톤(그대로 쓰지 말 것): '오히려 좋아', '현실부정', '현타 온다', '나만 없어', '이게 맞냐', '정신승리', '손절각'.",
			"반환(JSON) 키: title, subject, action, background, expression, image_prompt, humor_ko, why_funny_ko",
			"- title: 한국어 짧은 밈풍 제목(≤16자)",
			"- subject/action/background/expression: 영어, 간결하게",
			"- image_prompt: 영어로 자세히 작성(현실 사진 룩, 자연광, meme-ready 프레이밍). 이미지에 텍스트를 넣지 말 것.",
			"- humor_ko: 한국어 한 줄 캡션(≤28자), 이미지와 의도적 아이러니",
			"- why_funny_ko: 한국어 한 줄로 이미지와 캡션 사이의 아이러니가 왜 웃긴지 설명(≤40자)",
		].join("\n");

		const text = await callGeminiText(instruction);
		const obj = extractJsonObjectFromText(text);
		if (!obj?.image_prompt) {
			return res.status(502).json({ error: "invalid LLM response", raw: text });
		}
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
			prompt: obj.image_prompt,
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


