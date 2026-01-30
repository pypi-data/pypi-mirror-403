# messages.py
import random

CHAOS_MESSAGES = {
    0: [
        "Chaos disabled. Boring.",
        "System calm. Too calm.",
        "Everything is fine. Suspiciously fine.",
        "No chaos detected. This feels illegal.",
        "Zen mode activated.",
        "Absolute silence. The code sleeps.",
        "Peaceful execution. Enjoy it while it lasts.",
    ],
    1: [
        "⚠️ Minor chaos introduced. Keys slightly judgmental.",
        "⚠️ Chaos level low. Side effects may include sighing.",
        "⚠️ Mild chaos. Keyboard watching you.",
        "⚠️ Something feels… off.",
        "⚠️ The code knows your mistakes.",
        "⚠️ Warnings whisper softly.",
        "⚠️ Variables are side-eyeing you.",
        "⚠️ Syntax behaving strangely polite.",
        "⚠️ Mild instability detected.",
        "⚠️ This could go either way.",
    ],
    2: [
        "🔥 MAXIMUM CHAOS. MAY THE ODDS BE EVER IN YOUR FAVOR.",
        "🔥 Reality segmentation fault detected.",
        "🔥 Code has achieved self-awareness.",
        "🔥 Undefined behavior is now defined. Poorly.",
        "🔥 Abandon hope, ye who debug here.",
        "🔥 The debugger is afraid of you.",
        "🔥 Stack trace longer than your weekend.",
        "🔥 Heap corruption imminent.",
        "🔥 The logs scream in silence.",
        "🔥 The compiler laughs.",
        "🔥 This was not in the requirements.",
        "🔥 You have angered the runtime gods.",
        "🔥 Core dumped. Spirit shattered.",
        "🔥 The code bites back.",
    ]
}

EXCUSES = [
    "It works on my machine.",
    "Quantum fluctuations broke the code.",
    "The bug ran away when I opened the debugger.",
    "Cosmic rays flipped a bit.",
    "I blame the compiler.",
    "The spec was unclear.",
    "That’s expected behavior. Trust me.",
    "The bug is shy.",
    "Mercury is in retrograde.",
    "Someone touched my code.",
    "It passed yesterday.",
    "We’ll fix it in the next sprint.",
    "That part is legacy.",
    "The test environment is cursed.",
    "This is a known issue.",
    "Works if you don’t look at it.",
    "The demo gods are angry.",
    "It’s only broken on Fridays.",
    "The logs were rotated.",
    "The ticket didn’t mention that.",
    "The requirements changed.",
    "I was testing something.",
    "That’s a feature.",
    "The input was weird.",
    "The user did something unexpected.",
    "The cache needs warming up.",
    "That branch isn’t merged yet.",
]

FACTS = [
    "🐙 Octopuses have three hearts.",
    "🧠 The human brain uses about 20% of the body’s energy.",
    "🐱 Cats sleep for around 70% of their lives.",
    "💻 The first computer bug was an actual moth.",
    "🕒 Programmers are most productive late at night.",
    "🧊 Bananas are radioactive.",
    "🛰️ GPS wouldn’t work without relativity.",
    "🐝 Bees can recognize human faces.",
    "💾 The save icon is a floppy disk. Ancient tech.",
    "⚙️ Most bugs are caused by off-by-one errors.",
    "🌍 Earth isn’t perfectly round.",
    "🧬 Humans share ~60% DNA with bananas.",
    "⌨️ The QWERTY layout was designed to slow typing.",
    "💡 Rubber ducks improve debugging success.",
    "📡 Wi-Fi signals can be blocked by water.",
    "🕳️ Black holes evaporate over time.",
    "⚡ Lightning is hotter than the surface of the sun.",
    "📦 Git was created in under two weeks.",
    "🧪 Code comments rot faster than code.",
    "📈 Premature optimization is the root of all evil.",
]

DAD_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I would tell you a UDP joke, but you might not get it.",
    "Why did the developer go broke? Because he used up all his cache.",
    "Why do Java developers wear glasses? Because they don’t C#.",
    "A SQL query walks into a bar and asks: 'Can I join you?'",
    "Debugging: where you fix one bug and create two.",
    "There are 10 kinds of people: those who understand binary and those who don’t.",
    "I tried to catch fog yesterday. Mist.",
    "Why did the function return early? It was tired.",
    "My code and I are in a complicated relationship.",
    "I named my dog Exception. It keeps getting thrown.",
]

EXIT_MESSAGES = {
    "dramatic": [
        "And so, the program ends… not with a bang, but with a sigh.",
        "The curtain falls. Memory fades.",
        "Execution complete. Meaning unclear.",
        "The process exhales one last time.",
        "All threads join the void.",
    ],
    "theatrical": [
        "🎭 Exiting stage left. Applause optional.",
        "🎭 The show is over. Critics confused.",
        "🎭 Bowing to the terminal.",
        "🎭 Dramatic pause… exit.",
    ],
    "quiet": [
        "Program terminated.",
        "Exit code: 0. Probably.",
        "Goodbye.",
        "Silence.",
    ]
}

REACT_MESSAGES = {
    "late_night": [
        "It’s way too late. Go to sleep, human.",
        "Sleep is a feature, not a bug.",
        "Your future self regrets this.",
        "This commit will age poorly.",
        "Midnight coding detected.",
    ],
    "morning": [
        "Good morning. Coffee first. Code later.",
        "The brain is booting…",
        "Syntax loading slowly.",
        "Morning optimism detected.",
    ],
    "afternoon": [
        "Afternoon grind. Stay strong.",
        "Energy decreasing. Bugs increasing.",
        "Productivity plateau reached.",
        "This is where bugs are born.",
    ],
    "evening": [
        "Evening coding session activated.",
        "This is when legends are written.",
        "Focus mode engaged.",
        "The night belongs to coders.",
    ]
}
