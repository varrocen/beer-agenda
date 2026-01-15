module.exports = {
	testEnvironment: "jsdom",
	modulePathIgnorePatterns: [".venv"],
	moduleNameMapper: {
		"^@crawlers/(.*)$": "<rootDir>/crawlers/$1",
	},
};
