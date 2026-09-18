<script lang="ts">
	import type { ModelInfo as ModelInfoType } from '$lib/types/phishing';

	let { model }: { model: ModelInfoType | null } = $props();
</script>

<section class="panel">

	<div class="panel-title">
		<div class="model-icon">⚙</div>

		<div>
			<h3>Model Information</h3>
			<p>Machine learning configuration</p>
		</div>
	</div>

	{#if model}

		<div class="stats">

			<div class="stat">
				<span>Algorithm</span>
				<strong>{model.model_name}</strong>
			</div>

			<div class="stat">
				<span>Accuracy</span>
				<strong>{model.benchmark_test_accuracy}</strong>
			</div>

			<div class="stat">
				<span>F1 Score</span>
				<strong>{model.benchmark_f1_score}</strong>
			</div>

			<div class="stat">
				<span>Features</span>
				<strong>{model.total_features}</strong>
			</div>

			<div class="stat">
				<span>Estimators</span>
				<strong>{model.estimators_count}</strong>
			</div>

		</div>

		<div class="features">
			<div class="features-title">Features used by the model</div>

			<div class="feature-list">

				{#each model.feature_names as feature}
					<span>{feature}</span>
				{/each}

			</div>
		</div>

	{:else}

		<div class="loading">
			Model information unavailable.
		</div>

	{/if}

</section>

<style>
	.panel {
		background: #111827;
		border: 1px solid #1e293b;
		border-radius: 18px;
		padding: 22px;
	}

	.panel-title {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 20px;
	}

	.model-icon {
		width: 38px;
		height: 38px;
		display: grid;
		place-items: center;
		border-radius: 10px;
		background: rgba(99, 102, 241, 0.1);
	}

	h3 {
		margin: 0;
		color: #f1f5f9;
		font-size: 16px;
	}

	.panel-title p {
		margin: 4px 0 0;
		color: #64748b;
		font-size: 12px;
	}

	.stats {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 8px;
	}

	.stat {
		padding: 13px;
		border-radius: 10px;
		background: #0f172a;
	}

	.stat span {
		display: block;
		color: #64748b;
		font-size: 10px;
		text-transform: uppercase;
		margin-bottom: 5px;
	}

	.stat strong {
		color: #cbd5e1;
		font-size: 13px;
	}

	.features {
		margin-top: 18px;
	}

	.features-title {
		color: #64748b;
		font-size: 11px;
		margin-bottom: 9px;
	}

	.feature-list {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.feature-list span {
		padding: 5px 8px;
		border-radius: 6px;
		background: #1e293b;
		color: #94a3b8;
		font-size: 10px;
	}

	.loading {
		color: #64748b;
		font-size: 12px;
	}
</style>