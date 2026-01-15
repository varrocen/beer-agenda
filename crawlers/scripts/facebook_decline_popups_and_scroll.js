function findDeclineButton() {
	const buttons = [
		...document.querySelectorAll('div[role="button"], span, button'),
	];
	return buttons.find((button) =>
		button.textContent.includes("Decline optional cookies"),
	);
}

function findCloseButton() {
	return document.querySelector('[aria-label="Close"]');
}

function scrollToBottom() {
	window.scrollTo(0, document.body.scrollHeight);
}

function wait(ms) {
	return new Promise((r) => setTimeout(r, ms));
}

async function declinePopupsAndScroll() {
	// Wait for page to load
	await wait(2000);

	// Decline cookies popup
	const declineButton = findDeclineButton();
	if (declineButton) declineButton.click();

	// Wait for login popup and close it
	await wait(2000);
	const closeButton = findCloseButton();
	if (closeButton) closeButton.click();

	// Scroll to load more content
	await wait(1000);
	scrollToBottom();
}

if (typeof module !== "undefined" && module.exports) {
	module.exports = { findDeclineButton, findCloseButton, scrollToBottom, wait };
} else {
	declinePopupsAndScroll();
}
