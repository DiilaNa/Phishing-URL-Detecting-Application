<script lang="ts">
	import type { HealthStatus } from '$lib/types/phishing';

	let { health }: { health: HealthStatus | null } = $props();
</script>

<header class="header">
	<div class="header-inner">

		<div class="brand">
			<div class="brand-icon">
				🛡
			</div>

			<div>
				<div class="brand-name">Phishing URL Shield</div>
				<div class="brand-subtitle">Machine Learning Security</div>
			</div>
		</div>

		<div class="status">

			<span
				class:online={health?.model_loaded}
				class:offline={!health?.model_loaded}
				class="status-dot"
			></span>

			<span>
				{#if health?.model_loaded}
					Model Online
				{:else}
					Model Offline
				{/if}
			</span>

		</div>

	</div>
</header>

<style>
	.header {
		border-bottom: 1px solid #1e293b;
		background: rgba(15, 23, 42, 0.85);
		backdrop-filter: blur(12px);
		position: sticky;
		top: 0;
		z-index: 20;
	}

	.header-inner {
		max-width: 1180px;
		margin: 0 auto;
		padding: 18px 24px;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.brand-icon {
		width: 42px;
		height: 42px;
		display: grid;
		place-items: center;
		border-radius: 12px;
		background: linear-gradient(135deg, #2563eb, #7c3aed);
		font-size: 21px;
	}

	.brand-name {
		font-weight: 700;
		font-size: 16px;
		color: #f8fafc;
	}

	.brand-subtitle {
		color: #64748b;
		font-size: 12px;
		margin-top: 2px;
	}

	.status {
		display: flex;
		align-items: center;
		gap: 8px;
		color: #94a3b8;
		font-size: 13px;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.status-dot.online {
		background: #22c55e;
		box-shadow: 0 0 10px rgba(34, 197, 94, 0.7);
	}

	.status-dot.offline {
		background: #ef4444;
	}
</style>