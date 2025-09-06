export type BokeComponent = {
	subject: string;
	action: string;
	background: string;
	expression: string;
};

const subjects: string[] = [
	"A dignified shogun in full armor",
	"A stoic-faced cyborg from the future",
	"A nervous, timid librarian",
	"An elite secret agent on a mission",
	"A Michelin-starred chef",
	"An ancient, wise wizard",
	"A hyper-focused e-sports player",
];

const actions: string[] = [
	"Eating ramen with a fork and knife",
	"Typing on a keyboard made of popcorn",
	"Trying to insert a giant key into a USB port",
	"Fishing in a bathtub",
	"Using a large fish as a nunchaku",
	"Conducting a serious orchestra with two carrots",
	"Painting a masterpiece using ketchup and mustard",
];

const backgrounds: string[] = [
	"A silent, solemn Zen temple",
	"The bustling NASA mission control room",
	"The middle of a tense bomb disposal situation",
	"A luxurious royal coronation ceremony",
	"The trading floor of the New York Stock Exchange",
	"A quiet, high-stakes chess tournament",
	"Inside a top-secret military briefing room",
];

const expressions: string[] = [
	"Deadpan serious",
	"Intense concentration",
	"Mildly curious",
	"Calm and serene",
	"Genuinely confused but trying to hide it",
];

function pickRandom<T>(items: T[]): T {
	return items[Math.floor(Math.random() * items.length)];
}

export function buildScenario(): BokeComponent {
	return {
		subject: pickRandom(subjects),
		action: pickRandom(actions),
		background: pickRandom(backgrounds),
		expression: pickRandom(expressions),
	};
}

export function buildEnglishPrompt(s: BokeComponent): string {
	return [
		`Ultra-detailed, cinematic illustration of ${s.subject} in ${s.background}.`,
		`With a ${s.expression.toLowerCase()} expression, the subject is ${s.action.toLowerCase()} as if it is perfectly normal.`,
		"Glowing screens and props appropriate to the setting, subtle rim lighting, HDR, 4k, realistic textures, shallow depth of field. No text, no watermark.",
	].join(" ");
}


