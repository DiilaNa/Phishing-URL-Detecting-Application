<script lang="ts">
	import { onMount } from 'svelte';

	import Header from '$lib/components/Header.svelte';
	import UrlScanner from '$lib/components/UrlScanner.svelte';
	import ResultCard from '$lib/components/ResultCard.svelte';
	import HistoryPanel from '$lib/components/HistoryPanel.svelte';
	import ModelInfo from '$lib/components/ModelInfo.svelte';

	import {
		checkHealth,
		getHistory,
		getModelInfo,
		predictUrl
	} from '$lib/services/phishing-api';

	import type {
		HealthStatus,
		HistoryItem,
		ModelInfo as ModelInfoType,
		PredictionResult
	} from '$lib/types/phishing';

	let health = $state<HealthStatus | null>(null);
	let model = $state<ModelInfoType | null>(null);
	let history = $state<HistoryItem[]>([]);
	let result = $state<PredictionResult | null>(null);

	let loading = $state(false);
	let error = $state('');

	async function loadDashboard() {
		try {
			error = '';

			const [healthResponse, modelResponse, historyResponse] =
				await Promise.all([
					checkHealth(),
					getModelInfo(),
					getHistory()
				]);

			health = healthResponse;
			model = modelResponse;
			history = historyResponse.recent_scans;
		} catch (err) {
			console.error('Dashboard loading error:', err);

			error =
				err instanceof Error
					? err.message
					: 'Failed to load dashboard.';
		}
	}

	async function analyzeUrl(url: string) {
		loading = true;
		error = '';
		result = null;

		try {
			result = await predictUrl(url);

			const historyResponse = await getHistory();

			history = historyResponse.recent_scans;
		} catch (err) {
			console.error('URL analysis error:', err);

			error =
				err instanceof Error
					? err.message
					: 'Unable to analyze the URL.';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadDashboard();
	});
</script>

<svelte:head>
	<title>Phishing URL Shield</title>

	<meta
		name="description"
		content="Machine learning powered phishing URL detection"
	/>

	<meta name="theme-color" content="#020617" />
</svelte:head>

<div class="app">

	<Header {health} />

	<main class="container">

		<section class="hero">

			<div class="hero-badge">
				<span>✦</span>
				AI-Powered URL Security
			</div>

			<h1>
				Protect yourself from
				<span>phishing attacks.</span>
			</h1>

			<p>
				Analyze suspicious URLs using a Random Forest machine
				learning model and identify potentially malicious websites
				before you visit them.
			</p>

		</section>

		<UrlScanner
			onAnalyze={analyzeUrl}
			{loading}
		/>

		{#if error}
			<div class="error-message">

				<div class="error-icon">
					!
				</div>

				<div>
					<strong>Analysis failed</strong>

					<p>{error}</p>
				</div>

			</div>
		{/if}

		{#if result}
			<ResultCard {result} />
		{/if}

		<section class="dashboard">

			<HistoryPanel {history} />

			<ModelInfo model={model} />

		</section>

		<section class="features-section">

			<div class="section-heading">

				<div class="hero-badge">
					How it works
				</div>

				<h2>
					Multi-feature URL analysis
				</h2>

				<p>
					The model examines multiple characteristics of a URL
					to determine its phishing risk.
				</p>

			</div>

			<div class="feature-grid">

				<div class="feature-card">

					<div class="feature-number">
						01
					</div>

					<h3>
						URL Structure
					</h3>

					<p>
						Analyzes URL length, dots, hyphens, slashes
						and subdomains.
					</p>

				</div>

				<div class="feature-card">

					<div class="feature-number">
						02
					</div>

					<h3>
						Suspicious Patterns
					</h3>

					<p>
						Detects URL shortening services and
						phishing-related keywords.
					</p>

				</div>

				<div class="feature-card">

					<div class="feature-number">
						03
					</div>

					<h3>
						Domain Analysis
					</h3>

					<p>
						Checks for IP addresses, unusual domain
						patterns and spoofing indicators.
					</p>

				</div>

				<div class="feature-card">

					<div class="feature-number">
						04
					</div>

					<h3>
						ML Prediction
					</h3>

					<p>
						Combines extracted features using the
						Random Forest classifier.
					</p>

				</div>

			</div>

		</section>

	</main>

	<footer>
		<p>
			Phishing URL Shield · Machine Learning Security Project
		</p>
	</footer>

</div>

<style>
	:global(*) {
		box-sizing: border-box;
	}

	:global(html) {
		background: #020617;
	}

	:global(body) {
		margin: 0;
		background: #020617;

		font-family:
			Inter,
			ui-sans-serif,
			system-ui,
			-apple-system,
			BlinkMacSystemFont,
			"Segoe UI",
			sans-serif;
	}

	:global(button),
	:global(input) {
		font-family: inherit;
	}

	.app {
		min-height: 100vh;

		background:
			radial-gradient(
				circle at 50% -10%,
				rgba(37, 99, 235, 0.14),
				transparent 40%
			),
			#020617;

		color: #f8fafc;
	}

	.container {
		width: min(1180px, calc(100% - 48px));

		margin: 0 auto;

		padding: 75px 0 80px;
	}

	.hero {
		max-width: 760px;

		margin: 0 auto 45px;

		text-align: center;
	}

	.hero-badge {
		display: inline-flex;

		align-items: center;

		gap: 7px;

		padding: 7px 12px;

		border-radius: 999px;

		border: 1px solid rgba(96, 165, 250, 0.2);

		background: rgba(59, 130, 246, 0.08);

		color: #60a5fa;

		font-size: 11px;

		font-weight: 600;

		letter-spacing: 0.03em;
	}

	.hero h1 {
		margin: 20px 0 0;

		font-size: clamp(38px, 6vw, 62px);

		line-height: 1.05;

		letter-spacing: -0.045em;
	}

	.hero h1 span {
		display: block;

		background:
			linear-gradient(
				90deg,
				#60a5fa,
				#a78bfa
			);

		-webkit-background-clip: text;

		background-clip: text;

		color: transparent;
	}

	.hero p {
		max-width: 650px;

		margin: 22px auto 0;

		color: #64748b;

		font-size: 16px;

		line-height: 1.7;
	}

	.error-message {
		display: flex;

		align-items: center;

		gap: 12px;

		margin-top: 18px;

		padding: 15px;

		border: 1px solid rgba(239, 68, 68, 0.25);

		border-radius: 12px;

		background: rgba(127, 29, 29, 0.12);

		color: #fca5a5;
	}

	.error-icon {
		width: 30px;
		height: 30px;

		flex: 0 0 auto;

		display: grid;

		place-items: center;

		border-radius: 50%;

		background: rgba(239, 68, 68, 0.15);

		color: #f87171;

		font-weight: bold;
	}

	.error-message strong {
		font-size: 13px;
	}

	.error-message p {
		margin: 3px 0 0;

		font-size: 12px;

		color: #94a3b8;
	}

	.dashboard {
		display: grid;

		grid-template-columns: 1.15fr 0.85fr;

		gap: 18px;

		margin-top: 45px;
	}

	.features-section {
		margin-top: 85px;
	}

	.section-heading {
		text-align: center;

		max-width: 650px;

		margin: 0 auto 30px;
	}

	.section-heading h2 {
		margin: 15px 0 8px;

		font-size: 30px;

		letter-spacing: -0.025em;
	}

	.section-heading p {
		margin: 0;

		color: #64748b;

		font-size: 14px;

		line-height: 1.6;
	}

	.feature-grid {
		display: grid;

		grid-template-columns: repeat(4, 1fr);

		gap: 12px;
	}

	.feature-card {
		padding: 22px;

		border: 1px solid #1e293b;

		border-radius: 15px;

		background: #0f172a;
	}

	.feature-number {
		color: #3b82f6;

		font-size: 11px;

		font-weight: 800;

		letter-spacing: 0.1em;
	}

	.feature-card h3 {
		margin: 15px 0 8px;

		font-size: 15px;
	}

	.feature-card p {
		margin: 0;

		color: #64748b;

		font-size: 12px;

		line-height: 1.6;
	}

	footer {
		border-top: 1px solid #1e293b;

		padding: 25px;

		text-align: center;

		color: #475569;

		font-size: 11px;
	}

	@media (max-width: 850px) {
		.dashboard {
			grid-template-columns: 1fr;
		}

		.feature-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (max-width: 600px) {
		.container {
			width: min(100% - 28px, 1180px);

			padding-top: 45px;
		}

		.feature-grid {
			grid-template-columns: 1fr;
		}

		.hero h1 {
			font-size: 40px;
		}
	}
</style>