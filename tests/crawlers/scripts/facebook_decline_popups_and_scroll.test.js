const { readFileSync } = require("node:fs");
const {
	findCloseButton,
	findDeclineButton,
} = require("@crawlers/scripts/facebook_decline_popups_and_scroll.js");

const cookiesPopupFixture = readFileSync(
	"./tests/crawlers/scripts/fixtures/facebook_cookies_popup.html",
	"utf-8",
);

const loginPopupFixture = readFileSync(
	"./tests/crawlers/scripts/fixtures/facebook_login_popup.html",
	"utf-8",
);

describe("facebook_decline_popups_and_scroll", () => {
	describe("findDeclineButton", () => {
		beforeEach(() => {
			document.body.innerHTML = cookiesPopupFixture;
		});

		it("finds decline button by text content", () => {
			const declineButton = findDeclineButton();

			expect(declineButton).toBeDefined();
			expect(declineButton.textContent).toContain("Decline optional cookies");
		});

		it("does not match allow button", () => {
			const declineButton = findDeclineButton();

			expect(declineButton.textContent).not.toContain("Allow all cookies");
		});

		it("returns undefined when button is missing", () => {
			document.body.innerHTML = "<div>No buttons here</div>";

			const declineButton = findDeclineButton();

			expect(declineButton).toBeUndefined();
		});
	});

	describe("findCloseButton", () => {
		beforeEach(() => {
			document.body.innerHTML = loginPopupFixture;
		});

		it("finds close button by aria-label", () => {
			const closeButton = findCloseButton();

			expect(closeButton).toBeDefined();
			expect(closeButton.getAttribute("aria-label")).toBe("Close");
		});

		it("returns null when button is missing", () => {
			document.body.innerHTML = "<div>No close button</div>";

			const closeButton = findCloseButton();

			expect(closeButton).toBeNull();
		});
	});
});
