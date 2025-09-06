import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { buildScenario, buildEnglishPrompt } from "./boke/scenario.js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json({ limit: "1mb" }));

const PORT = Number(process.env.PORT || 5173);

app.get("/api/health", (_req, res) => {
	res.json({ ok: true });
});

app.get("/api/boke", (_req, res) => {
	const s = buildScenario();
	res.json({
		scenario: s,
		prompt: buildEnglishPrompt(s),
	});
});

// Gemini Images Generation proxy
// Note: Placeholder endpoint. You'll need to plug actual Google AI Images API here.
app.post("/api/generate", async (req, res) => {
	try {
		const { prompt } = req.body as { prompt?: string };
		if (!prompt) {
			return res.status(400).json({ error: "prompt is required" });
		}

		const apiKey = process.env.GEMINI_API_KEY;
		if (!apiKey) {
			return res.status(500).json({ error: "Server missing GEMINI_API_KEY" });
		}

		// TODO: Replace with actual Gemini Images API call.
		// For now, return a 1x1 transparent PNG as placeholder to wire frontend.
		const transparentPngBase64 =
			"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=";
		return res.json({
			imageBase64: transparentPngBase64,
		});
	} catch (err) {
		console.error(err);
		res.status(500).json({ error: "failed to generate image" });
	}
});

app.listen(PORT, () => {
	console.log(`boke server listening on http://localhost:${PORT}`);
});


