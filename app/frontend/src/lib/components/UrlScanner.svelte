<script lang="ts">
	let {
		onAnalyze,
		loading
	}: {
		onAnalyze: (url: string) => void;
		loading: boolean;
	} = $props();

	let url = '';

	function submit() {
		const trimmed = url.trim();

		if (!trimmed || loading) {
			return;
		}

		onAnalyze(trimmed);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			submit();
		}
	}
</script>

<section class="scanner">

	<div class="scanner-label">
		<span class="label-icon">⌕</span>
		Analyze a URL
	</div>

	<div class="input-row">

		<div class="input-wrapper">

			<span class="input-icon">🔗</span>

			<input
				type="text"
				bind:value={url}
				onkeydown={handleKeydown}
				placeholder="https://example.com"
				disabled={loading}
			/>

			{#if url}
				<button
					class="clear-button"
					onclick={() => (url = '')}
					aria-label="Clear URL"
				>
					×
				</button>
			{/if}

		</div>

		<button
			class="analyze-button"
			onclick={submit}
			disabled={loading || !url.trim()}
		>
			{#if loading}
				<span class="spinner"></span>
				Analyzing...
			{:else}
				Analyze URL
				<span>→</span>
			{/if}
		</button>

	</div>

	<div class="hint">
		Press Enter to analyze · Your URL is processed by the Random Forest model
	</div>

</section>

<style>
	.scanner {
		background: #111827;
		border: 1px solid #1e293b;
		border-radius: 20px;
		padding: 26px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
	}

	.scanner-label {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 14px;
		font-weight: 600;
		color: #e2e8f0;
		margin-bottom: 14px;
	}

	.label-icon {
		color: #60a5fa;
		font-size: 20px;
	}

	.input-row {
		display: flex;
		gap: 12px;
	}

	.input-wrapper {
		flex: 1;
		position: relative;
		display: flex;
		align-items: center;
	}

	.input-icon {
		position: absolute;
		left: 16px;
		font-size: 16px;
	}

	input {
		width: 100%;
		height: 54px;
		box-sizing: border-box;
		padding: 0 45px;
		border: 1px solid #334155;
		border-radius: 12px;
		background: #020617;
		color: #f8fafc;
		font-size: 15px;
		outline: none;
		transition: 0.2s;
	}

	input::placeholder {
		color: #475569;
	}

	input:focus {
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
	}

	input:disabled {
		opacity: 0.6;
	}

	.clear-button {
		position: absolute;
		right: 12px;
		border: none;
		background: transparent;
		color: #64748b;
		font-size: 22px;
		cursor: pointer;
	}

	.analyze-button {
		height: 54px;
		padding: 0 24px;
		border: none;
		border-radius: 12px;
		background: linear-gradient(135deg, #2563eb, #4f46e5);
		color: white;
		font-weight: 700;
		font-size: 14px;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 10px;
		transition: 0.2s;
		white-space: nowrap;
	}

	.analyze-button:hover:not(:disabled) {
		transform: translateY(-1px);
		filter: brightness(1.1);
	}

	.analyze-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.hint {
		margin-top: 12px;
		color: #64748b;
		font-size: 12px;
	}

	.spinner {
		width: 15px;
		height: 15px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 700px) {
		.input-row {
			flex-direction: column;
		}

		.analyze-button {
			justify-content: center;
		}
	}
</style>