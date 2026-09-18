<script lang="ts">
	import type { PredictionResult } from '$lib/types/phishing';

	let { result }: { result: PredictionResult } = $props();
</script>

<section
	class:danger={result.is_phishing}
	class:safe={!result.is_phishing}
	class="result-card"
>

	<div class="result-header">

		<div
			class:danger-icon={result.is_phishing}
			class:safe-icon={!result.is_phishing}
			class="result-icon"
		>
			{result.is_phishing ? '!' : '✓'}
		</div>

		<div>
			<div class="result-label">Analysis Result</div>

			<h2>
				{result.is_phishing ? 'Phishing / Malicious' : 'Legitimate / Safe'}
			</h2>
		</div>

	</div>

	<div class="risk-section">

		<div class="risk-header">
			<span>Risk Score</span>
			<strong>{result.risk_score_percentage}%</strong>
		</div>

		<div class="risk-bar">
			<div
				class:danger-bar={result.is_phishing}
				class:safe-bar={!result.is_phishing}
				class="risk-fill"
				style={`width: ${Math.min(result.risk_score_percentage, 100)}%`}
			></div>
		</div>

	</div>

	<div class="url-box">
		<div class="url-label">Analyzed URL</div>
		<div class="url-value">{result.url}</div>
	</div>

	<div class="details">

		<div>
			<span>Prediction</span>
			<strong>{result.status}</strong>
		</div>

		<div>
			<span>Analyzed</span>
			<strong>{result.timestamp}</strong>
		</div>

	</div>

	<div class="notice">
		{#if result.is_phishing}
			⚠ This URL was classified as potentially malicious by the machine learning model.
		{:else}
			✓ This URL was classified as legitimate by the machine learning model.
		{/if}
	</div>

</section>

<style>
	.result-card {
		margin-top: 24px;
		padding: 28px;
		border-radius: 20px;
		background: #111827;
		border: 1px solid #1e293b;
	}

	.result-card.safe {
		border-color: rgba(34, 197, 94, 0.25);
	}

	.result-card.danger {
		border-color: rgba(239, 68, 68, 0.3);
	}

	.result-header {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.result-icon {
		width: 52px;
		height: 52px;
		display: grid;
		place-items: center;
		border-radius: 50%;
		font-size: 25px;
		font-weight: 800;
	}

	.safe-icon {
		background: rgba(34, 197, 94, 0.12);
		color: #4ade80;
	}

	.danger-icon {
		background: rgba(239, 68, 68, 0.12);
		color: #f87171;
	}

	.result-label {
		font-size: 12px;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: #64748b;
	}

	h2 {
		margin: 4px 0 0;
		font-size: 22px;
	}

	.safe h2 {
		color: #4ade80;
	}

	.danger h2 {
		color: #f87171;
	}

	.risk-section {
		margin-top: 30px;
	}

	.risk-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 9px;
		color: #94a3b8;
		font-size: 13px;
	}

	.risk-header strong {
		color: white;
		font-size: 16px;
	}

	.risk-bar {
		height: 10px;
		background: #1e293b;
		border-radius: 20px;
		overflow: hidden;
	}

	.risk-fill {
		height: 100%;
		border-radius: 20px;
		transition: width 0.6s ease;
	}

	.safe-bar {
		background: linear-gradient(90deg, #22c55e, #4ade80);
	}

	.danger-bar {
		background: linear-gradient(90deg, #f97316, #ef4444);
	}

	.url-box {
		margin-top: 25px;
		padding: 16px;
		border-radius: 12px;
		background: #020617;
	}

	.url-label {
		font-size: 11px;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.url-value {
		margin-top: 7px;
		color: #cbd5e1;
		font-size: 14px;
		word-break: break-all;
	}

	.details {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
		margin-top: 16px;
	}

	.details div {
		padding: 14px;
		background: #0f172a;
		border-radius: 10px;
	}

	.details span {
		display: block;
		color: #64748b;
		font-size: 11px;
		margin-bottom: 5px;
	}

	.details strong {
		color: #cbd5e1;
		font-size: 13px;
	}

	.notice {
		margin-top: 20px;
		padding: 13px 15px;
		border-radius: 10px;
		background: #0f172a;
		color: #94a3b8;
		font-size: 12px;
		line-height: 1.5;
	}

	@media (max-width: 600px) {
		.details {
			grid-template-columns: 1fr;
		}
	}
</style>